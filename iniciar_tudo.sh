#!/bin/bash

# Script para iniciar Backend, Frontend e Opera Debug de forma resiliente.
# Uso: ./iniciar_tudo.sh [super-estavel|turbo-noturno]

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
OPERA_DEBUG_LOG="$LOG_DIR/opera_debug.log"
LOCAL_ENV_FILE="${LOCAL_ENV_FILE:-$PROJECT_DIR/.env.local}"

if [ -f "$LOCAL_ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$LOCAL_ENV_FILE"
fi

BACKEND_PID=""
FRONTEND_PID=""
OPERA_STARTED_BY_SCRIPT="0"
OPERA_WATCHDOG_PID=""
OPERA_WATCHDOG_LOG="$LOG_DIR/opera_watchdog.log"
VPN_GUARD_LOG="$LOG_DIR/vpn_guard.log"
KEEP_OPERA_DEBUG_ON_EXIT="${KEEP_OPERA_DEBUG_ON_EXIT:-0}"
CLEANUP_DONE="0"
OPERA_NORMAL_PROFILE_PATH="${OPERA_NORMAL_PROFILE_PATH:-$HOME/snap/opera/current/.config/opera/Default}"
OPERA_AUTOMATION_USER_DATA_DIR="${OPERA_AUTOMATION_USER_DATA_DIR:-$HOME/snap/opera/common/opera-automation}"
OPERA_SYNC_FROM_NORMAL="${OPERA_SYNC_FROM_NORMAL:-1}"
OPERA_SYNC_DELETE="${OPERA_SYNC_DELETE:-1}"
OPERA_NORMAL_USER_DATA_DIR=""
OPERA_NORMAL_PROFILE_NAME=""
OPERA_USER_DATA_DIR=""
OPERA_PROFILE_NAME=""
OPERA_SNAP_FALLBACK_USER_DATA_DIR="${OPERA_SNAP_FALLBACK_USER_DATA_DIR:-$HOME/snap/opera/common/opera-automation}"
AUTOMATION_AUTO_START="${AUTOMATION_AUTO_START:-0}"
AUTOMATION_DEVTOOLS_URL="${AUTOMATION_DEVTOOLS_URL:-http://127.0.0.1:9222}"
AUTOMATION_BATCH_SIZE="${AUTOMATION_BATCH_SIZE:-10}"
AUTOMATION_PRICE_MIN="${AUTOMATION_PRICE_MIN:-0}"
AUTOMATION_PRICE_LIMIT="${AUTOMATION_PRICE_LIMIT:-85}"
AUTOMATION_EXPORT_THRESHOLD="${AUTOMATION_EXPORT_THRESHOLD:-500}"
AUTOMATION_START_INDEX="${AUTOMATION_START_INDEX:-36}"
AUTOMATION_PERSON="${AUTOMATION_PERSON:-Mateus}"

# Guardião de VPN (US)
VPN_ENFORCE_US="${VPN_ENFORCE_US:-1}"
VPN_AUTO_CONNECT_US="${VPN_AUTO_CONNECT_US:-0}"
VPN_BLOCK_IF_NOT_US="${VPN_BLOCK_IF_NOT_US:-1}"
VPN_US_NMCLI_CONNECTION="${VPN_US_NMCLI_CONNECTION:-}"
VPN_CONNECT_COMMAND="${VPN_CONNECT_COMMAND:-}"
VPN_VERIFY_ATTEMPTS="${VPN_VERIFY_ATTEMPTS:-5}"
VPN_VERIFY_DELAY_SECONDS="${VPN_VERIFY_DELAY_SECONDS:-4}"
VPN_COUNTRY_CHECK_TIMEOUT="${VPN_COUNTRY_CHECK_TIMEOUT:-8}"
VPN_REQUIRED_COUNTRY="${VPN_REQUIRED_COUNTRY:-US}"
VPN_PROTON_API_FALLBACK="${VPN_PROTON_API_FALLBACK:-1}"
VPN_PROTON_CLIENT_TYPE="${VPN_PROTON_CLIENT_TYPE:-gui}"
VPN_PROTON_CONFIRM_BEFORE_CONNECT="${VPN_PROTON_CONFIRM_BEFORE_CONNECT:-1}"
VPN_DISCONNECT_ON_EXIT="${VPN_DISCONNECT_ON_EXIT:-1}"
VPN_DISCONNECT_COMMAND="${VPN_DISCONNECT_COMMAND:-}"
VPN_DISCONNECT_ALL_NMCLI="${VPN_DISCONNECT_ALL_NMCLI:-1}"
# Modo manual fixo: o script não gerencia VPN (sem checagem/conexão/desconexão).
VPN_MANUAL_MODE="1"

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
: > "$OPERA_DEBUG_LOG"
: > "$VPN_GUARD_LOG"

echo "=========================================="
echo "🚀 INICIANDO FBA AUTOMATION COMPLETO"
echo "=========================================="
echo ""
echo -e "${BLUE}⚙️  Perfil de performance ativo: ${AUTOMATION_PROFILE_ACTIVE}${NC}"
echo -e "${BLUE}   Abertura abas: parallel=${TAB_OPEN_MAX_PARALLEL}, timeout=${TAB_OPEN_TIMEOUT_MS}ms, delay=${TAB_OPEN_DELAY_SECONDS}s${NC}"
echo -e "${BLUE}   Captura: conc=${CAPTURE_MAX_CONCURRENCY}, per-page-timeout=${CAPTURE_PER_PAGE_TIMEOUT_MS}ms${NC}"
echo -e "${BLUE}   Guardião memória: mínimo livre=${MEMORY_MIN_AVAILABLE_MB}MB${NC}"
if [ "$VPN_MANUAL_MODE" = "1" ]; then
  echo -e "${BLUE}   VPN: modo manual (sem validação automática neste script)${NC}"
elif [ "$VPN_ENFORCE_US" = "1" ]; then
  echo -e "${BLUE}   Guardião VPN ${VPN_REQUIRED_COUNTRY}: ativo (auto-connect=${VPN_AUTO_CONNECT_US}, block=${VPN_BLOCK_IF_NOT_US})${NC}"
else
  echo -e "${BLUE}   Guardião VPN ${VPN_REQUIRED_COUNTRY}: desativado${NC}"
fi
echo ""

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo -e "${RED}❌ Comando obrigatório não encontrado: ${cmd}${NC}"
    exit 1
  fi
}

