# 🚀 COMO RODAR O PROGRAMA - GUIA COMPLETO

## ✅ Passo a Passo (SIGA EXATAMENTE ESSA ORDEM)

### 1️⃣ Instalar Dependências do Python

Abra o terminal e execute:

```bash
cd "/home/mateus/Documentos/Qota Store/códigos/fba-automation"

pip3 install -r requirements.txt
```

Se der erro de permissão, use:

```bash
pip3 install --user -r requirements.txt
```

### 2️⃣ Instalar Navegadores do Playwright

```bash
python3 -m playwright install chromium
```

### 3️⃣ Verificar se o Frontend está configurado (OPCIONAL)

Se você tem o frontend React, instale as dependências dele também:

```bash
cd frontend
npm install
cd ..
```

### 4️⃣ Rodar o Backend (MAIN.PY)

```bash
cd backend
python3 main.py
```

Você deverá ver algo assim:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

✅ **PRONTO! O servidor está rodando na porta 8001**

---

## 📋 Como Usar o Sistema

### Opção 1: Usar a Interface Web (Frontend)

Se você tem o frontend:

```bash
# Em outro terminal
cd frontend
npm start
```

Depois abra: `http://localhost:3000`

### Opção 2: Usar a API Diretamente

O backend está rodando em: `http://localhost:8001`

#### 🔍 Testar se está funcionando:

```bash
curl http://localhost:8001/api/health
```

Resposta esperada:
```json
{"status":"ok","message":"Backend rodando"}
```

---

## 🎯 Como Capturar Produtos com UPC

### Método 1: Capturar de Abas Abertas do Chrome

**Passo 1:** Abra o Chrome com debugging ativado:

```bash
google-chrome --remote-debugging-port=9222 &
```

Ou se usar Chromium:

```bash
chromium-browser --remote-debugging-port=9222 &
```

**Passo 2:** Abra as páginas de produtos que você quer capturar

**Passo 3:** Use a API para capturar:

```bash
curl -X POST "http://localhost:8001/api/capture/capture-tabs" \
  -H "Content-Type: application/json" \
  -d '{
    "devtools_url": "http://127.0.0.1:9222",
    "include_pattern": ".*",
    "same_domain_probe": 1,
    "aggressive_probe": 1
  }' | jq
```

**Explicação dos parâmetros:**
- `devtools_url`: URL do Chrome debugging
- `include_pattern`: Regex para filtrar URLs (use `.*` para todas)
- `same_domain_probe`: 1 = tenta buscar UPC em APIs do mesmo domínio
- `aggressive_probe`: 1 = tenta ainda mais métodos

**Resposta esperada:**
```json
{
  "total": 5,
  "processed": 5,
  "tabs": [
    {
      "product_title": "Nome do Produto",
      "upc": "012345678901",
      "upc_method": "json-ld",
      "url": "https://..."
    }
  ]
}
```

### Método 2: Fazer Scraping de um Site Fornecedor

```bash
curl -X POST "http://localhost:8001/api/supplier/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_url": "https://www.discountschoolsupply.com/Product/ProductList.aspx?category=3208"
  }' | jq
```

### Método 3: Baixar CSV de Produtos

```bash
curl -X POST "http://localhost:8001/api/supplier/scrape-and-download" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_url": "https://www.discountschoolsupply.com/Product/ProductList.aspx?category=3208"
  }' \
  -o produtos_$(date +%Y%m%d_%H%M%S).csv
```

Isso vai criar um arquivo CSV com:
- Nome do Produto
- UPC
- Link do Fornecedor
- Link de busca na Amazon por UPC
- Link de busca na Amazon por Nome

---

## 📊 Ver Documentação da API

Com o servidor rodando, acesse:

```
http://localhost:8001/docs
```

Isso abrirá a interface Swagger com TODOS os endpoints disponíveis!

---

## 🧪 Testar o Sistema de Extração de UPC

Para ver os 15 métodos em ação:

