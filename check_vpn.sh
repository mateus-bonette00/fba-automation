#!/bin/bash

echo "========================================"
echo "  VERIFICAÇÃO DE VPN E IP"
echo "========================================"
echo ""

echo "1️⃣  Verificando conexões VPN (nmcli)..."
echo ""
nmcli connection show | grep -E "NAME|TYPE|ACTIVE"
echo ""

echo "2️⃣  Verificando conexão ativa..."
echo ""
nmcli connection show --active
echo ""

echo "3️⃣  IP Público Atual..."
echo ""
echo "   Via ipinfo.io:"
curl -s https://ipinfo.io | jq '{ip: .ip, country: .country, city: .city}'
echo ""

echo "   Via ipapi.co:"
curl -s https://ipapi.co/json/ | jq '{ip: .ip, country_name: .country_name, city: .city}'
echo ""

echo "4️⃣  Verificando se consegue acessar us.tomy.com..."
echo ""
curl -s -I https://us.tomy.com/brands/ertl/ | head -5
echo ""

echo "5️⃣  Testando conexão específica para tomy.com..."
echo ""
timeout 5 curl -s https://us.tomy.com/brands/ertl/ -H "User-Agent: Mozilla/5.0" | head -100 | grep -i "price\|msrp\|product" || echo "   (Sem matches de preço)"
echo ""

echo "========================================"
echo "  ✅ Verificação concluída"
echo "========================================"