get_public_country_code() {
  local cc=""

  cc="$(curl -fsS --max-time "$VPN_COUNTRY_CHECK_TIMEOUT" "https://ipapi.co/country/" 2>/dev/null | tr -d '\r\n ' | tr '[:lower:]' '[:upper:]' || true)"
  if [[ "$cc" =~ ^[A-Z]{2}$ ]]; then
    echo "$cc"
    return 0
  fi

  cc="$(curl -fsS --max-time "$VPN_COUNTRY_CHECK_TIMEOUT" "https://ipinfo.io/country" 2>/dev/null | tr -d '\r\n ' | tr '[:lower:]' '[:upper:]' || true)"
  if [[ "$cc" =~ ^[A-Z]{2}$ ]]; then
    echo "$cc"
    return 0
  fi

  cc="$(curl -fsS --max-time "$VPN_COUNTRY_CHECK_TIMEOUT" "https://ifconfig.co/country-iso" 2>/dev/null | tr -d '\r\n ' | tr '[:lower:]' '[:upper:]' || true)"
  if [[ "$cc" =~ ^[A-Z]{2}$ ]]; then
    echo "$cc"
    return 0
  fi

  return 1
}

list_nmcli_vpn_connections() {
  nmcli -t -f NAME,TYPE connection show 2>/dev/null | awk -F: '$2=="vpn" || $2=="wireguard"{print $1}'
}

list_nmcli_active_vpn_connections() {
  nmcli -t -f NAME,TYPE connection show --active 2>/dev/null | awk -F: '$2=="vpn" || $2=="wireguard"{print $1}'
}

proton_api_imports_available() {
  python3 - <<'PY' >/dev/null 2>&1
import importlib
importlib.import_module("proton.vpn.core.api")
importlib.import_module("proton.vpn.core.session_holder")
PY
}

proton_api_available() {
  [ "$VPN_PROTON_API_FALLBACK" = "1" ] || return 1
  proton_api_imports_available
}

disconnect_vpn_with_proton_api() {
  python3 - "$VPN_PROTON_CLIENT_TYPE" <<'PY'
import asyncio
import inspect
import sys

client_type = (sys.argv[1] if len(sys.argv) > 1 else "gui").strip() or "gui"

try:
    from proton.vpn.core.api import ProtonVPNAPI
    from proton.vpn.core.session_holder import ClientTypeMetadata
except Exception as exc:
    print(f"proton-import-error: {exc}")
    raise SystemExit(31)


async def try_invoke(target, method_name):
    method = getattr(target, method_name, None)
    if method is None:
        return False
    try:
        result = method()
    except TypeError:
        return False
    if inspect.isawaitable(result):
        await result
    return True


async def main():
    api = ProtonVPNAPI(ClientTypeMetadata(type=client_type))
    if not api.is_user_logged_in():
        print("proton-not-logged-in")
        return 32

    connector = await api.get_vpn_connector()

    candidates = [connector, api]
    methods = [
        "disconnect",
        "disconnect_vpn",
        "disconnect_current_connection",
        "disconnect_current_vpn",
        "disconnect_vpn_connection",
    ]

    for candidate in candidates:
        for method_name in methods:
            try:
                if await try_invoke(candidate, method_name):
                    print(f"proton-disconnected-method={method_name}")
                    return 0
            except Exception:
                continue

    print("proton-disconnect-method-not-found")
    return 33


raise SystemExit(asyncio.run(main()))
PY
}

