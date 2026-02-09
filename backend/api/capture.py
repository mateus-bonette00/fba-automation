from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page
import asyncio, re, json, gc, os, httpx, unicodedata
from urllib.parse import urlparse, urljoin, parse_qs
from .upc_extractor import UPCExtractor
from .title_extractor import TitleExtractor

router = APIRouter()

# ===================== Regex / Utils =====================
UPC_INLINE_RE = re.compile(
    r"(?:\bUPC\b|\bGTIN-?1[2-4]\b|\bGTIN\b|\bBarcode\b|\buniversal product code\b)\D*?(\d{8}|\d{12,14})",
    re.I,
)
DIGITS = re.compile(r"\D+")

def _only_digits(s: str) -> str:
    return DIGITS.sub("", s or "")

def _normalize_upc(s: str) -> Optional[str]:
    d = _only_digits(s)
    if len(d) in (8, 12, 13, 14):
        return d
    m = re.search(r"(\d{12,14})", d)
    return m.group(1) if m else None

def _pick_title(candidates: List[str]) -> str:
    for t in candidates:
        t = (t or "").strip()
        if t:
            return t
    return "Sem título"

def _find_upc_in_obj(o: Any) -> Optional[str]:
    if isinstance(o, dict):
        for k, v in o.items():
            lk = str(k).lower()
            if any(x in lk for x in ["gtin", "gtin12", "gtin13", "gtin14", "upc", "barcode"]):
                u = _normalize_upc(str(v))
                if u:
                    return u
        # aninhados comuns
        for k in (
            "offers", "product", "item", "data", "props", "pageProps",
            "productInfo", "details", "attributes", "variants", "items"
        ):
            if k in o:
                u = _find_upc_in_obj(o[k])
                if u:
                    return u
        # percorre demais valores
        for v in o.values():
            u = _find_upc_in_obj(v)
            if u:
                return u
    elif isinstance(o, list):
        for item in o:
            u = _find_upc_in_obj(item)
            if u:
                return u
    return None

def _norm_text(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s.strip().lower())
    return s

# ---------- domínio-base (aceita subdomínios) ----------
def _base_domain(host: str) -> str:
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) >= 3:
        return ".".join(parts[-2:]).lower()
    return host.lower()

def _same_site(host: str, ref_host: str) -> bool:
    return _base_domain(host) == _base_domain(ref_host)

# ===================== Cache =====================
CACHE_PATH = os.getenv("UPC_CACHE_PATH", "upc_cache.json")

def _load_cache() -> Dict[str, str]:
    try:
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_cache(cache: Dict[str, str]) -> None:
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _cache_key(url: str) -> str:
    u = urlparse(url)
    # Inclui query parameters para diferenciar produtos com IDs diferentes
    key = f"{u.netloc}{u.path}"
    if u.query:
        key += f"?{u.query}"
    return key.rstrip("/").lower() or url.lower()

# ===================== Título robusto =====================
async def _robust_page_title(page: Page, timeout_ms: int = 1600) -> str:
    try:
        t = await asyncio.wait_for(page.title(), timeout=timeout_ms/1000)
        if t and t.strip():
            return t.strip()
    except Exception:
        pass
    try:
        t = await page.evaluate("document.title || ''", timeout=timeout_ms)
        if t and t.strip():
            return t.strip()
    except Exception:
        pass
    try:
        js = """
(() => {
  const pick = (sel) => {
    const el = document.querySelector(sel);
    return el ? (el.content || el.textContent || '').trim() : '';
  };
  return pick('meta[property="og:title"]') || pick('meta[name="twitter:title"]') || '';
})()
"""
        t = await page.evaluate(js, timeout=timeout_ms)
        if t and t.strip():
            return t.strip()
    except Exception:
        pass
    return ""

