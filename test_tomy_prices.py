#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json

print("="*80)
print("  TESTE DE PREÇOS - us.tomy.com")
print("="*80)
print()

url = "https://us.tomy.com/brands/ertl/"

print(f"🌐 Buscando: {url}")
print()

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)
    print(f"✅ Status HTTP: {response.status_code}")
    print(f"   Encoding: {response.encoding}")
    print()

    soup = BeautifulSoup(response.content, 'html.parser')

    print("📍 Procurando elementos de preço na página...")
    print()

    price_patterns = [
        ('price--withoutTax', 'BigCommerce: .price--withoutTax'),
        ('price--main', 'BigCommerce: .price--main'),
        ('price', 'Generic: .price'),
        ('product-price', 'Generic: .product-price'),
        ('amount', 'Generic: .amount'),
    ]

    found_any = False

    for pattern, description in price_patterns:
        elements = soup.find_all(class_=pattern)
        if elements:
            found_any = True
            print(f"✅ Encontrado: {description}")
            print(f"   Total: {len(elements)} elementos")
            print(f"   Primeiros 3:")
            for i, el in enumerate(elements[:3], 1):
                text = el.get_text(strip=True)
                print(f"      {i}. '{text}'")
            print()

    if not found_any:
        print("❌ Nenhum elemento de preço encontrado com padrões conhecidos")
        print()
        print("🔍 Buscando por qualquer texto com $...")
        text = soup.get_text()
        lines = text.split('\n')
        price_lines = [l.strip() for l in lines if '$' in l and len(l.strip()) < 100]

        if price_lines:
            print(f"   Encontrados {len(price_lines)} linhas com $:")
            for line in price_lines[:10]:
                print(f"      - {line}")
        else:
            print("   ❌ Nenhuma linha com $ encontrada!")
            print()
            print("   ⚠️  POSSÍVEL CAUSA:")
            print("   - Site bloqueou por IP fora dos EUA")
            print("   - VPN não está ativa ou com problema")
            print("   - Site retorna página HTML diferente para geolocalização")

    print()
    print("="*80)
    print("  ANÁLISE DO HTML")
    print("="*80)
    print()

    product_divs = soup.find_all(class_='product')
    if product_divs:
        print(f"✅ Encontrados {len(product_divs)} elementos .product")
        print()
        print("   Primeiro produto:")
        first = product_divs[0]
        print(f"      HTML (primeiros 200 chars):")
        print(f"      {str(first)[:200]}...")
    else:
        print("❌ Nenhum .product encontrado")

        # Tenta outros seletores
        alt_selectors = ['.card', '.item', '.product-item', '[data-product]']
        for sel in alt_selectors:
            items = soup.find_all(sel)
            if items:
                print(f"✅ Alternativa encontrada: {sel} ({len(items)} items)")

except requests.exceptions.RequestException as e:
    print(f"❌ Erro na requisição: {e}")

print()
print("="*80)
