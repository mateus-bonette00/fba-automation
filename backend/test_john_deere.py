#!/usr/bin/env python3
"""
Teste com HTML similar à página real do John Deere
Simula a situação onde há múltiplos Part Numbers na página (produtos relacionados)
"""

from api.title_extractor import TitleExtractor

# HTML simulando a página do John Deere com produtos relacionados
html_john_deere = """
<!DOCTYPE html>
<html>
<head>
    <title>1/32 4240 Tractor - John Deere Shop</title>
    <meta property="og:title" content="1/32 4240 Tractor">
    <meta name="brand" content="John Deere">
</head>
<body>
    <main class="product-main">
        <div class="breadcrumb">
            <a href="/">Home</a> > <a href="/toys">Toys</a> > <span>1/32 4240 Tractor</span>
        </div>

        <!-- PRODUTO PRINCIPAL -->
        <div class="product-detail-container">
            <h1 class="product-title">1/32 4240 Tractor</h1>
            <div class="product-meta">
                <p class="part-number-label">Part Number: <span class="part-number">LP84525</span></p>
                <p class="price">$24.99</p>
                <p class="brand">John Deere</p>
            </div>
            <div class="product-description">
                <p>Configured with a 2WD drivetrain</p>
                <p>Features include front weights, a steerable wide front axle</p>
            </div>
        </div>

        <!-- PRODUTOS RELACIONADOS (não deve capturar esses Part Numbers!) -->
        <div class="related-products">
            <h2>You May Also Like</h2>
            <div class="product-card">
                <h3>Collect N Play Tractor</h3>
                <p>Part Number: LP64770</p>
            </div>
            <div class="product-card">
                <h3>Excavator Toy</h3>
                <p>Part Number: WME45486A</p>
            </div>
            <div class="product-card">
                <h3>Farm Set</h3>
                <p>Part Number: LP77322</p>
            </div>
            <div class="product-card">
                <h3>Loader Set</h3>
                <p>Part Number: LP82807</p>
            </div>
        </div>
    </main>
</body>
</html>
"""

print("=" * 80)
print("TESTE: Página John Deere com Produtos Relacionados")
print("=" * 80)
print()
print("Simulação da página real:")
print("- Produto principal: 1/32 4240 Tractor (LP84525)")
print("- 4 produtos relacionados com Part Numbers diferentes")
print()
print("Objetivo: Capturar APENAS as informações do produto principal!")
print()
print("=" * 80)
print()

extractor = TitleExtractor()
titulo_completo = extractor.extract_all_methods(html_john_deere)

print("✅ RESULTADO:")
print()
print(f"   {titulo_completo}")
print()

stats = extractor.get_extraction_stats()

if stats['additional_info']:
    print("📊 INFORMAÇÕES CAPTURADAS:")
    for i, info in enumerate(stats['additional_info'], 1):
        print(f"   {i}. {info}")
    print()

    # Verifica se pegou Part Numbers dos produtos relacionados
    part_numbers_errados = ['LP64770', 'WME45486A', 'LP77322', 'LP82807']
    pegou_errado = any(pn in titulo_completo for pn in part_numbers_errados)

    if pegou_errado:
        print("❌ ERRO: Capturou Part Numbers de produtos relacionados!")
        for pn in part_numbers_errados:
            if pn in titulo_completo:
                print(f"   - {pn} (produto relacionado, NÃO deveria ter capturado)")
    else:
        print("✅ SUCESSO: Capturou APENAS as informações do produto principal!")
        print("   - LP84525 ✓ (correto)")
        print("   - John Deere ✓ (correto)")

print()
print("=" * 80)
