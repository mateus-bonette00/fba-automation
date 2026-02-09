#!/usr/bin/env python3
"""
Teste do extrator de título com informações adicionais
Demonstra a captura de Part Number, Model, SKU, etc junto com o título
"""

from api.title_extractor import TitleExtractor

# HTML de exemplo similar ao da imagem (us.tomy.com)
html_exemplo = """
<!DOCTYPE html>
<html>
<head>
    <title>Collect N Play 1/32 Tractor With Loader - TOMY</title>
    <meta property="og:title" content="Collect N Play 1/32 Tractor With Loader">
    <meta name="brand" content="John Deere">
    <meta itemprop="sku" content="LP64770">
</head>
<body>
    <div class="product-page">
        <h1 class="product-title">Collect N Play 1/32 Tractor With Loader</h1>
        <div class="product-meta">
            <p class="part-number">Part Number: LP64770</p>
            <p class="brand">Brand: John Deere</p>
        </div>
        <div class="product-details">
            <dl>
                <dt>Model</dt>
                <dd>1/32 Scale</dd>
                <dt>Age</dt>
                <dd>3+</dd>
                <dt>SKU</dt>
                <dd>LP64770</dd>
            </dl>
        </div>
        <p class="price">$5.99</p>
        <p class="description">
            Features a functional loader
            Durable die-cast and plastic construction
            Authentic decoration
            Ages 3+
        </p>
    </div>
</body>
</html>
"""

# HTML de exemplo 2 - outro formato
html_exemplo_2 = """
<!DOCTYPE html>
<html>
<head>
    <title>Premium Widget Pro - Model XYZ-2000</title>
</head>
<body>
    <h1>Premium Widget Pro</h1>
    <div class="product-info">
        <span>Model Number: XYZ-2000</span>
    </div>
    <table class="specs">
        <tr>
            <th>Part #</th>
            <td>ABC-12345</td>
        </tr>
        <tr>
            <th>Manufacturer</th>
            <td>WidgetCorp</td>
        </tr>
    </table>
</body>
</html>
"""

# HTML de exemplo 3 - formato inline
html_exemplo_3 = """
<!DOCTYPE html>
<html>
<body>
    <h1>Super Product XL</h1>
    <p>Item Number: ITM-99887 | MPN: MFG-7654</p>
</body>
</html>
"""

def testar_extracao():
    print("=" * 80)
    print("TESTE: Extração de Título com Informações Adicionais")
    print("=" * 80)
    print()

    exemplos = [
        ("Exemplo 1 - TOMY Tractor (similar à imagem)", html_exemplo),
        ("Exemplo 2 - Widget Pro", html_exemplo_2),
        ("Exemplo 3 - Inline Info", html_exemplo_3),
    ]

    for nome, html in exemplos:
        print(f"\n{'─' * 80}")
        print(f"🧪 {nome}")
        print('─' * 80)

        extractor = TitleExtractor()
        titulo_completo = extractor.extract_all_methods(html)

        print(f"\n📦 TÍTULO COMPLETO:")
        print(f"   {titulo_completo}")

        stats = extractor.get_extraction_stats()

        print(f"\n📊 DETALHES DA EXTRAÇÃO:")
        print(f"   Método usado: {stats['method_used']}")
        print(f"   Tentativas: {stats['methods_tried']}")

        if stats['additional_info']:
            print(f"\n✨ INFORMAÇÕES ADICIONAIS ENCONTRADAS:")
            for i, info in enumerate(stats['additional_info'], 1):
                print(f"   {i}. {info}")
        else:
            print(f"\n⚠️  Nenhuma informação adicional encontrada")

        print()

    print("=" * 80)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 80)
    print()
    print("💡 COMO USAR NA BUSCA DA AMAZON:")
    print()
    print("   Antes: 'Collect N Play 1/32 Tractor With Loader'")
    print("   Agora: 'Collect N Play 1/32 Tractor With Loader | LP64770 | John Deere'")
    print()
    print("   ✅ Muito mais específico!")
    print("   ✅ Maior chance de achar o produto exato!")
    print("   ✅ Part Number ajuda muito na busca!")
    print()

if __name__ == "__main__":
    testar_extracao()
