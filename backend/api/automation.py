import asyncio
import json
import logging
import os
import signal
import subprocess
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Paths principais
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "logs", "automation_run.log")
STATE_FILE = os.path.join(BASE_DIR, "automation_state.json")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
PROFILES_FILE = os.getenv(
    "AUTOMATION_PROFILES_FILE",
    os.path.join(BASE_DIR, "config", "automation_profiles.json"),
)

# Controle de seguranca
AUTOMATION_STOP_PROTECTION = os.getenv("AUTOMATION_STOP_PROTECTION", "0") == "1"
AUTOMATION_BOT_TOKEN = os.getenv("AUTOMATION_BOT_TOKEN", "")
AUTOMATION_BOT_ALLOW_UNAUTH = os.getenv("AUTOMATION_BOT_ALLOW_UNAUTH", "0") == "1"

DEFAULT_START_PARAMS: Dict[str, Any] = {
    "devtools_url": "http://127.0.0.1:9222",
    "batch_size": 10,
    "price_limit": 85.0,
    "price_min": 0.0,
    "export_threshold": 500,
    "start_index": "36",
    "end_index": "",
    "person": "Mateus",
    "resume": False,
}

# Estado em memoria do processo em execucao
automation_process = None
automation_runtime: Dict[str, Any] = {
    "profile_name": None,
    "started_at": None,
    "params": {},
    "vpn_active": False,
}

BOT_SESSION_TTL_SECONDS = int(os.getenv("AUTOMATION_BOT_SESSION_TTL_SECONDS", "900"))
bot_pending_sessions: Dict[str, Dict[str, Any]] = {}


def _cleanup_expired_bot_sessions() -> None:
    now = int(time.time())
    expired_keys = []
    for key, sess in bot_pending_sessions.items():
        updated_at = int(sess.get("updated_at", 0) or 0)
        if not updated_at or (now - updated_at) > BOT_SESSION_TTL_SECONDS:
            expired_keys.append(key)
    for key in expired_keys:
        bot_pending_sessions.pop(key, None)


def _get_bot_session_key(payload: Dict[str, Any]) -> str:
    candidates = [
        payload.get("session_id"),
        payload.get("conversation_id"),
        payload.get("chat_id"),
        payload.get("sender_id"),
        payload.get("user_id"),
        payload.get("from"),
        payload.get("phone"),
    ]
    for value in candidates:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return "default"


def _to_index_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def _process_is_running(proc) -> bool:
    return proc is not None and proc.poll() is None


def _clear_runtime() -> None:
    automation_runtime["profile_name"] = None
    automation_runtime["started_at"] = None
    automation_runtime["params"] = {}
    # vpn_active nao limpa aqui — e gerenciado pelo monitor


def _set_runtime(profile_name: str, params: Dict[str, Any]) -> None:
    automation_runtime["profile_name"] = profile_name
    automation_runtime["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    automation_runtime["params"] = params


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "sim", "s", "on"}
    return False


# =========================================================================
# VPN Hooks — conecta/desconecta VPN automaticamente por perfil
# =========================================================================

def _run_shell_command(cmd: str, timeout: int = 45) -> Dict[str, Any]:
    """Executa comando shell e retorna resultado."""
    try:
        result = subprocess.run(
            cmd, shell=True, timeout=timeout,
            capture_output=True, text=True,
        )
        logger.info(f"Shell [{cmd}] retornou code={result.returncode}")
        if result.stdout.strip():
            logger.info(f"  stdout: {result.stdout.strip()[:300]}")
        if result.stderr.strip():
            logger.warning(f"  stderr: {result.stderr.strip()[:300]}")
        return {
            "ok": result.returncode == 0,
            "code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Shell [{cmd}] timeout ({timeout}s)")
        return {"ok": False, "code": -1, "stdout": "", "stderr": f"timeout {timeout}s"}
    except Exception as e:
        logger.error(f"Shell [{cmd}] erro: {e}")
        return {"ok": False, "code": -1, "stdout": "", "stderr": str(e)}


