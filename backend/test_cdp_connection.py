#!/usr/bin/env python3
"""
Script para testar a conexão CDP e listar todas as abas disponíveis
"""
import asyncio
import sys
from playwright.async_api import async_playwright

async def test_cdp():
    devtools_url = "http://127.0.0.1:9222"

    print(f"🔍 Testando conexão com: {devtools_url}")
    print("=" * 60)

    try:
        async with async_playwright() as pw:
            print("✅ Playwright iniciado")

            # Tenta conectar ao navegador
            browser = await pw.chromium.connect_over_cdp(devtools_url)
            print(f"✅ Conectado ao navegador via CDP")

            # Lista todos os contextos
            contexts = browser.contexts
            print(f"\n📂 Contextos encontrados: {len(contexts)}")

            total_pages = 0
            for i, ctx in enumerate(contexts):
                print(f"\n  Contexto {i + 1}:")
                pages = ctx.pages
                print(f"    └─ Páginas: {len(pages)}")

                for j, page in enumerate(pages):
                    url = page.url
                    title = ""
                    try:
                        title = await page.title()
                    except:
                        title = "(sem título)"

                    print(f"      {j + 1}. {title[:50]}")
                    print(f"         URL: {url}")
                    total_pages += 1

            print(f"\n📊 Total de páginas/abas encontradas: {total_pages}")

            await browser.close()
            print("\n✅ Teste concluído com sucesso!")

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("\n💡 Dicas:")
        print("   1. Verifique se o Chrome está rodando com:")
        print("      google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug")
        print("   2. Tente matar processos na porta 9222:")
        print("      sudo fuser -k 9222/tcp")
        print("   3. Tente acessar: http://127.0.0.1:9222/json/version")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_cdp())
