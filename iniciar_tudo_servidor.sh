#!/bin/bash

# =============================================================================
# iniciar_tudo_servidor.sh
# Script para rodar o FBA Automation no SERVIDOR (openclaw-server) com CHROME.
#
# Equivalente ao iniciar_tudo.sh local, mas:
#   - Usa Google Chrome / Chromium em vez de Opera
#   - Suporta modo headless (sem display) para servidores sem GUI
#   - Sem frontend React (controle via API / ZoeBot)
#   - Sem gerenciamento de VPN (VPN_MANUAL_MODE=1 forçado)
#
# Uso:
#   ./iniciar_tudo_servidor.sh [super-estavel|turbo-noturno]
#   CHROME_HEADLESS=1 ./iniciar_tudo_servidor.sh
#   CHROME_BIN=/usr/bin/chromium-browser ./iniciar_tudo_servidor.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_DIR="$PROJECT_DIR/logs"
BACKEND_LOG="$LOG_DIR/backend.log"
CHROME_DEBUG_LOG="$LOG_DIR/chrome_debug.log"
CHROME_WATCHDOG_LOG="$LOG_DIR/chrome_watchdog.log"
LOCAL_ENV_FILE="${LOCAL_ENV_FILE:-$PROJECT_DIR/.env.server}"

# Carrega .env.server se existir (fallback para .env.local)
if [ -f "$LOCAL_ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$LOCAL_ENV_FILE"
elif [ -f "$PROJECT_DIR/.env.local" ]; then
  # shellcheck disable=SC1090
  source "$PROJECT_DIR/.env.local"
fi

# === PIDs e controle ===
BACKEND_PID=""
CHROME_STARTED_BY_SCRIPT="0"
CHROME_WATCHDOG_PID=""
KEEP_CHROME_DEBUG_ON_EXIT="${KEEP_CHROME_DEBUG_ON_EXIT:-0}"
CLEANUP_DONE="0"

# === Chrome Config ===
# Binário do Chrome. Auto-detecta google-chrome, google-chrome-stable, chromium, chromium-browser.
CHROME_BIN="${CHROME_BIN:-}"
# User data dir exclusivo para automação (NÃO usar o perfil pessoal do Chrome!)
CHROME_AUTOMATION_USER_DATA_DIR="${CHROME_AUTOMATION_USER_DATA_DIR:-$HOME/chrome-automation}"
# Porta do Chrome DevTools Protocol
CHROME_DEBUG_PORT="${CHROME_DEBUG_PORT:-9222}"
# 1 = inicia Chrome sem janela (ideal para servidor sem display)
CHROME_HEADLESS="${CHROME_HEADLESS:-0}"
# Copiar perfil de um Chrome normal para o de automação? (0 = não por padrão no servidor)
CHROME_SYNC_FROM_NORMAL="${CHROME_SYNC_FROM_NORMAL:-0}"
# Caminho do perfil normal do Chrome para copiar (só usado se CHROME_SYNC_FROM_NORMAL=1)
CHROME_NORMAL_USER_DATA_DIR="${CHROME_NORMAL_USER_DATA_DIR:-$HOME/.config/google-chrome}"

# === Automação Config (mesmas variáveis do iniciar_tudo.sh) ===
AUTOMATION_AUTO_START="${AUTOMATION_AUTO_START:-0}"
AUTOMATION_DEVTOOLS_URL="${AUTOMATION_DEVTOOLS_URL:-http://127.0.0.1:${CHROME_DEBUG_PORT}}"
AUTOMATION_BATCH_SIZE="${AUTOMATION_BATCH_SIZE:-10}"
AUTOMATION_PRICE_MIN="${AUTOMATION_PRICE_MIN:-0}"
AUTOMATION_PRICE_LIMIT="${AUTOMATION_PRICE_LIMIT:-85}"
AUTOMATION_EXPORT_THRESHOLD="${AUTOMATION_EXPORT_THRESHOLD:-500}"
AUTOMATION_START_INDEX="${AUTOMATION_START_INDEX:-36}"
AUTOMATION_PERSON="${AUTOMATION_PERSON:-Mateus}"

# VPN: no servidor, sempre modo manual.
VPN_MANUAL_MODE="1"

# === Perfil de Performance ===
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
      echo -e "${RED}Perfil de performance invalido: ${raw}${NC}"
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
: > "$CHROME_DEBUG_LOG"
: > "$CHROME_WATCHDOG_LOG"

echo "=========================================="
echo "  INICIANDO FBA AUTOMATION (SERVIDOR)"
echo "  Navegador: Google Chrome / Chromium"
echo "=========================================="
echo ""
echo -e "${BLUE}Perfil de performance ativo: ${AUTOMATION_PROFILE_ACTIVE}${NC}"
echo -e "${BLUE}   Abertura abas: parallel=${TAB_OPEN_MAX_PARALLEL}, timeout=${TAB_OPEN_TIMEOUT_MS}ms, delay=${TAB_OPEN_DELAY_SECONDS}s${NC}"
echo -e "${BLUE}   Captura: conc=${CAPTURE_MAX_CONCURRENCY}, per-page-timeout=${CAPTURE_PER_PAGE_TIMEOUT_MS}ms${NC}"
echo -e "${BLUE}   Guardiao memoria: minimo livre=${MEMORY_MIN_AVAILABLE_MB}MB${NC}"
echo -e "${BLUE}   VPN: modo manual (sem validacao automatica neste script)${NC}"
echo ""

# === Funcoes utilitarias ===

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo -e "${RED}Comando obrigatorio nao encontrado: ${cmd}${NC}"
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
  echo -e "${YELLOW}Porta ${port} ocupada. Encerrando processo(s): ${pids}${NC}"
  kill $pids 2>/dev/null || true
  sleep 1
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    kill -9 $pids 2>/dev/null || true
  fi
}

