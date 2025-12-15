# Sistema Avançado de Extração de UPC

## Visão Geral

O sistema foi completamente atualizado com **15 métodos diferentes** para extrair UPC de páginas de produtos. Agora o sistema tenta múltiplas estratégias automaticamente até encontrar o UPC.

## Métodos de Extração (Em ordem de prioridade)

### 1. **JSON-LD (Schema.org)**
- Busca em tags `<script type="application/ld+json">`
- Procura por campos: `gtin`, `gtin12`, `gtin13`, `gtin14`, `upc`, `ean`, `productID`
- Busca recursiva em objetos aninhados e arrays
- Verifica também em `offers` e sub-objetos

**Exemplo:**
```html
<script type="application/ld+json">
{
  "@type": "Product",
  "gtin13": "0012345678901"
}
</script>
```

---

### 2. **Meta Tags**
- Busca em meta tags com atributos `itemprop`, `property`, `name`
- Procura por palavras-chave nos nomes dos atributos
- Extrai o valor do atributo `content`

**Exemplo:**
```html
<meta itemprop="gtin13" content="0012345678901">
<meta property="product:upc" content="012345678901">
```

---

### 3. **Seletores CSS Específicos**
- Usa 20+ seletores CSS diferentes para encontrar UPC
- Inclui: `[itemprop="gtin"]`, `[data-upc]`, `.product-upc`, `#upc`, etc.
- Tenta extrair de atributos: `content`, `value`, `data-upc`, `data-gtin`
- Também tenta extrair do texto do elemento

**Exemplo:**
```html
<div class="product-upc">012345678901</div>
<span itemprop="gtin13">0012345678901</span>
<input data-upc="012345678901">
```

---

### 4. **Atributos data-* Estruturados**
- Busca TODOS os elementos com atributos `data-*`
- Verifica se o nome do atributo contém palavras-chave
- Tenta parsear JSON em valores de atributos data-*

**Exemplo:**
```html
<div data-product='{"upc": "012345678901"}'>
<div data-barcode="012345678901">
```

---

### 5. **Objetos Window (Next.js, Shopify, etc)**
- Busca em scripts por objetos globais comuns:
  - `window.__NEXT_DATA__`
  - `window.Shopify`
  - `window.__INITIAL_STATE__`
  - `window.dataLayer`
  - `window.__APOLLO_STATE__`
  - `var productData`
  - `const product`
- Parseia JSON e faz busca recursiva

**Exemplo:**
```javascript
window.__NEXT_DATA__ = {
  "props": {
    "pageProps": {
      "product": {
        "gtin": "012345678901"
      }
    }
  }
};
```

---

### 6. **Scripts JavaScript**
- Busca em TODOS os scripts da página
- Usa múltiplos padrões regex para encontrar UPC em código JS
- Procura por padrões como:
  - `"barcode": "012345678901"`
  - `gtin: "012345678901"`
  - `upc = "012345678901"`

**Exemplo:**
```javascript
var productData = {
  barcode: "012345678901",
  name: "Product Name"
};
```

---

### 7. **Detalhes do Produto**
- Busca em áreas comuns de detalhes:
  - `.product-details`
  - `.product-info`
  - `.product-specifications`
  - `.specs`
  - `.attributes`
- Aplica regex no texto dessas áreas

**Exemplo:**
```html
<div class="product-details">
  <p>UPC: 012345678901</p>
</div>
```

---

### 8. **Texto com Rótulos**
- Busca por padrões de texto rotulado em toda a página
- Padrões suportados:
  - `UPC: 012345678901`
  - `GTIN-13: 0012345678901`
  - `Barcode: 012345678901`
  - `EAN: 0012345678901`
  - `Item #: 012345678901`
  - `Product Code: 012345678901`
  - `Model #: 012345678901`

---

### 9. **Tabelas de Especificações**
- Busca em todas as tabelas `<table>`
- Procura por linhas onde a primeira célula contém palavras-chave
- Extrai o valor da segunda célula

**Exemplo:**
```html
<table>
  <tr>
    <td>UPC</td>
    <td>012345678901</td>
  </tr>
</table>
```

---

### 10. **Listas de Definição**
- Busca em listas `<dl>`, `<dt>`, `<dd>`
- Procura por `<dt>` com palavras-chave
- Extrai o valor do `<dd>` correspondente

**Exemplo:**
```html
<dl>
  <dt>UPC Code</dt>
  <dd>012345678901</dd>
</dl>
```

---

### 11. **Padrões de API/JSON**
- Busca por padrões de JSON em scripts
- Procura por objetos `product`, `item`, `variant`, `sku`
- Tenta parsear e extrair UPC

**Exemplo:**
```javascript
fetch('/api/product').then(r => r.json()).then(data => {
  console.log(data.item.upc); // "012345678901"
});
```

---

### 12. **Campos de Formulário**
- Busca em todos os formulários
- Verifica campos `<input>`, `<textarea>`, `<select>`
- Procura por palavras-chave no `name` ou `id`
- Extrai o valor do atributo `value`

**Exemplo:**
```html
<form>
  <input name="product_upc" value="012345678901">
</form>
```

---

