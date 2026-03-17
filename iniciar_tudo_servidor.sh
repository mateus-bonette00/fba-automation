#!/bin/bash

# Script para iniciar Backend, Frontend e Chrome Debug.
# Uso: ./iniciar_tudo_chrome.sh [super-estavel|turbo-noturno]

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
CHROME_DEBUG_LOG="$LOG_DIR/chrome_debug.log"
CHROME_WATCHDOG_LOG="$LOG_DIR/chrome_watchdog.log"
LOCAL_ENV_FILE="${LOCAL_ENV_FILE:-$PROJECT_DIR/.env.local}"

if [ -f "$LOCAL_ENV_FILE" ]; then
  source "$LOCAL_ENV_FILE"
fi

BACKEND_PID=""
FRONTEND_PID=""
CHROME_STARTED_BY_SCRIPT="0"
CHROME_WATCHDOG_PID=""
KEEP_CHROME_DEBUG_ON_EXIT="${KEEP_CHROME_DEBUG_ON_EXIT:-0}"
CLEANUP_DONE="0"
CHROME_USER_DATA_DIR="${CHROME_USER_DATA_DIR:-$HOME/.config/google-chrome-debug-profile}"
AUTOMATION_AUTO_START="${AUTOMATION_AUTO_START:-0}"
AUTOMATION_DEVTOOLS_URL="${AUTOMATION_DEVTOOLS_URL:-http://127.0.0.1:9222}"
AUTOMATION_BATCH_SIZE="${AUTOMATION_BATCH_SIZE:-10}"
AUTOMATION_PRICE_MIN="${AUTOMATION_PRICE_MIN:-0}"
AUTOMATION_PRICE_LIMIT="${AUTOMATION_PRICE_LIMIT:-85}"
AUTOMATION_EXPORT_THRESHOLD="${AUTOMATION_EXPORT_THRESHOLD:-500}"
AUTOMATION_START_INDEX="${AUTOMATION_START_INDEX:-36}"
AUTOMATION_PERSON="${AUTOMATION_PERSON:-Mateus}"

AUTOMATION_PROFILE_ARG="${1:-}"
if [[ "$AUTOMATION_PROFILE_ARG" == --profile=* ]]; then
  AUTOMATION_PROFILE_ARG="${AUTOMATION_PROFILE_ARG#--profile=}"
fi
AUTOMATION_PERFORMANCE_PROFILE="${AUTOMATION_PERFORMANCE_PROFILE:-${AUTOMATION_PROFILE_ARG:-super-estavel}}"
AUTOMATION_PROFILE_ACTIVE=""

set_profile_default() {
  local var_name="$1"
  local default_value="$2"
  if [ -z "${!var_name+x}" ] || [ -z "${!var_name}" ]; then
    printf -v "$var_name" "%s" "$default_value"
  fi
}

