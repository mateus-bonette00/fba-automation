#!/bin/bash

# Script para iniciar Opera em modo debug (remote debugging)
# Permite automação via Chrome DevTools Protocol

echo "🔧 Iniciando Opera em modo debug..."

# 1. Matar processos usando a porta 9222 (se houver)
echo "📌 Verificando porta 9222..."
if lsof -ti:9222 >/dev/null 2>&1; then
    echo "⚠️  Porta 9222 em uso. Finalizando processos..."
    lsof -ti:9222 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 2. Fechar todas as instâncias do Opera
echo "🛑 Fechando instâncias anteriores do Opera..."
pkill -f "opera.*remote-debugging" || true
sleep 1

# 3. Criar diretório temporário para profile do Opera Debug (se não existir)
PROFILE_DIR="/tmp/opera-debug-profile"
if [ ! -d "$PROFILE_DIR" ]; then
    echo "📁 Criando diretório de perfil: $PROFILE_DIR"
    mkdir -p "$PROFILE_DIR"
fi

# 4. Iniciar Opera com remote debugging habilitado
echo "🚀 Iniciando Opera com remote debugging na porta 9222..."
/snap/bin/opera \
  --remote-debugging-port=9222 \
  --user-data-dir="$PROFILE_DIR" \
  --disable-blink-features=AutomationControlled \
  --no-first-run \
  --no-default-browser-check \
  >/dev/null 2>&1 &

# Aguardar um pouco para o Opera iniciar
sleep 3

# 5. Verificar se o Opera está rodando e a porta está aberta
if lsof -ti:9222 >/dev/null 2>&1; then
    echo "✅ Opera iniciado com sucesso!"
    echo ""
    echo "📍 DevTools Protocol URL: http://localhost:9222"
    echo ""
    echo "💡 Dicas:"
    echo "   - Use esta URL no seu sistema de captura de abas"
    echo "   - Para ver todas as abas abertas: http://localhost:9222/json"
    echo "   - Para parar: pkill -f 'opera.*remote-debugging'"
    echo ""
else
    echo "❌ Erro: Opera não iniciou corretamente ou porta 9222 não está acessível"
    exit 1
fi