# === Auto-detectar binario do Chrome ===

detect_chrome_bin() {
  if [ -n "$CHROME_BIN" ] && [ -x "$CHROME_BIN" ]; then
    return 0
  fi

  # Ordem de preferencia
  local candidates=(
    "/usr/bin/google-chrome-stable"
    "/usr/bin/google-chrome"
    "/usr/bin/chromium-browser"
    "/usr/bin/chromium"
    "/snap/bin/chromium"
    "/snap/bin/google-chrome"
  )

  for candidate in "${candidates[@]}"; do
    if [ -x "$candidate" ]; then
      CHROME_BIN="$candidate"
      return 0
    fi
  done

  # Tenta via command -v
  for name in google-chrome-stable google-chrome chromium-browser chromium; do
    local found
    found="$(command -v "$name" 2>/dev/null || true)"
    if [ -n "$found" ] && [ -x "$found" ]; then
      CHROME_BIN="$found"
      return 0
    fi
  done

  echo -e "${RED}Nenhum Google Chrome ou Chromium encontrado no sistema.${NC}"
  echo -e "${YELLOW}Instale com: sudo apt install google-chrome-stable${NC}"
  echo -e "${YELLOW}Ou defina CHROME_BIN=/caminho/do/chrome${NC}"
  exit 1
}

# === Verifica se o CDP responde como Chrome/Chromium (nao Opera) ===

endpoint_reports_chrome() {
  local version_json=""
  version_json="$(curl -fsS "http://127.0.0.1:${CHROME_DEBUG_PORT}/json/version" 2>/dev/null || true)"
  if [ -z "$version_json" ]; then
    return 1
  fi
  # Aceita Chrome, Chromium, HeadlessChrome
  echo "$version_json" | grep -Eqi '"Browser"\s*:\s*"(Chrome|Chromium|HeadlessChrome)'
}

# === Sincronizar perfil do Chrome normal para automacao ===

sync_chrome_profile_to_automation() {
  if [ "$CHROME_SYNC_FROM_NORMAL" != "1" ]; then
    return 0
  fi

  if [ ! -d "$CHROME_NORMAL_USER_DATA_DIR/Default" ]; then
    echo -e "${YELLOW}Perfil normal do Chrome nao encontrado em: ${CHROME_NORMAL_USER_DATA_DIR}/Default${NC}"
    echo -e "${YELLOW}Pulando sincronizacao de perfil.${NC}"
    return 0
  fi

  echo -e "${BLUE}   Sincronizando perfil do Chrome normal -> automacao...${NC}"

  rsync -a --delete \
    --exclude='Singleton*' \
    --exclude='*.lock' \
    --exclude='lockfile' \
    --exclude='DevToolsActivePort' \
    --exclude='*/Cache/' \
    --exclude='*/GPUCache/' \
    --exclude='*/Code Cache/' \
    --exclude='*/ShaderCache/' \
    --exclude='*/GrShaderCache/' \
    --exclude='*/GraphiteDawnCache/' \
    --exclude='*/DawnGraphiteCache/' \
    --exclude='*/Crash Reports/' \
    "${CHROME_NORMAL_USER_DATA_DIR}/" "${CHROME_AUTOMATION_USER_DATA_DIR}/"

  # Remove lock files residuais
  find "$CHROME_AUTOMATION_USER_DATA_DIR" -maxdepth 3 -type f \
    \( -name 'Singleton*' -o -name '*.lock' -o -name 'lockfile' -o -name 'DevToolsActivePort' \) \
    -delete 2>/dev/null || true

  return 0
}