def _vpn_connect(vpn_up_cmd: str, verify_country: str = "") -> Dict[str, Any]:
    """Liga VPN e opcionalmente verifica o pais do IP publico."""
    logger.info(f"VPN UP: {vpn_up_cmd}")
    result = _run_shell_command(vpn_up_cmd)
    if not result["ok"]:
        return {"ok": False, "message": f"VPN UP falhou: {result['stderr'] or result['stdout']}"}

    if verify_country:
        # Aguarda a VPN estabilizar
        time.sleep(4)
        for attempt in range(1, 6):
            country = _get_public_country()
            if country and country.upper() == verify_country.upper():
                logger.info(f"VPN verificada: IP publico em {country}")
                return {"ok": True, "message": f"VPN conectada. IP em {country}."}
            logger.info(f"Verificacao VPN tentativa {attempt}/5: IP em '{country}' (esperado: {verify_country})")
            time.sleep(3)
        return {"ok": False, "message": f"VPN conectou mas IP nao esta em {verify_country} (ultimo: {country})"}

    return {"ok": True, "message": "VPN conectada."}


def _vpn_disconnect(vpn_down_cmd: str) -> Dict[str, Any]:
    """Desliga VPN."""
    logger.info(f"VPN DOWN: {vpn_down_cmd}")
    result = _run_shell_command(vpn_down_cmd)
    automation_runtime["vpn_active"] = False
    if result["ok"]:
        logger.info("VPN desconectada com sucesso.")
    else:
        logger.warning(f"VPN DOWN pode ter falhado: {result['stderr'] or result['stdout']}")
    return result


def _get_public_country() -> str:
    """Detecta o pais do IP publico via APIs gratuitas."""
    apis = [
        "curl -fsS --max-time 8 'https://ipapi.co/country/' 2>/dev/null",
        "curl -fsS --max-time 8 'https://ipinfo.io/country' 2>/dev/null",
        "curl -fsS --max-time 8 'https://ifconfig.co/country-iso' 2>/dev/null",
    ]
    for api_cmd in apis:
        result = _run_shell_command(api_cmd, timeout=12)
        if result["ok"] and result["stdout"]:
            cc = result["stdout"].strip().upper()[:2]
            if cc.isalpha() and len(cc) == 2:
                return cc
    return ""


def _start_vpn_finish_monitor(proc, vpn_down_cmd: str) -> None:
    """
    Thread em background que monitora o processo da automacao.
    Quando o processo terminar (sucesso ou falha), desconecta a VPN.
    """
    def _monitor():
        try:
            proc.wait()  # Bloqueia ate o processo acabar
            logger.info("Automacao finalizada. Desconectando VPN automaticamente...")
            _vpn_disconnect(vpn_down_cmd)
        except Exception as e:
            logger.error(f"Erro no monitor de VPN: {e}")
            # Tenta desconectar mesmo assim
            try:
                _vpn_disconnect(vpn_down_cmd)
            except Exception:
                pass

    t = threading.Thread(target=_monitor, daemon=True, name="vpn-finish-monitor")
    t.start()
    logger.info(f"Monitor de VPN iniciado (desconecta ao fim da automacao)")


# =========================================================================
# Normalizacao e build de comandos
# =========================================================================