disconnect_vpn_on_exit() {
  [ "$VPN_DISCONNECT_ON_EXIT" = "1" ] || return 0

  echo -e "${YELLOW}🔌 Encerrando VPN para voltar à rede normal...${NC}"
  local disconnected="0"
  local attempted="0"

  if [ -n "$VPN_DISCONNECT_COMMAND" ]; then
    attempted="1"
    if bash -lc "$VPN_DISCONNECT_COMMAND" >> "$VPN_GUARD_LOG" 2>&1; then
      disconnected="1"
    fi
  fi

  if command -v nmcli >/dev/null 2>&1; then
    local down_any="0"
    local vpn_name=""
    local -a active_vpn_list=()
    if [ "$VPN_DISCONNECT_ALL_NMCLI" = "1" ]; then
      mapfile -t active_vpn_list < <(list_nmcli_active_vpn_connections)
      if [ "${#active_vpn_list[@]}" -gt 0 ]; then
        attempted="1"
        for vpn_name in "${active_vpn_list[@]}"; do
          if nmcli connection down id "$vpn_name" >> "$VPN_GUARD_LOG" 2>&1; then
            down_any="1"
          fi
        done
      fi
    fi
    if [ "$down_any" = "1" ]; then
      disconnected="1"
    fi
  fi

  if [ "$disconnected" != "1" ] && command -v protonvpn-cli >/dev/null 2>&1; then
    attempted="1"
    if protonvpn-cli disconnect >> "$VPN_GUARD_LOG" 2>&1; then
      disconnected="1"
    fi
  fi

  if [ "$disconnected" != "1" ] && proton_api_imports_available; then
    attempted="1"
    if disconnect_vpn_with_proton_api >> "$VPN_GUARD_LOG" 2>&1; then
      disconnected="1"
    fi
  fi

  if [ "$disconnected" = "1" ]; then
    echo -e "${GREEN}✅ VPN desligada; rede normal restaurada.${NC}"
  elif [ "$attempted" = "1" ]; then
    echo -e "${YELLOW}⚠️  Não foi possível confirmar desligamento automático da VPN.${NC}"
    echo -e "${YELLOW}Confira manualmente. Log: ${VPN_GUARD_LOG}${NC}"
  else
    echo -e "${BLUE}ℹ️  Nenhum método de desligamento de VPN disponível.${NC}"
  fi
}

confirm_proton_vpn_connect() {
  local country_code="${1:-US}"
  [ "$VPN_PROTON_CONFIRM_BEFORE_CONNECT" = "1" ] || return 0

  local prompt_in=""
  local prompt_out=""
  if [ -r /dev/tty ] && [ -w /dev/tty ]; then
    prompt_in="/dev/tty"
    prompt_out="/dev/tty"
  elif [ -t 0 ] && [ -t 1 ]; then
    prompt_in="/dev/stdin"
    prompt_out="/dev/stdout"
  else
    echo -e "${YELLOW}⚠️  Confirmação do Proton VPN está ativa, mas não há terminal interativo.${NC}"
    echo -e "${YELLOW}Defina VPN_PROTON_CONFIRM_BEFORE_CONNECT=0 para execução não interativa.${NC}"
    return 1
  fi

  local answer=""
  while true; do
    printf "%b" "${YELLOW}⚠️  Iniciar VPN PROTON para ${country_code}? [s/N]: ${NC}" > "$prompt_out"
    read -r answer < "$prompt_in" || answer=""

    answer="$(printf '%s' "$answer" | tr '[:upper:]' '[:lower:]')"
    case "$answer" in
      s|sim|y|yes)
        return 0
        ;;
      ""|n|nao|não|no)
        printf "%b\n" "${YELLOW}⚠️  Conexão Proton cancelada por confirmação do usuário.${NC}" > "$prompt_out"
        return 1
        ;;
      *)
        printf "%b\n" "${YELLOW}Digite s para confirmar ou n para cancelar.${NC}" > "$prompt_out"
        ;;
    esac
  done
}