# ===================== Leitura rápida do DOM =====================
async def _read_quick(page: Page, timeout_ms: int = 1800) -> Dict[str, Any]:
    js = """
(() => {
  const out = {};
  const pick = (sel) => {
    const el = document.querySelector(sel);
    return el ? (el.content || el.textContent || '').trim() : '';
  };

  // candidatos a título
  out.meta_og = pick('meta[property="og:title"]');
  out.meta_tw = pick('meta[name="twitter:title"]');
  out.h1 = (() => {
    const el = document.querySelector('h1.pdp-title, h1.product_title, h1[itemprop="name"], h1.entry-title, h1');
    return el ? el.textContent.trim() : '';
  })();
  out.itemprop_name = pick('[itemprop="name"]');

  // json-ld
  out.jsonld = [];
  document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
    if (s.textContent) out.jsonld.push(s.textContent.trim());
  });

  // metas gtin/upc
  out.meta_gtin = [];
  document.querySelectorAll('meta[itemprop], meta[name], meta[property]').forEach(m => {
    const name = (m.getAttribute('itemprop') || m.getAttribute('name') || m.getAttribute('property') || '').toLowerCase();
    if (name.includes('gtin') || name.includes('upc') || name.includes('barcode')) {
      out.meta_gtin.push({ name, content: (m.getAttribute('content') || '').trim() });
    }
  });

  // scripts inteiros (para dataLayer/__NEXT_DATA__/window.__*)
  out.scripts = [];
  document.querySelectorAll('script').forEach(s => {
    const txt = (s.textContent || '').trim();
    if (txt) out.scripts.push(txt.slice(0, 250000));
  });

  // texto visível (limitado)
  const main = document.querySelector('main') || document.body;
  out.text = (main.innerText || '').slice(0, 180000);

  // URLs candidatas em <script>
  out.script_urls = [];
  const re = /["'](https?:\\/\\/[^"']+?|\\/.+?)(?=["'])/ig;
  for (const s of document.querySelectorAll('script')) {
    const t = (s.textContent || '');
    if (!t) continue;
    const matches = t.matchAll(re);
    for (const m of matches) out.script_urls.push(m[1]);
  }

  // Recursos de rede carregados
  out.res_urls = [];
  try {
    const perf = performance.getEntriesByType('resource') || [];
    for (const e of perf) if (e.name && typeof e.name === 'string') out.res_urls.push(e.name);
  } catch {}

  // links diretos na página
  out.link_urls = [];
  document.querySelectorAll('[href],[src]').forEach(el => {
    const u = el.getAttribute('href') || el.getAttribute('src');
    if (u) out.link_urls.push(u);
  });

  // alguns blobs comuns no window (strings JSON serializáveis)
  out.window_blobs = {};
  try {
    const keys = [
      '__NEXT_DATA__', '__APOLLO_STATE__', '__NUXT__',
      'Shopify', 'ShopifyAnalytics', 'dataLayer',
      '__INITIAL_STATE__', 'INITIAL_STATE', 'drupalSettings'
    ];
    keys.forEach(k => {
      if (window[k]) {
        try { out.window_blobs[k] = JSON.stringify(window[k]).slice(0, 300000); } catch (e) {}
      }
    });
  } catch {}

  return out;
})()
"""
    data = {}
    try:
        data = await page.evaluate(js, timeout=timeout_ms)
    except Exception:
        data = {
            "jsonld": [], "meta_gtin": [], "scripts": [], "text": "",
            "script_urls": [], "res_urls": [], "link_urls": [], "window_blobs": {}
        }

    try:
        data["doc_title"] = await _robust_page_title(page, timeout_ms)
    except Exception:
        data.setdefault("doc_title", "")

    return data

def _extract_title(data: Dict[str, Any]) -> str:
    return _pick_title([
        data.get("meta_og"),
        data.get("meta_tw"),
        data.get("h1"),
        data.get("itemprop_name"),
        data.get("doc_title"),
    ])

def _try_jsons(payloads: List[str]) -> Optional[str]:
    for raw in payloads or []:
        try:
            o = json.loads(raw)
        except Exception:
            m = re.findall(r'["\'](gtin(?:12|13|14)?|upc|barcode)["\']\s*:\s*["\']?(\d{8}|\d{12,14})["\']?', raw, flags=re.I)
            if m:
                return _normalize_upc(m[0][1])
            continue
        u = _find_upc_in_obj(o)
        if u:
            return u
    return None

def _extract_upc_local(data: Dict[str, Any]) -> Tuple[Optional[str], str]:
    # 1) json-ld
    u = _try_jsons(data.get("jsonld"))
    if u: return u, "json-ld"
    # 2) metas
    for m in data.get("meta_gtin", []):
        u = _normalize_upc(m.get("content", ""))
        if u: return u, "meta"
    # 3) window blobs (Shopify / Next / dataLayer / Nuxt / Drupal)
    if isinstance(data.get("window_blobs"), dict) and data["window_blobs"]:
        u = _try_jsons(list(data["window_blobs"].values()))
        if u: return u, "window"
    # 4) scripts inteiros
    u = _try_jsons(data.get("scripts"))
    if u: return u, "script"
    # 5) texto visível
    m = UPC_INLINE_RE.search(data.get("text") or "")
    if m:
        cand = _normalize_upc(m.group(1))
        if cand: return cand, "text"
    return None, ""

