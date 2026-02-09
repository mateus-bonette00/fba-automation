#!/usr/bin/env python3
"""Debug: Ver TUDO que o extrator está encontrando"""

from api.title_extractor import TitleExtractor

html = """
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
        </div>
    </main>
</body>
</html>
"""

extractor = TitleExtractor()

# Monkey patch para ver tudo que está sendo capturado
from bs4 import BeautifulSoup
import re

soup = BeautifulSoup(html, 'html.parser')
additional_info = []

# 1. Meta tags
print("=" * 80)
print("1. BUSCANDO EM META TAGS:")
print("=" * 80)
for meta in soup.find_all('meta'):
    name = (meta.get('name') or meta.get('property') or meta.get('itemprop') or '').lower()
    content = meta.get('content', '').strip()
    print(f"  Meta: name='{name}', content='{content}'")
    if content and len(content) < 100:
        if any(kw in name for kw in ['brand', 'manufacturer']):
            additional_info.append(content)
            print(f"    ✅ ADICIONADO: {content}")

# 2. Busca por "Scale: 1:64"
print()
print("=" * 80)
print("2. BUSCANDO PADRÃO 'Scale: 1:64' NO TEXTO:")
print("=" * 80)

h1_tag = soup.find('h1')
product_container = None
if h1_tag:
    for parent in h1_tag.parents:
        if parent.name in ['section', 'div', 'article', 'main']:
            classes = ' '.join(parent.get('class', [])).lower()
            if any(kw in classes for kw in ['product', 'item', 'detail', 'pdp', 'main-content']):
                product_container = parent
                break

if not product_container:
    product_container = soup

text_content = product_container.get_text()
print(f"Texto do container (primeiros 500 chars):")
print(text_content[:500])
print()

keywords = ['scale', 'model']
for keyword in keywords:
    patterns = [
        rf'{re.escape(keyword)}\s*:\s*([A-Z0-9\-_#\/\.\s]+?)(?:\s*\||$|\n|<)',
        rf'{re.escape(keyword)}\s*:\s*([A-Z0-9\-_#\/]+)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text_content, re.IGNORECASE)
        for match in matches:
            value = match.group(1).strip()
            value = ' '.join(value.split())
            print(f"  Encontrado com '{keyword}': '{value}'")
            if len(value) >= 3 and len(value) < 50:
                additional_info.append(value)
                print(f"    ✅ ADICIONADO: {value}")

print()
print("=" * 80)
print("INFORMAÇÕES CAPTURADAS:")
print("=" * 80)
for i, info in enumerate(additional_info, 1):
    print(f"{i}. {info}")

# Agora testa a extração completa
print()
print("=" * 80)
print("TESTANDO EXTRAÇÃO COMPLETA:")
print("=" * 80)
titulo = extractor.extract_all_methods(html)
print(f"Título: {titulo}")
stats = extractor.get_extraction_stats()
print(f"Additional Info: {stats['additional_info']}")