def _normalize_start_params(raw: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(DEFAULT_START_PARAMS)
    params.update(raw or {})

    try:
        params["devtools_url"] = str(params.get("devtools_url") or "").strip()
        params["batch_size"] = int(params.get("batch_size"))
        params["price_limit"] = float(params.get("price_limit"))
        params["price_min"] = float(params.get("price_min"))
        params["export_threshold"] = int(params.get("export_threshold"))
        params["start_index"] = str(params.get("start_index") or "").strip()
        params["end_index"] = str(params.get("end_index") or "").strip()
        params["person"] = str(params.get("person") or "Mateus").strip() or "Mateus"
        params["resume"] = _to_bool(params.get("resume", False))
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Parâmetros inválidos: {e}")

    if not params["devtools_url"]:
        raise HTTPException(status_code=400, detail="devtools_url é obrigatório.")
    if params["batch_size"] <= 0:
        raise HTTPException(status_code=400, detail="batch_size deve ser > 0.")
    if params["export_threshold"] <= 0:
        raise HTTPException(status_code=400, detail="export_threshold deve ser > 0.")
    if params["price_min"] < 0:
        raise HTTPException(status_code=400, detail="price_min não pode ser negativo.")
    if params["price_limit"] > 0 and params["price_min"] > params["price_limit"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Faixa de preço inválida: mínimo (${params['price_min']}) "
                f"maior que máximo (${params['price_limit']})."
            ),
        )
    start_idx_int = _to_index_int(params["start_index"])
    end_idx_int = _to_index_int(params["end_index"])
    if params["start_index"] and start_idx_int is None:
        raise HTTPException(status_code=400, detail="start_index deve ser um número inteiro.")
    if params["end_index"] and end_idx_int is None:
        raise HTTPException(status_code=400, detail="end_index deve ser um número inteiro.")
    if start_idx_int is not None and end_idx_int is not None and start_idx_int > end_idx_int:
        raise HTTPException(
            status_code=400,
            detail=f"Faixa de índice inválida: início ({start_idx_int}) maior que fim ({end_idx_int}).",
        )

    return params


def _build_run_command(params: Dict[str, Any]) -> list[str]:
    cmd = [
        "python3",
        "run_automation.py",
        "--devtools",
        str(params["devtools_url"]),
        "--batch-size",
        str(params["batch_size"]),
        "--price-limit",
        str(params["price_limit"]),
        "--price-min",
        str(params["price_min"]),
        "--export-threshold",
        str(params["export_threshold"]),
        "--person",
        str(params["person"]),
    ]

    if params["start_index"]:
        cmd.extend(["--start-index", str(params["start_index"])])
    if params["end_index"]:
        cmd.extend(["--end-index", str(params["end_index"])])

    return cmd


# =========================================================================
# Processo da automacao
# =========================================================================

def _start_automation_process(
    params: Dict[str, Any],
    profile_name: str = "custom",
    vpn_up_cmd: str = "",
    vpn_down_cmd: str = "",
    vpn_verify_country: str = "",
) -> Dict[str, Any]:
    global automation_process

    if _process_is_running(automation_process):
        raise HTTPException(status_code=400, detail="Automação já está rodando!")

    # --- VPN: conectar ANTES de iniciar a automacao ---
    vpn_result = None
    if vpn_up_cmd:
        vpn_result = _vpn_connect(vpn_up_cmd, verify_country=vpn_verify_country)
        if not vpn_result["ok"]:
            raise HTTPException(
                status_code=503,
                detail=f"Falha ao conectar VPN: {vpn_result['message']}",
            )
        automation_runtime["vpn_active"] = True

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Se não for resume, limpa log antigo
    if not params["resume"]:
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass

    # Se start_index foi informado e não é resume, limpa estado antigo
    if params["start_index"] and not params["resume"]:
        try:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
        except Exception as e:
            logger.error(f"Erro apagando estado: {e}")

    cmd = _build_run_command(params)
    try:
        log_out = open(LOG_FILE, "a", encoding="utf-8")
        automation_process = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            stdout=log_out,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        log_out.close()
    except Exception as e:
        logger.error(f"Erro ao iniciar automação: {e}")
        # Se VPN foi conectada mas automacao falhou, desconecta
        if vpn_down_cmd and automation_runtime.get("vpn_active"):
            _vpn_disconnect(vpn_down_cmd)
        raise HTTPException(status_code=500, detail=str(e))

    # --- VPN: iniciar monitor que desconecta quando a automacao terminar ---
    if vpn_down_cmd:
        _start_vpn_finish_monitor(automation_process, vpn_down_cmd)

    _set_runtime(profile_name=profile_name, params=params)

    result = {
        "status": "started",
        "pid": automation_process.pid,
        "profile": profile_name,
        "params": params,
    }
    if vpn_result:
        result["vpn"] = vpn_result["message"]
    return result


