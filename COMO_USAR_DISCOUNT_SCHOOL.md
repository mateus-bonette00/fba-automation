# Como Usar - Discount School Supply

## Resumo

Você tem **3 formas** de extrair produtos do Discount School Supply (ou qualquer outro fornecedor):

### 1. Via Interface Web (Recomendado)

A forma mais fácil e visual.

**Como usar:**
1. Inicie o backend e frontend
2. Acesse http://localhost:5173
3. Clique em "Fornecedor" no menu
4. Cole a URL: `https://www.discountschoolsupply.com/all-categories/school-supplies/clearance/c/offer_clearance`
5. Clique em "Baixar CSV Direto" ou "Extrair Produtos"

### 2. Script Específico para Discount School (Otimizado)

Use este script quando quiser rodar direto no terminal com melhor performance.

**Como usar:**
```bash
cd backend
source venv/bin/activate
python scrape_discount_school.py
```

Digite a URL quando solicitado ou pressione Enter para usar a URL padrão de clearance.

**Vantagens:**
- Otimizado especificamente para Discount School Supply
- Detecta automaticamente o total de páginas
- Mais rápido e eficiente
- Logs detalhados no terminal

### 3. Script Genérico (Para Qualquer Fornecedor)

Use este para outros fornecedores.

**Como usar:**
```bash
cd backend
source venv/bin/activate
python export_supplier_products.py
```

---

## O que o script faz?

Para a URL do Discount School Supply de clearance:

1. **Acessa a primeira página**
2. **Detecta que existem 346 items / 48 por página = 8 páginas**
3. **Varre todas as 8 páginas** e extrai os produtos
4. **Acessa cada produto individualmente** para pegar o UPC
5. **Gera CSV** com:
   - Nome do Produto
   - UPC
   - Link do Fornecedor
   - Link Amazon (busca por UPC)
   - Link Amazon (busca por Nome)

---

## Exemplo de URL

Para usar, basta colar a URL da categoria:

```
https://www.discountschoolsupply.com/all-categories/school-supplies/clearance/c/offer_clearance
```

Ou qualquer outra categoria:

```
https://www.discountschoolsupply.com/all-categories/arts-crafts/arts-crafts-supplies/collage-mosaic/c/927123
```

O script vai:
- Detectar automaticamente a paginação
- Varrer todas as páginas (1, 2, 3, 4, 5...)
- Extrair todos os produtos
- Pegar UPC de cada um

---

## Melhorias implementadas

### Para o Discount School Supply especificamente:

1. ✅ **Detecção automática de páginas** via texto "1-48 of 346 items"
2. ✅ **Geração de URLs de paginação** (pageSize=48&page=2)
3. ✅ **Espera networkidle** para JS carregar completamente
4. ✅ **Detecção por atributos data-product**
5. ✅ **Timeout aumentado** para 60 segundos

### Para fornecedores genéricos:

1. ✅ Detecção por atributos `data-product-*`
2. ✅ Detecção de paginação por query params
3. ✅ Múltiplos seletores CSS
4. ✅ Espera adequada para sites com JavaScript

---

## Formato do CSV

```csv
Nome do Produto,UPC,Link Fornecedor,Amazon (Busca por UPC),Amazon (Busca por Nome)
"Colorations® Wiggly Eyes, Black - 100 Pieces",123456789012,https://...,https://amazon.com/s?k=123456789012,https://amazon.com/s?k=Colorations...
```

---

## Performance

Para 346 produtos (exemplo da clearance):

- **Detecção de páginas:** ~5 segundos
- **Extração de produtos:** ~30 segundos (8 páginas)
- **Extração de UPCs:** ~10-15 minutos (346 produtos)
- **Total:** ~15-20 minutos

**Dica:** O script roda em **headless** na produção (invisível), mas você pode mudar para `headless=False` para ver o navegador funcionando.

---

## Troubleshooting

### "Nenhum produto encontrado"

O site pode ter mudado a estrutura. Verifique se:
- A URL está correta
- O site está acessível
- Não há captcha ou bloqueio

### "Timeout"

- Site pode estar lento
- Aumente o timeout no código (atualmente 60s)

### "UPC não encontrado"

- Nem todos os produtos têm UPC visível
- O script tenta múltiplas técnicas de extração

---

## Arquivos

**Scripts:**
- `backend/scrape_discount_school.py` - Específico otimizado
- `backend/export_supplier_products.py` - Genérico
- `backend/api/supplier_scraper.py` - API para interface web

**Interface:**
- Frontend em http://localhost:5173/supplier-scraper

---

## Próximos Passos

1. **Teste com a URL de clearance**
2. **Veja o CSV gerado**
3. **Compartilhe com seu amigo**
4. **Use com outras categorias** do Discount School Supply

Qualquer dúvida, é só perguntar!
