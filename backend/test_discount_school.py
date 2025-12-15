#!/usr/bin/env python3
"""
Script de teste para analisar a estrutura do Discount School Supply
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def test_site():
    url = "https://www.discountschoolsupply.com/all-categories/school-supplies/clearance/c/offer_clearance"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print(f"\n{'='*80}")
        print("TESTANDO DISCOUNT SCHOOL SUPPLY")
        print(f"{'='*80}\n")

        print(f"Acessando: {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        print("\n--- ANÁLISE DE PRODUTOS ---\n")

        # Testar diferentes seletores
        selectors_to_test = [
            ".product",
            ".product-item",
            "article.product",
            "[class*='product']",
            ".productListItem",
            ".product-list-item",
            ".grid-item",
            "[data-product]",
            ".item",
            ".product-card"
        ]

        for selector in selectors_to_test:
            elements = soup.select(selector)
            if elements:
                print(f"✓ {selector}: {len(elements)} elementos")
                if len(elements) > 0:
                    first = elements[0]
                    print(f"  Classes: {first.get('class')}")

                    # Tentar encontrar título
                    title = None
                    for title_sel in ["h2", "h3", ".title", ".name", "a"]:
                        title_elem = first.select_one(title_sel)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if title:
                                print(f"  Título: {title[:60]}")
                                break

                    # Tentar encontrar link
                    link = first.select_one("a[href]")
                    if link:
                        href = link.get("href")
                        print(f"  Link: {href[:80]}")

                    print()

        print("\n--- ANÁLISE DE PAGINAÇÃO ---\n")

        pagination_selectors = [
            ".pagination a",
            ".page-numbers a",
            "[class*='pagination'] a",
            "nav a",
            "a[href*='page']",
            ".pager a"
        ]

        for selector in pagination_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"✓ {selector}: {len(elements)} links")
                if len(elements) > 0:
                    sample_links = [e.get("href") for e in elements[:3]]
                    for link in sample_links:
                        if link:
                            print(f"  - {link}")

        # Tentar encontrar o número total de páginas
        print("\n--- INFORMAÇÕES DE PAGINAÇÃO ---\n")

        # Verificar se tem botões de página
        page_buttons = await page.query_selector_all("button, a")
        for btn in page_buttons[:50]:  # Limitar para não demorar muito
            text = await btn.text_content()
            if text and text.strip().isdigit():
                print(f"Botão de página encontrado: {text}")

        # Verificar se tem um elemento que mostra "1-48 of 346 items"
        items_info = soup.find(string=lambda x: x and "of" in x and "items" in x.lower())
        if items_info:
            print(f"Info de items: {items_info}")

        print("\n--- TESTANDO CLIQUE NA PÁGINA 2 ---\n")

        try:
            # Tentar encontrar e clicar no botão da página 2
            page_2 = await page.query_selector("text=2")
            if page_2:
                print("Encontrei botão da página 2, clicando...")
                await page_2.click()
                await page.wait_for_timeout(3000)
                new_url = page.url
                print(f"Nova URL: {new_url}")
        except:
            print("Não consegui clicar na página 2")

        print(f"\n{'='*80}")
        print("Análise completa! Pressione Enter para fechar o navegador...")
        print(f"{'='*80}\n")

        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_site())
