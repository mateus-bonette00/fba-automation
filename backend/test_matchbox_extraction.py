#!/usr/bin/env python3
"""
Teste: Extração de Brand + Modelo (SEM Part Number)
Valida que o sistema captura APENAS Brand + Escala para busca na Amazon
"""

from api.title_extractor import TitleExtractor

# HTML simulando a página Matchbox (exemplo do usuário)
html_matchbox = """
<!DOCTYPE html>
<html>
<head>
    <title>2024 Porsche Taycan - Matchbox</title>
    <meta property="og:title" content="2024 Porsche Taycan">
    <meta name="brand" content="Matchbox">
</head>
<body>
    <main class="product-main">
        <div class="product-detail-container">
            <h1 class="product-title">2024 Porsche Taycan</h1>
            <div class="product-meta">
                <p class="item-number">Item Number: <span>MB-2024-HVL75</span></p>
                <p class="brand">Brand: Matchbox</p>
                <p class="scale">Scale: 1:64</p>
                <p class="price">$5.99</p>
            </div>
            <div class="product-description">
                <p>Detailed die-cast model</p>
                <p>Authentic Porsche design</p>
            </div>
        </div>
    </main>
</body>
</html>
"""

# HTML John Deere (teste anterior)
html_john_deere = """
<!DOCTYPE html>
<html>
<head>
    <title>1/32 4240 Tractor - John Deere Shop</title>
    <meta property="og:title" content="1/32 4240 Tractor">
</head>
<body>
    <main>
        <div class="product-detail-container">
            <h1>1/32 4240 Tractor</h1>
            <div class="product-meta">
                <p>Part Number: <span>LP84525</span></p>
                <p class="brand">John Deere</p>
            </div>
        </div>
    </main>
</body>
</html>
"""

# HTML Johnny Lightning
html_johnny_lightning = """
<!DOCTYPE html>
<html>
<head>
    <title>1963 Pontiac Tempest - Johnny Lightning</title>
</head>
<body>
    <div class="product-container">
        <h1>1:64 1963 Pontiac Tempest</h1>
        <div class="product-info">
            <p>Item Number: JL-CG-06211</p>
            <p>Manufacturer: Johnny Lightning</p>
        </div>
    </div>
</body>
</html>
"""

def test_extraction(html, test_name, expected_brand, expected_model):
    print(f"\n{'=' * 80}")
    print(f"TESTE: {test_name}")
    print('=' * 80)
    print()

    extractor = TitleExtractor()
    titulo_completo = extractor.extract_all_methods(html)

    print(f"✅ TÍTULO COMPLETO CAPTURADO:")
    print(f"   {titulo_completo}")
    print()

    stats = extractor.get_extraction_stats()

    if stats['additional_info']:
        print(f"📊 INFORMAÇÕES ADICIONAIS:")
        for i, info in enumerate(stats['additional_info'], 1):
            print(f"   {i}. {info}")
        print()

    # Validação
    success = True

    # Verifica se tem a Brand esperada
    if expected_brand:
        if expected_brand.lower() in titulo_completo.lower():
            print(f"✅ Brand encontrada: {expected_brand}")
        else:
            print(f"❌ ERRO: Brand '{expected_brand}' não encontrada!")
            success = False

    # Verifica se tem o Modelo esperado
    if expected_model:
        if expected_model in titulo_completo:
            print(f"✅ Modelo encontrado: {expected_model}")
        else:
            print(f"❌ ERRO: Modelo '{expected_model}' não encontrado!")
            success = False

    # Verifica se NÃO capturou Part Numbers
    part_number_patterns = ['MB-2024-HVL75', 'LP84525', 'JL-CG-06211', 'Item Number:', 'Part Number:']
    has_part_number = any(pn in titulo_completo for pn in part_number_patterns)

    if has_part_number:
        print()
        print("❌ ERRO: Capturou Part Number/Item Number (não deveria!):")
        for pn in part_number_patterns:
            if pn in titulo_completo:
                print(f"   - {pn}")
        success = False
    else:
        print("✅ Part Numbers ignorados corretamente (não aparecem no título)")

    print()
    if success:
        print("🎉 TESTE PASSOU!")
    else:
        print("⚠️  TESTE FALHOU!")

    print()
    return success

# Executar testes
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("VALIDAÇÃO: Extração de Brand + Modelo (SEM Part Numbers)")
    print("=" * 80)
    print()
    print("OBJETIVO:")
    print("  ✅ Capturar APENAS: Brand (Matchbox, John Deere, etc) + Modelo (1:64, 1/32)")
    print("  ❌ NÃO capturar: Part Number, Item Number, SKU")
    print()
    print("MOTIVO:")
    print("  Part Numbers não funcionam bem na busca da Amazon")
    print("  'Matchbox 2024 Porsche Taycan 1:64' > 'MB-2024-HVL75'")
    print()

    all_passed = True

    # Teste 1: Matchbox
    all_passed &= test_extraction(
        html_matchbox,
        "Matchbox Porsche (exemplo do usuário)",
        expected_brand="Matchbox",
        expected_model="1:64"
    )

    # Teste 2: John Deere
    all_passed &= test_extraction(
        html_john_deere,
        "John Deere Tractor",
        expected_brand="John Deere",
        expected_model="1/32"
    )

    # Teste 3: Johnny Lightning
    all_passed &= test_extraction(
        html_johnny_lightning,
        "Johnny Lightning Pontiac",
        expected_brand="Johnny Lightning",
        expected_model="1:64"
    )

    # Resultado final
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        print()
        print("Sistema configurado corretamente:")
        print("  - Captura Brand + Modelo")
        print("  - Ignora Part Numbers")
        print("  - Queries otimizadas para Amazon")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print()
        print("Verifique os erros acima")
    print("=" * 80)
    print()
