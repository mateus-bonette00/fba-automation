from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from pydantic import BaseModel
from urllib.parse import quote_plus, urljoin, urlparse
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
    """Extrai UPC da página HTML"""
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
            for key in ("gtin", "gtin12", "gtin13", "gtin14", "upc", "sku"):
                val = o.get(key)
                if isinstance(val, str):
                    digits = re.sub(r"\D", "", val)
                    if len(digits) in (12, 13, 14):
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
        "[itemprop='gtin'], [itemprop='gtin12'], [itemprop='gtin13']",
        "[data-upc], [data-gtin], [data-sku]"
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
        patterns = [
            r'"(?:upc|gtin|gtin12|gtin13|ean)"\s*:\s*"(\d{12,14})"',
            r'"sku"\s*:\s*"(\d{12,14})"',
            r'upc["\']?\s*:\s*["\']?(\d{12,14})',
        ]
        for pattern in patterns:
            m = re.search(pattern, txt, flags=re.I)
            if m:
                return m.group(1)[:12]

    # 4) Texto com rótulo
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(?:\bUPC\b|\bGTIN\b|\bSKU\b)\D*?(\d{12,14})", text, flags=re.I)
    if m:
        d = re.sub(r"\D", "", m.group(1))
        if 12 <= len(d) <= 14:
            return d[:12]

    return None


async def extract_products_with_playwright(page: Page) -> list[dict]:
    """
    Extrai produtos usando Playwright API diretamente
    Mais robusto para sites com JavaScript
    """
    products = []

    # Esperar elementos aparecerem
    try:
        # Tentar esperar por elementos comuns de produtos
        selectors_to_wait = [
            'a[href*="/p/"]',
            'article',
            '[class*="product"]',
            '[data-product]'
        ]

        for selector in selectors_to_wait:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                break
            except:
                continue
    except:
        pass

    # Esperar um pouco extra para garantir
    await page.wait_for_timeout(3000)

    # Pegar todos os links da página
    links = await page.query_selector_all('a')

    for link in links:
        try:
            href = await link.get_attribute('href')
            text = await link.text_content()

            if not href or not text:
                continue

            text = text.strip()

            # Filtrar apenas links que parecem ser produtos
            # Geralmente têm /p/ na URL ou são links longos com texto descritivo
            if ('/p/' in href or '/product/' in href or len(text) > 15) and len(text) < 200:
                # Evitar links de navegação
                nav_keywords = ['home', 'cart', 'account', 'login', 'register', 'category', 'page', 'next', 'prev']
                if not any(kw in text.lower() for kw in nav_keywords):
                    full_url = page.url if href.startswith('/') else href
                    if href.startswith('/'):
                        parsed = urlparse(page.url)
                        full_url = f"{parsed.scheme}://{parsed.netloc}{href}"

                    products.append({
                        "title": text,
                        "url": full_url if href.startswith('http') else href
                    })
        except:
            continue

    # Remover duplicatas
    seen = set()
    unique_products = []
    for p in products:
        if p['url'] not in seen:
            seen.add(p['url'])
            unique_products.append(p)

    return unique_products


async def scrape_product_details(page: Page, url: str) -> dict:
    """Acessa a página do produto e extrai UPC e título completo"""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

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


async def get_total_pages(page: Page) -> int:
    """Detecta total de páginas"""
    html = await page.content()

    # Procurar por "1-48 of 346 items"
    match = re.search(r'(\d+)-(\d+)\s+of\s+(\d+)\s+items', html, re.I)
    if match:
        total_items = int(match.group(3))
        items_per_page = int(match.group(2)) - int(match.group(1)) + 1
        total_pages = (total_items + items_per_page - 1) // items_per_page
        return total_pages

    return 1


@router.post("/scrape")
async def scrape_supplier(request: SupplierScrapeRequest):
    """
    Varre o site do fornecedor e retorna produtos com UPC e links da Amazon
    Versão melhorada usando Playwright API
    """
    supplier_url = request.supplier_url.strip()

    if not supplier_url or not supplier_url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL inválida")

    all_products = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Mude para True em produção
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            # 1. Acessar primeira página
            await page.goto(supplier_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)

            # 2. Detectar total de páginas
            total_pages = await get_total_pages(page)

            # 3. Processar cada página
            product_urls = []

            for page_num in range(1, min(total_pages + 1, 10)):  # Limitar a 10 páginas por segurança
                if page_num > 1:
                    parsed = urlparse(supplier_url)
                    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    page_url = f"{base}?pageSize=48&page={page_num}"

                    await page.goto(page_url, wait_until="networkidle", timeout=60000)
                    await page.wait_for_timeout(5000)

                # Extrair produtos usando Playwright
                products = await extract_products_with_playwright(page)
                product_urls.extend(products)

            # Remover duplicatas
            seen = set()
            unique_products = []
            for p in product_urls:
                if p['url'] not in seen:
                    seen.add(p['url'])
                    unique_products.append(p)

            # 4. Extrair UPC de cada produto
            for product in unique_products[:50]:  # Limitar a 50 produtos para teste
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
            "pages_scraped": min(total_pages, 10)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer scraping: {str(e)}")


@router.post("/scrape-and-download")
async def scrape_and_download(request: SupplierScrapeRequest):
    """Varre e retorna CSV"""
    # Chama a função de scraping
    result = await scrape_supplier(request)

    # Gera CSV
    output = io.StringIO()
    if result['products']:
        fieldnames = [
            "Nome do Produto",
            "UPC",
            "Link Fornecedor",
            "Amazon (Busca por UPC)",
            "Amazon (Busca por Nome)"
        ]

        csv_data = []
        for p in result['products']:
            csv_data.append({
                "Nome do Produto": p['nome'],
                "UPC": p['upc'] or "Não encontrado",
                "Link Fornecedor": p['link_fornecedor'],
                "Amazon (Busca por UPC)": p['amazon_upc'] or "N/A",
                "Amazon (Busca por Nome)": p['amazon_nome']
            })

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)

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