apply_performance_profile() {
  local raw="$1"
  local normalized
  normalized="$(echo "$raw" | tr '[:upper:]' '[:lower:]' | tr '_' '-' | tr -s '-')"

  case "$normalized" in
    turbo|turbo-noturno|night-turbo|night)
      AUTOMATION_PROFILE_ACTIVE="turbo-noturno"
      set_profile_default TAB_OPEN_TIMEOUT_MS "12000"
      set_profile_default TAB_OPEN_DELAY_SECONDS "0.02"
      set_profile_default TAB_OPEN_MAX_PARALLEL "5"
      set_profile_default TAB_OPEN_PARALLEL_LOW_MEM "2"
      set_profile_default LIST_PAGE_SETTLE_SECONDS "0.9"
      set_profile_default POST_BATCH_SETTLE_SECONDS "0.15"
      set_profile_default CAPTURE_MAX_CONCURRENCY "8"
      set_profile_default CAPTURE_PER_PAGE_TIMEOUT_MS "1800"
      set_profile_default CAPTURE_API_TIMEOUT_SECONDS "100"
      set_profile_default LOAD_MORE_WAIT_SECONDS "1.4"
      set_profile_default INFINITE_SCROLL_WAIT_SECONDS "1.0"
      set_profile_default MEMORY_MIN_AVAILABLE_MB "850"
      set_profile_default LOW_MEMORY_COOLDOWN_SECONDS "5"
      set_profile_default MAX_CONSECUTIVE_LOW_MEMORY_HITS "3"
      set_profile_default MIN_DYNAMIC_BATCH_SIZE "4"
      set_profile_default HIGH_PRICE_PAGE_MIN_PRICED_ITEMS "5"
      set_profile_default HIGH_PRICE_PAGE_CONSECUTIVE_THRESHOLD "1"
      set_profile_default URL_FAILURE_QUARANTINE_THRESHOLD "3"
      set_profile_default DOMAIN_FAILURE_QUARANTINE_THRESHOLD "7"
      ;;
    super-estavel|estavel|stable|safe)
      AUTOMATION_PROFILE_ACTIVE="super-estavel"
      set_profile_default TAB_OPEN_TIMEOUT_MS "18000"
      set_profile_default TAB_OPEN_DELAY_SECONDS "0.10"
      set_profile_default TAB_OPEN_MAX_PARALLEL "3"
      set_profile_default TAB_OPEN_PARALLEL_LOW_MEM "1"
      set_profile_default LIST_PAGE_SETTLE_SECONDS "1.8"
      set_profile_default POST_BATCH_SETTLE_SECONDS "0.35"
      set_profile_default CAPTURE_MAX_CONCURRENCY "5"
      set_profile_default CAPTURE_PER_PAGE_TIMEOUT_MS "2600"
      set_profile_default CAPTURE_API_TIMEOUT_SECONDS "160"
      set_profile_default LOAD_MORE_WAIT_SECONDS "2.5"
      set_profile_default INFINITE_SCROLL_WAIT_SECONDS "2.0"
      set_profile_default MEMORY_MIN_AVAILABLE_MB "1200"
      set_profile_default LOW_MEMORY_COOLDOWN_SECONDS "10"
      set_profile_default MAX_CONSECUTIVE_LOW_MEMORY_HITS "2"
      set_profile_default MIN_DYNAMIC_BATCH_SIZE "3"
      set_profile_default HIGH_PRICE_PAGE_MIN_PRICED_ITEMS "6"
      set_profile_default HIGH_PRICE_PAGE_CONSECUTIVE_THRESHOLD "1"
      set_profile_default URL_FAILURE_QUARANTINE_THRESHOLD "2"
      set_profile_default DOMAIN_FAILURE_QUARANTINE_THRESHOLD "5"
      ;;
    *)
      echo -e "${RED}❌ Perfil de performance inválido: ${raw}${NC}"
      echo -e "${YELLOW}Use: super-estavel | turbo-noturno${NC}"
      exit 1
      ;;
  esac
}

apply_performance_profile "$AUTOMATION_PERFORMANCE_PROFILE"

export TAB_OPEN_TIMEOUT_MS
export TAB_OPEN_DELAY_SECONDS
export TAB_OPEN_MAX_PARALLEL
export TAB_OPEN_PARALLEL_LOW_MEM
export LIST_PAGE_SETTLE_SECONDS
export POST_BATCH_SETTLE_SECONDS
export MIN_DYNAMIC_BATCH_SIZE
export MEMORY_MIN_AVAILABLE_MB
export LOW_MEMORY_COOLDOWN_SECONDS
export MAX_CONSECUTIVE_LOW_MEMORY_HITS
export HIGH_PRICE_PAGE_MIN_PRICED_ITEMS
export HIGH_PRICE_PAGE_CONSECUTIVE_THRESHOLD
export URL_FAILURE_QUARANTINE_THRESHOLD
export DOMAIN_FAILURE_QUARANTINE_THRESHOLD
export CAPTURE_MAX_CONCURRENCY
export CAPTURE_PER_PAGE_TIMEOUT_MS
export CAPTURE_API_TIMEOUT_SECONDS
export LOAD_MORE_WAIT_SECONDS
export INFINITE_SCROLL_WAIT_SECONDS

mkdir -p "$LOG_DIR"
: > "$BACKEND_LOG"
: > "$FRONTEND_LOG"
: > "$CHROME_DEBUG_LOG"
: > "$CHROME_WATCHDOG_LOG"

echo "=========================================="
echo "🚀 INICIANDO FBA AUTOMATION COMPLETO"
echo "=========================================="
echo ""
echo -e "${BLUE}⚙️  Perfil de performance ativo: ${AUTOMATION_PROFILE_ACTIVE}${NC}"
echo -e "${BLUE}   Abertura abas: parallel=${TAB_OPEN_MAX_PARALLEL}, timeout=${TAB_OPEN_TIMEOUT_MS}ms, delay=${TAB_OPEN_DELAY_SECONDS}s${NC}"
echo -e "${BLUE}   Captura: conc=${CAPTURE_MAX_CONCURRENCY}, per-page-timeout=${CAPTURE_PER_PAGE_TIMEOUT_MS}ms${NC}"
echo -e "${BLUE}   Guardião memória: mínimo livre=${MEMORY_MIN_AVAILABLE_MB}MB${NC}"
echo ""

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo -e "${RED}❌ Comando obrigatório não encontrado: ${cmd}${NC}"
    exit 1
  fi
}

