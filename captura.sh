#!/bin/bash
# Script para iniciar/parar Chrome de captura

if [ "$1" == "start" ]; then
    echo "🚀 Iniciando Chrome para captura..."

    # MATA O KARMA PRIMEIRO (ng test)
    echo "1️⃣  Matando processos Karma..."
    pkill -9 -f "ng test" 2>/dev/null
    pkill -9 -f "karma" 2>/dev/null

    # Mata qualquer Chrome existente
    echo "2️⃣  Fechando Chromes..."
    pkill -9 chrome 2>/dev/null
    sleep 2

    # Inicia novo Chrome com os parâmetros corretos
    google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-profile --disable-extensions --disable-gpu --disable-background-networking --disable-background-timer-throttling --no-first-run --no-default-browser-check --disk-cache-dir=/tmp/chrome-cache --js-flags="--max-old-space-size=512" &
    sleep 2

    echo "✅ Chrome iniciado!"
    echo "📋 Agora abra as abas dos produtos nesse Chrome"

elif [ "$1" == "stop" ]; then
    echo "🛑 Parando Chrome..."
    pkill -9 chrome
    echo "✅ Chrome fechado!"

elif [ "$1" == "status" ]; then
    if lsof -i :9222 >/dev/null 2>&1; then
        echo "🟢 Navegador ONLINE"
    else
        echo "🔴 Navegador OFFLINE"
    fi

else
    echo "Uso: $0 {start|stop|status}"
    echo ""
    echo "  start  - Inicia Chrome para captura"
    echo "  stop   - Para Chrome"
    echo "  status - Verifica status"
fi
