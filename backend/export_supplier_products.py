#!/usr/bin/env python3
"""
Script para extrair produtos de um fornecedor e gerar CSV
com links para Amazon (busca por UPC e por nome)
"""

import asyncio
import csv
import re
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
import json
from api.upc_extractor import extract_upc_from_html


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
    """
    Extrai produtos da página.
    Você pode precisar customizar os seletores CSS dependendo do site.
    """
    soup = BeautifulSoup(html, "html.parser")
    products = []

    # CUSTOMIZE AQUI: seletores típicos de produtos em páginas de e-commerce
    # Exemplo genérico - você pode precisar ajustar para seu fornecedor específico
    product_selectors = [
        ".product",
        ".product-item",
        ".woocommerce-LoopProduct-link",
        "article.product",
        ".products .product",
        "li.product",
        "div.product-card",
        ".product-list-item"
    ]

    product_elements = []
    for selector in product_selectors:
        elements = soup.select(selector)
        if elements:
            product_elements = elements
            break

    for elem in product_elements:
        # Extrai título
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

        # Extrai URL do produto
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
        await page.wait_for_timeout(1000)  # Pequena espera para JS carregar

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Extrai título completo
        title = ""
        title_selectors = [
            "h1.product_title",
            "h1.entry-title",
            "h1",
            "meta[property='og:title']",
            "meta[name='twitter:title']"
        ]

        for sel in title_selectors:
            el = soup.select_one(sel)
            if el:
                if el.name == "meta" and el.get("content"):
                    title = el["content"].strip()
                else:
                    txt = el.get_text(strip=True)
                    if txt:
                        title = txt
                if title:
                    break

        # Extrai UPC
        upc = extract_upc_from_html(html)

        return {
            "title": title,
            "upc": upc,
            "url": url
        }
    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")
        return {
            "title": "",
            "upc": None,
            "url": url
        }


async def get_all_page_urls(page: Page, start_url: str) -> list[str]:
    """
    Detecta automaticamente paginação e retorna todas as URLs de páginas.
    Você pode precisar customizar os seletores de paginação.
    """
    urls = [start_url]

    try:
        await page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # CUSTOMIZE AQUI: seletores comuns de paginação
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

        # Filtra apenas URLs válidas da mesma seção
        base_path = start_url.split("?")[0].rstrip("/")
        valid_pages = []

        for url in page_links:
            url_base = url.split("?")[0].rstrip("/")
            if url_base.startswith(base_path) or "/page/" in url or "paged=" in url:
                valid_pages.append(url)

        if valid_pages:
            urls.extend(sorted(set(valid_pages)))
            print(f"Encontradas {len(urls)} páginas para varrer")
        else:
            print("Apenas 1 página encontrada (sem paginação)")

    except Exception as e:
        print(f"Erro ao detectar paginação: {e}")

    return list(set(urls))


async def scrape_supplier(supplier_url: str, output_file: str = None):
    """
    Varre todas as páginas do fornecedor e extrai produtos.

    Args:
        supplier_url: URL da seção/categoria do fornecedor
        output_file: Nome do arquivo CSV de saída (opcional)
    """
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"produtos_fornecedor_{timestamp}.csv"

    all_products = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print(f"\nIniciando scraping de: {supplier_url}")
        print("="*80)

        # 1. Descobrir todas as páginas
        print("\n[1/3] Detectando paginação...")
        page_urls = await get_all_page_urls(page, supplier_url)

        # 2. Extrair produtos de cada página
        print(f"\n[2/3] Extraindo produtos de {len(page_urls)} página(s)...")
        product_urls = []

        for i, page_url in enumerate(page_urls, 1):
            print(f"  - Varrendo página {i}/{len(page_urls)}: {page_url}")
            try:
                await page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(1500)

                html = await page.content()
                products = extract_products_from_page(html, page_url)
                product_urls.extend(products)
                print(f"    → {len(products)} produtos encontrados")
            except Exception as e:
                print(f"    ✗ Erro: {e}")

        print(f"\nTotal de produtos encontrados: {len(product_urls)}")

        # 3. Acessar cada produto para extrair UPC
        print(f"\n[3/3] Extraindo detalhes dos produtos...")
        for i, product in enumerate(product_urls, 1):
            print(f"  [{i}/{len(product_urls)}] {product['title'][:60]}")

            details = await scrape_product_details(page, product['url'])

            # Monta o produto completo
            title = details['title'] or product['title']
            upc = details['upc']
            supplier_link = details['url']

            # Gera links da Amazon
            amazon_upc_link = ""
            amazon_title_link = ""

            if upc:
                amazon_upc_link = f"https://www.amazon.com/s?k={upc}"

            if title:
                search_query = quote_plus(title)
                amazon_title_link = f"https://www.amazon.com/s?k={search_query}"

            all_products.append({
                "Nome do Produto": title,
                "UPC": upc or "Não encontrado",
                "Link Fornecedor": supplier_link,
                "Amazon (Busca por UPC)": amazon_upc_link or "N/A",
                "Amazon (Busca por Nome)": amazon_title_link
            })

            print(f"    UPC: {upc or 'Não encontrado'}")

        await browser.close()

    # Gera CSV
    print(f"\n{'='*80}")
    print(f"Gerando CSV: {output_file}")

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        if all_products:
            fieldnames = [
                "Nome do Produto",
                "UPC",
                "Link Fornecedor",
                "Amazon (Busca por UPC)",
                "Amazon (Busca por Nome)"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_products)

    print(f"✓ CSV gerado com sucesso!")
    print(f"✓ Total de produtos: {len(all_products)}")
    print(f"✓ Produtos com UPC: {sum(1 for p in all_products if p['UPC'] != 'Não encontrado')}")
    print(f"\nArquivo salvo em: {output_file}")


async def main():
    """Função principal - configure aqui"""

    # CONFIGURE AQUI: URL da seção/categoria do fornecedor
    supplier_url = input("\nDigite a URL da seção/categoria do fornecedor: ").strip()

    if not supplier_url:
        print("URL inválida!")
        return

    # Nome do arquivo de saída (opcional)
    output = input("Nome do arquivo CSV (Enter para nome automático): ").strip()

    await scrape_supplier(supplier_url, output if output else None)


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" EXTRATOR DE PRODUTOS DO FORNECEDOR PARA CSV ".center(80))
    print("="*80)
    asyncio.run(main())
