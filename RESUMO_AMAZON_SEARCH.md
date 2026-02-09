# 🔍 Estratégia de Busca na Amazon - OTIMIZADA

## ✅ O Que Mudou

### ANTES (Problema):
```
Título capturado: "2024 Porsche Taycan | Item Number:MB-2024-HVL75 | Matchbox | 1:64"
Query na Amazon: "MB-2024-HVL75"  ❌ NÃO encontrava produtos
```

### AGORA (Solução):
```
Título capturado: "2024 Porsche Taycan | Matchbox | 1:64"
Query na Amazon: "Matchbox 2024 Porsche Taycan 1:64"  ✅ ENCONTRA!
```

---

## 📊 Como Funciona Agora

### 1. Backend (`title_extractor.py`)

**Captura APENAS:**
- ✅ **Brand** (Matchbox, John Deere, Johnny Lightning, Hot Wheels, etc)
- ✅ **Modelo/Escala** (1:64, 1/32, etc)

**IGNORA completamente:**
- ❌ Part Number (LP84525, MB-2024-HVL75, etc)
- ❌ Item Number
- ❌ SKU
- ❌ Model Number

**Resultado:**
```
"2024 Porsche Taycan | Matchbox | 1:64"
```

### 2. Frontend (`CaptureTabsPage.jsx`)

**Estratégia de busca:**

```javascript
Input:  "2024 Porsche Taycan | Matchbox | 1:64"

Extrai:
- Brand: "Matchbox"
- Título: "2024 Porsche Taycan"
- Modelo: "1:64"

Monta query: "Matchbox 2024 Porsche Taycan 1:64"
```

**Prioridade:**
1. Se tem **Brand**: adiciona na query
2. Sempre adiciona o **Título**
3. Se tem **Modelo/Escala**: adiciona na query

---

## 🎯 Exemplos Práticos

| Produto | Título Capturado | Query na Amazon |
|---------|------------------|-----------------|
| Matchbox Porsche | `2024 Porsche Taycan \| Matchbox \| 1:64` | `Matchbox 2024 Porsche Taycan 1:64` |
| John Deere Tractor | `4240 Tractor \| John Deere \| 1/32` | `John Deere 4240 Tractor 1/32` |
| Johnny Lightning | `1963 Pontiac Tempest \| Johnny Lightning \| 1:64` | `Johnny Lightning 1963 Pontiac Tempest 1:64` |
| Hot Wheels (sem escala) | `Tesla Cybertruck \| Hot Wheels` | `Hot Wheels Tesla Cybertruck` |

---

## 🔧 Marcas Reconhecidas

O sistema reconhece automaticamente estas marcas:

- John Deere
- Matchbox
- Hot Wheels
- Johnny Lightning
- TOMY / ERTL
- Maisto
- Greenlight
- Jada
- Mattel
- Bruder / SIKU
- Corgi / Dinky
- Auto World
- Racing Champions
- M2 Machines
- Schleich / Papo

---

## 📝 Arquivos Modificados

### Backend:
- `backend/api/title_extractor.py`
  - Linha 359-369: Lista de keywords incluindo "scale"
  - Linha 453-465: Regex melhorado para capturar "1:64", "1/32"
  - Linha 544-567: Lista de marcas conhecidas
  - Linha 571-576: Retorna APENAS Brand + Modelo (sem Part Number)

### Frontend:
- `frontend/src/pages/CaptureTabsPage.jsx`
  - Linha 119-191: Função `buildAmazonSearchUrl()` otimizada
  - IGNORA Part Numbers completamente
  - Monta query com Brand + Título + Modelo

---

## ✅ Testes

Execute para validar:

```bash
cd backend
source venv/bin/activate
python test_matchbox_extraction.py
```

**Resultado esperado:**
```
✅ Brand encontrada: Matchbox
✅ Modelo encontrado: 1:64
✅ Part Numbers ignorados corretamente
🎉 TESTE PASSOU!
```

---

## 🚀 Como Usar

1. Capture produtos normalmente (Capturar Abas)
2. Clique no botão **"Título"** para buscar na Amazon
3. A busca agora vai com:
   - ✅ Brand + Nome do Produto + Escala
   - ❌ SEM Part Numbers que a Amazon não conhece

**Muito mais efetivo para encontrar produtos na Amazon!** 🎯