# ---------- candidatos “mesmo domínio-base” ----------
KEY_HINTS = ("api", "ajax", "json", "product", "item", "variant", "catalog", "v1", "v2", "graphql")

def _looks_jsonish(url: str) -> bool:
    u = url.lower()
    if ".json" in u: return True
    if "/api/" in u or "/ajax/" in u: return True
    if any(h in u for h in KEY_HINTS): return True
    # query string com "json=1" ou "format=json"
    try:
        qs = parse_qs(urlparse(url).query)
        if "json" in qs or qs.get("format", [""])[0] == "json":
            return True
    except Exception:
        pass
    return False

def _same_domain_candidates(product_url: str, data: Dict[str, Any], aggressive: bool) -> List[str]:
    u = urlparse(product_url)
    origin = f"{u.scheme}://{u.netloc}"

    raw_urls = set()
    for lst in (data.get("script_urls", []), data.get("res_urls", []), data.get("link_urls", [])):
        for s in lst:
            if s:
                raw_urls.add(s.strip())

    cands: List[str] = []
    for raw in raw_urls:
        try:
            url = raw.strip().strip('"\'')
            if url.startswith("//"):
                url = f"{u.scheme}:{url}"
            if url.startswith("/"):
                url = urljoin(origin, url)
            host = urlparse(url).netloc
            if host and _same_site(host, u.netloc):
                if _looks_jsonish(url) or aggressive:
                    cands.append(url)
        except Exception:
            continue

    # remove duplicadas
    seen = set()
    uniq = []
    for x in cands:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

async def _fetch_json_inside_page(page: Page, url: str, timeout_ms: int) -> Optional[str]:
    js = """
async (url, ms) => {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), ms);
  try {
    const r = await fetch(url, {
      credentials: 'include',
      headers: { 'accept': 'application/json,text/*' },
      signal: controller.signal
    });
    const txt = await r.text();
    return txt.slice(0, 500000);
  } catch (e) {
    return null;
  } finally {
    clearTimeout(t);
  }
}
"""
    try:
        txt = await page.evaluate(js, url, timeout_ms)
        return txt
    except Exception:
        return None

async def _detect_product_apis(page: Page, timeout_ms: int = 2000) -> List[str]:
    """Detecta APIs de produto analisando requisições de rede"""
    detected_apis = []

    js = """
    async (ms) => {
        const apis = [];
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.initiatorType === 'xmlhttprequest' || entry.initiatorType === 'fetch') {
                    const url = entry.name.toLowerCase();
                    // Detecta padrões comuns de API de produto
                    if (url.includes('product') || url.includes('item') ||
                        url.includes('api') || url.includes('catalog') ||
                        url.includes('detail') || url.includes('info') ||
                        url.includes('.json') || url.includes('/ajax/')) {
                        apis.push(entry.name);
                    }
                }
            }
        });
        observer.observe({ entryTypes: ['resource'] });

        // Aguarda um pouco para capturar requisições
        await new Promise(resolve => setTimeout(resolve, ms));
        observer.disconnect();

        return [...new Set(apis)];  // Remove duplicatas
    }
    """

    try:
        detected = await page.evaluate(js, timeout_ms)
        if detected:
            detected_apis.extend(detected)
    except Exception:
        pass

    return detected_apis

async def _same_domain_probe(product_url: str, page: Page, data: Dict[str, Any],
                             timeout_ms: int = 3500, max_urls: int = 12,
                             aggressive: bool = False) -> Optional[Tuple[str,str]]:
    # Tenta detectar APIs de produto automaticamente
    detected_apis = await _detect_product_apis(page, 1500)

    # Combina APIs detectadas com candidatos estáticos
    cands = _same_domain_candidates(product_url, data, aggressive)

    # Prioriza APIs detectadas (mais chances de ter UPC)
    all_candidates = detected_apis + [c for c in cands if c not in detected_apis]

    if not all_candidates:
        return None

    tried = 0
    for url in all_candidates:
        if tried >= max_urls:
            break
        tried += 1
        txt = await _fetch_json_inside_page(page, url, timeout_ms)
        if not txt:
            continue
        try:
            js = json.loads(txt)
            upc = _find_upc_in_obj(js)
            if upc:
                return upc, f"same-domain:{url}"
        except Exception:
            pass
        m = re.search(
            r'(gtin(?:12|13|14)?|upc|barcode|universal product code)["\']?\s*[:=]\s*["\']?(\d{8}|\d{12,14})',
            txt, flags=re.I
        )
        if m:
            upc = _normalize_upc(m.group(2))
            if upc:
                return upc, f"same-domain:{url}"
    return None

