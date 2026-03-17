import json
import os

STATE_FILE = "automation_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "start_index": "",
        "current_supplier_row": None,
        "current_page_url": None,
        "processed_links": [],  # Links of the current session/page
        "accumulated_items": [],
        "total_captured_for_supplier": 0,
        "processed_suppliers_indices": [],
        "deferred_suppliers_indices": [],  # Fornecedores pulados temporariamente (ex: captcha timeout)
        "global_captured_urls": [], # Historico eterno de URLs ja capturadas
        "link_fail_counts": {},     # Falhas por URL (abertura/captura)
        "domain_fail_counts": {},   # Falhas agregadas por domínio
        "quarantined_links": {},    # URL -> unix timestamp (fim quarentena)
        "quarantined_domains": {},  # domínio -> unix timestamp (fim quarentena)
    }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def clear_supplier_state():
    state = load_state()
    next_start_index = ""
    
    # Registra esse fornecedor como concluído para sempre para não refazer
    if state.get("current_supplier_row"):
        idx = state["current_supplier_row"].get("indice")
        idx_str = str(idx).strip() if idx is not None else ""
        if idx_str:
            completed = [str(x).strip() for x in state.get("processed_suppliers_indices", []) if str(x).strip()]
            if idx_str not in completed:
                completed.append(idx_str)
            state["processed_suppliers_indices"] = completed

            # Modo sequencial estrito: após concluir N, força início em N+1.
            if idx_str.isdigit():
                next_start_index = str(int(idx_str) + 1)
            
    state["current_supplier_row"] = None
    state["current_page_url"] = None
    state["processed_links"] = []
    state["total_captured_for_supplier"] = 0
    state["start_index"] = next_start_index
    save_state(state)