connect_vpn_with_proton_api() {
  local country_code="${1:-US}"
  if ! proton_api_available; then
    return 1
  fi

  if ! confirm_proton_vpn_connect "$country_code"; then
    return 1
  fi

  echo -e "${YELLOW}🔐 Conectando VPN via Proton API (${country_code})...${NC}"
  python3 - "$country_code" "$VPN_PROTON_CLIENT_TYPE" <<'PY'
import asyncio
import sys

country = (sys.argv[1] if len(sys.argv) > 1 else "US").upper().strip()
client_type = (sys.argv[2] if len(sys.argv) > 2 else "gui").strip() or "gui"

try:
    from proton.vpn.core.api import ProtonVPNAPI
    from proton.vpn.core.session_holder import ClientTypeMetadata
except Exception as exc:
    print(f"proton-import-error: {exc}")
    raise SystemExit(31)


async def main():
    api = ProtonVPNAPI(ClientTypeMetadata(type=client_type))
    if not api.is_user_logged_in():
        print("proton-not-logged-in")
        return 32

    connector = await api.get_vpn_connector()
    server = api.server_list.get_fastest_in_country(country)
    if server is None:
        print(f"proton-no-server-{country}")
        return 33

    vpn_server = connector.get_vpn_server(server, api.refresher.client_config)
    print(f"proton-connecting-server={server.name}")
    await connector.connect(vpn_server)
    return 0


raise SystemExit(asyncio.run(main()))
PY
}

connect_vpn_us() {
  local method_attempted="0"
  local target_country="$VPN_REQUIRED_COUNTRY"

  if [ -n "$VPN_CONNECT_COMMAND" ]; then
    method_attempted="1"
    echo -e "${YELLOW}🔐 Executando comando customizado de VPN...${NC}"
    if bash -lc "$VPN_CONNECT_COMMAND"; then
      return 0
    fi
    echo -e "${YELLOW}⚠️  Comando customizado de VPN falhou. Tentando fallback...${NC}"
  fi

  if [ -n "$VPN_US_NMCLI_CONNECTION" ]; then
    method_attempted="1"
    require_command nmcli
    local vpn_name="$VPN_US_NMCLI_CONNECTION"
    if [ "$vpn_name" = "auto" ]; then
      mapfile -t vpn_list < <(list_nmcli_vpn_connections)
      if [ "${#vpn_list[@]}" -eq 1 ]; then
        vpn_name="${vpn_list[0]}"
      else
        echo -e "${YELLOW}⚠️  VPN_US_NMCLI_CONNECTION=auto requer exatamente 1 conexão no nmcli (vpn|wireguard).${NC}"
        echo -e "${YELLOW}Conexões detectadas (${#vpn_list[@]}):${NC}" >> "$VPN_GUARD_LOG"
        printf '%s\n' "${vpn_list[@]}" >> "$VPN_GUARD_LOG"
        vpn_name=""
      fi
    fi
    if [ -n "$vpn_name" ]; then
      echo -e "${YELLOW}🔐 Conectando VPN via NetworkManager: ${vpn_name}${NC}"
      if nmcli connection up id "$vpn_name"; then
        return 0
      fi
      echo -e "${YELLOW}⚠️  Conexão via NetworkManager falhou. Tentando fallback...${NC}"
    fi
  fi

  if connect_vpn_with_proton_api "$target_country"; then
    return 0
  fi

  if [ "$method_attempted" = "0" ]; then
    echo -e "${YELLOW}⚠️  Sem método de conexão automática configurado e fallback Proton indisponível.${NC}"
    echo -e "${YELLOW}   Configure VPN_US_NMCLI_CONNECTION ou VPN_CONNECT_COMMAND.${NC}"
    return 1
  fi

  echo -e "${YELLOW}⚠️  Todos os métodos de conexão automática falharam.${NC}"
  return 1
}

