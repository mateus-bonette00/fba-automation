# 🔍 Guia de Debug - Problema com Preços $0.00 e Links de Carrinho

## Problema
No servidor, o fornecedor `us.tomy.com` (índice 2) mostra:
- Preço `$0.00` para todos os produtos (são filtrados)
- Possível presença de links de carrinho (agora filtrados)

No notebook (com VPN local) funciona corretamente.

## Causa Provável
1. **IP fora dos EUA** - O site `us.tomy.com` bloqueia ou mostra preço zero para IPs fora dos EUA
2. **VPN desligada ou com problema** - VPN não está ativa no servidor
3. **Geolocalização incorreta** - VPN conecta em local errado

---

## ✅ Passo 1: Verificar VPN e IP

### No servidor, execute:

```bash
cd /home/mateus/Documentos/Qota Store/códigos/fba-automation
chmod +x check_vpn.sh
./check_vpn.sh
```

### O que procurar:
- **Conexão ativa**: Deve mostrar `usa-newyork-udp` (ou similar) como ACTIVE
- **IP Público**: Deve estar em país `US` (não Brasil)
- **Exemplo correto:**
  ```
  "ip": "1.2.3.4",
  "country": "US"
  ```

- **Exemplo ERRADO** (problema):
  ```
  "ip": "1.2.3.4",
  "country": "BR"
  ```

---

## ✅ Passo 2: Verificar Estrutura HTML do Site

```bash
cd /home/mateus/Documentos/Qota Store/códigos/fba-automation
python3 test_tomy_prices.py
```

### O que procurar:
- **Esperado:** Encontrar elementos com preços (`.price--withoutTax`, etc.)
- **Problema:** Se não encontrar preços e não houver `$` no HTML, significa:
  - Site bloqueou por IP
  - VPN não está funcionando

---

## ✅ Passo 3: Debug Detalhado de Um Fornecedor

Certifique-se que o Chrome está rodando em modo debug:

```bash
# Terminal 1: Chrome em modo debug (se não estiver rodando)
google-chrome --remote-debugging-port=9222 &

# Terminal 2: Rodar o debug
cd /home/mateus/Documentos/Qota Store/códigos/fba-automation
python3 backend/debug_supplier.py 2 http://127.0.0.1:9222
```

### Saída esperada:
```
✅ Fornecedor encontrado: {'indice': 2, 'url': 'http://us.tomy.com/brands/ertl/', ...}
📊 Estatísticas:
   Total de links extraídos: 23
   Links de carrinho (filtrados): 0  <-- Deve ser 0 (agora filtrados)
   Links com preço $0.00 (filtrados): 0  <-- Deve ser 0 (VPN OK)
   Links com preço não parseável: 2
   Links com preço válido: 21
   Total válido para captura: 23
```

### Se aparecer preço $0.00:
```
⚠️  PROBLEMA DETECTADO: 23 produtos com preço $0.00
   Possíveis causas:
   1. IP fora dos EUA (site us.tomy.com bloqueia)
   2. VPN desligada ou com problema
   3. Geolocalização incorreta
```

---

## 🔧 Solução: Se VPN Está Desligada

### Verificar conexões VPN disponíveis:
```bash
nmcli connection show
```

### Ligar VPN US:
```bash
nmcli connection up id 'usa-newyork-udp'
```

### Desligar VPN:
```bash
nmcli connection down id 'usa-newyork-udp'
```

### Verificar status:
```bash
nmcli connection show --active
```

---

## 🔧 Solução: Se VPN Está Ligada Mas IP Errado

### Verifique qual VPN está conectada:
```bash
nmcli connection show --active | grep vpn
```

### Se conectada em local errado, tente:

1. **Desconectar VPN atual:**
   ```bash
   nmcli connection down id 'usa-newyork-udp'
   ```

2. **Aguardar 5 segundos:**
   ```bash
   sleep 5
   ```

3. **Conectar novamente:**
   ```bash
   nmcli connection up id 'usa-newyork-udp'
   ```

4. **Verificar IP:**
   ```bash
   curl -s https://ipinfo.io | jq '.country'
   ```

---

## 📋 Checklist de Debug

- [ ] VPN está ativa: `nmcli connection show --active`
- [ ] IP é dos EUA: `curl -s https://ipinfo.io | jq '.country'`
- [ ] Preços aparecem no teste: `python3 test_tomy_prices.py`
- [ ] Links de carrinho foram filtrados (scripts atualizados)
- [ ] Debug do fornecedor mostra preços válidos: `python3 backend/debug_supplier.py 2`
- [ ] Rodar automação novamente

---

## 📊 Comparação: Antes vs Depois

### ANTES (Problemas)
```
❌ Links de carrinho capturados: https://us.tomy.com/cart.php?action=add&product_id=4450
❌ Preço $0.00 não filtrado no servidor
```

### DEPOIS (Corrigido)
```
✅ Links de carrinho filtrados em 2 camadas:
   1. JavaScript (extractPrice, isActionUrl)
   2. Python (run_automation.py)

✅ Preço $0.00:
   - Filtrado corretamente (comportamento esperado)
   - Se aparecer = problema de VPN/IP (detectável via debug)
```

---

## 🚀 Próximas Ações

1. **Rodar os scripts de debug** e coletar logs
2. **Validar VPN** está em US
3. **Re-testar fornecedor índice 2** com a automação
4. **Verificar logs** para confirmar que links de carrinho foram filtrados

Depois disso, a captura deve funcionar corretamente! 🎯
