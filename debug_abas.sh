#!/bin/bash

echo "=========================================="
echo "🔍 DEBUG: Verificando abas abertas"
echo "=========================================="
echo ""

# Verificar se Chrome está rodando na porta 9222
echo "1. Verificando conexão com Chrome Debug..."
if curl -s http://127.0.0.1:9222/json/version > /dev/null 2>&1; then
    echo "   ✅ Chrome conectado na porta 9222"
else
    echo "   ❌ Chrome NÃO está rodando na porta 9222"
    exit 1
fi

echo ""
echo "2. Listando todas as abas abertas:"
echo ""

# Lista todas as abas com formatação
curl -s http://127.0.0.1:9222/json | python3 -c "
import json
import sys

try:
    tabs = json.load(sys.stdin)
    print(f'   Total de abas: {len(tabs)}')
    print('')

    for i, tab in enumerate(tabs, 1):
        url = tab.get('url', '')
        title = tab.get('title', 'Sem título')
        tab_type = tab.get('type', '')

        print(f'   Aba {i}:')
        print(f'      Tipo: {tab_type}')
        print(f'      Título: {title}')
        print(f'      URL: {url}')
        print('')

except Exception as e:
    print(f'   ❌ Erro ao processar abas: {e}')
"

echo ""
echo "3. Testando captura via API..."
echo ""

# Testa a captura via API
response=$(curl -s -X POST "http://localhost:8001/api/capture/capture-tabs?devtools_url=http%3A%2F%2F127.0.0.1%3A9222&include_pattern=&exclude_pattern=&fast=1&concurrency=6&per_page_timeout_ms=1200")

echo "$response" | python3 -c "
import json
import sys

try:
    result = json.load(sys.stdin)
    total = result.get('total', 0)
    processed = result.get('processed', 0)
    tabs = result.get('tabs', [])

    print(f'   Total de abas encontradas: {total}')
    print(f'   Abas processadas: {processed}')
    print('')

    if len(tabs) > 0:
        print('   ✅ Produtos capturados:')
        for i, tab in enumerate(tabs, 1):
            print(f'      {i}. {tab.get(\"product_title\", \"Sem título\")}')
            print(f'         UPC: {tab.get(\"upc\", \"Não encontrado\")}')
            print(f'         URL: {tab.get(\"url\", \"\")}')
            print('')
    else:
        print('   ⚠️  Nenhuma aba foi capturada!')
        print('')
        print('   Possíveis motivos:')
        print('   - As URLs estão sendo filtradas (verifique os padrões de exclusão)')
        print('   - As abas não são do tipo \"page\"')
        print('   - Há um erro de conexão com o Chrome')

except json.JSONDecodeError as e:
    print(f'   ❌ Resposta inválida da API: {e}')
    print(f'   Resposta recebida: {sys.stdin.read()[:500]}')
except Exception as e:
    print(f'   ❌ Erro ao processar resposta: {e}')
"

echo ""
echo "=========================================="
echo "✅ Debug completo!"
echo "=========================================="
