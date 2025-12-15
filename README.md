# 🚀 FBA Automation - Sistema de Captura de Produtos

Sistema completo de automação para captura e análise de produtos de fornecedores para Amazon FBA.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node](https://img.shields.io/badge/Node-20%20LTS-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-cyan.svg)](https://reactjs.org/)

## ✨ Funcionalidades Principais

- 🌐 **Captura automática de abas** - Processa múltiplas páginas simultaneamente
- 🔍 **Extração inteligente de UPC** - 15+ métodos diferentes de extração
- 📊 **Interface moderna** - Frontend React com design profissional
- ⚡ **Alta performance** - Processamento paralelo otimizado
- 💾 **Sistema de cache** - Evita reprocessamento
- 📤 **Exportação CSV** - Com links diretos para Amazon
- 🎯 **Filtros avançados** - Regex para incluir/excluir URLs

---

## 🚀 Instalação Rápida

### Linux/Mac

```bash
# Clone o repositório
git clone <seu-repositorio>
cd fba-automation

# Execute o instalador
chmod +x iniciar_tudo.sh
./iniciar_tudo.sh
```

### Windows

```powershell
# Execute como Administrador
.\instalar_windows.ps1

# Depois, para iniciar:
.\iniciar_tudo.bat
```

📖 **Guia completo para Windows:** [INSTALACAO_WINDOWS.md](INSTALACAO_WINDOWS.md)

---

## 📋 O que o Sistema Faz?

### 1. Captura de Abas Abertas do Chrome
- Abre o Chrome com produtos
- Captura automaticamente: nome + UPC
- Usa **15 métodos diferentes** para encontrar o UPC

### 2. Scraping de Sites Fornecedores
- Varre todo o site do fornecedor
- Extrai produtos de todas as páginas
- Gera CSV com links para Amazon

### 3. Geração Automática de Links Amazon
- Busca por UPC
- Busca por nome do produto

---

## 🔧 Endpoints da API

Com o servidor rodando (`http://localhost:8001`):

### 📖 Documentação Interativa
```
http://localhost:8001/docs
```

### ✅ Verificar Saúde do Sistema
```bash
curl http://localhost:8001/api/health
```

### 🔍 Capturar Abas do Chrome
```bash
# 1. Abra o Chrome com debugging
google-chrome --remote-debugging-port=9222 &

# 2. Abra páginas de produtos no Chrome

# 3. Capture
curl -X POST "http://localhost:8001/api/capture/capture-tabs" \
  -H "Content-Type: application/json" \
  -d '{"devtools_url":"http://127.0.0.1:9222","include_pattern":".*"}'
```

### 🌐 Scraping de Fornecedor
```bash
curl -X POST "http://localhost:8001/api/supplier/scrape" \
  -H "Content-Type: application/json" \
  -d '{"supplier_url":"https://exemplo.com/produtos"}'
```

### 📥 Download de CSV
```bash
curl -X POST "http://localhost:8001/api/supplier/scrape-and-download" \
  -H "Content-Type: application/json" \
  -d '{"supplier_url":"https://exemplo.com/produtos"}' \
  -o produtos.csv
```

---

## ⭐ Os 15 Métodos de Extração de UPC

1. ✅ **JSON-LD** (Schema.org)
2. ✅ **Meta Tags** (itemprop, property, name)
3. ✅ **CSS Selectors** (20+ seletores)
4. ✅ **Data Attributes** (data-upc, data-gtin, etc)
5. ✅ **Window Objects** (Shopify, Next.js, Apollo, Nuxt, Drupal)
6. ✅ **JavaScript Scripts**
7. ✅ **Product Details Sections**
8. ✅ **Labeled Text** (UPC: 123...)
9. ✅ **HTML Tables**
10. ✅ **Definition Lists** (dl/dt/dd)
11. ✅ **API/JSON Patterns**
12. ✅ **Form Inputs**
13. ✅ **Image Alt Text**
14. ✅ **HTML Comments**
15. ✅ **Context Heuristic**

**Ver detalhes:** [METODOS_EXTRACAO_UPC.md](METODOS_EXTRACAO_UPC.md)

---

## 🧪 Testar o Sistema

```bash
cd backend
python3 test_upc_extraction.py
```

Isso mostra os 15 métodos em ação com exemplos reais!

---

## 📁 Estrutura do Projeto

```
fba-automation/
├── backend/
│   ├── api/
│   │   ├── upc_extractor.py     # ⭐ NOVO - 15 métodos
│   │   ├── capture.py           # Captura de abas
│   │   ├── supplier_scraper_v2.py # Scraping
│   │   ├── sellers.py           # Sellers
│   │   └── products.py          # Products
│   ├── main.py                  # 🚀 PONTO DE ENTRADA
│   └── test_upc_extraction.py   # Testes
├── frontend/                    # Interface (opcional)
├── iniciar.sh                   # ⭐ Script automático
├── requirements.txt             # Dependências
└── README.md                    # Este arquivo
```

---

## 📚 Documentação Completa

- **[COMO_RODAR.md](COMO_RODAR.md)** - Guia completo passo a passo
- **[METODOS_EXTRACAO_UPC.md](METODOS_EXTRACAO_UPC.md)** - Detalhes dos 15 métodos
- **[INSTALACAO_RAPIDA.md](INSTALACAO_RAPIDA.md)** - Instalação rápida

---

## 🐛 Problemas Comuns

### "ModuleNotFoundError"
```bash
pip3 install -r requirements.txt
```

### "Port already in use"
```bash
lsof -i :8001
kill -9 [PID]
```

### "Can't connect to browser"
```bash
google-chrome --remote-debugging-port=9222 &
```

---

## 💪 Benefícios do Novo Sistema

### Antes:
- ❌ 5-6 métodos básicos
- ❌ Muitos UPCs não eram encontrados
- ❌ Funcionava só com alguns sites

### Agora:
- ✅ **15 métodos avançados**
- ✅ **Taxa de sucesso muito maior**
- ✅ **Funciona com praticamente qualquer site**
- ✅ Shopify, WooCommerce, Next.js, React, e mais!

---

## 🎯 Casos de Uso

1. **Arbitragem Online**: Encontre produtos de fornecedores e compare na Amazon
2. **Pesquisa de Produtos**: Capture UPCs para pesquisa de mercado
3. **Listagem em Massa**: Gere planilhas para upload na Amazon
4. **Comparação de Preços**: Compare fornecedores vs Amazon

---

## 📊 Formato do CSV Gerado

```csv
Nome do Produto,UPC,Link Fornecedor,Amazon (Busca por UPC),Amazon (Busca por Nome)
"Product Name","012345678901","https://...","https://amazon.com/s?k=012345678901","https://amazon.com/s?k=Product+Name"
```

---

## 🚀 Quick Start (3 comandos)

```bash
# 1. Entre no diretório
cd "/home/mateus/Documentos/Qota Store/códigos/fba-automation"

# 2. Execute o script
./iniciar.sh

# 3. Acesse a documentação
# http://localhost:8001/docs
```

---

## ✨ Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **Playwright** - Automação de navegador
- **BeautifulSoup** - Parsing de HTML
- **Python 3** - Linguagem principal

---

## 📞 Suporte

1. Leia a documentação em [COMO_RODAR.md](COMO_RODAR.md)
2. Execute os testes: `python3 backend/test_upc_extraction.py`
3. Verifique os logs do servidor

---

**Versão:** 2.0
**Última Atualização:** 2025-10-26
**Status:** ✅ Pronto para uso com 15 métodos de extração!