# === Iniciar Chrome Debug ===

start_chrome_debug() {
  local chrome_flags=(
    "--remote-debugging-port=${CHROME_DEBUG_PORT}"
    "--user-data-dir=${CHROME_AUTOMATION_USER_DATA_DIR}"
    # --- Anti-deteccao maxima (evitar CAPTCHAs e bloqueios de bot) ---
    "--disable-blink-features=AutomationControlled"
    "--disable-features=AutomationControlled,EnableAutomation,CalculateNativeWinOcclusion,TranslateUI"
    "--disable-infobars"
    "--disable-notifications"
    "--disable-popup-blocking"
    "--disable-save-password-bubble"
    "--disable-single-click-autofill"
    "--disable-translate"
    "--disable-sync"
    "--no-default-browser-check"
    "--no-first-run"
    "--password-store=basic"
    # --- Performance e estabilidade ---
    "--disable-background-networking"
    "--disable-background-timer-throttling"
    "--disable-renderer-backgrounding"
    "--disable-backgrounding-occluded-windows"
    "--disable-backgrounding-occluded-windows-for-testing"
    "--disable-dev-shm-usage"
    "--disable-gpu"
    "--disable-software-rasterizer"
    # --- Parecer navegador humano real ---
    "--window-size=1920,1080"
    "--start-maximized"
    "--lang=en-US,en"
  )

  if [ "$CHROME_HEADLESS" = "1" ]; then
    chrome_flags+=("--headless=new")
    echo -e "${BLUE}   Modo headless ativado${NC}"
  fi

  # Se nao tem display e nao e headless, forca headless
  if [ "$CHROME_HEADLESS" != "1" ] && [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo -e "${YELLOW}Nenhum display detectado (DISPLAY/WAYLAND_DISPLAY vazio). Forcando modo headless.${NC}"
    chrome_flags+=("--headless=new")
  fi

  nohup "$CHROME_BIN" "${chrome_flags[@]}" \
    >>"$CHROME_DEBUG_LOG" 2>&1 &
  disown "$!" 2>/dev/null || true
}

# === Watchdog do Chrome Debug ===

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

      if curl -fsS "http://127.0.0.1:${CHROME_DEBUG_PORT}/json/version" >/dev/null 2>&1; then
        restarting=0
        fail_count=0
        continue
      fi

      fail_count=$((fail_count + 1))
      if [ "$fail_count" -lt 3 ]; then
        continue
      fi

      if pgrep -af "chrome.*remote-debugging-port=${CHROME_DEBUG_PORT}" >/dev/null 2>&1; then
        {
          echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: CDP ${CHROME_DEBUG_PORT} sem resposta, mas Chrome Debug ainda em execucao. Aguardando."
        } >> "$CHROME_WATCHDOG_LOG"
        continue
      fi

      if [ "$restarting" -eq 1 ]; then
        continue
      fi

      restarting=1
      {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: Chrome Debug offline (${CHROME_DEBUG_PORT}). Tentando relancar..."
      } >> "$CHROME_WATCHDOG_LOG"

      if start_chrome_debug >> "$CHROME_WATCHDOG_LOG" 2>&1; then
        {
          echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Chrome Debug relancado com sucesso."
        } >> "$CHROME_WATCHDOG_LOG"
        fail_count=0
      else
        {
          echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Falha ao relancar Chrome Debug."
        } >> "$CHROME_WATCHDOG_LOG"
      fi

      restarting=0
    done
  ) &

  CHROME_WATCHDOG_PID="$!"
}

# === Auto-start da automacao via API ===

