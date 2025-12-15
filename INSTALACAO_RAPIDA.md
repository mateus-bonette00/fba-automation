# Instalação Rápida - Sistema de Extração de UPC

## 1. Instalar Dependências

```bash
# Navegar até o diretório do projeto
cd "/home/mateus/Documentos/Qota Store/códigos/fba-automation"

# Instalar dependências Python
pip3 install -r requirements.txt

# Instalar navegadores do Playwright
python3 -m playwright install chromium
```

## 2. Testar o Sistema de Extração

```bash
# Executar os testes
cd backend
python3 test_upc_extraction.py
```

Você deverá ver algo como:

```
================================================================================
TESTE DO SISTEMA AVANÇADO DE EXTRAÇÃO DE UPC
================================================================================

1. Testando: JSON-LD Schema.org
--------------------------------------------------------------------------------
✅ PASSOU - UPC encontrado: 0012345678901
   Método usado: json-ld
   Métodos tentados: 1

2. Testando: Meta Tags
--------------------------------------------------------------------------------
✅ PASSOU - UPC encontrado: 0012345678901
   Método usado: meta-tags
   Métodos tentados: 2

...

================================================================================
RESUMO DOS TESTES
================================================================================
Total: 17
✅ Passaram: 17
❌ Falharam: 0
Taxa de sucesso: 100.0%
```

## 3. Iniciar o Servidor API

```bash
# Voltar para o diretório raiz
cd ..

# Iniciar o servidor FastAPI
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 4. Usar a API

### 4.1 Capturar abas do navegador

Primeiro, abra o Chrome com debugging:

```bash
# Linux
google-chrome --remote-debugging-port=9222

# Ou Chrome
chromium-browser --remote-debugging-port=9222
```

Depois, use a API:

```bash
curl -X POST "http://localhost:8000/api/capture/capture-tabs" \
  -H "Content-Type: application/json" \
  -d '{
    "devtools_url": "http://127.0.0.1:9222",
    "include_pattern": ".*"
  }'
```

### 4.2 Fazer scraping de um site fornecedor

```bash
curl -X POST "http://localhost:8000/api/supplier/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_url": "https://www.discountschoolsupply.com/Product/ProductList.aspx?category=3208"
  }'
```

### 4.3 Baixar CSV com produtos

```bash
curl -X POST "http://localhost:8000/api/supplier/scrape-and-download" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_url": "https://www.discountschoolsupply.com/Product/ProductList.aspx?category=3208"
  }' \
  -o produtos.csv
```

## 5. Usar Scripts Standalone

### 5.1 Discount School Supply

```bash
cd backend
python3 scrape_discount_school.py
```

### 5.2 Exportar produtos genérico

```bash
cd backend
python3 export_supplier_products.py
```

## 6. Verificar Melhorias

Para verificar que o novo sistema está funcionando, você pode:

1. **Abrir abas no navegador** com produtos que antes não tinham UPC capturado
2. **Usar a API de captura** para extrair os dados
3. **Verificar os resultados** - agora com os 15 métodos, a taxa de sucesso deve ser muito maior!

## 7. Documentação Completa

- [Métodos de Extração de UPC](METODOS_EXTRACAO_UPC.md) - Documentação completa dos 15 métodos
- [Como Usar Discount School](COMO_USAR_DISCOUNT_SCHOOL.md) - Se disponível
- [Guia do Fornecedor](GUIA_FORNECEDOR.md) - Se disponível

## 8. Estrutura dos Arquivos

```
fba-automation/
├── backend/
│   ├── api/
│   │   ├── capture.py              # API de captura (ATUALIZADO)
│   │   ├── supplier_scraper.py     # Scraper genérico (ATUALIZADO)
│   │   ├── supplier_scraper_v2.py  # Scraper v2 (ATUALIZADO)
│   │   └── upc_extractor.py        # ⭐ NOVO - 15 métodos de extração
│   ├── scrape_discount_school.py   # Script standalone (ATUALIZADO)
│   ├── export_supplier_products.py # Export script (ATUALIZADO)
│   └── test_upc_extraction.py      # ⭐ NOVO - Testes
├── requirements.txt                 # ⭐ NOVO - Dependências
├── INSTALACAO_RAPIDA.md            # ⭐ NOVO - Este arquivo
└── METODOS_EXTRACAO_UPC.md         # ⭐ NOVO - Documentação completa
```

## 9. Troubleshooting

### Erro: ModuleNotFoundError

```bash
pip3 install -r requirements.txt
```

### Erro: playwright not installed

```bash
python3 -m playwright install chromium
```

### Erro: Can't connect to browser

Certifique-se de que o Chrome está rodando com debugging:

```bash
google-chrome --remote-debugging-port=9222
```

### API não inicia

Verifique se a porta 8000 está livre:

```bash
lsof -i :8000
# Se estiver em uso, mate o processo ou use outra porta
```

## 10. Próximos Passos

1. ✅ Instalar dependências
2. ✅ Testar extração de UPC
3. ✅ Iniciar servidor API
4. ✅ Testar com sites reais
5. ✅ Verificar melhoria na taxa de captura de UPC

---

**Aproveite os novos 15 métodos de extração de UPC!** 🚀