# ===================== Extração da página =====================
async def _extract_page_fast(page: Page, timeout_ms: int = 1800) -> Dict[str, Any]:
    # OTIMIZAÇÃO: Removido scroll e sleep - muito lento!
    # Scroll na página para carregar conteúdo lazy-loaded (DESABILITADO para velocidade)
    # try:
    #     await page.evaluate("""
    #         () => {
    #             window.scrollTo(0, document.body.scrollHeight / 2);
    #             window.scrollTo(0, document.body.scrollHeight);
    #             window.scrollTo(0, 0);
    #         }
    #     """)
    #     await asyncio.sleep(0.5)
    # except Exception:
    #     pass

    d = await _read_quick(page, timeout_ms)

    # Extração de título - método rápido
    title = _extract_title(d)

    # Extração de UPC - método rápido primeiro
    upc, source = _extract_upc_local(d)

    # Variável para armazenar HTML (pega apenas uma vez)
    html = None

    # Se não achou UPC pelo método rápido, usa extrator avançado
    if not upc:
        try:
            html = await page.content()
            if html:
                # Usa extrator de UPC completo (BeautifulSoup) - TODOS os 26+ métodos
                extractor = UPCExtractor()
                upc_advanced = extractor.extract_all_methods(html)
                if upc_advanced:
                    upc = upc_advanced
                    source = f"advanced:{extractor.method_used}" if extractor.method_used else "advanced"
        except Exception:
            pass

    # Se não achou título adequado, tenta extrator avançado de título
    if not title or title == "Sem título":
        try:
            # Se ainda não pegou HTML, pega agora
            if not html:
                html = await page.content()

            if html:
                from .title_extractor import TitleExtractor
                title_extractor = TitleExtractor()
                title_advanced = title_extractor.extract_all_methods(html)
                if title_advanced and title_advanced != "Sem título":
                    title = title_advanced
        except Exception:
            pass

    result = {
        "_raw": d,
        "product_title": title or "Sem título",
        "upc": upc or "",
        "upc_method": source or ""
    }

    return result

# ===================== Rotas =====================
@router.get("/browser-status")
async def browser_status(devtools_url: str = "http://127.0.0.1:9222"):
    try:
        import requests
        r = requests.get(devtools_url + "/json/version", timeout=5)
        return {"status": "online" if r.status_code == 200 else "offline"}
    except Exception:
        return {"status": "offline"}

