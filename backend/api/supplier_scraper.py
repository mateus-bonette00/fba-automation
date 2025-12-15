from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from pydantic import BaseModel
from urllib.parse import quote_plus, urljoin
import json
import re
import csv
import io
from datetime import datetime
from .upc_extractor import extract_upc_from_html
from .title_extractor import extract_title_from_html

router = APIRouter()


class SupplierScrapeRequest(BaseModel):
    supplier_url: str


def extract_upc_from_html_legacy(html: str) -> str | None:
    """Extrai UPC da página HTML usando múltiplas técnicas"""
    soup = BeautifulSoup(html, "html.parser")

    # 1) JSON-LD
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        txt = tag.get_text(strip=True)
        if not txt:
            continue
        try:
            data = json.loads(txt)
        except:
            continue

        def check_obj(o: dict) -> str | None:
            for key in ("gtin", "gtin12", "gtin13", "gtin14", "upc"):
                val = o.get(key)
                if isinstance(val, str):
                    digits = re.sub(r"\D", "", val)
                    if len(digits) in (12, 13, 14):
                        return digits[:12]
            if "offers" in o and isinstance(o["offers"], dict):
                val = o["offers"].get("gtin13") or o["offers"].get("gtin12")
                if val:
                    digits = re.sub(r"\D", "", str(val))
                    if len(digits) in (12, 13):
                        return digits[:12]
            return None

        if isinstance(data, dict):
            upc = check_obj(data)
            if upc:
                return upc
        elif isinstance(data, list):
            for o in data:
                if isinstance(o, dict):
                    upc = check_obj(o)
                    if upc:
                        return upc

    # 2) Microdata / Atributos
    for sel in [
        "[itemprop='gtin'], [itemprop='gtin12'], [itemprop='gtin13'], [itemprop='gtin14']",
        "[data-upc], [data-gtin], [data-gtin12], [data-gtin13]"
    ]:
        el = soup.select_one(sel)
        if el:
            val = el.get("content") or el.get("value") or el.get("data-upc") or el.get_text(strip=True)
            if val:
                d = re.sub(r"\D", "", val)
                if 12 <= len(d) <= 14:
                    return d[:12]

    # 3) Scripts
    for scr in soup.find_all("script"):
        txt = scr.get_text() or ""
        if any(k in txt.lower() for k in ("barcode", "gtin", "upc")):
            m = re.search(r'"(?:barcode|gtin|gtin12|gtin13|gtin14|upc)"\s*:\s*"(\d{12,14})"', txt, flags=re.I)
            if m:
                return m.group(1)[:12]

    # 4) Texto com rótulo
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(?:\bUPC\b|\bGTIN-?1[2-4]\b|\bBarcode\b)\D*?(\d{12,14})", text, flags=re.I)
    if m:
        d = re.sub(r"\D", "", m.group(1))
        if 12 <= len(d) <= 14:
            return d[:12]

    # 5) Heurística - UPC solto no texto
    for m in re.finditer(r"\b(\d{12})\b", text):
        start = max(0, m.start() - 80)
        end = min(len(text), m.end() + 80)
        win = text[start:end].lower()
        if any(k in win for k in ("upc", "gtin", "barcode", "ean")):
            return m.group(1)

    return None


def extract_products_from_page(html: str, base_url: str) -> list[dict]:
    """Extrai produtos da página"""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    # Primeiro tentar por atributos data (sites modernos)
    products_by_data = soup.find_all(attrs=lambda x: any(k.startswith('data-product') for k in (x or {}).keys()))
    if products_by_data:
        for elem in products_by_data:
            link = elem if elem.name == 'a' else elem.select_one("a[href]")
            if link:
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if href and title:
                    products.append({
                        "title": title,
                        "url": urljoin(base_url, href)
                    })
        if products:
            return products

    # Seletores CSS comuns
    product_selectors = [
        ".product",
        ".product-item",
        ".productListItem",
        ".woocommerce-LoopProduct-link",
        "article.product",
        ".products .product",
        "li.product",
        "div.product-card",
        ".product-list-item",
        "[class*='product']"
    ]

    product_elements = []
    for selector in product_selectors:
        elements = soup.select(selector)
        if elements:
            product_elements = elements
            break

    for elem in product_elements:
        title = ""
        title_selectors = [
            "h2 a",
            "h3 a",
            ".product-title",
            ".woocommerce-loop-product__title",
            "a.product-link"
        ]
        for sel in title_selectors:
            title_elem = elem.select_one(sel)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break

        product_url = ""
        link_elem = elem.select_one("a[href]")
        if link_elem:
            href = link_elem.get("href", "")
            if href:
                product_url = urljoin(base_url, href)

        if not title or not product_url:
            continue

        products.append({
            "title": title,
            "url": product_url
        })

    return products


async def scrape_product_details(page: Page, url: str) -> dict:
    """Acessa a página do produto e extrai UPC e título completo"""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1000)

        html = await page.content()

        # Usa os extratores avançados
        title = extract_title_from_html(html)
        upc = extract_upc_from_html(html)

        return {
            "title": title or "",
            "upc": upc,
            "url": url
        }
    except Exception as e:
        return {
            "title": "",
            "upc": None,
            "url": url
        }