def _load_profiles() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(PROFILES_FILE):
        return {}

    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha lendo profiles de automação ({PROFILES_FILE}): {e}",
        )

    items = raw.get("profiles", []) if isinstance(raw, dict) else []
    profiles: Dict[str, Dict[str, Any]] = {}
    for item in items:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        profiles[name] = {
            "name": name,
            "description": str(item.get("description", "")).strip(),
            "params": item.get("params", {}) if isinstance(item.get("params"), dict) else {},
            "vpn_up": str(item.get("vpn_up", "")).strip(),
            "vpn_down": str(item.get("vpn_down", "")).strip(),
            "vpn_verify_country": str(item.get("vpn_verify_country", "")).strip(),
        }
    return profiles


def _build_status_payload() -> Dict[str, Any]:
    global automation_process
    is_running = _process_is_running(automation_process)

    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    exports = []
    if os.path.exists(EXPORTS_DIR):
        try:
            for root, _dirs, files in os.walk(EXPORTS_DIR):
                for file in files:
                    if file.endswith(".xlsx"):
                        rel_path = os.path.relpath(os.path.join(root, file), EXPORTS_DIR)
                        exports.append(rel_path.replace("\\", "/"))
            exports.sort(reverse=True)
        except Exception as e:
            logger.error(f"Erro processando exports: {e}")

    runtime = dict(automation_runtime)
    if is_running and _process_is_running(automation_process):
        runtime["pid"] = automation_process.pid
    else:
        runtime["pid"] = None

    return {
        "is_running": is_running,
        "state": state,
        "exports": exports,
        "runtime": runtime,
    }


def terminate_automation_process(grace_seconds: int = 12, force_kill: bool = True) -> bool:
    """
    Finaliza o processo da automação e toda a process-group.
    Retorna True se o processo foi efetivamente encerrado.
    """
    global automation_process

    proc = automation_process
    if not _process_is_running(proc):
        automation_process = None
        _clear_runtime()
        return False

    try:
        pgid = os.getpgid(proc.pid)
    except Exception:
        pgid = None

    try:
        if pgid is not None:
            os.killpg(pgid, signal.SIGTERM)
        else:
            proc.terminate()
    except ProcessLookupError:
        automation_process = None
        _clear_runtime()
        return True
    except Exception as e:
        logger.error(f"Erro enviando SIGTERM para automação: {e}")

    deadline = time.time() + max(1, grace_seconds)
    while time.time() < deadline:
        if proc.poll() is not None:
            automation_process = None
            _clear_runtime()
            return True
        time.sleep(0.2)

    if force_kill and proc.poll() is None:
        try:
            if pgid is not None:
                os.killpg(pgid, signal.SIGKILL)
            else:
                proc.kill()
        except ProcessLookupError:
            pass
        except Exception as e:
            logger.error(f"Erro enviando SIGKILL para automação: {e}")
        time.sleep(0.2)

    stopped = proc.poll() is not None
    if stopped:
        automation_process = None
        _clear_runtime()
    return stopped


async def stop_automation_on_shutdown() -> None:
    """
    Hook para shutdown do backend: impede órfãos do run_automation.py.
    """
    await asyncio.to_thread(terminate_automation_process, 8, True)


async def _stop_automation(force: bool = False) -> Dict[str, Any]:
    global automation_process

    if AUTOMATION_STOP_PROTECTION and not force:
        raise HTTPException(
            status_code=423,
            detail=(
                "Modo protegido ativo: stop bloqueado para evitar interrupção acidental. "
                "Use force=true se precisar parar."
            ),
        )

    if not _process_is_running(automation_process):
        automation_process = None
        _clear_runtime()
        return {"status": "stopped", "message": "Nenhum script rodando."}

    stopped = await asyncio.to_thread(terminate_automation_process, 12, True)
    if stopped:
        # O monitor de VPN vai detectar que o processo morreu e desconectar.
        # Mas se o usuario pediu parada manual, a thread monitor tambem vai agir.
        return {"status": "stopped", "message": "Automação e processos filhos encerrados."}

    raise HTTPException(status_code=500, detail="Falha ao encerrar automação.")