```bash
cd backend
python3 test_upc_extraction.py
```

Você verá todos os métodos sendo testados e a taxa de sucesso.

---

## 🐛 Resolução de Problemas

### Erro: "ModuleNotFoundError: No module named 'fastapi'"

**Solução:**
```bash
pip3 install -r requirements.txt
```

### Erro: "ModuleNotFoundError: No module named 'playwright'"

**Solução:**
```bash
pip3 install playwright
python3 -m playwright install chromium
```

### Erro: "Address already in use" (porta 8001 ocupada)

**Solução 1:** Matar o processo que está usando a porta:
```bash
lsof -i :8001
kill -9 [PID]
```

**Solução 2:** Usar outra porta editando o main.py:
```python
# Linha 34 do main.py
uvicorn.run(app, host="0.0.0.0", port=8002)  # Mudou de 8001 para 8002
```

### Erro: "Can't connect to browser" ao capturar abas

**Solução:** Certifique-se de abrir o Chrome com debugging:
```bash
google-chrome --remote-debugging-port=9222 &
```

### UPC não está sendo encontrado

**Agora com os 15 métodos, isso deve ser MUITO RARO!**

Se ainda assim não encontrar:
1. Veja qual método foi tentado: olhe o campo `upc_method` na resposta
2. Verifique manualmente se o UPC está visível na página
3. Envie o HTML da página para análise

---

## 📁 Estrutura do Projeto

```
fba-automation/
├── backend/
│   ├── api/
│   │   ├── capture.py          # ✅ Captura de abas (ATUALIZADO)
│   │   ├── supplier_scraper_v2.py  # ✅ Scraping (ATUALIZADO)
│   │   ├── upc_extractor.py    # ⭐ NOVO - 15 métodos
│   │   ├── sellers.py          # Gerenciamento de sellers
│   │   └── products.py         # Gerenciamento de produtos
│   ├── main.py                 # ✅ PONTO DE ENTRADA
│   └── test_upc_extraction.py  # ⭐ Testes
├── frontend/                   # Interface React (se houver)
├── requirements.txt            # ⭐ Dependências
└── *.md                        # Documentação
```

---

## 🎯 Comandos Rápidos (Resumo)

```bash
# 1. Instalar tudo
cd "/home/mateus/Documentos/Qota Store/códigos/fba-automation"
pip3 install -r requirements.txt
python3 -m playwright install chromium

# 2. Rodar o servidor
cd backend
python3 main.py

# 3. Testar (em outro terminal)
curl http://localhost:8001/api/health

# 4. Capturar abas (com Chrome aberto em debug mode)
google-chrome --remote-debugging-port=9222 &
curl -X POST "http://localhost:8001/api/capture/capture-tabs" \
  -H "Content-Type: application/json" \
  -d '{"devtools_url":"http://127.0.0.1:9222","include_pattern":".*"}' | jq
```

---

## ✨ Novo Sistema de UPC

Agora com **15 métodos diferentes**, o sistema encontra UPC de praticamente qualquer site:

✅ JSON-LD
✅ Meta Tags
✅ CSS Selectors
✅ Data Attributes
✅ Window Objects (Shopify, Next.js, etc)
✅ JavaScript Variables
✅ Product Details
✅ Labeled Text
✅ Tables
✅ Definition Lists
✅ API Patterns
✅ Form Inputs
✅ Image Alt Text
✅ HTML Comments
✅ Context Heuristic

**Veja mais:** [METODOS_EXTRACAO_UPC.md](METODOS_EXTRACAO_UPC.md)

---

## 📞 Suporte

Se tiver qualquer problema:

1. Verifique se seguiu TODOS os passos acima
2. Veja os logs do servidor para erros
3. Teste com `curl http://localhost:8001/api/health`
4. Execute os testes: `python3 test_upc_extraction.py`

---

**Última atualização:** 2025-10-26
**Versão:** 2.0 com 15 métodos de extração de UPC