start_automation_job() {
  local start_url
  local response
  start_url="http://127.0.0.1:8001/api/automation/start?devtools_url=${AUTOMATION_DEVTOOLS_URL}&batch_size=${AUTOMATION_BATCH_SIZE}&price_min=${AUTOMATION_PRICE_MIN}&price_limit=${AUTOMATION_PRICE_LIMIT}&export_threshold=${AUTOMATION_EXPORT_THRESHOLD}&start_index=${AUTOMATION_START_INDEX}&person=${AUTOMATION_PERSON}&resume=true"
  response="$(curl -sS -X POST "$start_url" 2>/dev/null || true)"

  if echo "$response" | grep -q '"status":"started"'; then
    echo -e "${GREEN}Robo de automacao iniciado automaticamente${NC}"
    return 0
  fi

  if echo "$response" | grep -q 'ja esta rodando\|já está rodando'; then
    echo -e "${GREEN}Robo ja estava rodando (reutilizando)${NC}"
    return 0
  fi

  echo -e "${YELLOW}Nao foi possivel confirmar auto-start do robo.${NC}"
  echo -e "${YELLOW}Resposta API: ${response:-sem resposta}${NC}"
  return 1
}

# === Cleanup ===

cleanup() {
  if [ "$CLEANUP_DONE" = "1" ]; then
    return 0
  fi
  CLEANUP_DONE="1"

  echo ""
  echo -e "${YELLOW}Encerrando processos iniciados por este script...${NC}"

  # Parar automacao via API
  if wait_http "http://127.0.0.1:8001/api/health" 1; then
    curl -fsS -X POST "http://127.0.0.1:8001/api/automation/stop?force=true" >/dev/null 2>&1 || true
  fi

  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" 2>/dev/null || true
    echo -e "${GREEN}Backend encerrado${NC}"
  fi

  if [ -n "$CHROME_WATCHDOG_PID" ] && kill -0 "$CHROME_WATCHDOG_PID" >/dev/null 2>&1; then
    kill "$CHROME_WATCHDOG_PID" 2>/dev/null || true
    echo -e "${GREEN}Watchdog do Chrome Debug encerrado${NC}"
  fi

  if [ "$CHROME_STARTED_BY_SCRIPT" = "1" ] && [ "$KEEP_CHROME_DEBUG_ON_EXIT" = "0" ]; then
    pkill -f "chrome.*remote-debugging-port=${CHROME_DEBUG_PORT}" 2>/dev/null || true
    pkill -f "chromium.*remote-debugging-port=${CHROME_DEBUG_PORT}" 2>/dev/null || true
    echo -e "${GREEN}Chrome debug encerrado${NC}"
  elif [ "$CHROME_STARTED_BY_SCRIPT" = "1" ]; then
    echo -e "${BLUE}Chrome debug mantido aberto (KEEP_CHROME_DEBUG_ON_EXIT=1)${NC}"
  fi

  # Seguranca extra contra orfaos
  pkill -f "python3 run_automation.py" 2>/dev/null || true

  echo ""
  echo "Ate logo!"
  exit 0
}

trap cleanup EXIT SIGINT SIGTERM

# === Verificar dependencias ===

require_command curl
require_command lsof
require_command python3

# rsync so e obrigatorio se sync de perfil estiver ativo
if [ "$CHROME_SYNC_FROM_NORMAL" = "1" ]; then
  require_command rsync
fi

# === ETAPA 0: Detectar Chrome ===

cd "$PROJECT_DIR"

echo -e "${BLUE}0. DETECTANDO CHROME${NC}"
detect_chrome_bin
echo -e "${GREEN}Chrome encontrado: ${CHROME_BIN}${NC}"

# Mostrar versao
chrome_version="$("$CHROME_BIN" --version 2>/dev/null | head -1 || echo "desconhecida")"
echo -e "${BLUE}   Versao: ${chrome_version}${NC}"
echo ""

# === ETAPA 1: Chrome Debug ===

echo -e "${BLUE}1. CHROME DEBUG (porta ${CHROME_DEBUG_PORT})${NC}"
echo -e "${BLUE}   User data dir: ${CHROME_AUTOMATION_USER_DATA_DIR}${NC}"
echo -e "${BLUE}   Log: ${CHROME_DEBUG_LOG}${NC}"