wait_http() {
  local url="$1"
  local timeout="${2:-40}"
  local attempt=1
  while [ "$attempt" -le "$timeout" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
  return 1
}

is_port_busy() {
  local port="$1"
  lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

port_listener_pids() {
  local port="$1"
  lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
}

port_belongs_to_project() {
  local port="$1"
  local pids
  pids="$(port_listener_pids "$port")"
  if [ -z "$pids" ]; then
    return 1
  fi

  for pid in $pids; do
    local cmdline
    local cwd_path
    cmdline="$(ps -p "$pid" -o args= 2>/dev/null || true)"
    cwd_path="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
    if [[ "$cmdline" == *"$PROJECT_DIR"* ]] || [[ "$cwd_path" == "$PROJECT_DIR"* ]]; then
      return 0
    fi
  done

  return 1
}

kill_port_listeners() {
  local port="$1"
  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -z "$pids" ]; then
    return 0
  fi
  echo -e "${YELLOW}⚠️  Porta ${port} ocupada. Encerrando processo(s): ${pids}${NC}"
  kill $pids 2>/dev/null || true
  sleep 1
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    kill -9 $pids 2>/dev/null || true
  fi
}

resolve_chrome_paths() {
  local candidates=(
    "google-chrome-stable"
    "google-chrome"
    "chromium-browser"
    "chromium"
    "/snap/bin/chromium"
  )

  CHROME_BIN=""
  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      CHROME_BIN="$(command -v "$candidate")"
      break
    fi
    if [ -x "$candidate" ]; then
      CHROME_BIN="$candidate"
      break
    fi
  done

  if [ -z "$CHROME_BIN" ]; then
    echo -e "${RED}❌ Chrome/Chromium não encontrado.${NC}"
    echo -e "${YELLOW}Instale google-chrome ou chromium e rode novamente.${NC}"
    exit 1
  fi

  mkdir -p "$CHROME_USER_DATA_DIR"
}

endpoint_reports_chrome() {
  local version_json=""
  version_json="$(curl -fsS "http://127.0.0.1:9222/json/version" 2>/dev/null || true)"
  if [ -z "$version_json" ]; then
    return 1
  fi
  echo "$version_json" | grep -Eqi '"Browser"\s*:\s*"(Chrome|Chromium)'
}

kill_chrome_debug_9222() {
  local chrome_debug_pids=""
  chrome_debug_pids="$(ps -eo pid,args | grep -E '([g]oogle-chrome|[c]hromium).*remote-debugging-port=9222' | awk '{print $1}' || true)"
  if [ -n "$chrome_debug_pids" ]; then
    echo -e "${YELLOW}⚠️  Encerrando Chrome Debug em 9222: ${chrome_debug_pids}${NC}"
    kill $chrome_debug_pids 2>/dev/null || true
    sleep 1
    chrome_debug_pids="$(ps -eo pid,args | grep -E '([g]oogle-chrome|[c]hromium).*remote-debugging-port=9222' | awk '{print $1}' || true)"
    if [ -n "$chrome_debug_pids" ]; then
      kill -9 $chrome_debug_pids 2>/dev/null || true
    fi
  fi

  if is_port_busy 9222 && ! endpoint_reports_chrome; then
    echo -e "${YELLOW}⚠️  Porta 9222 ocupada por outro processo. Liberando...${NC}"
    kill_port_listeners 9222
  fi
}

start_chrome_debug() {
  nohup env DISPLAY=:0 XAUTHORITY="$HOME/.Xauthority" "$CHROME_BIN" \
    --new-window \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port=9222 \
    --user-data-dir="$CHROME_USER_DATA_DIR" \
    --disable-blink-features=AutomationControlled \
    --disable-background-networking \
    --disable-background-timer-throttling \
    --disable-renderer-backgrounding \
    --disable-backgrounding-occluded-windows \
    --disable-backgrounding-occluded-windows-for-testing \
    --disable-features=CalculateNativeWinOcclusion \
    --disable-dev-shm-usage \
    --no-default-browser-check \
    --no-first-run \
    --password-store=basic \
    about:blank \
    >>"$CHROME_DEBUG_LOG" 2>&1 &
  disown "$!" 2>/dev/null || true
}

start_chrome_watchdog() {
  if [ -n "$CHROME_WATCHDOG_PID" ] && kill -0 "$CHROME_WATCHDOG_PID" >/dev/null 2>&1; then
    return 0
  fi

  touch "$CHROME_WATCHDOG_LOG"
  (
    restarting=0
    fail_count=0
    while true; do
      sleep 4

      if curl -fsS "http://127.0.0.1:9222/json/version" >/dev/null 2>&1; then
        restarting=0
        fail_count=0
        continue
      fi

      fail_count=$((fail_count + 1))
      if [ "$fail_count" -lt 3 ]; then
        continue
      fi

      if pgrep -af "(google-chrome|chromium).*remote-debugging-port=9222" >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: CDP 9222 sem resposta, mas Chrome Debug ainda está em execução. Aguardando sem reiniciar." >> "$CHROME_WATCHDOG_LOG"
        continue
      fi

      if [ "$restarting" -eq 1 ]; then
        continue
      fi

      restarting=1
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: Chrome Debug offline (9222). Tentando relançar..." >> "$CHROME_WATCHDOG_LOG"

      if start_chrome_debug >> "$CHROME_WATCHDOG_LOG" 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Chrome Debug relançado com sucesso." >> "$CHROME_WATCHDOG_LOG"
        fail_count=0
      else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Falha ao relançar Chrome Debug." >> "$CHROME_WATCHDOG_LOG"
      fi

      restarting=0
    done
  ) &

  CHROME_WATCHDOG_PID="$!"
}

start_automation_job() {
  local start_url
  local response
  start_url="http://127.0.0.1:8001/api/automation/start?devtools_url=${AUTOMATION_DEVTOOLS_URL}&batch_size=${AUTOMATION_BATCH_SIZE}&price_min=${AUTOMATION_PRICE_MIN}&price_limit=${AUTOMATION_PRICE_LIMIT}&export_threshold=${AUTOMATION_EXPORT_THRESHOLD}&start_index=${AUTOMATION_START_INDEX}&person=${AUTOMATION_PERSON}&resume=true"
  response="$(curl -sS -X POST "$start_url" 2>/dev/null || true)"

  if echo "$response" | grep -q '"status":"started"'; then
    echo -e "${GREEN}✅ Robô de automação iniciado automaticamente${NC}"
    return 0
  fi

  if echo "$response" | grep -q 'já está rodando'; then
    echo -e "${GREEN}✅ Robô já estava rodando (reutilizando)${NC}"
    return 0
  fi

  echo -e "${YELLOW}⚠️  Não foi possível confirmar auto-start do robô.${NC}"
  echo -e "${YELLOW}Resposta API: ${response:-sem resposta}${NC}"
  return 1
}

cleanup() {
  if [ "$CLEANUP_DONE" = "1" ]; then
    return 0
  fi
  CLEANUP_DONE="1"

  echo ""
  echo -e "${YELLOW}🛑 Encerrando processos iniciados por este script...${NC}"

  if wait_http "http://127.0.0.1:8001/api/health" 1; then
    curl -fsS -X POST "http://127.0.0.1:8001/api/automation/stop?force=true" >/dev/null 2>&1 || true
  fi

  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" 2>/dev/null || true
    echo -e "${GREEN}✅ Backend encerrado${NC}"
  fi

  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID" 2>/dev/null || true
    echo -e "${GREEN}✅ Frontend encerrado${NC}"
  fi

  if [ -n "$CHROME_WATCHDOG_PID" ] && kill -0 "$CHROME_WATCHDOG_PID" >/dev/null 2>&1; then
    kill "$CHROME_WATCHDOG_PID" 2>/dev/null || true
    echo -e "${GREEN}✅ Watchdog do Chrome Debug encerrado${NC}"
  fi

  if [ "$CHROME_STARTED_BY_SCRIPT" = "1" ] && [ "$KEEP_CHROME_DEBUG_ON_EXIT" = "0" ]; then
    pkill -f "(google-chrome|chromium).*remote-debugging-port=9222" 2>/dev/null || true
    echo -e "${GREEN}✅ Chrome Debug encerrado${NC}"
  elif [ "$CHROME_STARTED_BY_SCRIPT" = "1" ]; then
    echo -e "${BLUE}ℹ️  Chrome Debug mantido aberto (KEEP_CHROME_DEBUG_ON_EXIT=1)${NC}"
  fi

  pkill -f "python3 run_automation.py" 2>/dev/null || true

  echo ""
  echo "👋 Até logo!"
  exit 0
}

trap cleanup EXIT SIGINT SIGTERM

require_command curl
require_command lsof
require_command python3
require_command npm

cd "$PROJECT_DIR"
resolve_chrome_paths

echo -e "${BLUE}1️⃣  CHROME DEBUG${NC}"
echo -e "${BLUE}   Binário:         ${CHROME_BIN}${NC}"
echo -e "${BLUE}   Perfil automação: ${CHROME_USER_DATA_DIR}${NC}"
echo -e "${BLUE}   Log Chrome Debug: ${CHROME_DEBUG_LOG}${NC}"
kill_chrome_debug_9222
if wait_http "http://127.0.0.1:9222/json/version" 2 && endpoint_reports_chrome; then
  echo -e "${GREEN}✅ Chrome Debug já está ativo em 9222 (reutilizando)${NC}"
else
  if wait_http "http://127.0.0.1:9222/json/version" 1 && ! endpoint_reports_chrome; then
    echo -e "${YELLOW}⚠️  Porta 9222 está ativa, mas não é Chrome Debug. Reiniciando com Chrome...${NC}"
    kill_port_listeners 9222
    sleep 1
  fi

  echo -e "${YELLOW}🚀 Iniciando Chrome Debug...${NC}"
  if ! start_chrome_debug; then
    echo -e "${RED}❌ Falha ao iniciar o Chrome Debug.${NC}"
    exit 1
  fi
  CHROME_STARTED_BY_SCRIPT="1"
  if ! wait_http "http://127.0.0.1:9222/json/version" 25; then
    echo -e "${RED}❌ Falha ao conectar no Chrome Debug (9222).${NC}"
    echo -e "${YELLOW}Últimas linhas do log do Chrome Debug:${NC}"
    tail -n 80 "$CHROME_DEBUG_LOG" || true
    exit 1
  fi
  if ! endpoint_reports_chrome; then
    echo -e "${RED}❌ A porta 9222 não está respondendo como Chrome Debug.${NC}"
    echo -e "${YELLOW}Últimas linhas do log do Chrome Debug:${NC}"
    tail -n 80 "$CHROME_DEBUG_LOG" || true
    exit 1
  fi
  echo -e "${GREEN}✅ Chrome Debug iniciado em 9222${NC}"
fi
echo ""

echo -e "${BLUE}1️⃣.5️⃣  WATCHDOG CHROME DEBUG${NC}"
start_chrome_watchdog
echo -e "${GREEN}✅ Watchdog ativo (reinicia Chrome Debug automaticamente se 9222 cair)${NC}"
echo ""

echo -e "${BLUE}2️⃣  BACKEND API (8001)${NC}"
if wait_http "http://127.0.0.1:8001/api/health" 2 && port_belongs_to_project 8001; then
  echo -e "${GREEN}✅ Backend já está ativo em 8001 (reutilizando)${NC}"
else
  if wait_http "http://127.0.0.1:8001/api/health" 1 && ! port_belongs_to_project 8001; then
    echo -e "${YELLOW}⚠️  Porta 8001 está com outro projeto. Reiniciando com o backend do FBA Automation...${NC}"
  fi
  if is_port_busy 8001; then
    kill_port_listeners 8001
  fi

  if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${YELLOW}📦 Criando venv do backend...${NC}"
    python3 -m venv "$BACKEND_DIR/venv"
  fi

  echo -e "${YELLOW}📦 Garantindo dependências do backend...${NC}"
  (
    cd "$BACKEND_DIR"
    source venv/bin/activate
    pip install -q -r ../requirements.txt
    python3 -c "import playwright" >/dev/null 2>&1 || {
      pip install -q playwright
      python3 -m playwright install chromium
    }
    echo -e "${YELLOW}🚀 Subindo backend...${NC}"
    python3 main.py > "$BACKEND_LOG" 2>&1 &
    echo $! > "$LOG_DIR/backend.pid"
  )
  BACKEND_PID="$(cat "$LOG_DIR/backend.pid")"

  if ! wait_http "http://127.0.0.1:8001/api/health" 45; then
    echo -e "${RED}❌ Backend não ficou disponível em 8001.${NC}"
    echo -e "${YELLOW}Últimas linhas do log do backend:${NC}"
    tail -n 80 "$BACKEND_LOG" || true
    exit 1
  fi
  echo -e "${GREEN}✅ Backend ativo em http://127.0.0.1:8001${NC}"
fi
echo ""

if [ "$AUTOMATION_AUTO_START" = "1" ]; then
  echo -e "${BLUE}2️⃣.5️⃣  AUTO START DO ROBÔ${NC}"
  start_automation_job || true
  echo ""
fi

echo -e "${BLUE}3️⃣  FRONTEND (5173)${NC}"
if wait_http "http://127.0.0.1:5173" 2 && port_belongs_to_project 5173; then
  echo -e "${GREEN}✅ Frontend já está ativo em 5173 (reutilizando)${NC}"
else
  if wait_http "http://127.0.0.1:5173" 1 && ! port_belongs_to_project 5173; then
    echo -e "${YELLOW}⚠️  Porta 5173 está com outro projeto. Reiniciando com o frontend do FBA Automation...${NC}"
  fi
  if is_port_busy 5173; then
    kill_port_listeners 5173
  fi

  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}📦 Instalando dependências do frontend...${NC}"
    (cd "$FRONTEND_DIR" && npm install)
  fi

  echo -e "${YELLOW}🚀 Subindo frontend...${NC}"
  (
    cd "$FRONTEND_DIR"
    npm run dev -- --host 0.0.0.0 --port 5173 > "$FRONTEND_LOG" 2>&1 &
    echo $! > "$LOG_DIR/frontend.pid"
  )
  FRONTEND_PID="$(cat "$LOG_DIR/frontend.pid")"

  if ! wait_http "http://127.0.0.1:5173" 45; then
    echo -e "${RED}❌ Frontend não ficou disponível em 5173.${NC}"
    echo -e "${YELLOW}Últimas linhas do log do frontend:${NC}"
    tail -n 80 "$FRONTEND_LOG" || true
    exit 1
  fi
  echo -e "${GREEN}✅ Frontend ativo em http://127.0.0.1:5173${NC}"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ SISTEMA PRONTO${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}📍 Serviços:${NC}"