ensure_us_vpn() {
  if [ "$VPN_ENFORCE_US" != "1" ]; then
    echo -e "${BLUE}🔐 Guardião VPN: desativado (VPN_ENFORCE_US=0)${NC}"
    return 0
  fi

  local country=""
  local required_country
  required_country="$(echo "$VPN_REQUIRED_COUNTRY" | tr '[:lower:]' '[:upper:]')"
  country="$(get_public_country_code || true)"
  if [ "$country" = "$required_country" ]; then
    echo -e "${GREEN}✅ VPN/Geo OK: IP público em ${required_country}${NC}"
    return 0
  fi

  if [ -n "$country" ]; then
    echo -e "${YELLOW}⚠️  IP público atual fora de ${required_country}: ${country}${NC}"
  else
    echo -e "${YELLOW}⚠️  Não foi possível determinar país do IP público.${NC}"
  fi

  if [ "$VPN_AUTO_CONNECT_US" = "1" ]; then
    if connect_vpn_us >> "$VPN_GUARD_LOG" 2>&1; then
      local attempt=1
      while [ "$attempt" -le "$VPN_VERIFY_ATTEMPTS" ]; do
        sleep "$VPN_VERIFY_DELAY_SECONDS"
        country="$(get_public_country_code || true)"
        if [ "$country" = "$required_country" ]; then
          echo -e "${GREEN}✅ VPN conectada com sucesso: IP público em ${required_country}${NC}"
          return 0
        fi
        attempt=$((attempt + 1))
      done
      echo -e "${YELLOW}⚠️  VPN conectou, mas geo ainda não confirmou ${required_country}.${NC}"
    else
      echo -e "${YELLOW}⚠️  Falha ao executar conexão automática de VPN.${NC}"
    fi
  fi

  if [ "$VPN_BLOCK_IF_NOT_US" = "1" ]; then
    echo -e "${RED}❌ Guardião VPN bloqueou a inicialização fora de ${required_country}.${NC}"
    echo -e "${YELLOW}Configure uma destas opções e rode novamente:${NC}"
    echo "  1) VPN_US_NMCLI_CONNECTION=\"NOME_DA_VPN\" VPN_AUTO_CONNECT_US=1 ./iniciar_tudo.sh"
    echo "     (ou) VPN_US_NMCLI_CONNECTION=\"auto\" VPN_AUTO_CONNECT_US=1 ./iniciar_tudo.sh"
    echo "  2) VPN_CONNECT_COMMAND=\"comando-da-sua-vpn\" VPN_AUTO_CONNECT_US=1 ./iniciar_tudo.sh"
    echo "  3) Proton VPN App (Ubuntu): mantenha login ativo e use VPN_AUTO_CONNECT_US=1 (fallback Proton API)"
    echo "  4) (não recomendado) VPN_BLOCK_IF_NOT_US=0 ./iniciar_tudo.sh"
    if command -v nmcli >/dev/null 2>&1; then
      mapfile -t vpn_list < <(list_nmcli_vpn_connections)
      if [ "${#vpn_list[@]}" -gt 0 ]; then
        echo -e "${YELLOW}VPNs detectadas no nmcli:${NC}"
        printf '  - %s\n' "${vpn_list[@]}"
      else
        echo -e "${YELLOW}Nenhuma conexão VPN detectada no nmcli (type=vpn|wireguard).${NC}"
      fi
    fi
    echo -e "${YELLOW}Opcional: crie ${LOCAL_ENV_FILE} para não digitar sempre as variáveis.${NC}"
    echo -e "${YELLOW}Logs de conexão automática: ${VPN_GUARD_LOG}${NC}"
    exit 1
  fi

  echo -e "${YELLOW}⚠️  Prosseguindo sem confirmação de IP ${required_country} (VPN_BLOCK_IF_NOT_US=0).${NC}"
}

running_snap_opera() {
  [ -x "/snap/bin/opera" ] || [ -x "/snap/opera/current/usr/lib/x86_64-linux-gnu/opera/opera" ]
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

resolve_opera_profile_paths() {
  local requested_profile="$OPERA_NORMAL_PROFILE_PATH"
  local fallback_current="$HOME/snap/opera/current/.config/opera/Default"
  local detected_snap_profile=""

  detected_snap_profile="$(
    for dir in "$HOME"/snap/opera/[0-9]*; do
      if [ -f "$dir/.config/opera/Default/Preferences" ]; then
        printf '%s\n' "$dir/.config/opera/Default"
      fi
    done | sort -V | tail -n1
  )"

  # Perfil normal explicitamente no formato ".../Default"
  if [ -d "$requested_profile" ] && [ -f "$requested_profile/Preferences" ]; then
    OPERA_NORMAL_USER_DATA_DIR="$(dirname "$requested_profile")"
    OPERA_NORMAL_PROFILE_NAME="$(basename "$requested_profile")"
  # Perfil normal no formato ".../opera" (user data dir)
  elif [ -d "$requested_profile/Default" ]; then
    OPERA_NORMAL_USER_DATA_DIR="$requested_profile"
    OPERA_NORMAL_PROFILE_NAME="Default"
  # Fallback para caminho "current" do snap
  elif [ -d "$fallback_current" ] && [ -f "$fallback_current/Preferences" ]; then
    OPERA_NORMAL_USER_DATA_DIR="$(dirname "$fallback_current")"
    OPERA_NORMAL_PROFILE_NAME="$(basename "$fallback_current")"
  # Fallback robusto: escolhe a revisao numerica mais recente com perfil valido
  elif [ -n "$detected_snap_profile" ]; then
    OPERA_NORMAL_USER_DATA_DIR="$(dirname "$detected_snap_profile")"
    OPERA_NORMAL_PROFILE_NAME="$(basename "$detected_snap_profile")"
    echo -e "${YELLOW}⚠️  Usando fallback automático de perfil Opera: ${detected_snap_profile}${NC}"
  else
    echo -e "${RED}❌ Perfil normal do Opera não encontrado: ${requested_profile}${NC}"
    echo -e "${YELLOW}Defina OPERA_NORMAL_PROFILE_PATH com um caminho válido e rode novamente.${NC}"
    exit 1
  fi

  # No snap, diretórios ocultos fora de ~/snap/opera/common costumam falhar por confinamento.
  if running_snap_opera && [[ "$OPERA_AUTOMATION_USER_DATA_DIR" == "$HOME/."* ]]; then
    echo -e "${YELLOW}⚠️  OPERA_AUTOMATION_USER_DATA_DIR aponta para pasta oculta (${OPERA_AUTOMATION_USER_DATA_DIR}).${NC}"
    echo -e "${YELLOW}   Ajustando automaticamente para ${OPERA_SNAP_FALLBACK_USER_DATA_DIR}.${NC}"
    OPERA_AUTOMATION_USER_DATA_DIR="$OPERA_SNAP_FALLBACK_USER_DATA_DIR"
  fi

  OPERA_USER_DATA_DIR="$OPERA_AUTOMATION_USER_DATA_DIR"
  OPERA_PROFILE_NAME="$OPERA_NORMAL_PROFILE_NAME"

  mkdir -p "$OPERA_USER_DATA_DIR/$OPERA_PROFILE_NAME"

  local normal_real automation_real
  normal_real="$(readlink -f "$OPERA_NORMAL_USER_DATA_DIR" 2>/dev/null || echo "$OPERA_NORMAL_USER_DATA_DIR")"
  automation_real="$(readlink -f "$OPERA_USER_DATA_DIR" 2>/dev/null || echo "$OPERA_USER_DATA_DIR")"
  if [ "$normal_real" = "$automation_real" ]; then
    echo -e "${RED}❌ Perfil de automação não pode ser o mesmo perfil do Opera normal.${NC}"
    echo -e "${YELLOW}Ajuste OPERA_AUTOMATION_USER_DATA_DIR e rode novamente.${NC}"
    exit 1
  fi
}