# Matar processos Chrome debug antigos que nao sao deste projeto
if is_port_busy "$CHROME_DEBUG_PORT"; then
  if wait_http "http://127.0.0.1:${CHROME_DEBUG_PORT}/json/version" 2 && endpoint_reports_chrome; then
    echo -e "${GREEN}Chrome debug ja esta ativo em ${CHROME_DEBUG_PORT} (reutilizando)${NC}"
  else
    echo -e "${YELLOW}Porta ${CHROME_DEBUG_PORT} ocupada por processo que nao e Chrome Debug. Liberando...${NC}"
    kill_port_listeners "$CHROME_DEBUG_PORT"
    sleep 1
  fi
fi

if ! wait_http "http://127.0.0.1:${CHROME_DEBUG_PORT}/json/version" 2; then
  # Sincronizar perfil se configurado
  sync_chrome_profile_to_automation

  # Criar diretorio de automacao se nao existir
  mkdir -p "$CHROME_AUTOMATION_USER_DATA_DIR"

  echo -e "${YELLOW}Iniciando Chrome debug...${NC}"
  if ! start_chrome_debug; then
    echo -e "${RED}Falha ao iniciar o Chrome debug.${NC}"
    exit 1
  fi
  CHROME_STARTED_BY_SCRIPT="1"

  if ! wait_http "http://127.0.0.1:${CHROME_DEBUG_PORT}/json/version" 25; then
    echo -e "${RED}Falha ao conectar no Chrome debug (${CHROME_DEBUG_PORT}).${NC}"
    echo -e "${YELLOW}Ultimas linhas do log do Chrome Debug:${NC}"
    tail -n 80 "$CHROME_DEBUG_LOG" || true
    exit 1
  fi

  echo -e "${GREEN}Chrome debug iniciado em ${CHROME_DEBUG_PORT}${NC}"
fi