async def get_all_page_urls(page: Page, start_url: str) -> list[str]:
    """Detecta automaticamente paginação e retorna todas as URLs de páginas"""
    urls = [start_url]

    try:
        await page.goto(start_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)  # Espera extra para JS carregar

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Detectar paginação por links
        pagination_selectors = [
            ".pagination a",
            ".page-numbers a",
            ".woocommerce-pagination a",
            "nav.pagination a",
            ".pager a",
            "a.next",
            "a[rel='next']"
        ]

        page_links = set()
        for selector in pagination_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get("href")
                if href:
                    full_url = urljoin(start_url, href)
                    page_links.add(full_url)

        # Detectar total de páginas por texto (ex: "1-48 of 346 items")
        total_pages = 1
        items_text = soup.find(string=lambda x: x and "of" in str(x) and "items" in str(x).lower())
        if items_text:
            match = re.search(r'of\s+(\d+)\s+items', str(items_text), re.I)
            if match:
                total_items = int(match.group(1))
                items_per_page_match = re.search(r'(\d+)-(\d+)\s+of', str(items_text))
                if items_per_page_match:
                    items_per_page = int(items_per_page_match.group(2)) - int(items_per_page_match.group(1)) + 1
                else:
                    items_per_page = 48  # padrão comum
                total_pages = (total_items + items_per_page - 1) // items_per_page

                # Gerar URLs de páginas
                from urllib.parse import urlparse, parse_qs, urlencode
                parsed = urlparse(start_url)
                base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

                for i in range(2, total_pages + 1):
                    page_url = f"{base}?pageSize={items_per_page}&page={i}"
                    page_links.add(page_url)

        base_path = start_url.split("?")[0].rstrip("/")
        valid_pages = []

        for url in page_links:
            url_base = url.split("?")[0].rstrip("/")
            if url_base.startswith(base_path) or "/page/" in url or "page=" in url or "paged=" in url:
                valid_pages.append(url)

        if valid_pages:
            urls.extend(sorted(set(valid_pages)))

    except Exception as e:
        pass

    return list(set(urls))


@router.post("/scrape")
async def scrape_supplier(request: SupplierScrapeRequest):
    """
    Varre o site do fornecedor e retorna produtos com UPC e links da Amazon
    """
    supplier_url = request.supplier_url.strip()

    if not supplier_url or not supplier_url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL inválida")

    all_products = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # False = ver navegador
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            # 1. Descobrir todas as páginas
            page_urls = await get_all_page_urls(page, supplier_url)

            # 2. Extrair produtos de cada página
            product_urls = []
            for page_url in page_urls:
                try:
                    await page.goto(page_url, wait_until="networkidle", timeout=60000)
                    await page.wait_for_timeout(2000)

                    html = await page.content()
                    products = extract_products_from_page(html, page_url)
                    product_urls.extend(products)
                except Exception as e:
                    continue

            # 3. Acessar cada produto para extrair UPC
            for i, product in enumerate(product_urls):
                details = await scrape_product_details(page, product['url'])

                title = details['title'] or product['title']
                upc = details['upc']
                supplier_link = details['url']

                amazon_upc_link = ""
                amazon_title_link = ""

                if upc:
                    # Link de busca da Amazon com parâmetros extras para parecer mais legítimo
                    amazon_upc_link = f"https://www.amazon.com/s?k={upc}&ref=nb_sb_noss"

                if title:
                    search_query = quote_plus(title)
                    # Link de busca da Amazon com parâmetros extras
                    amazon_title_link = f"https://www.amazon.com/s?k={search_query}&ref=nb_sb_noss"

                all_products.append({
                    "nome": title,
                    "upc": upc or "",
                    "link_fornecedor": supplier_link,
                    "amazon_upc": amazon_upc_link,
                    "amazon_nome": amazon_title_link,
                    "status": "ok"
                })

            await browser.close()

        return {
            "total": len(all_products),
            "products": all_products,
            "pages_scraped": len(page_urls)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer scraping: {str(e)}")


@router.post("/scrape-and-download")
async def scrape_and_download(request: SupplierScrapeRequest):
    """
    Varre o site do fornecedor e retorna CSV para download
    """
    supplier_url = request.supplier_url.strip()

    if not supplier_url or not supplier_url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL inválida")

    all_products = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # False = ver navegador
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            page_urls = await get_all_page_urls(page, supplier_url)
            product_urls = []

            for page_url in page_urls:
                try:
                    await page.goto(page_url, wait_until="networkidle", timeout=60000)
                    await page.wait_for_timeout(2000)
                    html = await page.content()
                    products = extract_products_from_page(html, page_url)
                    product_urls.extend(products)
                except:
                    continue

            for product in product_urls:
                details = await scrape_product_details(page, product['url'])
                title = details['title'] or product['title']
                upc = details['upc']
                supplier_link = details['url']

                amazon_upc_link = ""
                amazon_title_link = ""

                if upc:
                    # Link de busca da Amazon com parâmetros extras para parecer mais legítimo
                    amazon_upc_link = f"https://www.amazon.com/s?k={upc}&ref=nb_sb_noss"
                if title:
                    search_query = quote_plus(title)
                    # Link de busca da Amazon com parâmetros extras
                    amazon_title_link = f"https://www.amazon.com/s?k={search_query}&ref=nb_sb_noss"

                all_products.append({
                    "Nome do Produto": title,
                    "UPC": upc or "Não encontrado",
                    "Link Fornecedor": supplier_link,
                    "Amazon (Busca por UPC)": amazon_upc_link or "N/A",
                    "Amazon (Busca por Nome)": amazon_title_link
                })

            await browser.close()

        # Gera CSV
        output = io.StringIO()
        if all_products:
            fieldnames = [
                "Nome do Produto",
                "UPC",
                "Link Fornecedor",
                "Amazon (Busca por UPC)",
                "Amazon (Busca por Nome)"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_products)

        output.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"produtos_fornecedor_{timestamp}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer scraping: {str(e)}")