retry_opera_with_snap_profile_if_needed() {
  if ! running_snap_opera; then
    return 1
  fi

  if [[ "$OPERA_USER_DATA_DIR" == "$OPERA_SNAP_FALLBACK_USER_DATA_DIR" ]]; then
    return 1
  fi

  echo -e "${YELLOW}⚠️  Tentando fallback de perfil Snap para Opera Debug...${NC}"
  OPERA_USER_DATA_DIR="$OPERA_SNAP_FALLBACK_USER_DATA_DIR"
  mkdir -p "$OPERA_USER_DATA_DIR/$OPERA_PROFILE_NAME"

  if ! sync_opera_profile_to_automation; then
    echo -e "${RED}❌ Falha ao sincronizar perfil no fallback Snap.${NC}"
    return 1
  fi

  if ! start_opera_debug; then
    return 1
  fi

  wait_http "http://127.0.0.1:9222/json/version" 25 && endpoint_reports_opera
}

sync_opera_profile_to_automation() {
  if [ "$OPERA_SYNC_FROM_NORMAL" != "1" ]; then
    return 0
  fi

  if [ ! -d "$OPERA_NORMAL_USER_DATA_DIR/$OPERA_NORMAL_PROFILE_NAME" ]; then
    echo -e "${RED}❌ Perfil normal de origem não encontrado: ${OPERA_NORMAL_USER_DATA_DIR}/${OPERA_NORMAL_PROFILE_NAME}${NC}"
    return 1
  fi

  echo -e "${BLUE}   Sincronizando perfil do Opera normal -> automação...${NC}"

  local rsync_delete_flag=""
  if [ "$OPERA_SYNC_DELETE" = "1" ]; then
    rsync_delete_flag="--delete"
  fi

  rsync -a $rsync_delete_flag \
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
    "${OPERA_NORMAL_USER_DATA_DIR}/" "${OPERA_USER_DATA_DIR}/"

  # Garante remoção de arquivos de lock/copias sujas de sessão
  find "$OPERA_USER_DATA_DIR" -maxdepth 3 -type f \
    \( -name 'Singleton*' -o -name '*.lock' -o -name 'lockfile' -o -name 'DevToolsActivePort' \) \
    -delete 2>/dev/null || true

  return 0
}

endpoint_reports_opera() {
  local version_json=""
  version_json="$(curl -fsS "http://127.0.0.1:9222/json/version" 2>/dev/null || true)"
  if [ -z "$version_json" ]; then
    return 1
  fi

  # Opera via Chromium pode expor Browser=Chrome, então aceitamos:
  # - Browser contendo "Opera"
  # - User-Agent contendo "OPR/"
  echo "$version_json" | grep -Eqi '"Browser"\s*:\s*"Opera|OPR/'
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

  # Se ainda houver listener em 9222 que não seja Opera, derruba para liberar a porta.
  if is_port_busy 9222 && ! endpoint_reports_opera; then
    echo -e "${YELLOW}⚠️  Porta 9222 ocupada por processo que não é Opera Debug. Liberando...${NC}"
    kill_port_listeners 9222
  fi
}