# Exibe info do browser conectado
chrome_info="$(curl -fsS "http://127.0.0.1:${CHROME_DEBUG_PORT}/json/version" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f\"Browser: {d.get('Browser', 'N/A')}\")
    print(f\"Protocol: {d.get('Protocol-Version', 'N/A')}\")
    print(f\"User-Agent: {d.get('User-Agent', 'N/A')[:80]}\")
except:
    print('N/A')
" 2>/dev/null || echo "N/A")"
echo -e "${BLUE}   ${chrome_info}${NC}"
echo ""

# === ETAPA 1.5: Watchdog do Chrome ===

echo -e "${BLUE}1.5. WATCHDOG CHROME DEBUG${NC}"
start_chrome_watchdog
echo -e "${GREEN}Watchdog ativo (reinicia Chrome Debug automaticamente se ${CHROME_DEBUG_PORT} cair)${NC}"
echo ""

# === ETAPA 2: Backend API ===

echo -e "${BLUE}2. BACKEND API (8001)${NC}"
if wait_http "http://127.0.0.1:8001/api/health" 2 && port_belongs_to_project 8001; then
  echo -e "${GREEN}Backend ja esta ativo em 8001 (reutilizando)${NC}"
else
  if wait_http "http://127.0.0.1:8001/api/health" 1 && ! port_belongs_to_project 8001; then
    echo -e "${YELLOW}Porta 8001 esta com outro projeto. Reiniciando com o backend do FBA Automation...${NC}"
  fi
  if is_port_busy 8001; then
    kill_port_listeners 8001
  fi

  # Cria venv se nao existir
  if [ ! -d "$BACKEND_DIR/venv" ] && [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo -e "${YELLOW}Criando venv do backend...${NC}"
    if [ -d "$PROJECT_DIR/.venv" ]; then
      : # .venv ja existe na raiz
    else
      python3 -m venv "$BACKEND_DIR/venv"
    fi
  fi

  # Detecta qual venv usar
  VENV_DIR=""
  if [ -d "$PROJECT_DIR/.venv" ]; then
    VENV_DIR="$PROJECT_DIR/.venv"
  elif [ -d "$BACKEND_DIR/venv" ]; then
    VENV_DIR="$BACKEND_DIR/venv"
  fi

  echo -e "${YELLOW}Garantindo dependencias do backend...${NC}"
  (
    cd "$BACKEND_DIR"
    if [ -n "$VENV_DIR" ]; then
      source "$VENV_DIR/bin/activate"
    fi
    pip install -q -r ../requirements.txt 2>/dev/null || pip install -q -r ../requirements.txt
    python3 -c "import playwright" >/dev/null 2>&1 || {
      pip install -q playwright
      python3 -m playwright install chromium
    }
    echo -e "${YELLOW}Subindo backend...${NC}"
    python3 main.py > "$BACKEND_LOG" 2>&1 &
    echo $! > "$LOG_DIR/backend.pid"
  )
  BACKEND_PID="$(cat "$LOG_DIR/backend.pid")"

  if ! wait_http "http://127.0.0.1:8001/api/health" 45; then
    echo -e "${RED}Backend nao ficou disponivel em 8001.${NC}"
    echo -e "${YELLOW}Ultimas linhas do log do backend:${NC}"
    tail -n 80 "$BACKEND_LOG" || true
    exit 1
  fi
  echo -e "${GREEN}Backend ativo em http://127.0.0.1:8001${NC}"
fi
echo ""

# === ETAPA 2.5: Auto-start do robo (opcional) ===

if [ "$AUTOMATION_AUTO_START" = "1" ]; then
  echo -e "${BLUE}2.5. AUTO START DO ROBO${NC}"
  start_automation_job || true
  echo ""
fi

# === ETAPA 3: Frontend (DESABILITADO no servidor) ===

echo -e "${BLUE}3. FRONTEND${NC}"
echo -e "${BLUE}   Frontend desabilitado no modo servidor.${NC}"
echo -e "${BLUE}   Controle via API REST ou ZoeBot.${NC}"
echo ""

# === Resumo final ===

echo "=========================================="
echo -e "${GREEN}SISTEMA PRONTO (SERVIDOR)${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}Servicos:${NC}"
echo "   Backend API:     http://127.0.0.1:8001"
echo "   Docs API:        http://127.0.0.1:8001/docs"
echo "   Chrome Debug:    http://127.0.0.1:${CHROME_DEBUG_PORT}"
echo "   Health Check:    curl http://127.0.0.1:8001/api/health"
if [ "$AUTOMATION_AUTO_START" = "1" ]; then
  echo "   Robo:            AUTO-START ligado (indice=${AUTOMATION_START_INDEX}, preco>=${AUTOMATION_PRICE_MIN}, preco<=${AUTOMATION_PRICE_LIMIT}, lote=${AUTOMATION_BATCH_SIZE})"
else
  echo "   Robo:            AUTO-START desligado (inicie via API ou ZoeBot)"
fi
echo ""
echo -e "${BLUE}Comandos uteis:${NC}"
echo "   Status:      curl http://127.0.0.1:8001/api/automation/status"
echo "   Iniciar:     curl -X POST 'http://127.0.0.1:8001/api/automation/start?resume=true&start_index=${AUTOMATION_START_INDEX}&price_limit=${AUTOMATION_PRICE_LIMIT}'"
echo "   Parar:       curl -X POST 'http://127.0.0.1:8001/api/automation/stop?force=true'"
echo "   Logs:        curl http://127.0.0.1:8001/api/automation/logs?lines=50"
echo "   Perfis:      curl http://127.0.0.1:8001/api/automation/profiles"
echo ""
echo -e "${BLUE}Logs em Segundo Plano:${NC}"
echo "   Backend:     tail -f $BACKEND_LOG"
echo "   Chrome WD:   tail -f $CHROME_WATCHDOG_LOG"
echo "   Chrome:      tail -f $CHROME_DEBUG_LOG"
echo "   Diagnostico: tail -f $PROJECT_DIR/backend/logs/automation_diagnostics.jsonl"
echo ""
echo -e "${BLUE}Troca Rapida de Perfil:${NC}"
echo "   Super estavel: ./iniciar_tudo_servidor.sh super-estavel"
echo "   Turbo noturno: ./iniciar_tudo_servidor.sh turbo-noturno"
echo "   Headless:      CHROME_HEADLESS=1 ./iniciar_tudo_servidor.sh"
echo "   Auto-start:    AUTOMATION_AUTO_START=1 ./iniciar_tudo_servidor.sh"
echo "   Config:        use $LOCAL_ENV_FILE"
echo ""
echo -e "${YELLOW}Pressione Ctrl+C para encerrar TODOS os processos iniciados por este script${NC}"
echo -e "${BLUE}Para manter Chrome aberto ao sair: KEEP_CHROME_DEBUG_ON_EXIT=1${NC}"
echo ""

# Fica vivo monitorando o backend
tail -f "$BACKEND_LOG"
