#!/usr/bin/env python3
"""
Scraper específico para Discount School Supply
Otimizado para extrair produtos de páginas com paginação
"""

import asyncio
import csv
import re
from datetime import datetime
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from api.upc_extractor import extract_upc_from_html


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
        # Procurar padrões comuns
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


async def scrape_discount_school_supply(start_url: str):
    """
    Scraper específico para Discount School Supply
    """
    print(f"\n{'='*80}")
    print(" DISCOUNT SCHOOL SUPPLY SCRAPER ".center(80))
    print(f"{'='*80}\n")

    all_products = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=True para produção
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print(f"[1] Acessando: {start_url}\n")
        await page.goto(start_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        # Descobrir quantas páginas existem
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Procurar informação de total de items (ex: "1-48 of 346 items")
        total_pages = 1
        items_text = soup.find(string=lambda x: x and "of" in str(x) and "items" in str(x).lower())
        if items_text:
            match = re.search(r'of\s+(\d+)\s+items', str(items_text), re.I)
            if match:
                total_items = int(match.group(1))
                items_per_page = 48  # padrão do site
                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(f"✓ Total de items: {total_items}")
                print(f"✓ Total de páginas: {total_pages}\n")

        # Processar cada página
        for page_num in range(1, total_pages + 1):
            print(f"[{page_num}/{total_pages}] Varrendo página {page_num}...")

            if page_num > 1:
                # Ir para a próxima página
                # O site usa query params: ?pageSize=48&page=2
                parsed = urlparse(start_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                page_url = f"{base_url}?pageSize=48&page={page_num}"

                await page.goto(page_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Extrair produtos - testar diferentes seletores
            product_elements = []

            # Tentar encontrar pelo atributo data
            products_by_data = soup.find_all(attrs={"data-product-code": True})
            if products_by_data:
                product_elements = products_by_data
                print(f"  ✓ Encontrados {len(product_elements)} produtos (data-product-code)")
            else:
                # Tentar por classes comuns
                for selector in [".product-item", ".productListItem", "[class*='product']"]:
                    products_by_class = soup.select(selector)
                    if products_by_class:
                        product_elements = products_by_class
                        print(f"  ✓ Encontrados {len(product_elements)} produtos ({selector})")
                        break

            if not product_elements:
                print(f"  ✗ Nenhum produto encontrado na página {page_num}")
                continue

            # Extrair info de cada produto
            for elem in product_elements:
                # Extrair título
                title = ""
                for sel in ["h2", "h3", ".name", ".title", "a.product-link"]:
                    title_elem = elem.select_one(sel)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title:
                            break

                # Extrair URL do produto
                product_url = ""
                link = elem.select_one("a[href]")
                if link:
                    href = link.get("href")
                    if href:
                        product_url = urljoin(start_url, href)

                if title and product_url:
                    all_products.append({
                        "title": title,
                        "url": product_url
                    })

            print(f"  → {len(product_elements)} produtos adicionados\n")

        print(f"\n{'='*80}")
        print(f"Total de produtos coletados: {len(all_products)}")
        print(f"{'='*80}\n")

        # Agora visitar cada produto para pegar UPC
        print("[2] Extraindo UPCs dos produtos...\n")

        products_with_upc = []
        for i, product in enumerate(all_products, 1):
            print(f"  [{i}/{len(all_products)}] {product['title'][:60]}")

            try:
                await page.goto(product['url'], wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1500)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Extrair título completo
                full_title = product['title']
                for sel in ["h1", "h1.product-name", ".product-title"]:
                    h1 = soup.select_one(sel)
                    if h1:
                        full_title = h1.get_text(strip=True)
                        break

                # Extrair UPC
                upc = extract_upc_from_html(html)

                # Gerar links Amazon
                amazon_upc = f"https://www.amazon.com/s?k={upc}" if upc else ""
                amazon_title = f"https://www.amazon.com/s?k={quote_plus(full_title)}"

                products_with_upc.append({
                    "Nome do Produto": full_title,
                    "UPC": upc or "Não encontrado",
                    "Link Fornecedor": product['url'],
                    "Amazon (Busca por UPC)": amazon_upc or "N/A",
                    "Amazon (Busca por Nome)": amazon_title
                })

                if upc:
                    print(f"    UPC: {upc} ✓")
                else:
                    print(f"    UPC: Não encontrado ✗")

            except Exception as e:
                print(f"    Erro: {e}")
                continue

        await browser.close()

    # Gerar CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"discount_school_supply_{timestamp}.csv"

    print(f"\n{'='*80}")
    print(f"Gerando CSV: {filename}")
    print(f"{'='*80}\n")

    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        if products_with_upc:
            fieldnames = [
                "Nome do Produto",
                "UPC",
                "Link Fornecedor",
                "Amazon (Busca por UPC)",
                "Amazon (Busca por Nome)"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products_with_upc)

    print(f"✓ CSV gerado com sucesso!")
    print(f"✓ Total de produtos: {len(products_with_upc)}")
    print(f"✓ Produtos com UPC: {sum(1 for p in products_with_upc if p['UPC'] != 'Não encontrado')}")
    print(f"\nArquivo salvo em: {filename}")


async def main():
    # URL padrão - pode ser alterada
    url = "https://www.discountschoolsupply.com/all-categories/school-supplies/clearance/c/offer_clearance"

    print("\nDigite a URL da página (ou Enter para usar clearance):")
    user_input = input().strip()

    if user_input:
        url = user_input

    await scrape_discount_school_supply(url)


if __name__ == "__main__":
    asyncio.run(main())
