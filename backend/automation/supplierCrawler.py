import asyncio
import os
import re
from typing import List, Dict, Any, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

LOAD_MORE_WAIT_SECONDS = float(os.getenv("LOAD_MORE_WAIT_SECONDS", "2.0"))
INFINITE_SCROLL_WAIT_SECONDS = float(os.getenv("INFINITE_SCROLL_WAIT_SECONDS", "1.5"))

TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "_pos",
    "_sid",
    "_ss",
    "_fid",
    "searchid",
    "search_query",
    "section",
}


def normalize_product_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
        if not parsed.scheme or not parsed.netloc:
            return raw

        filtered_qs = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if key.lower() in TRACKING_QUERY_KEYS:
                continue
            filtered_qs.append((key, value))

        normalized_path = parsed.path or "/"
        if normalized_path != "/" and normalized_path.endswith("/"):
            normalized_path = normalized_path[:-1]

        return urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                normalized_path,
                parsed.params,
                urlencode(filtered_qs, doseq=True),
                "",
            )
        )
    except Exception:
        return raw.split("#")[0].strip()

async def fetch_product_links_from_page(page) -> List[Dict]:
    """Extrai links de produtos baseados em heurísticas comuns em sites B2B/fornecedores."""
    
    # 1. Tentar pegar cards genéricos
    links = []
    
    js_extract = """
    () => {
        const results = [];
        const selectors = [
            '.product-item a', '.product-card a', 'li.item a',
            '.grid-item a', '.product a', 'article a', 'a.product-link'
        ];

        const outOfStockTexts = ['sold out', 'out of stock', 'esgotado', 'indisponível'];

        function isOutOfStock(element) {
            const text = (element.innerText || "").toLowerCase();
            return outOfStockTexts.some(oos => text.includes(oos));
        }

        function isActionUrl(href) {
            if (!href) return false;
            const lower = href.toLowerCase();
            return lower.includes('cart.php?action=')
                || lower.includes('/cart/add')
                || lower.includes('add-to-cart')
                || lower.includes('addtocart')
                || lower.includes('/wishlist/')
                || lower.includes('action=add')
                || lower.includes('/checkout')
                || lower.includes('login')
                || lower.includes('account')
                || lower.match(/^(mailto:|tel:|javascript:)/);
        }

        function extractPrice(card) {
            if (!card) return "";
            const priceSelectors = [
                '.price .price--withoutTax',
                '.price-section .price--withoutTax',
                '[data-product-price-without-tax]',
                '.price--main',
                '.price--withoutTax',
                '.price .amount',
                '.price-value',
                '.current-price',
                '.sale-price',
                '.regular-price',
                '.price, [class*="price"], .amount'
            ];
            for (const sel of priceSelectors) {
                const el = card.querySelector(sel);
                if (el) {
                    const txt = (el.innerText || el.textContent || "").trim();
                    if (txt && /\d/.test(txt)) return txt;
                }
            }
            const allPriceEls = card.querySelectorAll('.price, [class*="price"], .amount');
            for (const el of allPriceEls) {
                const txt = (el.innerText || el.textContent || "").trim();
                if (txt && /\$[\d.,]+/.test(txt)) return txt;
            }
            return "";
        }

        for (const sel of selectors) {
            document.querySelectorAll(sel).forEach(el => {
                if (!el.href || isActionUrl(el.href)) return;
                if (results.find(x => x.url === el.href)) return;

                const card = el.closest('.product-item, .product-card, li.item, .grid-item, .product, article');

                if (card && isOutOfStock(card)) return;

                const priceText = extractPrice(card);
                results.push({url: el.href, price_text: priceText});
            });
            if (results.length > 0) break;
        }

        if(results.length === 0) {
           document.querySelectorAll('a[href]').forEach(el => {
                if (isActionUrl(el.href)) return;
                const href = el.href.toLowerCase();
                if(href.includes('/product/') || href.includes('/p/') || href.includes('/item/')) {
                    const container = el.parentElement || el;
                    if (!isOutOfStock(container)) {
                        results.push({url: el.href, price_text: ""});
                    }
                }
           });
        }
        return results;
    }
    """
    try:
        raw_links = await page.evaluate(js_extract)
        # Filter duplicates and base URLs
        seen = set()
        for item in raw_links:
            u = normalize_product_url(item.get("url", ""))
            if u not in seen:
                seen.add(u)
                links.append(item)
    except Exception as e:
        print(f"Erro extraindo links da listagem: {e}")
        
    return links

