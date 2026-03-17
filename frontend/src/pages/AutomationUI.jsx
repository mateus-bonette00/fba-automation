import React, { useState, useEffect, useRef } from "react";
import "./AutomationUI.css"; // Módulo de CSS Customizado

const AutomationUI = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [stateData, setStateData] = useState({});
  const [exportsList, setExportsList] = useState([]);
  const [logs, setLogs] = useState([]);
  const [config, setConfig] = useState({
    devtools_url: "http://127.0.0.1:9222",
    batch_size: 10,
    price_min: 0,
    price_limit: 85,
    export_threshold: 500,
    start_index: "36",
    person: "Mateus",
  });

  const logsEndRef = useRef(null);

  // Poll status every 2 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${window.API_URL}/api/automation/status`);
        const data = await res.json();
        setIsRunning(data.is_running);
        setStateData(data.state || {});
        setExportsList(data.exports || []);
      } catch (err) {
        console.error("Failed to fetch automation status", err);
      }
    };
    fetchStatus();
    const intv = setInterval(fetchStatus, 2000);
    return () => clearInterval(intv);
  }, []);

  // Poll logs every 1 second
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch(
          `${window.API_URL}/api/automation/logs?lines=100`,
        );
        const data = await res.json();
        // Backend returns lines as a single string with \n
        if (data.logs) {
          const lines = data.logs.split("\n").filter((l) => l.trim() !== "");
          setLogs(lines);
        }
      } catch (err) {
        // silently fail on logs if API disconnects temporarily
      }
    };
    fetchLogs();
    const intv = setInterval(fetchLogs, 1000);
    return () => clearInterval(intv);
  }, []);

  // Auto scroll logs to bottom only if user hasn't scrolled up manually
  useEffect(() => {
    if (!logsEndRef.current) return;
    const terminal = logsEndRef.current.parentElement;

    // Check if user is scrolled to the bottom (with a 50px threshold buffer)
    const isAtBottom =
      terminal.scrollHeight - terminal.scrollTop - terminal.clientHeight < 50;

    // Always scroll on first load, or if they were already at the bottom
    if (isAtBottom || logs.length <= 1) {
      terminal.scrollTop = terminal.scrollHeight;
    }
  }, [logs]);

  const handleStart = async (isResume = false) => {
    try {
      const payload = { ...config, resume: isResume };
      if (payload.price_min === "") payload.price_min = 0;
      if (payload.price_limit === "") payload.price_limit = 0;
      
      const qs = new URLSearchParams(payload).toString();
      const res = await fetch(`${window.API_URL}/api/automation/start?${qs}`, {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) alert(data.message || data.detail);
      else setIsRunning(true);
    } catch (err) {
      alert("Error contacting API");
    }
  };

  const handleStop = async () => {
    try {
      const res = await fetch(`${window.API_URL}/api/automation/stop?force=true`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        alert(data.message || data.detail || "Stop bloqueado.");
        return;
      }
      setIsRunning(false);
    } catch (err) {
      alert("Error stopping automation");
    }
  };

  const handleDownload = (filename) => {
    window.open(
      `${window.API_URL}/api/automation/download/${filename}`,
      "_blank",
    );
  };

  const handleClearData = async () => {
    if (
      !window.confirm(
        "Certeza que deseja limpar os logs e o cache de estados ao vivo?",
      )
    )
      return;
    try {
      const res = await fetch(`${window.API_URL}/api/automation/clear`, {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) alert(data.message || data.detail);
      else {
        setLogs([]);
        setStateData({});
      }
    } catch (err) {
      alert("Erro limpando os dados");
    }
  };

  return (
    <div className="automation-dashboard">
      <header className="auto-header">
        <h1>FBA Full Automation Panel</h1>
        <div
          className="header-actions"
          style={{ display: "flex", gap: "15px", alignItems: "center" }}
        >
          <button
            className="btn btn-warning"
            onClick={handleClearData}
            disabled={isRunning}
            style={{
              backgroundColor: "#ff9800",
              color: "#fff",
              border: "none",
              padding: "6px 12px",
              borderRadius: "4px",
              cursor: isRunning ? "not-allowed" : "pointer",
            }}
          >
            🧹 Limpar Tudo
          </button>
          <div className={`status-badge ${isRunning ? "running" : "stopped"}`}>
            {isRunning ? "🟢 Varrer Planilha: Em Progresso..." : "🔴 Parado"}
          </div>
        </div>
      </header>

      <div className="auto-grid">
        {/* Left Col - Configs & Control */}
        <div className="card control-panel">
          <h3>Controles de Execução</h3>
          <div className="inputs-grid">
            <div className="input-group">
              <label>Tamanho do Lote (Tabs)</label>
              <input
                type="number"
                value={config.batch_size}
                onChange={(e) =>
                  setConfig({ ...config, batch_size: Number(e.target.value) })
                }
                disabled={isRunning}
              />
            </div>
            <div className="input-group">
              <label>Para Quem essa Tabela?</label>
              <select
                value={config.person}
                onChange={(e) =>
                  setConfig({ ...config, person: e.target.value })
                }
                disabled={isRunning}
              >
                <option value="Mateus">Mateus</option>
                <option value="Daniel">Daniel</option>
              </select>
            </div>
            
            <div className="input-group">
              <label>Corte de Preço Mín. ($)</label>
              <input
                type="number"
                step="0.5"
                value={config.price_min}
                onChange={(e) =>
                  setConfig({ ...config, price_min: e.target.value === "" ? "" : Number(e.target.value) })
                }
                disabled={isRunning}
              />
            </div>
            <div className="input-group">
              <label>Corte de Preço Máx. ($)</label>
              <input
                type="number"
                step="0.5"
                value={config.price_limit}
                onChange={(e) =>
                  setConfig({ ...config, price_limit: e.target.value === "" ? "" : Number(e.target.value) })
                }
                disabled={isRunning}
              />
            </div>
            <div className="input-group">
              <label>Corte de Exportação Exata (Qtd)</label>
              <input
                type="number"
                step="50"
                value={config.export_threshold}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    export_threshold: Number(e.target.value),
                  })
                }
                disabled={isRunning}
              />
            </div>
            <div className="input-group">
              <label>Índice Inicial (Opcional)</label>
              <input
                type="text"
                placeholder="Ex: 18"
                value={config.start_index}
                onChange={(e) =>
                  setConfig({ ...config, start_index: e.target.value })
                }
                disabled={isRunning}
              />
            </div>
            <div className="input-group full-width">
              <label>Chrome CDP (DevTools URL)</label>
              <input
                type="text"
                value={config.devtools_url}
                onChange={(e) =>
                  setConfig({ ...config, devtools_url: e.target.value })
                }
                disabled={isRunning}
              />
            </div>
          </div>
          <div
            className="button-group"
            style={{ display: "flex", gap: "10px" }}
          >
            {!isRunning ? (
              <>
                <button
                  className="btn btn-primary"
                  onClick={() => handleStart(false)}
                  style={{ flex: 1 }}
                >
                  🚀 Começar / Reiniciar
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => handleStart(true)}
                  style={{
                    flex: 1,
                    backgroundColor: "#4caf50",
                    border: "none",
                  }}
                >
                  ▶️ Continuar Automação
                </button>
              </>
            ) : (
              <button
                className="btn btn-danger"
                onClick={handleStop}
                style={{ flex: 1 }}
              >
                🛑 Forçar Parada (Stop)
              </button>
            )}
          </div>
        </div>

        {/* Right Col - Live State Stats */}
        <div className="card stats-panel">
          <h3>Status ao Vivo do Supplier</h3>
          {stateData.current_supplier_row ? (
            <div className="stats-box">
              <div className="stat-row">
                <span className="label">Fornecedor Indice Lendo:</span>
                <span className="val bold">
                  {stateData.current_supplier_row.indice}
                </span>
              </div>
              <div className="stat-row">
                <span className="label">Fornecedor URL Base:</span>
                <span className="val trunck">
                  {stateData.current_supplier_row.url}
                </span>
              </div>
              <div className="stat-row highlight">
                <span className="label">Abas Acumuladas Ram Atual:</span>
                <span className="val big">
                  {(stateData.accumulated_items || []).length} /{" "}
                  {config.export_threshold}
                </span>
              </div>
              <div className="stat-row">
                <span className="label">Total itens processados desse ID:</span>
                <span className="val">
                  {stateData.total_captured_for_supplier || 0}
                </span>
              </div>
            </div>
          ) : (
            <p className="idle-msg">Nenhum snapshot de dado carregado ainda.</p>
          )}
        </div>
      </div>

      {/* Terminal View */}
      <div className="terminal-container card">
        <h3>Terminal de Logs (Em tempo real)</h3>
        <div className="terminal-bg">
          {logs.map((L, i) => (
            <div
              key={i}
              className={`log-line ${L.includes("CAPTCHA") || L.includes("WARNING") ? "warning" : ""} ${L.includes("ERROR") ? "error" : ""}`}
            >
              {L}
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Download History Grid */}
      <div className="card downloads-panel">
        <h3>Downloads Gerados (Baixar XLSX Template)</h3>
        {exportsList.length > 0 ? (
          <ul className="download-grid">
            {exportsList.map((item) => (
              <li key={item}>
                <span>{item}</span>
                <button className="btn-dl" onClick={() => handleDownload(item)}>
                  📦 Download
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="idle-msg">
            As extrações aparecerão aqui depois de cortarem do Lote de
            Exportação.
          </p>
        )}
      </div>
    </div>
  );
};

export default AutomationUI;
