import asyncio
import argparse
import json
import os
import sys
import logging
import time
from playwright.async_api import async_playwright
from datetime import datetime
from urllib.parse import urlparse

# Modifica o path para achar as pastas locais
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.state import load_state, save_state, clear_supplier_state
from automation.sheets import get_next_supplier
from automation.supplierCrawler import (
    fetch_product_links_from_page,
    parse_price_details,
    find_next_page,
    normalize_product_url,
)
from automation.captureRunner import call_capture_api
from automation.exporter import export_to_xlsx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CAPTCHA_MAX_WAIT_SECONDS = int(os.getenv("CAPTCHA_MAX_WAIT_SECONDS", "900"))
NO_SUPPLIER_CONFIRM_ATTEMPTS = int(os.getenv("NO_SUPPLIER_CONFIRM_ATTEMPTS", "3"))
NO_SUPPLIER_CONFIRM_DELAY_SECONDS = int(os.getenv("NO_SUPPLIER_CONFIRM_DELAY_SECONDS", "20"))
SHEETS_ERROR_RETRY_SECONDS = int(os.getenv("SHEETS_ERROR_RETRY_SECONDS", "30"))
MAX_CONSECUTIVE_CAPTURE_FAILURES = int(os.getenv("MAX_CONSECUTIVE_CAPTURE_FAILURES", "5"))
TAB_OPEN_TIMEOUT_MS = int(os.getenv("TAB_OPEN_TIMEOUT_MS", "15000"))
TAB_OPEN_DELAY_SECONDS = float(os.getenv("TAB_OPEN_DELAY_SECONDS", "0.05"))
TAB_OPEN_MAX_PARALLEL = int(os.getenv("TAB_OPEN_MAX_PARALLEL", "4"))
TAB_OPEN_PARALLEL_LOW_MEM = int(os.getenv("TAB_OPEN_PARALLEL_LOW_MEM", "2"))
LIST_PAGE_SETTLE_SECONDS = float(os.getenv("LIST_PAGE_SETTLE_SECONDS", "1.2"))
POST_BATCH_SETTLE_SECONDS = float(os.getenv("POST_BATCH_SETTLE_SECONDS", "0.25"))
MIN_DYNAMIC_BATCH_SIZE = int(os.getenv("MIN_DYNAMIC_BATCH_SIZE", "4"))
BATCH_DOWNSHIFT_FAILURE_RATIO = float(os.getenv("BATCH_DOWNSHIFT_FAILURE_RATIO", "0.5"))
MAX_CONSECUTIVE_OPEN_FAILURE_BATCHES = int(os.getenv("MAX_CONSECUTIVE_OPEN_FAILURE_BATCHES", "4"))
URL_FAILURE_QUARANTINE_THRESHOLD = int(os.getenv("URL_FAILURE_QUARANTINE_THRESHOLD", "3"))
DOMAIN_FAILURE_QUARANTINE_THRESHOLD = int(os.getenv("DOMAIN_FAILURE_QUARANTINE_THRESHOLD", "7"))
URL_QUARANTINE_MINUTES = int(os.getenv("URL_QUARANTINE_MINUTES", "720"))
DOMAIN_QUARANTINE_MINUTES = int(os.getenv("DOMAIN_QUARANTINE_MINUTES", "240"))
MEMORY_MIN_AVAILABLE_MB = int(os.getenv("MEMORY_MIN_AVAILABLE_MB", "900"))
LOW_MEMORY_COOLDOWN_SECONDS = int(os.getenv("LOW_MEMORY_COOLDOWN_SECONDS", "8"))
MAX_CONSECUTIVE_LOW_MEMORY_HITS = int(os.getenv("MAX_CONSECUTIVE_LOW_MEMORY_HITS", "3"))
HIGH_PRICE_PAGE_MIN_PRICED_ITEMS = int(os.getenv("HIGH_PRICE_PAGE_MIN_PRICED_ITEMS", "6"))
HIGH_PRICE_PAGE_CONSECUTIVE_THRESHOLD = int(os.getenv("HIGH_PRICE_PAGE_CONSECUTIVE_THRESHOLD", "1"))
AUTOMATION_DIAGNOSTICS_ENABLED = os.getenv("AUTOMATION_DIAGNOSTICS_ENABLED", "1") == "1"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTOMATION_DIAGNOSTICS_LOG = os.getenv(
    "AUTOMATION_DIAGNOSTICS_LOG",
    os.path.join(BASE_DIR, "logs", "automation_diagnostics.jsonl")
)


