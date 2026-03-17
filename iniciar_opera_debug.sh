#!/bin/bash

# Script para iniciar Opera em modo debug (remote debugging)
# Permite automação via Chrome DevTools Protocol
set -euo pipefail

echo "🔧 Iniciando Opera em modo debug..."

if curl -fsS "http://127.0.0.1:9222/json/version" >/dev/null 2>&1; then
    echo "✅ Opera debug já está ativo em 9222"
    exit 0
fi

# 1. Se já existe processo Opera com 9222 mas sem responder, não mata automaticamente
if pgrep -af "opera.*remote-debugging-port=9222" >/dev/null 2>&1; then
    echo "⚠️  Já existe um Opera Debug em execução, mas a porta 9222 ainda não respondeu."
    echo "⏳ Aguardando 6s para estabilizar..."
    sleep 6
    if curl -fsS "http://127.0.0.1:9222/json/version" >/dev/null 2>&1; then
        echo "✅ Opera debug respondeu após espera."
        exit 0
    fi
    echo "❌ Opera Debug em execução sem resposta no CDP. Feche manualmente o Opera e rode novamente."
    exit 1
fi

# 2. Se outra aplicação ocupa 9222, não força kill para não derrubar processos errados
if lsof -ti:9222 >/dev/null 2>&1; then
    echo "❌ Porta 9222 ocupada por outro processo. Libere a porta e rode novamente."
    exit 1
fi

# 3. Utilizar o perfil do Opera Normal (Opção B - Cuidado ao abrir os dois ao mesmo tempo)
# IMPORTANTE: Não inicie este script se o Opera "normal" já estiver aberto com o mesmo perfil.
PROFILE_DIR="/home/mateus/snap/opera/current/.config/opera"
if [ ! -d "$PROFILE_DIR" ]; then
    echo "📁 Diretório de perfil não encontrado em: $PROFILE_DIR. Tem certeza que o Opera está instalado?"
fi

# Opera via snap wrapper pode reaproveitar uma instância já aberta sem flags.
# Preferimos o binário real do snap para garantir que remote-debugging seja aplicado.
OPERA_BIN="/snap/opera/current/usr/lib/x86_64-linux-gnu/opera/opera"
if [ ! -x "$OPERA_BIN" ]; then
  OPERA_BIN="/snap/bin/opera"
fi

# 4. Iniciar Opera com remote debugging habilitado
echo "🚀 Iniciando Opera com remote debugging na porta 9222..."
"$OPERA_BIN" \
  --remote-debugging-port=9222 \
  --user-data-dir="$PROFILE_DIR" \
  --profile-directory=Default \
  --disable-blink-features=AutomationControlled \
  --disable-background-networking \
  --disable-background-timer-throttling \
  --disable-renderer-backgrounding \
  --disable-features=CalculateNativeWinOcclusion \
  --disable-dev-shm-usage \
  --no-default-browser-check \
  --no-first-run \
  --password-store=basic \
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
