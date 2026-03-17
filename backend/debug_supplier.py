import asyncio
import sys
import logging
from playwright.async_api import async_playwright

sys.path.append('.')

from automation.supplierCrawler import fetch_product_links_from_page, parse_price_details
from automation.sheets import get_next_supplier

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_supplier(supplier_index="2", devtools_url="http://127.0.0.1:9222"):
    """Debug um fornecedor específico."""

    try:
        supplier = get_next_supplier(start_index=supplier_index, skip_indices=[])
        if not supplier:
            logger.error(f"Fornecedor índice {supplier_index} não encontrado")
            return

        logger.info(f"✅ Fornecedor encontrado: {supplier}")
        supplier_url = supplier.get("url")

        async with async_playwright() as pw:
            logger.info(f"🔌 Conectando ao Chrome em {devtools_url}...")
            browser = await pw.chromium.connect_over_cdp(devtools_url)
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()

            logger.info(f"🌐 Navegando para: {supplier_url}")
            await page.goto(supplier_url, wait_until="domcontentloaded", timeout=45000)

            logger.info("⏱️ Aguardando estabilização da página...")
            await asyncio.sleep(2)

            page_title = await page.title()
            logger.info(f"📄 Título da página: {page_title}")

            current_url = page.url
            logger.info(f"📍 URL atual (após redirects): {current_url}")

            logger.info("📸 Extraindo links de produtos...")
            links = await fetch_product_links_from_page(page)
            logger.info(f"✅ Total de links extraídos: {len(links)}")

            logger.info("\n" + "="*80)
            logger.info("ANÁLISE DETALHADA DOS LINKS")
            logger.info("="*80 + "\n")

            cart_links = []
            valid_links = []
            zero_price_links = []
            unparseable_price_links = []

            for idx, item in enumerate(links, 1):
                url = item.get("url", "")
                price_text = item.get("price_text", "").strip()

                logger.info(f"\n[Link {idx}/{len(links)}]")
                logger.info(f"  URL: {url}")
                logger.info(f"  Preço Raw: '{price_text}'")

                url_lower = url.lower()

                if "cart.php?action=" in url_lower or "/cart/add" in url_lower:
                    logger.warning(f"  ⚠️  TIPO: URL de carrinho (FILTRADA)")
                    cart_links.append(url)
                    continue

                if not price_text:
                    logger.warning(f"  ⚠️  TIPO: Sem preço extraído")
                    price_info = {"value": None, "status": "missing", "raw": ""}
                else:
                    price_info = parse_price_details(price_text)
                    logger.info(f"  Preço Parseado: {price_info}")

                    if price_info.get("status") == "zero":
                        logger.warning(f"  ⚠️  TIPO: Preço zero (FILTRADA)")
                        zero_price_links.append(url)
                        continue
                    elif price_info.get("status") == "invalid_format":
                        logger.warning(f"  ⚠️  TIPO: Preço não parseável (MANTIDA para validação)")
                        unparseable_price_links.append((url, price_text))
                    elif price_info.get("status") == "ok":
                        logger.info(f"  ✅ TIPO: Preço válido")
                        valid_links.append(url)
                    else:
                        logger.info(f"  ℹ️  TIPO: {price_info.get('status')}")

            logger.info("\n" + "="*80)
            logger.info("RESUMO DO DEBUG")
            logger.info("="*80)
            logger.info(f"\n📊 Estatísticas:")
            logger.info(f"   Total de links extraídos: {len(links)}")
            logger.info(f"   Links de carrinho (filtrados): {len(cart_links)}")
            logger.info(f"   Links com preço $0.00 (filtrados): {len(zero_price_links)}")
            logger.info(f"   Links com preço não parseável (mantidos): {len(unparseable_price_links)}")
            logger.info(f"   Links com preço válido: {len(valid_links)}")
            logger.info(f"   Total válido para captura: {len(unparseable_price_links) + len(valid_links)}")

            if zero_price_links:
                logger.warning(f"\n⚠️  PROBLEMA DETECTADO: {len(zero_price_links)} produtos com preço $0.00")
                logger.warning("   Possíveis causas:")
                logger.warning("   1. IP fora dos EUA (site us.tomy.com bloqueia)")
                logger.warning("   2. VPN desligada ou com problema")
                logger.warning("   3. Geolocalização incorreta")
                logger.warning("\n   Exemplo de links com $0.00:")
                for url in zero_price_links[:3]:
                    logger.warning(f"   - {url}")

            if cart_links:
                logger.warning(f"\n🛒 Detectados {len(cart_links)} links de carrinho (agora filtrados)")
                logger.warning("   Exemplos:")
                for url in cart_links[:2]:
                    logger.warning(f"   - {url}")

            if unparseable_price_links:
                logger.warning(f"\n📝 {len(unparseable_price_links)} produtos com preço não parseável na listagem")
                logger.warning("   Serão abertos para validação no produto. Exemplos:")
                for url, price_text in unparseable_price_links[:2]:
                    logger.warning(f"   - {price_text} -> {url}")

            logger.info("\n" + "="*80)
            logger.info("PRÓXIMOS PASSOS")
            logger.info("="*80)
            logger.info("\n1. Verifique se há links de carrinho no resultado (agora devem estar filtrados)")
            logger.info("2. Se houver preço $0.00:")
            logger.info("   - Verifique se VPN US está ativa no servidor: nmcli connection show")
            logger.info("   - Teste IP: curl https://ipinfo.io")
            logger.info("   - Deve estar em US/USA")
            logger.info("3. Links não parseáveis serão abertos nas abas (comportamento esperado)")

            await browser.close()

    except Exception as e:
        logger.error(f"❌ Erro durante debug: {e}", exc_info=True)

if __name__ == "__main__":
    supplier_idx = sys.argv[1] if len(sys.argv) > 1 else "2"
    devtools = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:9222"

    logger.info(f"\n🔍 Iniciando debug do fornecedor índice {supplier_idx}")
    logger.info(f"   DevTools URL: {devtools}\n")

    asyncio.run(debug_supplier(supplier_idx, devtools))