### 13. **Texto Alternativo de Imagens**
- Busca em atributos `alt` de imagens
- Aplica regex para encontrar UPC no alt text

**Exemplo:**
```html
<img src="product.jpg" alt="Product - UPC: 012345678901">
```

---

### 14. **Comentários HTML**
- Busca em comentários HTML `<!-- -->`
- Aplica padrões regex nos comentários
- Útil para dados de debug deixados por desenvolvedores

**Exemplo:**
```html
<!-- Product UPC: 012345678901 -->
<!-- {"gtin": "012345678901"} -->
```

---

### 15. **Heurística de Contexto**
- Encontra TODOS os números de 12 dígitos na página
- Para cada número, analisa 100 caracteres antes e depois
- Se encontrar palavras-chave próximas, considera como UPC
- Método de última tentativa quando nada mais funciona

**Exemplo:**
```html
<div>
  Este produto possui o código universal 012345678901
  que pode ser usado para busca.
</div>
```

---

## Validação de UPC

O sistema valida automaticamente:
- Remove todos os caracteres não-numéricos
- Aceita apenas tamanhos válidos: **8, 12, 13 ou 14 dígitos**
- Se o número for maior que 14 dígitos, tenta extrair uma sequência válida

---

## Como Usar

### 1. **Via API (capture.py)**

O sistema já está integrado automaticamente. Quando você usa a API de captura:

```bash
curl -X POST "http://localhost:8000/api/capture/capture-tabs" \
  -H "Content-Type: application/json" \
  -d '{
    "devtools_url": "http://127.0.0.1:9222",
    "include_pattern": ".*"
  }'
```

O sistema tentará automaticamente todos os 15 métodos até encontrar o UPC.

### 2. **Via Scraper (supplier_scraper.py)**

```bash
curl -X POST "http://localhost:8000/api/supplier/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_url": "https://exemplo.com/produtos"
  }'
```

### 3. **Scripts Standalone**

```bash
# Discount School
python backend/scrape_discount_school.py

# Exportar produtos
python backend/export_supplier_products.py
```

### 4. **Uso Direto em Python**

```python
from api.upc_extractor import UPCExtractor

# HTML da página
html = """<html>...</html>"""

# Criar extrator
extractor = UPCExtractor()

# Extrair UPC (tenta todos os métodos)
upc = extractor.extract_all_methods(html)

# Ver estatísticas
stats = extractor.get_extraction_stats()
print(f"UPC encontrado: {stats['upc_found']}")
print(f"Método usado: {stats['method_used']}")
print(f"Métodos tentados: {stats['methods_tried']}")
```

---

## Estatísticas de Extração

O extrator fornece informações detalhadas sobre a extração:

```python
extractor = UPCExtractor()
upc = extractor.extract_all_methods(html)

stats = extractor.get_extraction_stats()
# {
#   'upc_found': '012345678901',
#   'method_used': 'json-ld',
#   'methods_tried': 1,
#   'all_methods': ['json-ld']
# }
```

---

## Arquivos Atualizados

Todos os seguintes arquivos foram atualizados para usar o novo sistema:

1. ✅ `backend/api/upc_extractor.py` - **NOVO** - Sistema avançado de extração
2. ✅ `backend/api/capture.py` - Integrado com UPCExtractor
3. ✅ `backend/api/supplier_scraper.py` - Usando nova função
4. ✅ `backend/api/supplier_scraper_v2.py` - Usando nova função
5. ✅ `backend/scrape_discount_school.py` - Usando nova função
6. ✅ `backend/export_supplier_products.py` - Usando nova função

---

## Benefícios

### Antes:
- ❌ 5-6 métodos básicos
- ❌ Muitos UPCs não eram encontrados
- ❌ Apenas JSON-LD e algumas meta tags

### Agora:
- ✅ **15 métodos diferentes**
- ✅ **Busca recursiva** em objetos aninhados
- ✅ **Suporte para frameworks modernos** (Next.js, Shopify, etc)
- ✅ **Múltiplos padrões regex**
- ✅ **Heurística inteligente** como fallback
- ✅ **Extração de qualquer elemento HTML**
- ✅ **Busca em scripts, comentários, forms, tabelas**
- ✅ **Validação automática de formato**

---

## Resultado Esperado

Com esses 15 métodos, o sistema agora consegue extrair UPC de:

- ✅ Sites Shopify
- ✅ Sites WooCommerce
- ✅ Sites Next.js
- ✅ Sites React com Apollo
- ✅ Sites com Nuxt
- ✅ Sites com Drupal
- ✅ Sites customizados
- ✅ Sites antigos com tabelas HTML
- ✅ Sites modernos com JSON-LD
- ✅ Sites com dados em comentários
- ✅ Sites com formulários
- ✅ Sites com dados em atributos data-*
- ✅ E muitos mais!

---

## Suporte

Se um UPC ainda não for encontrado:

1. Verifique o HTML da página manualmente
2. Procure onde o UPC está visível
3. O sistema pode ser expandido com novos métodos específicos
4. Entre em contato para adicionar suporte ao site específico

---

**Criado em:** 2025-10-26
**Versão:** 2.0
**Métodos:** 15+