@router.get("/list-tabs")
async def list_tabs(devtools_url: str = "http://127.0.0.1:9222"):
    """Lista todas as abas abertas no navegador para debug"""
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(devtools_url)

            all_tabs = []
            for ctx in browser.contexts:
                for p in ctx.pages:
                    url = p.url or ""
                    title = ""
                    try:
                        title = await p.title()
                    except:
                        title = "Sem título"

                    all_tabs.append({
                        "url": url,
                        "title": title
                    })

            await browser.close()

            return {
                "total": len(all_tabs),
                "tabs": all_tabs
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao listar abas: {e}")

@router.post("/capture-tabs")
async def capture_tabs(
    devtools_url: str,
    include_pattern: str = "",
    exclude_pattern: str = "",
    fast: int = 1,
    concurrency: int = 15,          # OTIMIZADO: 15 paralelos (balanceado)
    per_page_timeout_ms: int = 3000, # OTIMIZADO: 3s (balanceado)
    skip: int = 0,
    limit: int = 500,
    pause_ms: int = 0,              # ZERO delay
    same_domain_probe: int = 0,     # DESABILITADO
    aggressive_probe: int = 0,
    use_cache: int = 1,
    debug: int = 0
):
    """
    Genérico: filtra por include/exclude (regex), processa em lotes, extrai título/UPC
    de múltiplas fontes e caça JSONs do mesmo domínio-base (subdomínios incluídos).
    """
    try:
        include_re = re.compile(include_pattern, re.I) if include_pattern else None
        exclude_re = re.compile(exclude_pattern, re.I) if exclude_pattern else None

        local_cache = _load_cache() if use_cache else {}

        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(devtools_url)

            # lista e filtra abas
            all_pages: List[Page] = []

            # Padrões para ignorar automaticamente (páginas internas, dev tools, etc)
            auto_exclude_patterns = [
                r'about:',
                r'chrome://',
                r'chrome-extension://',
                r'opera://',           # Páginas internas do Opera
                r'devtools://',
                r'localhost:9222',
            ]
            auto_exclude_re = re.compile('|'.join(auto_exclude_patterns), re.I)

            for ctx in browser.contexts:
                for p in ctx.pages:
                    url = p.url or ""

                    # Ignora páginas vazias e internas automaticamente
                    if not url or url.strip() == "" or auto_exclude_re.search(url):
                        continue

                    # Aplica filtros do usuário
                    if include_re and not include_re.search(url):
                        continue
                    if exclude_re and exclude_re.search(url):
                        continue

                    all_pages.append(p)

            total = len(all_pages)
            if total == 0:
                await browser.close()
                return {"total": 0, "tabs": [], "has_more": False, "next_skip": None}

            # janela do lote
            start = max(0, int(skip))
            end = min(total, start + max(1, int(limit)))
            pages = all_pages[start:end]

            sem = asyncio.Semaphore(max(1, int(concurrency)))
            cache_lock = asyncio.Lock()  # Proteção para acesso ao cache compartilhado
            results: List[Dict[str, Any]] = []

            async def process(p: Page):
                async with sem:
                    url = p.url or ""
                    try:
                        # OTIMIZAÇÃO: Não espera load state - usa o conteúdo atual da página
                        # Se fast mode está ativado, pula wait_for_load_state completamente
                        if not fast:
                            try:
                                await p.wait_for_load_state("domcontentloaded", timeout=per_page_timeout_ms)
                            except Exception:
                                pass

                        data = await _extract_page_fast(p, per_page_timeout_ms)
                        raw = data.pop("_raw", {})

                        # 1) cache (com proteção de concorrência)
                        ck = _cache_key(url)
                        if use_cache and not data.get("upc"):
                            async with cache_lock:
                                if ck in local_cache:
                                    cached = local_cache.get(ck)
                                    # Só usa cache se o UPC for válido (não começar com muitos zeros)
                                    if (cached and _normalize_upc(cached) and
                                        not cached.startswith("00000000") and
                                        cached not in ["000000000044", "00000000", "0000000000"]):
                                        data["upc"] = _normalize_upc(cached) or ""
                                        data["upc_method"] = data.get("upc_method") or "cache"

                        # 2) probe de mesmo domínio-base
                        if same_domain_probe and not data.get("upc"):
                            try:
                                pr = await _same_domain_probe(
                                    url, p, raw,
                                    timeout_ms=3500,
                                    max_urls=12 if aggressive_probe else 8,
                                    aggressive=bool(aggressive_probe)
                                )
                                if pr:
                                    upc, origin = pr
                                    data["upc"] = upc
                                    data["upc_method"] = data.get("upc_method") or origin
                            except Exception:
                                pass

                        # 3) grava cache se achou UPC VÁLIDO (com proteção de concorrência)
                        if use_cache and data.get("upc"):
                            upc_val = data["upc"]
                            # Não salva UPCs obviamente inválidos (zeros, muito curtos, etc)
                            if (len(upc_val) >= 8 and
                                upc_val not in ["000000000044", "00000000", "0000000000", "000000000000"] and
                                not upc_val.startswith("00000000")):
                                async with cache_lock:
                                    local_cache[ck] = data["upc"]

                        data["url"] = url

                        # Remove informações de debug se não solicitado
                        if not debug and "_debug" in data:
                            del data["_debug"]

                        results.append(data)
                    except Exception as e:
                        results.append({"product_title": "Sem título", "upc": "", "upc_method": "", "url": url})
                    finally:
                        if pause_ms > 0:
                            await asyncio.sleep(pause_ms/1000.0)

            await asyncio.gather(*(process(p) for p in pages))
            results.sort(key=lambda x: x.get("url", ""))

            await browser.close()
            gc.collect()

            if use_cache:
                _save_cache(local_cache)

            has_more = end < total
            next_skip = end if has_more else None

            return {
                "total": total,
                "processed": len(results),
                "skip": start,
                "limit": end - start,
                "has_more": has_more,
                "next_skip": next_skip,
                "tabs": results
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao capturar abas: {e}")
