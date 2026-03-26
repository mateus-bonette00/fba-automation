#!/bin/bash
# Script para iniciar o Chrome com remote debugging

echo "🔧 Preparando Chrome para captura de abas..."
echo ""

# Mata processos na porta 9222 se existir
echo "1️⃣  Liberando porta 9222..."
lsof -ti:9222 | xargs kill -9 2>/dev/null
sleep 1

# Mata todos os processos do Chrome para garantir
echo "2️⃣  Fechando todas as instâncias do Chrome..."
killall chrome 2>/dev/null
killall google-chrome 2>/dev/null
killall Chrome 2>/dev/null
pkill -9 -f "chrome.*9222" 2>/dev/null
sleep 2

# Remove locks e perfis antigos
echo "3️⃣  Limpando perfis temporários..."
rm -rf /tmp/chrome-debug-profile /tmp/chrome-cache 2>/dev/null
rm -f ~/.config/google-chrome/SingletonLock 2>/dev/null
sleep 1

# Inicia o Chrome com remote debugging
echo "4️⃣  Iniciando Chrome com remote debugging..."
echo ""
echo "⚠️  IMPORTANTE: Use ESTE Chrome para abrir as abas dos produtos!"
echo "   Não abra outro Chrome separado."
echo ""

# Cria uma página HTML temporária para identificar o Chrome Debug
cat > /tmp/chrome-debug-start.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>🔧 CHROME DEBUG - ABRA SEUS PRODUTOS AQUI!</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            text-align: center;
        }
        .container {
            max-width: 700px;
            padding: 40px;
        }
        h1 {
            font-size: 48px;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .badge {
            background: rgba(255,255,255,0.2);
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 20px;
            font-weight: bold;
            margin: 20px 0;
            display: inline-block;
        }
        .instructions {
            background: rgba(0,0,0,0.2);
            padding: 30px;
            border-radius: 15px;
            margin-top: 30px;
            text-align: left;
        }
        .step {
            margin: 15px 0;
            font-size: 18px;
        }
        .warning {
            background: rgba(255,193,7,0.3);
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 5px solid #ffc107;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 CHROME DEBUG</h1>
        <div class="badge">✅ Conectado na porta 9222</div>

        <div class="instructions">
            <h2>📋 Como usar:</h2>
            <div class="step">1️⃣ Abra NOVAS ABAS neste Chrome (Ctrl+T)</div>
            <div class="step">2️⃣ Cole as URLs dos produtos nas novas abas</div>
            <div class="step">3️⃣ Volte para http://localhost:5173/capture</div>
            <div class="step">4️⃣ Clique em "Capturar Abas"</div>
        </div>

        <div class="warning">
            <strong>⚠️ IMPORTANTE:</strong><br>
            Use APENAS este Chrome para abrir os produtos!<br>
            Se usar outro Chrome, a captura não vai funcionar.
        </div>
    </div>
</body>
</html>
EOF

# Força uma nova instância com --new-window
/usr/bin/google-chrome \
  --new-window \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile \
  --disable-extensions \
  --disable-gpu \
  --disable-background-networking \
  --disable-background-timer-throttling \
  --no-first-run \
  --no-default-browser-check \
  --disk-cache-dir=/tmp/chrome-cache \
  --js-flags="--max-old-space-size=512" \
  "file:///tmp/chrome-debug-start.html" \
  > /tmp/chrome-debug.log 2>&1 &

CHROME_PID=$!

# Aguarda o Chrome iniciar
echo "⏳ Aguardando Chrome inicializar (PID: $CHROME_PID)..."
sleep 4

# Verifica se está rodando
MAX_RETRIES=10
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
  if curl -s http://127.0.0.1:9222/json/version > /dev/null 2>&1; then
    echo ""
    echo "✅ Chrome iniciado com sucesso na porta 9222!"
    echo ""
    echo "🔍 Status do navegador:"
    curl -s http://127.0.0.1:9222/json | jq -r '.[] | "   - \(.title) (\(.url))"' 2>/dev/null || echo "   Navegador pronto"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Abra as abas dos produtos NESTE Chrome que acabou de abrir"
    echo "   2. Volte para http://localhost:5173/capture"
    echo "   3. Clique em 'Capturar Abas'"
    echo ""
    echo "💡 Dica: Não feche este Chrome! Ele precisa ficar aberto para capturar."
    echo ""
    exit 0
  fi
  RETRY=$((RETRY+1))
  sleep 1
done

echo ""
echo "❌ Erro ao iniciar Chrome na porta 9222."
echo "📝 Verifique o log em: /tmp/chrome-debug.log"
echo ""
echo "Últimas linhas do log:"
tail -10 /tmp/chrome-debug.log 2>/dev/null || echo "   (log vazio)"
echo ""
exit 1