start_opera_debug() {
  local OPERA_BIN="/snap/bin/opera"
  if [ ! -x "$OPERA_BIN" ]; then
    OPERA_BIN="/snap/opera/current/usr/lib/x86_64-linux-gnu/opera/opera"
  fi
  if [ ! -x "$OPERA_BIN" ]; then
    echo -e "${RED}❌ Binário do Opera não encontrado.${NC}"
    return 1
  fi

  nohup "$OPERA_BIN" \
    --new-window \
    --remote-debugging-port=9222 \
    --user-data-dir="$OPERA_USER_DATA_DIR" \
    --profile-directory="$OPERA_PROFILE_NAME" \
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
    >>"$OPERA_DEBUG_LOG" 2>&1 &
  disown "$!" 2>/dev/null || true
}

start_opera_watchdog() {
  if [ -n "$OPERA_WATCHDOG_PID" ] && kill -0 "$OPERA_WATCHDOG_PID" >/dev/null 2>&1; then
    return 0
  fi

  touch "$OPERA_WATCHDOG_LOG"
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

      if pgrep -af "opera.*remote-debugging-port=9222" >/dev/null 2>&1; then
        {
          echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: CDP 9222 sem resposta, mas Opera Debug ainda esta em execucao. Aguardando sem reiniciar."
        } >> "$OPERA_WATCHDOG_LOG"
        continue
      fi

      if [ "$restarting" -eq 1 ]; then
        continue
      fi

      restarting=1
      {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: Opera Debug offline (9222). Tentando relancar..."
      } >> "$OPERA_WATCHDOG_LOG"

      if start_opera_debug >> "$OPERA_WATCHDOG_LOG" 2>&1; then
        {
          echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Opera Debug relancado com sucesso."
        } >> "$OPERA_WATCHDOG_LOG"
        fail_count=0
      else
        {
          echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Falha ao relancar Opera Debug."
        } >> "$OPERA_WATCHDOG_LOG"
      fi

      restarting=0
    done
  ) &

  OPERA_WATCHDOG_PID="$!"
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

  # Primeiro tenta parar automação via API para encerrar process-group do run_automation.py.
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

  if [ -n "$OPERA_WATCHDOG_PID" ] && kill -0 "$OPERA_WATCHDOG_PID" >/dev/null 2>&1; then
    kill "$OPERA_WATCHDOG_PID" 2>/dev/null || true
    echo -e "${GREEN}✅ Watchdog do Opera Debug encerrado${NC}"
  fi

  if [ "$OPERA_STARTED_BY_SCRIPT" = "1" ] && [ "$KEEP_OPERA_DEBUG_ON_EXIT" = "0" ]; then
    pkill -f "opera.*remote-debugging-port=9222" 2>/dev/null || true
    echo -e "${GREEN}✅ Opera debug encerrado${NC}"
  elif [ "$OPERA_STARTED_BY_SCRIPT" = "1" ]; then
    echo -e "${BLUE}ℹ️  Opera debug mantido aberto (KEEP_OPERA_DEBUG_ON_EXIT=1)${NC}"
  fi

  # Segurança extra contra órfãos fora do backend.
  pkill -f "python3 run_automation.py" 2>/dev/null || true

  if [ "$VPN_MANUAL_MODE" != "1" ]; then
    disconnect_vpn_on_exit
  fi

  echo ""
  echo "👋 Até logo!"
  exit 0
}

trap cleanup EXIT SIGINT SIGTERM

require_command curl
require_command lsof
require_command python3
require_command npm
require_command rsync

cd "$PROJECT_DIR"
if [ "$VPN_MANUAL_MODE" = "1" ]; then
  echo -e "${BLUE}0️⃣  VPN${NC}"
  echo -e "${BLUE}   Modo manual ativo: pulando validação/conexão automática.${NC}"
else
  echo -e "${BLUE}0️⃣  VERIFICAÇÃO VPN/GEO (${VPN_REQUIRED_COUNTRY})${NC}"
  ensure_us_vpn
fi
echo ""

resolve_opera_profile_paths

echo -e "${BLUE}1️⃣  OPERA DEBUG${NC}"
echo -e "${BLUE}   Perfil normal:    ${OPERA_NORMAL_USER_DATA_DIR}/${OPERA_NORMAL_PROFILE_NAME}${NC}"
echo -e "${BLUE}   Perfil automação: ${OPERA_USER_DATA_DIR}/${OPERA_PROFILE_NAME}${NC}"
echo -e "${BLUE}   Log Opera Debug:  ${OPERA_DEBUG_LOG}${NC}"
kill_chrome_debug_9222
if wait_http "http://127.0.0.1:9222/json/version" 2 && endpoint_reports_opera; then
  echo -e "${GREEN}✅ Opera debug já está ativo em 9222 (reutilizando)${NC}"