def _ensure_bot_auth(x_bot_token: Optional[str]) -> None:
    if AUTOMATION_BOT_ALLOW_UNAUTH:
        return
    if not AUTOMATION_BOT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="AUTOMATION_BOT_TOKEN não configurado no servidor.",
        )
    if (x_bot_token or "").strip() != AUTOMATION_BOT_TOKEN:
        raise HTTPException(status_code=401, detail="Token do bot inválido.")


def _profiles_text(profiles: Dict[str, Dict[str, Any]]) -> str:
    if not profiles:
        return "Nenhum perfil configurado."
    lines = []
    for name in sorted(profiles.keys()):
        desc = profiles[name].get("description") or "sem descricao"
        vpn_tag = " [VPN]" if profiles[name].get("vpn_up") else ""
        lines.append(f"- {name}: {desc}{vpn_tag}")
    return "\n".join(lines)


def _resolve_profile_name(profiles: Dict[str, Dict[str, Any]], requested_name: str) -> str:
    requested = (requested_name or "").strip()
    if not requested:
        return ""
    if requested in profiles:
        return requested
    low = requested.lower()
    for name in profiles.keys():
        if name.lower() == low:
            return name
    return ""


def _save_bot_session(session_key: str, data: Dict[str, Any]) -> None:
    data["updated_at"] = int(time.time())
    bot_pending_sessions[session_key] = data


def _clear_bot_session(session_key: str) -> None:
    bot_pending_sessions.pop(session_key, None)


def _start_profile_wizard(session_key: str, profile_name: str) -> None:
    _save_bot_session(
        session_key,
        {
            "type": "start_profile_wizard",
            "profile_name": profile_name,
            "step": "start_index",
            "answers": {},
        },
    )


def _wizard_prompt_for_step(step: str) -> str:
    if step == "start_index":
        return "Por qual INDICE você quer começar?"
    if step == "end_index":
        return "Até qual INDICE você quer finalizar?"
    if step == "price_min":
        return "Qual preço mínimo (USD)? Ex: 0"
    if step == "price_limit":
        return "Qual preço máximo (USD)? Ex: 85"
    if step == "batch_size":
        return "Quantas abas você quer abrir por lote? Ex: 10"
    return "Informe o próximo valor."


