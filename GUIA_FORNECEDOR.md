# Guia de Uso - Extrator de Produtos do Fornecedor

## O que foi implementado

Uma nova funcionalidade completa no seu sistema FBA Automation para extrair produtos de fornecedores e gerar CSV com:

- Nome do Produto
- UPC do Produto
- Link do Produto no Fornecedor
- Link de Busca na Amazon (por UPC)
- Link de Busca na Amazon (por Nome)

## Como usar

### 1. Iniciar o Backend

```bash
cd backend
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate no Windows

python main.py
```

O backend vai rodar em: `http://localhost:8001`

### 2. Iniciar o Frontend

Em outro terminal:

```bash
cd frontend
npm run dev
```

O frontend vai rodar em: `http://localhost:5173`

### 3. Acessar a nova funcionalidade

1. Abra o navegador em `http://localhost:5173`
2. Clique em **"Fornecedor"** no menu superior
3. Cole a URL da categoria/seção do fornecedor
4. Escolha uma das opções:
   - **Extrair Produtos**: Visualiza na tela primeiro
   - **Baixar CSV Direto**: Faz download direto do CSV

### 4. Exemplo de uso

**URL do Fornecedor:**
```
https://www.exemplo.com/categoria/brinquedos
```

O sistema irá:
1. Detectar automaticamente todas as páginas (paginação)
2. Varrer todas as páginas
3. Extrair cada produto
4. Buscar o UPC na página de cada produto
5. Gerar links da Amazon

**Resultado:**
- CSV com todos os produtos
- Links clicáveis para abrir no fornecedor
- Links de busca na Amazon (por UPC e por Nome)

## Funcionalidades

### Backend (API)

**Rota:** `POST /api/supplier/scrape`
- Extrai produtos e retorna JSON

**Rota:** `POST /api/supplier/scrape-and-download`
- Extrai produtos e retorna CSV para download

### Frontend (Interface)

**Página:** `/supplier-scraper`
- Interface visual bonita
- Botão para extrair e visualizar
- Botão para baixar CSV direto
- Tabela com resultados
- Exportar CSV

## Formato do CSV gerado

```csv
Nome do Produto,UPC,Link Fornecedor,Amazon (Busca por UPC),Amazon (Busca por Nome)
"Brinquedo XYZ",123456789012,https://fornecedor.com/produto/xyz,https://amazon.com/s?k=123456789012,https://amazon.com/s?k=Brinquedo+XYZ
"Jogo ABC","Não encontrado",https://fornecedor.com/produto/abc,N/A,https://amazon.com/s?k=Jogo+ABC
```

## Compartilhar com seu amigo

Depois de gerar o CSV:
1. Clique em "Exportar CSV" ou "Baixar CSV Direto"
2. O arquivo será baixado automaticamente
3. Envie o arquivo `.csv` para seu amigo
4. Ele pode abrir no Excel, Google Sheets, etc.

## Customização

Se os produtos não estiverem sendo detectados corretamente para um fornecedor específico, você pode customizar os seletores CSS em:

**Arquivo:** `backend/api/supplier_scraper.py`

**Seletores de produtos** (linha ~109):
```python
product_selectors = [
    ".product",
    ".product-item",
    # Adicione o seletor do seu fornecedor
]
```

**Seletores de paginação** (linha ~220):
```python
pagination_selectors = [
    ".pagination a",
    ".page-numbers a",
    # Adicione o seletor de paginação
]
```

## Troubleshooting

**Erro: "Nenhum produto encontrado"**
- Verifique se a URL está correta
- Tente customizar os seletores CSS

**CSV vazio ou incompleto**
- Aguarde o processamento completo
- Alguns sites podem ter proteção contra scraping

**UPCs não encontrados**
- Nem todos os sites exibem UPC
- O sistema tenta múltiplas técnicas de extração

**Timeout/Erro de conexão**
- Site pode estar lento
- Tente novamente mais tarde

## Arquivos criados

### Backend:
- `backend/api/supplier_scraper.py` - API de scraping
- `backend/main.py` - Rota adicionada

### Frontend:
- `frontend/src/pages/SupplierScraperPage.jsx` - Página React
- `frontend/src/pages/SupplierScraperPage.css` - Estilos
- `frontend/src/App.jsx` - Rota adicionada
- `frontend/src/components/Navbar.jsx` - Menu atualizado

## Features

- ✅ Detecção automática de paginação
- ✅ Extração de UPC (múltiplas técnicas)
- ✅ Links da Amazon (busca por UPC e Nome)
- ✅ Interface visual moderna
- ✅ Exportar CSV formatado (UTF-8 com BOM)
- ✅ Progress indicators
- ✅ Error handling
- ✅ Responsive design

Agora você pode extrair produtos de qualquer fornecedor e compartilhar o CSV com seu amigo!
