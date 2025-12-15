#!/usr/bin/env python3
"""
Script para testar extração de UPC de uma página específica
"""
import asyncio
from playwright.async_api import async_playwright

async def test_upc_extraction():
    devtools_url = "http://127.0.0.1:9222"

    print("🔍 Testando extração de UPC...")
    print("=" * 80)

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(devtools_url)
            context = browser.contexts[0]
            pages = context.pages

            if not pages:
                print("❌ Nenhuma aba aberta!")
                return

            # Pega a primeira página
            page = pages[0]
            url = page.url

            print(f"\n📄 Testando: {url}")
            print("=" * 80)

            # Pega o HTML da página
            html = await page.content()

            # Procura por "UPC" no HTML
            import re

            # Busca padrões comuns de UPC
            patterns = [
                r'["\']upc["\']\s*:\s*["\']?(\d{8,14})["\']?',
                r'["\']gtin["\']\s*:\s*["\']?(\d{8,14})["\']?',
                r'<.*?UPC:?\s*<\/.*?>.*?(\d{12,14})',
                r'data-upc=["\'](\d{8,14})["\']',
                r'itemprop=["\']gtin\d*["\']\s+content=["\'](\d{8,14})["\']',
                r'UPC:\s*<\/[^>]+>\s*(\d{12,14})',
            ]

            found = []
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    found.extend(matches)

            if found:
                print(f"\n✅ UPCs encontrados no HTML:")
                for upc in set(found):
                    print(f"   - {upc}")
            else:
                print("\n❌ Nenhum UPC encontrado com regex!")

                # Procura a palavra "UPC" no HTML
                if 'UPC' in html or 'upc' in html:
                    print("\n⚠️  Mas a palavra 'UPC' aparece no HTML!")

                    # Mostra o contexto
                    idx = html.upper().find('UPC:')
                    if idx != -1:
                        context_snippet = html[max(0, idx-100):min(len(html), idx+300)]
                        print(f"\n📝 Contexto ao redor de 'UPC:':")
                        print(context_snippet[:500])

            # Testa o método atual do sistema
            print("\n" + "=" * 80)
            print("🔧 Testando extração do sistema atual...")
            print("=" * 80)

            # Importa o extrator
            import sys
            sys.path.insert(0, '/home/mateus/Documentos/Qota Store/códigos/fba-automation/backend')

            from api.upc_extractor import UPCExtractor

            extractor = UPCExtractor()
            upc_result = extractor.extract_all_methods(html)

            if upc_result:
                print(f"\n✅ Sistema extraiu: {upc_result}")
                print(f"   Método usado: {extractor.method_used}")
                print(f"   Métodos tentados: {len(extractor.methods_tried)}")
            else:
                print(f"\n❌ Sistema NÃO conseguiu extrair UPC")
                print(f"   Métodos tentados: {len(extractor.methods_tried)}")
                for method in extractor.methods_tried:
                    print(f"      - {method}")

            await browser.close()

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_upc_extraction())