def _consume_wizard_answer(
    session_key: str,
    answer_text: str,
    profiles: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    session = bot_pending_sessions.get(session_key) or {}
    step = str(session.get("step") or "")
    answers = session.setdefault("answers", {})
    raw = (answer_text or "").strip().replace(",", ".")

    if step == "start_index":
        idx = _to_index_int(raw)
        if idx is None:
            return {"ok": False, "reply": "Índice inicial inválido. Informe um número inteiro. Ex: 4"}
        answers["start_index"] = str(idx)
        session["step"] = "end_index"
        _save_bot_session(session_key, session)
        return {"ok": True, "reply": _wizard_prompt_for_step("end_index")}

    if step == "end_index":
        end_idx = _to_index_int(raw)
        start_idx = _to_index_int(answers.get("start_index"))
        if end_idx is None:
            return {"ok": False, "reply": "Índice final inválido. Informe um número inteiro. Ex: 12"}
        if start_idx is not None and end_idx < start_idx:
            return {
                "ok": False,
                "reply": (
                    f"Índice final inválido. O fim ({end_idx}) não pode ser menor que o início ({start_idx})."
                ),
            }
        answers["end_index"] = str(end_idx)
        session["step"] = "price_min"
        _save_bot_session(session_key, session)
        return {"ok": True, "reply": _wizard_prompt_for_step("price_min")}

    if step == "price_min":
        try:
            price_min = float(raw)
        except (TypeError, ValueError):
            return {"ok": False, "reply": "Preço mínimo inválido. Ex: 0 ou 12.5"}
        if price_min < 0:
            return {"ok": False, "reply": "Preço mínimo não pode ser negativo."}
        answers["price_min"] = price_min
        session["step"] = "price_limit"
        _save_bot_session(session_key, session)
        return {"ok": True, "reply": _wizard_prompt_for_step("price_limit")}

    if step == "price_limit":
        try:
            price_limit = float(raw)
        except (TypeError, ValueError):
            return {"ok": False, "reply": "Preço máximo inválido. Ex: 85"}
        if price_limit <= 0:
            return {"ok": False, "reply": "Preço máximo deve ser maior que zero."}
        if price_limit < float(answers.get("price_min", 0)):
            return {
                "ok": False,
                "reply": (
                    f"Preço máximo inválido. O máximo (${price_limit}) não pode ser menor que o mínimo (${answers.get('price_min')})."
                ),
            }
        answers["price_limit"] = price_limit
        session["step"] = "batch_size"
        _save_bot_session(session_key, session)
        return {"ok": True, "reply": _wizard_prompt_for_step("batch_size")}

    if step == "batch_size":
        batch = _to_index_int(raw)
        if batch is None or batch <= 0:
            return {"ok": False, "reply": "Quantidade de abas inválida. Informe um inteiro > 0. Ex: 10"}
        answers["batch_size"] = int(batch)

        profile_name = str(session.get("profile_name") or "")
        resolved_profile = _resolve_profile_name(profiles, profile_name)
        if not resolved_profile:
            _clear_bot_session(session_key)
            return {"ok": False, "reply": f"Perfil '{profile_name}' não encontrado."}

        profile = profiles[resolved_profile]
        raw_params = dict(profile.get("params", {}))
        raw_params.update(
            {
                "start_index": str(answers.get("start_index") or ""),
                "end_index": str(answers.get("end_index") or ""),
                "price_min": float(answers.get("price_min") or 0),
                "price_limit": float(answers.get("price_limit") or 0),
                "batch_size": int(answers.get("batch_size") or 10),
                "resume": False,
            }
        )

        try:
            params = _normalize_start_params(raw_params)
        except HTTPException as e:
            _clear_bot_session(session_key)
            return {"ok": False, "reply": str(e.detail)}

        try:
            result = _start_automation_process(
                params=params,
                profile_name=resolved_profile,
                vpn_up_cmd=profile.get("vpn_up", ""),
                vpn_down_cmd=profile.get("vpn_down", ""),
                vpn_verify_country=profile.get("vpn_verify_country", ""),
            )
        except HTTPException as e:
            _clear_bot_session(session_key)
            return {"ok": False, "reply": str(e.detail)}

        _clear_bot_session(session_key)
        reply = (
            f"Automação iniciada com perfil '{resolved_profile}' (pid={result['pid']}).\n"
            f"Índice: {params['start_index']} até {params['end_index']}\n"
            f"Faixa de preço: ${params['price_min']} até ${params['price_limit']}\n"
            f"Abas por lote: {params['batch_size']}"
        )
        if result.get("vpn"):
            reply += f"\nVPN: {result['vpn']}"
        if profile.get("vpn_down"):
            reply += "\nVPN será desconectada automaticamente ao fim da varredura."
        return {"ok": True, "reply": reply, "result": result}

    _clear_bot_session(session_key)
    return {"ok": False, "reply": "Sessão inválida. Envie novamente: iniciar varrer-fornecedores"}


async def _execute_bot_command(text: str, session_key: str = "default") -> Dict[str, Any]:
    _cleanup_expired_bot_sessions()
    cmd = (text or "").strip()
    if not cmd:
        return {"ok": False, "reply": "Comando vazio."}

    low = cmd.lower()
    profiles = _load_profiles()

    if low in {"cancelar", "cancel", "sair", "parar"} and session_key in bot_pending_sessions:
        _clear_bot_session(session_key)
        return {"ok": True, "reply": "Fluxo cancelado. Quando quiser, envie: iniciar varrer-fornecedores"}

    if low in {"ajuda", "help", "menu", "comandos"}:
        return {
            "ok": True,
            "reply": (
                "Comandos:\n"
                "- listar automacoes\n"
                "- iniciar <perfil>\n"
                "- status automacao\n"
                "- parar automacao\n"
                "- cancelar (cancela perguntas pendentes)"
            ),
        }

    if low.startswith("listar"):
        return {
            "ok": True,
            "reply": "Perfis disponíveis:\n" + _profiles_text(profiles),
            "profiles": sorted(profiles.keys()),
        }

    if low.startswith("status"):
        status = _build_status_payload()
        if status["is_running"]:
            profile = status.get("runtime", {}).get("profile_name") or "custom"
            pid = status.get("runtime", {}).get("pid")
            started_at = status.get("runtime", {}).get("started_at") or "n/d"
            vpn = "Sim" if status.get("runtime", {}).get("vpn_active") else "Nao"
            return {
                "ok": True,
                "reply": (
                    f"Automação rodando.\n"
                    f"Perfil: {profile}\n"
                    f"PID: {pid}\n"
                    f"VPN ativa: {vpn}\n"
                    f"Iniciada em: {started_at}"
                ),
                "status": status,
            }
        return {"ok": True, "reply": "Nenhuma automação em execução.", "status": status}

    if low.startswith("parar"):
        result = await _stop_automation(force=True)
        return {"ok": True, "reply": result["message"], "result": result}

    pending = bot_pending_sessions.get(session_key)
    if pending and pending.get("type") == "start_profile_wizard":
        return _consume_wizard_answer(session_key, cmd, profiles)

    if low.startswith("iniciar"):
        # Aceita: "iniciar perfil", "iniciar automacao perfil"
        profile_name = cmd[len("iniciar") :].strip()
        if profile_name.lower().startswith("automacao "):
            profile_name = profile_name[10:].strip()

        if not profile_name:
            return {
                "ok": False,
                "reply": "Informe o perfil. Ex: iniciar varrer-fornecedores",
                "profiles": sorted(profiles.keys()),
            }

        resolved_profile_name = _resolve_profile_name(profiles, profile_name)
        if not resolved_profile_name:
            return {
                "ok": False,
                "reply": (
                    f"Perfil '{profile_name}' não encontrado.\n"
                    f"Use 'listar automacoes' para ver os nomes."
                ),
                "profiles": sorted(profiles.keys()),
            }

        if resolved_profile_name.lower() == "varrer-fornecedores":
            _start_profile_wizard(session_key, resolved_profile_name)
            return {
                "ok": True,
                "reply": (
                    "Antes de iniciar varrer-fornecedores, preciso de alguns parâmetros.\n"
                    f"{_wizard_prompt_for_step('start_index')}\n"
                    "Se quiser desistir, responda: cancelar"
                ),
            }

        profile = profiles[resolved_profile_name]
        raw_params = dict(profile.get("params", {}))
        params = _normalize_start_params(raw_params)

        vpn_up = profile.get("vpn_up", "")
        vpn_down = profile.get("vpn_down", "")
        vpn_verify = profile.get("vpn_verify_country", "")

        try:
            result = _start_automation_process(
                params=params,
                profile_name=resolved_profile_name,
                vpn_up_cmd=vpn_up,
                vpn_down_cmd=vpn_down,
                vpn_verify_country=vpn_verify,
            )
        except HTTPException as e:
            return {"ok": False, "reply": e.detail}

        reply = f"Automação iniciada com perfil '{resolved_profile_name}' (pid={result['pid']})."
        if result.get("vpn"):
            reply += f"\nVPN: {result['vpn']}"
        if vpn_down:
            reply += "\nVPN será desconectada automaticamente ao fim da varredura."

        return {
            "ok": True,
            "reply": reply,
            "result": result,
        }

    return {
        "ok": False,
        "reply": (
            "Comando não reconhecido. Use:\n"
            "- listar automacoes\n"
            "- iniciar <perfil>\n"
            "- status automacao\n"
            "- parar automacao"
        ),
    }


@router.get("/profiles")
async def list_profiles():
    profiles = _load_profiles()
    return {
        "profiles": [profiles[name] for name in sorted(profiles.keys())],
        "count": len(profiles),
        "profiles_file": PROFILES_FILE,
    }


@router.post("/start")
async def start_automation(
    devtools_url: str = "http://127.0.0.1:9222",
    batch_size: int = 10,
    price_limit: float = 85.0,
    price_min: float = 0.0,
    export_threshold: int = 500,
    start_index: str = "36",
    end_index: str = "",
    person: str = "Mateus",
    resume: bool = False,
):
    params = _normalize_start_params(
        {
            "devtools_url": devtools_url,
            "batch_size": batch_size,
            "price_limit": price_limit,
            "price_min": price_min,
            "export_threshold": export_threshold,
            "start_index": start_index,
            "end_index": end_index,
            "person": person,
            "resume": resume,
        }
    )
    return _start_automation_process(params=params, profile_name="custom")


@router.post("/start-profile/{profile_name}")
async def start_automation_profile(
    profile_name: str,
    resume: bool = False,
    devtools_url: Optional[str] = None,
    start_index: Optional[str] = None,
    end_index: Optional[str] = None,
    person: Optional[str] = None,
):
    profiles = _load_profiles()
    if profile_name not in profiles:
        raise HTTPException(
            status_code=404,
            detail=f"Perfil '{profile_name}' não encontrado em {PROFILES_FILE}.",
        )

    profile = profiles[profile_name]
    raw_params = dict(profile.get("params", {}))
    if devtools_url is not None:
        raw_params["devtools_url"] = devtools_url
    if start_index is not None:
        raw_params["start_index"] = start_index
    if end_index is not None:
        raw_params["end_index"] = end_index
    if person is not None:
        raw_params["person"] = person
    raw_params["resume"] = resume

    params = _normalize_start_params(raw_params)
    return _start_automation_process(
        params=params,
        profile_name=profile_name,
        vpn_up_cmd=profile.get("vpn_up", ""),
        vpn_down_cmd=profile.get("vpn_down", ""),
        vpn_verify_country=profile.get("vpn_verify_country", ""),
    )


@router.post("/stop")
async def stop_automation(force: bool = False):
    return await _stop_automation(force=force)


@router.post("/clear")
async def clear_automation_data():
    global automation_process
    if _process_is_running(automation_process):
        raise HTTPException(
            status_code=400,
            detail="Não é possível limpar enquanto a automação está rodando!",
        )

    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")

        return {"status": "cleared", "message": "Cache e logs limpos com sucesso!"}
    except Exception as e:
        logger.error(f"Erro ao limpar dados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    return _build_status_payload()


@router.get("/logs")
async def get_logs(lines: int = 150):
    if not os.path.exists(LOG_FILE):
        return {"logs": "Nenhum log encontrado. Pressione START para iniciar."}

    try:
        proc = subprocess.Popen(
            ["tail", "-n", str(lines), LOG_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, _ = proc.communicate()
        return {"logs": out.decode("utf-8", errors="replace")}
    except Exception as e:
        return {"logs": f"Erro lendo logs: {e}"}


@router.get("/download/{filename:path}")
async def download_excel(filename: str):
    file_path = os.path.join(EXPORTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(
        path=file_path,
        filename=os.path.basename(filename),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/bot/command")
async def bot_command(
    payload: Dict[str, Any],
    x_bot_token: Optional[str] = Header(default=None),
):
    _ensure_bot_auth(x_bot_token)
    text = str(payload.get("text") or payload.get("message") or payload.get("command") or "")
    session_key = _get_bot_session_key(payload)
    return await _execute_bot_command(text, session_key=session_key)
