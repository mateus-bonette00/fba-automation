# Como Usar o Extrator de Produtos do Fornecedor

## O que faz?

Este script extrai todos os produtos de uma seção/categoria de um site fornecedor e gera um CSV com:

- **Nome do Produto**: Título completo do produto
- **UPC**: Código UPC/GTIN extraído da página
- **Link Fornecedor**: URL da página do produto no site do fornecedor
- **Amazon (Busca por UPC)**: Link de busca na Amazon usando o UPC
- **Amazon (Busca por Nome)**: Link de busca na Amazon usando o nome do produto

O script varre **automaticamente todas as páginas** da seção (paginação).

---

## Instalação

Certifique-se de ter as dependências instaladas:

```bash
cd backend
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install playwright beautifulsoup4
playwright install chromium
```

---

## Como Usar

1. **Execute o script:**

```bash
cd backend
python export_supplier_products.py
```

2. **Digite a URL da seção/categoria do fornecedor**

Exemplo:
```
https://www.fornecedor.com/categoria/produtos
```

3. **Digite o nome do arquivo CSV (ou deixe em branco para nome automático)**

Exemplo:
```
produtos_brinquedos.csv
```

Ou apenas aperte Enter para gerar um nome automático como: `produtos_fornecedor_20251026_143052.csv`

4. **Aguarde o processamento**

O script irá:
- Detectar paginação automaticamente
- Varrer todas as páginas
- Extrair cada produto
- Acessar a página de cada produto para pegar o UPC
- Gerar o CSV formatado

---

## Exemplo de Saída (CSV)

| Nome do Produto | UPC | Link Fornecedor | Amazon (Busca por UPC) | Amazon (Busca por Nome) |
|----------------|-----|----------------|----------------------|------------------------|
| Brinquedo XYZ | 123456789012 | https://fornecedor.com/produto/xyz | https://www.amazon.com/s?k=123456789012 | https://www.amazon.com/s?k=Brinquedo+XYZ |
| Jogo ABC | Não encontrado | https://fornecedor.com/produto/abc | N/A | https://www.amazon.com/s?k=Jogo+ABC |

---

## Customização

Se o script não estiver encontrando produtos corretamente, você pode precisar ajustar os **seletores CSS** para o site específico do seu fornecedor.

### Onde customizar:

1. **Seletores de produtos** (linha ~104):
```python
product_selectors = [
    ".product",
    ".product-item",
    # Adicione os seletores do seu fornecedor aqui
]
```

2. **Seletores de paginação** (linha ~190):
```python
pagination_selectors = [
    ".pagination a",
    ".page-numbers a",
    # Adicione os seletores de paginação do seu fornecedor
]
```

### Como descobrir os seletores:

1. Acesse a página do fornecedor
2. Clique com botão direito em um produto → "Inspecionar"
3. Veja o HTML e identifique as classes CSS (ex: `class="product-card"`)
4. Adicione o seletor na lista (ex: `".product-card"`)

---

## Dicas

- **UPCs não encontrados**: Nem todos os produtos têm UPC visível na página. O script usa múltiplas técnicas (JSON-LD, microdata, scripts, texto) para tentar encontrar.

- **Performance**: O script acessa cada produto individualmente para garantir UPC correto. Para 100 produtos, pode levar 5-10 minutos.

- **Headless**: O navegador roda em modo invisível (headless). Para debug, mude `headless=True` para `headless=False` na linha 222.

- **Timeout**: Se o site for lento, aumente o timeout na linha 226: `timeout=30000` (30 segundos)

---

## Troubleshooting

**Erro: "Nenhum produto encontrado"**
→ Ajuste os `product_selectors` para o seu fornecedor

**Erro: "Paginação não detectada"**
→ Ajuste os `pagination_selectors` ou adicione URLs manualmente

**Erro de conexão/timeout**
→ Verifique sua conexão ou aumente o timeout

**UPCs não são encontrados**
→ Verifique se o site realmente exibe UPC nas páginas dos produtos

---

## Compartilhando com seu amigo

Para enviar o CSV para alguém sem acesso ao código:

1. Execute o script
2. Aguarde a geração do CSV
3. Envie o arquivo `.csv` gerado
4. Seu amigo pode abrir no Excel, Google Sheets ou qualquer planilha

O CSV está em formato UTF-8 com BOM para compatibilidade com Excel.