async def find_next_page(page) -> str:
    """Procura por botões de NEXT ou '>' e clica. Se mudou de URL, retorna a nova.
    Também tenta clicar em 'Show More' ou dar scroll. Se isso carregar itens novos, retorna 'SAME_PAGE'.
    """
    curr_url = page.url
    
    # 1. Tentar botões de "Load More" na mesma página
    js_load_more = """
    () => {
        const texts = ['show more', 'load more', 'carregar mais', 'mostrar mais', 'view more', 'show more products'];
        const elements = Array.from(document.querySelectorAll('button, a, span, div.btn'));
        for (let el of elements) {
            const t = (el.innerText || "").toLowerCase().trim();
            for (let target of texts) {
                if (t === target || t.includes(target)) {
                    // Verifica se element ta visivel
                    if (el.offsetWidth > 0 && el.offsetHeight > 0) {
                        el.click();
                        return true;
                    }
                }
            }
        }
        return false;
    }
    """
    try:
        clicked = await page.evaluate(js_load_more)
        if clicked:
            await asyncio.sleep(max(0.5, LOAD_MORE_WAIT_SECONDS)) # Espera novo conteudo renderizar
            return "SAME_PAGE"
    except Exception as e:
        print(f"Erro no auto-click show more: {e}")

    # 2. Tentar scroll infinito
    try:
        # Pega a altura atual
        prev_height = await page.evaluate("document.body.scrollHeight")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(max(0.5, INFINITE_SCROLL_WAIT_SECONDS)) # Espera rolagem async
        new_height = await page.evaluate("document.body.scrollHeight")
        # Se a pagina cresceu, entao rolou infinite scroll
        if new_height > prev_height:
            return "SAME_PAGE"
    except Exception as e:
        pass

    # 3. Tentar next page tradicional
    js_next = """
    () => {
        const nextTexts = ['next', 'próxima', '>>', '>', 'next page'];
        const links = Array.from(document.querySelectorAll('a'));
        for(let a of links) {
            const t = (a.innerText || "").toLowerCase().trim();
            if(nextTexts.includes(t) || t === 'next') {
                if(a.href) return a.href;
            }
        }
        // Fallback p/ classes de seta
        const nextClass = document.querySelector('.next, .pagination-next, [rel="next"]');
        if(nextClass && nextClass.href) return nextClass.href;
        return null;
    }
    """
    try:
        nxt_href = await page.evaluate(js_next)
        if nxt_href and nxt_href != curr_url:
            return nxt_href
    except:
        pass
        
    return None

def parse_price_details(price_text: str) -> Dict[str, Any]:
    raw = (price_text or "").strip()
    if not raw:
        return {"value": None, "status": "missing", "raw": raw}

    text = raw.lower()
    if any(token in text for token in ("contact", "sob consulta", "call for price", "request quote")):
        return {"value": None, "status": "inquiry", "raw": raw}

    # Mantém apenas números, ponto e vírgula para tentar parse robusto.
    number_match = re.search(r"[\d\.,]+", raw)
    if not number_match:
        return {"value": None, "status": "invalid_format", "raw": raw}

    candidate = number_match.group(0).strip()
    if "," in candidate and "." in candidate:
        # Usa o último separador como decimal.
        if candidate.rfind(",") > candidate.rfind("."):
            candidate = candidate.replace(".", "").replace(",", ".")
        else:
            candidate = candidate.replace(",", "")
    elif "," in candidate:
        candidate = candidate.replace(",", ".")

    try:
        value = float(candidate)
    except (TypeError, ValueError):
        return {"value": None, "status": "parse_error", "raw": raw}

    if value == 0:
        return {"value": 0.0, "status": "zero", "raw": raw}
    return {"value": value, "status": "ok", "raw": raw}


def parse_price(price_text: str) -> float:
    info = parse_price_details(price_text)
    value: Optional[float] = info.get("value")
    if value is None:
        return 0.0
    return float(value)