echo "   🌐 Frontend:      http://localhost:5173"
echo "   🔧 Backend API:   http://localhost:8001"
echo "   📖 Docs API:      http://localhost:8001/docs"
echo "   🌍 Chrome Debug:  http://localhost:9222"
if [ "$AUTOMATION_AUTO_START" = "1" ]; then
  echo "   🤖 Robô:          AUTO-START ligado (indice=${AUTOMATION_START_INDEX}, preço>=${AUTOMATION_PRICE_MIN}, preço<=${AUTOMATION_PRICE_LIMIT}, lote=${AUTOMATION_BATCH_SIZE})"
else
  echo "   🤖 Robô:          AUTO-START desligado (inicie manualmente no botão da UI)"
fi
echo ""
echo -e "${BLUE}📊 Logs em Segundo Plano:${NC}"
echo "   Backend:   tail -f $BACKEND_LOG"
echo "   Frontend:  tail -f $FRONTEND_LOG"
echo "   Chrome WD: tail -f $CHROME_WATCHDOG_LOG"
echo "   Diagnóstico: tail -f $PROJECT_DIR/backend/logs/automation_diagnostics.jsonl"
echo ""
echo -e "${BLUE}⚙️  Troca Rápida de Perfil:${NC}"
echo "   Super estável: ./iniciar_tudo_chrome.sh super-estavel"
echo "   Turbo noturno: ./iniciar_tudo_chrome.sh turbo-noturno"
echo "   (alternativa) AUTOMATION_PERFORMANCE_PROFILE=turbo-noturno ./iniciar_tudo_chrome.sh"
echo "   Auto-start faixa de preço: AUTOMATION_PRICE_MIN=10 AUTOMATION_PRICE_LIMIT=85 AUTOMATION_AUTO_START=1 ./iniciar_tudo_chrome.sh"
echo "   Config persistente: use $LOCAL_ENV_FILE"
echo ""
echo -e "${YELLOW}⚠️  Pressione Ctrl+C para encerrar TODOS os processos iniciados por este script${NC}"
echo -e "${BLUE}ℹ️  O padrão é encerrar também o Chrome Debug ao sair. Para manter aberto, rode com KEEP_CHROME_DEBUG_ON_EXIT=1${NC}"
echo ""

tail -f "$BACKEND_LOG" "$FRONTEND_LOG"