else
  if wait_http "http://127.0.0.1:9222/json/version" 1 && ! endpoint_reports_opera; then
    echo -e "${YELLOW}⚠️  Porta 9222 está ativa, mas não é Opera Debug. Reiniciando com Opera...${NC}"
    kill_port_listeners 9222
    sleep 1
  fi

  if ! sync_opera_profile_to_automation; then
    echo -e "${RED}❌ Falha ao sincronizar perfil de automação do Opera.${NC}"
    exit 1
  fi

  echo -e "${YELLOW}🚀 Iniciando Opera debug...${NC}"
  if ! start_opera_debug; then
    echo -e "${RED}❌ Falha ao iniciar o Opera debug.${NC}"
    exit 1
  fi
  OPERA_STARTED_BY_SCRIPT="1"
  if ! wait_http "http://127.0.0.1:9222/json/version" 25; then
    if ! retry_opera_with_snap_profile_if_needed; then
      echo -e "${RED}❌ Falha ao conectar no Opera debug (9222).${NC}"
      echo -e "${YELLOW}Últimas linhas do log do Opera Debug:${NC}"
      tail -n 80 "$OPERA_DEBUG_LOG" || true
      exit 1
    fi
  fi
  if ! endpoint_reports_opera; then
    if ! retry_opera_with_snap_profile_if_needed; then
      echo -e "${RED}❌ A porta 9222 não está respondendo como Opera Debug.${NC}"
      echo -e "${YELLOW}Últimas linhas do log do Opera Debug:${NC}"
      tail -n 80 "$OPERA_DEBUG_LOG" || true
      exit 1
    fi
  fi
  echo -e "${GREEN}✅ Opera debug iniciado em 9222${NC}"
fi
echo ""

echo -e "${BLUE}1️⃣.5️⃣  WATCHDOG OPERA DEBUG${NC}"
start_opera_watchdog
echo -e "${GREEN}✅ Watchdog ativo (reinicia Opera Debug automaticamente se 9222 cair)${NC}"
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
echo "   🌐 Frontend:     http://localhost:5173"
echo "   🔧 Backend API:  http://localhost:8001"
echo "   📖 Docs API:     http://localhost:8001/docs"
echo "   🌍 Opera Debug:  http://localhost:9222"
if [ "$AUTOMATION_AUTO_START" = "1" ]; then
  echo "   🤖 Robô:         AUTO-START ligado (indice=${AUTOMATION_START_INDEX}, preço>=${AUTOMATION_PRICE_MIN}, preço<=${AUTOMATION_PRICE_LIMIT}, lote=${AUTOMATION_BATCH_SIZE})"
else
  echo "   🤖 Robô:         AUTO-START desligado (inicie manualmente no botão da UI)"
fi
echo ""
echo -e "${BLUE}📊 Logs em Segundo Plano:${NC}"
echo "   Backend:  tail -f $BACKEND_LOG"
echo "   Frontend: tail -f $FRONTEND_LOG"
echo "   Opera WD: tail -f $OPERA_WATCHDOG_LOG"
echo "   Diagnóstico: tail -f $PROJECT_DIR/backend/logs/automation_diagnostics.jsonl"
if [ "$VPN_MANUAL_MODE" != "1" ]; then
  echo "   VPN Guard: tail -f $VPN_GUARD_LOG"
fi
echo ""
echo -e "${BLUE}⚙️  Troca Rápida de Perfil:${NC}"
echo "   Super estável: ./iniciar_tudo.sh super-estavel"
echo "   Turbo noturno: ./iniciar_tudo.sh turbo-noturno"
echo "   (alternativa) AUTOMATION_PERFORMANCE_PROFILE=turbo-noturno ./iniciar_tudo.sh"
echo "   Auto-start faixa de preço: AUTOMATION_PRICE_MIN=10 AUTOMATION_PRICE_LIMIT=85 AUTOMATION_AUTO_START=1 ./iniciar_tudo.sh"
echo "   Config persistente: use $LOCAL_ENV_FILE"
echo ""
echo -e "${YELLOW}⚠️  Pressione Ctrl+C para encerrar TODOS os processos iniciados por este script${NC}"
echo -e "${BLUE}ℹ️  O padrão é encerrar também o Opera Debug ao sair. Para manter aberto, rode com KEEP_OPERA_DEBUG_ON_EXIT=1${NC}"
echo ""

tail -f "$BACKEND_LOG" "$FRONTEND_LOG"