def write_diagnostic(event, **fields):
    if not AUTOMATION_DIAGNOSTICS_ENABLED:
        return
    try:
        os.makedirs(os.path.dirname(AUTOMATION_DIAGNOSTICS_LOG), exist_ok=True)
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            **fields,
        }
        with open(AUTOMATION_DIAGNOSTICS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Diagnóstico nunca pode derrubar o robô.
        pass


def clean_product_url(url):
    return normalize_product_url(url)


def extract_domain(url):
    try:
        return (urlparse(url).netloc or "").lower()
    except Exception:
        return ""


def ensure_runtime_state_keys(state):
    state.setdefault("link_fail_counts", {})
    state.setdefault("domain_fail_counts", {})
    state.setdefault("quarantined_links", {})
    state.setdefault("quarantined_domains", {})


def clear_expired_quarantines(state):
    ensure_runtime_state_keys(state)
    now = int(time.time())
    changed = False

    for key in ("quarantined_links", "quarantined_domains"):
        mapping = state.get(key, {})
        expired = [k for k, until in mapping.items() if int(until or 0) <= now]
        for k in expired:
            mapping.pop(k, None)
            changed = True
        state[key] = mapping

    return changed


def quarantine_status(state, url):
    ensure_runtime_state_keys(state)
    now = int(time.time())
    cleaned = clean_product_url(url)
    domain = extract_domain(cleaned)

    link_until = int(state["quarantined_links"].get(cleaned, 0) or 0)
    if link_until > now:
        return True, "link", link_until, cleaned, domain

    domain_until = int(state["quarantined_domains"].get(domain, 0) or 0) if domain else 0
    if domain_until > now:
        return True, "domain", domain_until, cleaned, domain

    return False, "", 0, cleaned, domain


def register_link_failure(state, url, reason):
    ensure_runtime_state_keys(state)

    now = int(time.time())
    cleaned = clean_product_url(url)
    domain = extract_domain(cleaned)

    state["link_fail_counts"][cleaned] = int(state["link_fail_counts"].get(cleaned, 0)) + 1
    link_fail_count = state["link_fail_counts"][cleaned]

    domain_fail_count = 0
    if domain:
        state["domain_fail_counts"][domain] = int(state["domain_fail_counts"].get(domain, 0)) + 1
        domain_fail_count = state["domain_fail_counts"][domain]

    link_quarantined_until = 0
    domain_quarantined_until = 0

    if link_fail_count >= URL_FAILURE_QUARANTINE_THRESHOLD:
        link_quarantined_until = now + max(1, URL_QUARANTINE_MINUTES) * 60
        state["quarantined_links"][cleaned] = link_quarantined_until

    if domain and domain_fail_count >= DOMAIN_FAILURE_QUARANTINE_THRESHOLD:
        domain_quarantined_until = now + max(1, DOMAIN_QUARANTINE_MINUTES) * 60
        state["quarantined_domains"][domain] = domain_quarantined_until

    return {
        "cleaned_url": cleaned,
        "domain": domain,
        "reason": reason,
        "link_fail_count": link_fail_count,
        "domain_fail_count": domain_fail_count,
        "link_quarantined_until": link_quarantined_until,
        "domain_quarantined_until": domain_quarantined_until,
    }


def register_link_success(state, url):
    ensure_runtime_state_keys(state)
    cleaned = clean_product_url(url)
    domain = extract_domain(cleaned)

    state["link_fail_counts"].pop(cleaned, None)
    state["quarantined_links"].pop(cleaned, None)

    # Se um link do domínio abriu, remove quarentena do domínio.
    if domain:
        state["quarantined_domains"].pop(domain, None)


def read_memory_snapshot():
    """
    Lê memória do sistema via /proc/meminfo sem dependências externas.
    """
    try:
        mem = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                mem[key.strip()] = int(value.strip().split()[0])  # kB

        total_kb = int(mem.get("MemTotal", 0))
        avail_kb = int(mem.get("MemAvailable", 0))
        return {
            "total_mb": round(total_kb / 1024, 2),
            "available_mb": round(avail_kb / 1024, 2),
        }
    except Exception:
        return None


def url_suggests_price_ascending(url):
    u = (url or "").lower()
    patterns = (
        "sort_by=price-ascending",
        "sort_by=price_ascending",
        "sort=price-asc",
        "sort=price_asc",
        "orderby=price",
        "price-low-to-high",
        "price_asc",
    )
    return any(p in u for p in patterns)


def parse_supplier_index(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


async def open_tabs_in_parallel(ctx, urls, timeout_ms, max_parallel, delay_seconds=0.0):
    sem = asyncio.Semaphore(max(1, max_parallel))

    async def _open(url):
        page = None
        try:
            async with sem:
                page = await ctx.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
                return {"url": url, "page": page, "error": None}
        except Exception as e:
            if page is not None:
                try:
                    await page.close()
                except Exception:
                    pass
            return {"url": url, "page": None, "error": str(e)}

    return await asyncio.gather(*[_open(url) for url in urls])


def flush_accumulated_export(state, export_dir, template_path, reason):
    items = state.get("accumulated_items", [])
    if not items:
        return None

    ts = datetime.now()
    base_name = f"Produtos_{ts.strftime('%d_%m_%Y')}_{ts.strftime('%H%M%S')}.xlsx"
    out_path = os.path.join(export_dir, base_name)
    export_to_xlsx(items, template_path, out_path)
    logger.info(f"Exportação ({reason}) concluída em: {out_path}")
    state["accumulated_items"] = []
    save_state(state)
    return out_path


def defer_supplier_in_state(state, supplier_idx):
    deferred = state.get("deferred_suppliers_indices", [])
    if supplier_idx and supplier_idx not in deferred:
        deferred.append(supplier_idx)
    state["deferred_suppliers_indices"] = deferred

    # Limpa somente o contexto do fornecedor atual para seguir fluxo
    state["current_supplier_row"] = None
    state["current_page_url"] = None
    state["processed_links"] = []
    state["total_captured_for_supplier"] = 0
    save_state(state)

async def close_product_tabs(browser, main_page):
    """
    Fecha todas as abas extratidas, mantendo apenas a aba principal (listing).
    """
    for ctx in browser.contexts:
        for page in ctx.pages:
            if page == main_page:
                continue
            url = page.url
            # Não fecha aba de debug e outras internas
            if not url or url.startswith("devtools://") or url.startswith("chrome://"):
                continue
            
            try:
                await page.close()
            except Exception as e:
                logger.error(f"Erro fechando aba {url}: {e}")

async def close_pages_safely(pages):
    for page in pages:
        if page is None:
            continue
        try:
            if not page.is_closed():
                await page.close()
        except Exception:
            pass

async def run_automation(
    devtools_url,
    batch_size,
    price_limit,
    price_min,
    export_threshold,
    headless,
    start_index=None,
    end_index=None,
):
    if price_min < 0:
        logger.warning(f"price_min inválido ({price_min}). Ajustando para 0.")
        price_min = 0
    if price_limit > 0 and price_min > price_limit:
        raise ValueError(
            f"Faixa de preço inválida: mínimo (${price_min}) maior que máximo (${price_limit})."
        )
    start_idx_int = parse_supplier_index(start_index) if start_index else None
    end_idx_int = parse_supplier_index(end_index) if end_index else None
    if start_index and start_idx_int is None:
        raise ValueError(f"start_index inválido: {start_index}")
    if end_index and end_idx_int is None:
        raise ValueError(f"end_index inválido: {end_index}")
    if start_idx_int is not None and end_idx_int is not None and start_idx_int > end_idx_int:
        raise ValueError(
            f"Faixa de índice inválida: início ({start_idx_int}) maior que fim ({end_idx_int})."
        )

    logger.info("Iniciando modo automação contínua...")
    logger.info(f"Diagnóstico detalhado: {AUTOMATION_DIAGNOSTICS_LOG}")
    write_diagnostic(
        "automation_start",
        devtools_url=devtools_url,
        batch_size=batch_size,
        price_limit=price_limit,
        price_min=price_min,
        export_threshold=export_threshold,
        requested_start_index=start_index,
        requested_end_index=end_index,
    )
    
    while True:
        logger.info("Verificando estado atual de automação...")
        state = load_state()
        ensure_runtime_state_keys(state)
        if clear_expired_quarantines(state):
            save_state(state)
            write_diagnostic("expired_quarantine_cleared")
        write_diagnostic(
            "state_loaded",
            has_current_supplier=bool(state.get("current_supplier_row")),
            start_index_state=state.get("start_index"),
            processed_suppliers_count=len(state.get("processed_suppliers_indices", [])),
            deferred_suppliers_count=len(state.get("deferred_suppliers_indices", [])),
            accumulated_items_count=len(state.get("accumulated_items", [])),
            quarantined_links_count=len(state.get("quarantined_links", {})),
            quarantined_domains_count=len(state.get("quarantined_domains", {})),
        )
        
        # Override do state start_index caso passado pelo usuario inicialmente
        if start_index and start_index.strip() != "":
            # Se for pedido para pular para outro indice no meio de um resume
            if state.get("current_supplier_row"):
                curr_idx = str(state["current_supplier_row"].get("indice", ""))
                if curr_idx != start_index.strip():
                    logger.info(f"Índice de Resumo Forçado: Pulando de {curr_idx} direto para {start_index.strip()}!")
                    write_diagnostic(
                        "forced_start_index_jump",
                        from_index=curr_idx,
                        to_index=start_index.strip(),
                    )
                    completed = state.get("processed_suppliers_indices", [])
                    if curr_idx not in completed:
                        completed.append(curr_idx)
                    state["processed_suppliers_indices"] = completed
                    
                    state["current_supplier_row"] = None
                    state["current_page_url"] = None
                    state["processed_links"] = []
                    
            state["start_index"] = start_index.strip()
            save_state(state)
            write_diagnostic("start_index_updated", start_index=state["start_index"])
            start_index = None # Limpa para as proximas iteracoes do loop while
            
        saved_start_index = state.get("start_index", "")
        processed_indices = state.get("processed_suppliers_indices", [])
        deferred_indices = state.get("deferred_suppliers_indices", [])
        skip_indices = list(dict.fromkeys(processed_indices + deferred_indices))
        
        # Criação da pasta de exportação e refencia do template globais
        template_path = os.path.join(BASE_DIR, "SRAM 05_01_2026.xlsx")
        export_dir = os.path.join(BASE_DIR, "exports", "ARQUIVOS XLSX")
        os.makedirs(export_dir, exist_ok=True)

        # 1. Obter fornecedor se não houver no estado
        if not state.get("current_supplier_row"):
            supplier = None
            had_sheet_error = False

            for check_attempt in range(1, NO_SUPPLIER_CONFIRM_ATTEMPTS + 1):
                try:
                    supplier = get_next_supplier(start_index=saved_start_index, skip_indices=skip_indices)
                except Exception as e:
                    had_sheet_error = True
                    logger.error(f"Falha ao ler planilha de fornecedores (tentativa {check_attempt}/{NO_SUPPLIER_CONFIRM_ATTEMPTS}): {e}")
                    write_diagnostic(
                        "sheet_read_error",
                        attempt=check_attempt,
                        max_attempts=NO_SUPPLIER_CONFIRM_ATTEMPTS,
                        error=str(e),
                        start_index=saved_start_index,
                    )
                    await asyncio.sleep(SHEETS_ERROR_RETRY_SECONDS)
                    continue

                if supplier:
                    write_diagnostic(
                        "supplier_selected",
                        supplier_index=supplier.get("indice"),
                        supplier_url=supplier.get("url"),
                        start_index=saved_start_index,
                    )
                    break

                # Confirma ausência para evitar encerrar por oscilação temporária de leitura
                if check_attempt < NO_SUPPLIER_CONFIRM_ATTEMPTS:
                    logger.info(
                        f"Nenhum fornecedor encontrado (confirmação {check_attempt}/{NO_SUPPLIER_CONFIRM_ATTEMPTS}). "
                        f"Nova checagem em {NO_SUPPLIER_CONFIRM_DELAY_SECONDS}s..."
                    )
                    await asyncio.sleep(NO_SUPPLIER_CONFIRM_DELAY_SECONDS)

            if not supplier:
                if had_sheet_error:
                    logger.warning(
                        "Não foi possível confirmar o fim da planilha por erro de acesso. "
                        "Mantendo robô ativo e tentando novamente em 60s..."
                    )
                    write_diagnostic("supplier_lookup_retry_due_to_sheet_error", wait_seconds=60)
                    await asyncio.sleep(60)
                    continue

                if deferred_indices:
                    logger.warning(
                        f"Sem novos fornecedores pendentes. Reprocessando {len(deferred_indices)} fornecedor(es) "
                        "que foram adiados por timeout de CAPTCHA."
                    )
                    state["deferred_suppliers_indices"] = []
                    save_state(state)
                    write_diagnostic(
                        "reprocessing_deferred_suppliers",
                        deferred_count=len(deferred_indices),
                    )
                    await asyncio.sleep(5)
                    continue

                logger.info("Nenhum fornecedor pendente encontrado na planilha Google Sheets.")
                logger.info("Automação concluída!")
                write_diagnostic("automation_completed_no_pending_suppliers")

                flush_accumulated_export(state, export_dir, template_path,"lote final")
                break
            supplier_idx_int = parse_supplier_index(supplier.get("indice"))
            if end_idx_int is not None and supplier_idx_int is not None and supplier_idx_int > end_idx_int:
                logger.info(
                    f"Índice final ({end_idx_int}) atingido. Encerrando varredura antes do fornecedor {supplier.get('indice')}."
                )
                write_diagnostic(
                    "automation_completed_end_index_reached",
                    end_index=end_idx_int,
                    next_supplier_index=supplier.get("indice"),
                )
                flush_accumulated_export(state, export_dir, template_path,"lote final")
                break

            logger.info(f"Iniciando Fornecedor Indice {supplier['indice']} -> {supplier['url']}")
            write_diagnostic(
                "supplier_started",
                supplier_index=supplier.get("indice"),
                supplier_url=supplier.get("url"),
            )
            state["current_supplier_row"] = supplier
            state["current_page_url"] = supplier["url"]
            save_state(state)
        else:
            supplier = state["current_supplier_row"]
            supplier_idx_int = parse_supplier_index(supplier.get("indice"))
            if end_idx_int is not None and supplier_idx_int is not None and supplier_idx_int > end_idx_int:
                logger.info(
                    f"Fornecedor atual ({supplier.get('indice')}) excede índice final ({end_idx_int}). Encerrando."
                )
                write_diagnostic(
                    "automation_completed_current_supplier_out_of_range",
                    end_index=end_idx_int,
                    current_supplier_index=supplier.get("indice"),
                )
                flush_accumulated_export(state, export_dir, template_path,"lote final")
                break
            logger.info(f"Retomando automação Fornecedor indice: {supplier['indice']}")
            write_diagnostic(
                "supplier_resumed",
                supplier_index=supplier.get("indice"),
                supplier_url=supplier.get("url"),
            )

        async with async_playwright() as pw:
            # Se for headless true, iniciamos navegador proprio, caso contrario usamos o Chrome CDP do usuario
            browser = None
            main_page = None
            
            try:
                logger.info(f"Conectando ao browser em {devtools_url}...")
                browser = await pw.chromium.connect_over_cdp(devtools_url)
                ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
                main_page = await ctx.new_page()
                write_diagnostic(
                    "cdp_connected",
                    devtools_url=devtools_url,
                    contexts=len(browser.contexts),
                    pages_in_ctx=len(ctx.pages),
                )
            except Exception as e:
                logger.error(f"Não foi possível conectar ao browser: {e}")
                logger.info("Verifique se você iniciou o Chromium em modo debug usando o INICIAR_CHROME_DEBUG.bat ou .sh")
                write_diagnostic("cdp_connect_error", devtools_url=devtools_url, error=str(e))
                raise RuntimeError(f"Falha de conexão CDP em {devtools_url}: {e}")
                
            current_url = state.get("current_page_url")
            processed_links = set(state.get("processed_links", []))
            
            # Variaveis de pasta ja declaradas acima
            
            over_price = False
            supplier_ended = False
            captcha_timed_out = False
            consecutive_capture_failures = 0
            consecutive_open_failure_batches = 0
            consecutive_low_memory_hits = 0
            consecutive_high_price_pages = 0
            dynamic_batch_size = max(1, batch_size)
            
            same_page_stuck_count = 0
            last_page_total_links = 0

            while current_url and not over_price and not supplier_ended:
                nav_started = asyncio.get_running_loop().time()
                nav_status = None
                nav_error = ""
                final_url = current_url
                try:
                    logger.info(f"Navegando/Processando a página: {current_url}")
                    # Change to domcontentloaded to avoid getting stuck on tracking pixels
                    response = await main_page.goto(current_url, wait_until="domcontentloaded", timeout=45000)
                    nav_status = response.status if response else None
                    final_url = main_page.url
                    if LIST_PAGE_SETTLE_SECONDS > 0:
                        await asyncio.sleep(LIST_PAGE_SETTLE_SECONDS)
                except Exception as e:
                    # Timeout doesn't mean failure, Cloudflare challenge pages often timeout on "load". Do NOT break.
                    logger.warning(f"Aviso de navegação longa ou Timeout: {e}")
                    nav_error = str(e)
                write_diagnostic(
                    "page_navigation",
                    supplier_index=supplier.get("indice"),
                    requested_url=current_url,
                    final_url=final_url,
                    http_status=nav_status,
                    elapsed_ms=int((asyncio.get_running_loop().time() - nav_started) * 1000),
                    error=nav_error,
                )

                # CAPTCHA / Cloudflare verificação visual pelo titulo
                page_title = ""
                try:
                    page_title = await main_page.title()
                except Exception as e:
                    logger.warning(f"Erro lendo titulo da página: {e}")
                    
                def is_captcha(t):
                    tl = t.lower()
                    return any(x in tl for x in ["captcha", "human", "security", "just a moment", "challenge", "verifying"])
                    
                if is_captcha(page_title):
                    logger.warning(f"🛑 VERIFICAÇÃO HUMANA/CLOUDFLARE DETECTADA 🛑")
                    logger.warning(f"Detectado em: {current_url}")
                    logger.warning("Vá até o navegador Opera (janela de debug) e solucione o desafio humano manualmente!")
                    logger.warning(
                        f"O robô ficará em stand-by verificando a página a cada 5 segundos "
                        f"(timeout de {CAPTCHA_MAX_WAIT_SECONDS}s para não travar a madrugada)."
                    )
                    write_diagnostic(
                        "captcha_detected",
                        supplier_index=supplier.get("indice"),
                        url=current_url,
                        title=page_title,
                        timeout_seconds=CAPTCHA_MAX_WAIT_SECONDS,
                    )
                    captcha_wait_start = asyncio.get_running_loop().time()
                    
                    while is_captcha(page_title):
                        await asyncio.sleep(5)
                        try:
                            page_title = await main_page.title()
                        except:
                            pass

                        elapsed = asyncio.get_running_loop().time() - captcha_wait_start
                        if elapsed >= CAPTCHA_MAX_WAIT_SECONDS:
                            logger.error(
                                f"CAPTCHA não resolvido após {CAPTCHA_MAX_WAIT_SECONDS}s. "
                                "Pulando fornecedor atual para manter a automação ativa."
                            )
                            write_diagnostic(
                                "captcha_timeout",
                                supplier_index=supplier.get("indice"),
                                url=current_url,
                                waited_seconds=int(elapsed),
                            )
                            captcha_timed_out = True
                            supplier_ended = True
                            break
                            
                    if captcha_timed_out:
                        break

                    logger.info("✅ Desafio humano resolvido! A página carregou o catálogo. Retomando o robô em 5s...")
                    write_diagnostic(
                        "captcha_resolved",
                        supplier_index=supplier.get("indice"),
                        url=current_url,
                        waited_seconds=int(asyncio.get_running_loop().time() - captcha_wait_start),
                    )
                    await asyncio.sleep(5)
                    
                links = await fetch_product_links_from_page(main_page)
                logger.info(f"Página extratida: {len(links)} links encontrados")

                # Filtra links 
                valid_links = []
                blacklist = ["milwaukee"]
                global_history = set(state.get("global_captured_urls", []))
                priced_items_count = 0
                above_price_count = 0
                below_price_count = 0
                
                for item in links:
                    url_lower = item["url"].lower()
                    clean_url = clean_product_url(item["url"])
                    
                    if item["url"] in processed_links:
                        continue
                        
                    # Filtragem Global: Se o produto já foi capturado para sempre em qualquer momento da história do App
                    if clean_url in global_history:
                        logger.info(f"Produto ignorado (Já foi capturado anteriormente na história): {clean_url}")
                        # Adiciona no processed dessa pagina tbm p/ evitar rechecks inuteis
                        processed_links.add(item["url"])
                        continue
                        
                    if not url_lower.startswith("http"):
                        logger.info(f"Link ignorado (formato inválido): {item['url']}")
                        continue

                    action_patterns = [
                        "cart.php?action=", "/cart/add", "add-to-cart",
                        "addtocart", "/wishlist/", "/checkout",
                        "action=add&product_id=",
                    ]
                    if any(p in url_lower for p in action_patterns):
                        logger.info(f"Link ignorado (URL de ação/carrinho): {item['url']}")
                        processed_links.add(item["url"])
                        continue

                    # Ignorar marcas na blacklist
                    if any(b in url_lower for b in blacklist):
                        logger.info(f"Produto ignorado (Blacklist: {blacklist}): {item['url']}")
                        continue

                    is_quarantined, quarantine_type, until_ts, _, q_domain = quarantine_status(state, item["url"])
                    if is_quarantined:
                        processed_links.add(item["url"])
                        write_diagnostic(
                            "link_skipped_quarantine",
                            supplier_index=supplier.get("indice"),
                            page_url=current_url,
                            product_url=item["url"],
                            quarantine_type=quarantine_type,
                            quarantined_until=until_ts,
                            domain=q_domain,
                        )
                        continue
                        
                    price_info = parse_price_details(item.get("price_text", ""))
                    price = price_info.get("value")
                    price_status = price_info.get("status")
                    raw_price = price_info.get("raw", "")

                    if raw_price:
                        priced_items_count += 1

                    if price_status == "zero":
                        logger.info(
                            f"Ignorando produto com preço zero (raw='{raw_price}') -> {item['url']}"
                        )
                        write_diagnostic(
                            "product_skipped_zero_price",
                            supplier_index=supplier.get("indice"),
                            page_url=current_url,
                            product_url=item["url"],
                            raw_price=raw_price,
                        )
                        continue

                    if price_status == "inquiry":
                        logger.info(
                            f"Ignorando produto com preço sob consulta (raw='{raw_price}') -> {item['url']}"
                        )
                        write_diagnostic(
                            "product_skipped_inquiry_price",
                            supplier_index=supplier.get("indice"),
                            page_url=current_url,
                            product_url=item["url"],
                            raw_price=raw_price,
                        )
                        continue

                    if price_status in {"parse_error", "invalid_format"} and raw_price:
                        logger.info(
                            f"Preço não parseável na listagem (status={price_status}, raw='{raw_price}'). "
                            f"Mantendo para validação no produto -> {item['url']}"
                        )
                        write_diagnostic(
                            "product_price_parse_warning",
                            supplier_index=supplier.get("indice"),
                            page_url=current_url,
                            product_url=item["url"],
                            raw_price=raw_price,
                            parse_status=price_status,
                        )

                    if price is not None and price_min > 0 and price < price_min:
                        below_price_count += 1
                        logger.info(f"Ignorando produto < ${price_min} (preço lido: ${price}) -> {item['url']}")
                        continue

                    if price is not None and price_limit > 0 and price > price_limit:
                        above_price_count += 1
                        logger.info(f"Ignorando produto > ${price_limit} (preço lido: ${price}) -> {item['url']}")
                        continue
                        
                    valid_links.append(item["url"])
                    
                if len(valid_links) == 0:
                    logger.info("Nenhum produto válido/novo na página iterada.")
                    if (
                        price_limit > 0
                        and priced_items_count >= HIGH_PRICE_PAGE_MIN_PRICED_ITEMS
                        and above_price_count == priced_items_count
                        and url_suggests_price_ascending(current_url)
                    ):
                        consecutive_high_price_pages += 1
                    else:
                        consecutive_high_price_pages = 0

                    if consecutive_high_price_pages >= HIGH_PRICE_PAGE_CONSECUTIVE_THRESHOLD:
                        over_price = True
                        supplier_ended = True
                        logger.info(
                            f"Página acima do corte de preço detectada ({above_price_count}/{priced_items_count} acima de ${price_limit}) "
                            "em ordenação ascendente. Encerrando fornecedor para ganhar velocidade."
                        )
                        write_diagnostic(
                            "supplier_stopped_high_price_ceiling",
                            supplier_index=supplier.get("indice"),
                            page_url=current_url,
                            price_limit=price_limit,
                            priced_items=priced_items_count,
                            above_price_items=above_price_count,
                            consecutive_pages=consecutive_high_price_pages,
                        )
                    write_diagnostic(
                        "page_no_valid_links",
                        supplier_index=supplier.get("indice"),
                        url=current_url,
                        total_links=len(links),
                        priced_items=priced_items_count,
                        below_price_items=below_price_count,
                        above_price_items=above_price_count,
                        consecutive_high_price_pages=consecutive_high_price_pages,
                    )
                else:
                    consecutive_high_price_pages = 0
                    write_diagnostic(
                        "page_links_ready",
                        supplier_index=supplier.get("indice"),
                        url=current_url,
                        total_links=len(links),
                        valid_links=len(valid_links),
                        priced_items=priced_items_count,
                        below_price_items=below_price_count,
                        above_price_items=above_price_count,
                        dynamic_batch_size=dynamic_batch_size,
                    )
                    # Abrir as abas, bater na API e processar com batch adaptativo para evitar travamentos.
                    cursor = 0
                    while cursor < len(valid_links):
                        effective_batch_size = max(
                            1, min(dynamic_batch_size, len(valid_links) - cursor)
                        )
                        batch = valid_links[cursor:cursor + effective_batch_size]

                        mem_snapshot = read_memory_snapshot()
                        if mem_snapshot and mem_snapshot["available_mb"] < MEMORY_MIN_AVAILABLE_MB:
                            old_size = dynamic_batch_size
                            dynamic_batch_size = max(MIN_DYNAMIC_BATCH_SIZE, dynamic_batch_size // 2)
                            consecutive_low_memory_hits += 1
                            logger.warning(
                                f"Memória baixa ({mem_snapshot['available_mb']} MB livre). "
                                f"Reduzindo lote de {old_size} para {dynamic_batch_size} e aguardando..."
                            )
                            write_diagnostic(
                                "memory_pressure_backoff",
                                supplier_index=supplier.get("indice"),
                                page_url=current_url,
                                available_mb=mem_snapshot["available_mb"],
                                total_mb=mem_snapshot["total_mb"],
                                old_batch_size=old_size,
                                new_batch_size=dynamic_batch_size,
                                consecutive_low_memory_hits=consecutive_low_memory_hits,
                            )
                            await close_product_tabs(browser, main_page)
                            if consecutive_low_memory_hits >= MAX_CONSECUTIVE_LOW_MEMORY_HITS:
                                raise RuntimeError(
                                    f"Memória baixa persistente ({consecutive_low_memory_hits} ciclos). "
                                    "Reiniciando sessão para auto-healing."
                                )
                            await asyncio.sleep(LOW_MEMORY_COOLDOWN_SECONDS)
                            continue

                        consecutive_low_memory_hits = 0
                        cursor += effective_batch_size

                        logger.info(
                            f"Abrindo lote de {len(batch)} abas "
                            f"(configurado={batch_size}, efetivo={effective_batch_size})..."
                        )
                        open_parallel = max(1, min(effective_batch_size, TAB_OPEN_MAX_PARALLEL))
                        if mem_snapshot and mem_snapshot["available_mb"] < (MEMORY_MIN_AVAILABLE_MB + 400):
                            open_parallel = max(1, min(open_parallel, TAB_OPEN_PARALLEL_LOW_MEM))
                        write_diagnostic(
                            "batch_start",
                            supplier_index=supplier.get("indice"),
                            page_url=current_url,
                            batch_requested=len(batch),
                            batch_configured=batch_size,
                            batch_effective=effective_batch_size,
                            dynamic_batch_size=dynamic_batch_size,
                            tab_open_parallel=open_parallel,
                        )

                        opened_urls = []
                        opened_pages = []
                        failed_opens = 0
                        state_dirty_by_failures = False

                        open_results = await open_tabs_in_parallel(
                            ctx=ctx,
                            urls=batch,
                            timeout_ms=TAB_OPEN_TIMEOUT_MS,
                            max_parallel=open_parallel,
                            delay_seconds=TAB_OPEN_DELAY_SECONDS,
                        )
                        for open_result in open_results:
                            url = open_result["url"]
                            error_msg = open_result["error"]
                            page = open_result["page"]

                            if error_msg is None and page is not None:
                                opened_pages.append(page)
                                opened_urls.append(url)
                                register_link_success(state, url)
                                continue

                            failed_opens += 1
                            fail_info = register_link_failure(state, url, "tab_open_error")
                            state_dirty_by_failures = True
                            if fail_info["link_quarantined_until"] > 0 or fail_info["domain_quarantined_until"] > 0:
                                processed_links.add(url)
                            logger.error(f"Erro abrindo aba {url}: {error_msg}")
                            write_diagnostic(
                                "tab_open_error",
                                supplier_index=supplier.get("indice"),
                                page_url=current_url,
                                product_url=url,
                                error=error_msg,
                                link_fail_count=fail_info["link_fail_count"],
                                domain=fail_info["domain"],
                                domain_fail_count=fail_info["domain_fail_count"],
                                link_quarantined_until=fail_info["link_quarantined_until"],
                                domain_quarantined_until=fail_info["domain_quarantined_until"],
                            )
                            if fail_info["link_quarantined_until"] > 0:
                                write_diagnostic(
                                    "link_quarantined",
                                    supplier_index=supplier.get("indice"),
                                    page_url=current_url,
                                    product_url=url,
                                    quarantine_type="link",
                                    quarantined_until=fail_info["link_quarantined_until"],
                                    reason="tab_open_error",
                                )
                            if fail_info["domain_quarantined_until"] > 0:
                                write_diagnostic(
                                    "link_quarantined",
                                    supplier_index=supplier.get("indice"),
                                    page_url=current_url,
                                    product_url=url,
                                    quarantine_type="domain",
                                    domain=fail_info["domain"],
                                    quarantined_until=fail_info["domain_quarantined_until"],
                                    reason="tab_open_error",
                                )

                        if state_dirty_by_failures:
                            state["processed_links"] = list(processed_links)
                            save_state(state)

                        failure_ratio = failed_opens / max(1, len(batch))
                        if failure_ratio >= BATCH_DOWNSHIFT_FAILURE_RATIO and dynamic_batch_size > MIN_DYNAMIC_BATCH_SIZE:
                            old_size = dynamic_batch_size
                            dynamic_batch_size = max(MIN_DYNAMIC_BATCH_SIZE, dynamic_batch_size // 2)
                            if dynamic_batch_size < old_size:
                                logger.warning(
                                    f"Lote reduzido para {dynamic_batch_size} devido a falhas de abertura "
                                    f"({failed_opens}/{len(batch)})."
                                )
                        elif failed_opens == 0 and dynamic_batch_size < batch_size:
                            dynamic_batch_size = min(batch_size, dynamic_batch_size + 1)

                        write_diagnostic(
                            "batch_open_summary",
                            supplier_index=supplier.get("indice"),
                            page_url=current_url,
                            opened=len(opened_urls),
                            failed=failed_opens,
                            failure_ratio=round(failure_ratio, 3),
                            dynamic_batch_size=dynamic_batch_size,
                        )

                        if failed_opens == len(batch):
                            consecutive_open_failure_batches += 1
                        else:
                            consecutive_open_failure_batches = 0

                        if not opened_urls:
                            logger.warning("Nenhuma aba do lote abriu com sucesso. Tentando próximo lote.")
                            write_diagnostic(
                                "batch_skipped_no_opened_tabs",
                                supplier_index=supplier.get("indice"),
                                page_url=current_url,
                                consecutive_open_failure_batches=consecutive_open_failure_batches,
                            )
                            await close_pages_safely(opened_pages)
                            if consecutive_open_failure_batches >= MAX_CONSECUTIVE_OPEN_FAILURE_BATCHES:
                                raise RuntimeError(
                                    f"Muitas falhas consecutivas na abertura de abas "
                                    f"({consecutive_open_failure_batches}). Reiniciando sessão para auto-healing."
                                )
                            await asyncio.sleep(2)
                            continue

                        logger.info("Aguardando estabilidade das abas e chamando captura...")
                        if POST_BATCH_SETTLE_SECONDS > 0:
                            await asyncio.sleep(POST_BATCH_SETTLE_SECONDS)

                        captured_items = []
                        try:
                            captured_items = await call_capture_api(devtools_url, opened_urls, fast_mode=True)
                        except Exception as e:
                            consecutive_capture_failures += 1
                            failure_updates = []
                            for failed_url in opened_urls:
                                fail_info = register_link_failure(state, failed_url, "capture_error")
                                failure_updates.append(fail_info)
                                if fail_info["link_quarantined_until"] > 0 or fail_info["domain_quarantined_until"] > 0:
                                    processed_links.add(failed_url)
                                if fail_info["link_quarantined_until"] > 0:
                                    write_diagnostic(
                                        "link_quarantined",
                                        supplier_index=supplier.get("indice"),
                                        page_url=current_url,
                                        product_url=failed_url,
                                        quarantine_type="link",
                                        quarantined_until=fail_info["link_quarantined_until"],
                                        reason="capture_error",
                                    )
                                if fail_info["domain_quarantined_until"] > 0:
                                    write_diagnostic(
                                        "link_quarantined",
                                        supplier_index=supplier.get("indice"),
                                        page_url=current_url,
                                        product_url=failed_url,
                                        quarantine_type="domain",
                                        domain=fail_info["domain"],
                                        quarantined_until=fail_info["domain_quarantined_until"],
                                        reason="capture_error",
                                    )

                            state["processed_links"] = list(processed_links)
                            save_state(state)
                            logger.error(
                                f"Falha na captura do lote ({consecutive_capture_failures}/"
                                f"{MAX_CONSECUTIVE_CAPTURE_FAILURES}): {e}"
                            )
                            write_diagnostic(
                                "batch_capture_error",
                                supplier_index=supplier.get("indice"),
                                page_url=current_url,
                                opened_tabs=len(opened_urls),
                                consecutive_capture_failures=consecutive_capture_failures,
                                max_capture_failures=MAX_CONSECUTIVE_CAPTURE_FAILURES,
                                error=str(e),
                                failures_updated=len(failure_updates),
                            )

                            if consecutive_capture_failures >= MAX_CONSECUTIVE_CAPTURE_FAILURES:
                                raise RuntimeError(
                                    f"Muitas falhas consecutivas na captura ({consecutive_capture_failures}). "
                                    "Reiniciando sessão para auto-healing."
                                )
                            await asyncio.sleep(4)
                            continue
                        finally:
                            await close_pages_safely(opened_pages)

                        # Captura bem-sucedida: zera contador de falhas
                        consecutive_capture_failures = 0
                        logger.info(f"Capturados {len(captured_items)} itens.")
                        write_diagnostic(
                            "batch_capture_success",
                            supplier_index=supplier.get("indice"),
                            page_url=current_url,
                            opened_tabs=len(opened_urls),
                            captured_items=len(captured_items),
                        )

                        # Marca o lote como processado apenas após captura concluir
                        for done_url in opened_urls:
                            processed_links.add(done_url)

                        # Add to global history to never capture again
                        global_history = state.get("global_captured_urls", [])
                        for c_item in captured_items:
                            clean_c_url = c_item.get("url", "").split('#')[0].split('?')[0]
                            if clean_c_url and clean_c_url not in global_history:
                                global_history.append(clean_c_url)
                        state["global_captured_urls"] = global_history

                        state["accumulated_items"].extend(captured_items)
                        state["processed_links"] = list(processed_links)
                        state["total_captured_for_supplier"] += len(captured_items)
                        save_state(state)

                        if len(state["accumulated_items"]) >= export_threshold:
                            logger.info(f"Threshold atingido ({export_threshold}). Exportando lote...")
                            write_diagnostic(
                                "export_threshold_reached",
                                supplier_index=supplier.get("indice"),
                                accumulated_items=len(state["accumulated_items"]),
                                export_threshold=export_threshold,
                            )
                            flush_accumulated_export(
                                state=state,
                                export_dir=export_dir,
                                template_path=template_path,
                                reason=f"threshold {export_threshold}",
                            )

                if supplier_ended:
                    break

                # Go Next Page
                next_url = await find_next_page(main_page)
                
                if next_url == "SAME_PAGE":
                    logger.info("Tentativa de carregar mais produtos na mesma página (Scroll/Load More).")
                    write_diagnostic(
                        "pagination_same_page",
                        supplier_index=supplier.get("indice"),
                        page_url=current_url,
                        same_page_stuck_count=same_page_stuck_count,
                        total_links=len(links),
                    )
                    if len(links) <= last_page_total_links:
                        same_page_stuck_count += 1
                        if same_page_stuck_count >= 2:
                            logger.info("Foram feitas tentativas de carregar mais itens mas nenhum novo produto surgiu. Fim da paginação.")
                            supplier_ended = True
                    else:
                        same_page_stuck_count = 0
                    last_page_total_links = len(links)
                elif next_url and next_url != current_url:
                    write_diagnostic(
                        "pagination_next_page",
                        supplier_index=supplier.get("indice"),
                        from_url=current_url,
                        to_url=next_url,
                    )
                    current_url = next_url
                    state["current_page_url"] = current_url
                    save_state(state)
                    same_page_stuck_count = 0
                    last_page_total_links = 0
                else:
                    logger.info("Fim da paginação (Sem mais botões de Next).")
                    write_diagnostic(
                        "pagination_finished",
                        supplier_index=supplier.get("indice"),
                        page_url=current_url,
                    )
                    supplier_ended = True

            # Fim do processamento do supplier
            logger.info(f"Finalizando Fornecedor INDICE: {supplier['indice']}")
            if captcha_timed_out:
                logger.warning(
                    f"Fornecedor INDICE {supplier['indice']} foi encerrado por timeout de CAPTCHA "
                    f"({CAPTCHA_MAX_WAIT_SECONDS}s) para evitar travamento da automação."
                )
                defer_supplier_in_state(state, supplier["indice"])
                write_diagnostic(
                    "supplier_deferred_captcha_timeout",
                    supplier_index=supplier.get("indice"),
                    timeout_seconds=CAPTCHA_MAX_WAIT_SECONDS,
                )
            else:
                # Limpa estado de paginação e links, MAS MANTEM accumulated_items (ver state.py)
                clear_supplier_state()
                write_diagnostic(
                    "supplier_completed",
                    supplier_index=supplier.get("indice"),
                    captured_for_supplier=state.get("total_captured_for_supplier", 0),
                )
            
            await browser.close()
            logger.info("Automação do Fornecedor concluída! Passando para o próximo...")
            write_diagnostic("supplier_cycle_end", supplier_index=supplier.get("indice"))
            
            # Pequena pausa antes de pegar o próximo
            await asyncio.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automação end-to-end de captura do Fornecedor.")
    parser.add_argument("--devtools", default="http://127.0.0.1:9222", help="URL do Chrome remote debug port")
    parser.add_argument("--batch-size", type=int, default=10, help="Quantidade de abas a processar de uma vez")
    parser.add_argument("--price-limit", type=float, default=85.0, help="Filtro máximo de preço")
    parser.add_argument("--price-min", type=float, default=0.0, help="Filtro mínimo de preço (0 desativa)")
    parser.add_argument("--export-threshold", type=int, default=500, help="Quantidade de produtos até forçar um export e flush de memória")
    parser.add_argument("--start-index", default="36", help="Inicia a partir do indice exato")
    parser.add_argument("--end-index", default="", help="Finaliza no indice informado (inclusive)")
    parser.add_argument("--headless", action="store_true", help="Rodar browser interno via playrigtht puro (Requer auth externa)")

    args = parser.parse_args()
    
    import time
    while True:
        try:
            asyncio.run(
                run_automation(
                    args.devtools,
                    args.batch_size,
                    args.price_limit,
                    args.price_min,
                    args.export_threshold,
                    args.headless,
                    args.start_index,
                    args.end_index,
                )
            )
            break # Terminou com sucesso ou via break interno
        except Exception as e:
            logger.error(f"⚠️ Erro Crítico ou Desconexão do Navegador detectada: {e}")
            write_diagnostic("automation_crash_restart", error=str(e))
            logger.info("♻️ O robô auto-healing irá reiniciar a sessão e retomar do último salvamento na RAM em 10 segundos...")
            time.sleep(10)
