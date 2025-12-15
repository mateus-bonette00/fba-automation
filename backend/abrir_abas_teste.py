#!/usr/bin/env python3
"""
Script para abrir abas de teste no Chrome com remote debugging
"""
import asyncio
from playwright.async_api import async_playwright

async def abrir_abas_teste():
    devtools_url = "http://127.0.0.1:9222"

    # URLs de teste - você pode substituir pelas URLs reais dos produtos
    urls_teste = [
        "https://www.amleo.com/15-inch-orange-chainsaw-strap-with-snap/p/140-A1002",
        "https://www.amleo.com/badger-light-duty-ground-anchor-by-gripple/p/140-BA1",
        "https://www.amleo.com/self-watering-napa-round-8-planter-rust/p/140-NA008RU",
    ]

    print("🌐 Abrindo abas de teste no Chrome...")
    print("=" * 60)

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(devtools_url)

            # Pega o primeiro contexto disponível
            context = browser.contexts[0]

            print(f"📂 Usando contexto com {len(context.pages)} página(s) existente(s)")

            # Abre novas abas
            for i, url in enumerate(urls_teste, 1):
                print(f"\n{i}. Abrindo: {url}")
                page = await context.new_page()
                await page.goto(url, timeout=30000)
                print(f"   ✅ Carregado")

            print(f"\n✅ Total de abas abertas: {len(context.pages)}")
            print("\n💡 Agora volte para a aplicação e clique em 'Capturar Abas'")
            print("   As abas permanecerão abertas para você processar.")

            await browser.close()

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        return

if __name__ == "__main__":
    asyncio.run(abrir_abas_teste())
