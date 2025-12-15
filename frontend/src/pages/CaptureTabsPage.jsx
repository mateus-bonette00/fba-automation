import { useState, useEffect } from 'react'
import './CaptureTabsPage.css'

function CaptureTabsPage() {
  const [devtoolsUrl, setDevtoolsUrl] = useState('http://127.0.0.1:9222')
  const [includePattern, setIncludePattern] = useState('')
  const [excludePattern, setExcludePattern] = useState('')
  const [loading, setLoading] = useState(false)
  const [tabs, setTabs] = useState(null)
  const [error, setError] = useState(null)
  const [browserStatus, setBrowserStatus] = useState('checking')
  const [copied, setCopied] = useState(false)
  const [clickedButtons, setClickedButtons] = useState(new Set())
  const [debugTabs, setDebugTabs] = useState(null)
  const [showingDebug, setShowingDebug] = useState(false)

  // ===== NOVO: Controles de performance =====
  const [fastMode, setFastMode] = useState(true)               // fast=1
  const [concurrency, setConcurrency] = useState(6)            // 6 em paralelo
  const [perPageTimeoutMs, setPerPageTimeoutMs] = useState(1200) // 1200 ms

  // ===== Persistência dos controles de performance =====
  useEffect(() => {
    try {
      const raw = localStorage.getItem('qota:capture_perf')
      if (raw) {
        const cfg = JSON.parse(raw)
        if (typeof cfg.fastMode === 'boolean') setFastMode(cfg.fastMode)
        if (typeof cfg.concurrency === 'number') setConcurrency(cfg.concurrency)
        if (typeof cfg.perPageTimeoutMs === 'number') setPerPageTimeoutMs(cfg.perPageTimeoutMs)
      }
    } catch {}
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem('qota:capture_perf', JSON.stringify({
        fastMode, concurrency, perPageTimeoutMs
      }))
    } catch {}
  }, [fastMode, concurrency, perPageTimeoutMs])

  // === ACUMULADO (CSV Único) ===
  const [accumulatedProducts, setAccumulatedProducts] = useState([])

  useEffect(() => {
    try {
      const raw = localStorage.getItem('qota:produtos_acumulados')
      if (raw) {
        const arr = JSON.parse(raw)
        if (Array.isArray(arr)) setAccumulatedProducts(arr)
      }
    } catch {}
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem('qota:produtos_acumulados', JSON.stringify(accumulatedProducts))
    } catch {}
  }, [accumulatedProducts])

  useEffect(() => {
    checkBrowserStatus()
  }, [devtoolsUrl])

  const checkBrowserStatus = async () => {
    try {
      const res = await fetch(
        `${window.API_URL}/api/capture/browser-status?devtools_url=${encodeURIComponent(devtoolsUrl)}`
      )
      const result = await res.json()
      setBrowserStatus(result.status)
    } catch {
      setBrowserStatus('offline')
    }
  }

  const handleCapture = async () => {
    setLoading(true)
    setError(null)
    setTabs(null)
    setClickedButtons(new Set())

    try {
      const params = new URLSearchParams({
        devtools_url: devtoolsUrl,
        include_pattern: includePattern,
        exclude_pattern: excludePattern,
        fast: fastMode ? '1' : '0',
        concurrency: String(concurrency || 1),
        per_page_timeout_ms: String(perPageTimeoutMs || 1200),
      })

      const res = await fetch(`${window.API_URL}/api/capture/capture-tabs?${params}`, {
        method: 'POST'
      })

      if (!res.ok) {
        throw new Error('Erro ao capturar abas')
      }

      const result = await res.json()
      setTabs(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const copyTabsToClipboard = () => {
    const text = tabs?.tabs?.map(t => t.url).join('\n') || ''
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const buildAmazonSearchUrl = (query) => {
    return `https://www.amazon.com/s?k=${encodeURIComponent(query)}`
  }

  const handleButtonClick = (buttonId) => {
    setClickedButtons(prev => {
      const newSet = new Set(prev)
      newSet.add(buttonId)
      return newSet
    })
  }

  const isButtonClicked = (buttonId) => clickedButtons.has(buttonId)

  const handleClearAll = () => {
    setTabs(null)
    setClickedButtons(new Set())
    setError(null)
  }

  // === ACUMULADO: adicionar, limpar, exportar ===
  const handleAddToAccumulated = () => {
    if (!tabs || !tabs.tabs) return
    const existing = new Map(accumulatedProducts.map(p => [p.url, p]))
    for (const tab of tabs.tabs) {
      if (!existing.has(tab.url)) {
        existing.set(tab.url, {
          product_title: tab.product_title || tab.title || 'Sem título',
          upc: tab.upc || '',
          upc_method: tab.upc_method || '',
          url: tab.url
        })
      }
    }
    setAccumulatedProducts(Array.from(existing.values()))
    setTabs(null)
    setClickedButtons(new Set())
  }

  const handleClearAccumulated = () => {
    if (window.confirm('Tem certeza que deseja limpar todos os produtos acumulados?')) {
      setAccumulatedProducts([])
      try { localStorage.removeItem('qota:produtos_acumulados') } catch {}
    }
  }

  const handleShowDebugTabs = async () => {
    setShowingDebug(true)
    try {
      const res = await fetch(`${window.API_URL}/api/capture/list-tabs?devtools_url=${encodeURIComponent(devtoolsUrl)}`)
      if (!res.ok) throw new Error('Erro ao listar abas')
      const result = await res.json()
      setDebugTabs(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setShowingDebug(false)
    }
  }

  const handleExportAccumulated = () => {
    if (accumulatedProducts.length === 0) {
      alert('Nenhum produto acumulado para exportar!')
      return
    }
    const rows = accumulatedProducts.map(p => ({
      product_title: p.product_title,
      upc: p.upc,
      upc_method: p.upc_method,
      url: p.url
    }))
    exportToCSV(rows, 'produtos_acumulados.csv')
  }

  return (
    <div className="capture-page">
      <h1>Capturar Abas do Navegador</h1>

      {/* Barra do acumulado */}
      <div className="card accumulated-bar">
        <div className="accumulated-left">
          <strong>Acumulados:</strong> {accumulatedProducts.length}
        </div>
        <div className="accumulated-actions">
          <button onClick={handleExportAccumulated} className="btn btn-secondary">
            Exportar CSV Único
          </button>
          <button onClick={handleClearAccumulated} className="btn btn-danger">
            Limpar acumulado
          </button>
        </div>
      </div>

      <div className="card setup-section">
        <h2>Configuração Rápida</h2>

        <div className="setup-steps">
          <div className="step">
            <span className="step-number">1</span>
            <div>
              <h4>Abra Chrome com DevTools</h4>
              <p>Execute no terminal (na pasta do projeto):</p>
              <code className="code-block">
                ./iniciar_chrome_debug.sh
              </code>
              <p style={{ fontSize: '12px', color: '#f59e0b', marginTop: '5px' }}>
                ⚠️ Uma nova janela do Chrome irá abrir (diferente do seu Chrome normal)
              </p>
            </div>
          </div>
          <div className="step">
            <span className="step-number">2</span>
            <div>
              <h4>Abra os produtos NESSE Chrome</h4>
              <p style={{ fontWeight: 'bold', color: '#10b981' }}>
                ✅ Abra as abas dos produtos NO CHROME que abriu no passo 1
              </p>
              <p style={{ fontSize: '12px', color: '#ef4444', marginTop: '5px' }}>
                ❌ NÃO use seu Chrome normal! Use apenas o Chrome do passo 1
              </p>
            </div>
          </div>
          <div className="step">
            <span className="step-number">3</span>
            <div>
              <h4>Verifique e Capture</h4>
              <p>Clique em "Ver Abas Abertas" para confirmar que as abas foram detectadas</p>
              <p style={{ fontSize: '12px', marginTop: '5px' }}>
                Se não aparecer nenhuma aba, volte ao passo 2
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card capture-section">
        <h2>Capturar Abas</h2>

        <div className="browser-status">
          <span className={`status-indicator ${browserStatus}`}></span>
          Navegador: <strong>{browserStatus.toUpperCase()}</strong>
        </div>

        <div className="form-grid">
          <div className="form-group">
            <label>DevTools URL</label>
            <input
              type="text"
              value={devtoolsUrl}
              onChange={(e) => setDevtoolsUrl(e.target.value)}
              placeholder="http://127.0.0.1:9222"
            />
          </div>

          <div className="form-group">
            <label>Incluir (padrão/regex)</label>
            <input
              type="text"
              value={includePattern}
              onChange={(e) => setIncludePattern(e.target.value)}
              placeholder="Ex: ^https?://(www\\.)?meu-fornecedor\\.com/"
            />
          </div>

          <div className="form-group">
            <label>Excluir (padrão/regex)</label>
            <input
              type="text"
              value={excludePattern}
              onChange={(e) => setExcludePattern(e.target.value)}
              placeholder="Ex: facebook\\.com|youtube\\.com"
            />
          </div>

          {/* === NOVO: controles de performance === */}
          <div className="form-group">
            <label>Fast Mode</label>
            <div className="toggle-row">
              <input
                id="fastMode"
                type="checkbox"
                checked={fastMode}
                onChange={(e) => setFastMode(e.target.checked)}
              />
              <label htmlFor="fastMode" className="inline-label">Usar extração rápida (recomendado)</label>
            </div>
          </div>

          <div className="form-group">
            <label>Concorrência</label>
            <input
              type="number"
              min={1}
              max={16}
              value={concurrency}
              onChange={(e) => setConcurrency(Number(e.target.value))}
              placeholder="6"
            />
            <small>Dica: 5–8 geralmente é ótimo</small>
          </div>

          <div className="form-group">
            <label>Timeout por página (ms)</label>
            <input
              type="number"
              min={300}
              max={5000}
              step={100}
              value={perPageTimeoutMs}
              onChange={(e) => setPerPageTimeoutMs(Number(e.target.value))}
              placeholder="1200"
            />
            <small>Suba se o site demorar p/ exibir DOM</small>
          </div>
        </div>

        <div className="actions-row" style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            onClick={handleCapture}
            disabled={loading || browserStatus === 'offline'}
            className="btn btn-primary"
          >
            {loading ? (
              <>
                <span className="loader"></span> Capturando...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <path d="M20.49 15a9 9 0 1 1-2-8.12"></path>
                </svg>
                Capturar Abas
              </>
            )}
          </button>

          <button
            onClick={handleShowDebugTabs}
            disabled={showingDebug || browserStatus === 'offline'}
            className="btn btn-secondary"
            style={{ backgroundColor: '#6c757d' }}
          >
            {showingDebug ? (
              <>
                <span className="loader"></span> Verificando...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
                Ver Abas Abertas
              </>
            )}
          </button>

          <button
            onClick={handleAddToAccumulated}
            disabled={!tabs || !tabs.tabs || tabs.tabs.length === 0}
            className="btn"
          >
            Adicionar ao acumulado
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}
      </div>

      {debugTabs && (
        <div className="card results-section" style={{ backgroundColor: '#2d3748', borderLeft: '4px solid #f59e0b' }}>
          <div className="results-header">
            <h2>🔍 Abas Detectadas no Chrome Debug ({debugTabs.total})</h2>
            <button onClick={() => setDebugTabs(null)} className="btn btn-secondary">
              Fechar
            </button>
          </div>

          {debugTabs.total === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center' }}>
              <p style={{ fontSize: '18px', marginBottom: '10px' }}>⚠️ Nenhuma aba detectada!</p>
              <p style={{ color: '#9ca3af' }}>
                Certifique-se de abrir as abas dos produtos <strong>NO CHROME</strong> que foi iniciado com o script:<br/>
                <code style={{ backgroundColor: '#1f2937', padding: '5px 10px', borderRadius: '4px', display: 'inline-block', marginTop: '10px' }}>
                  ./iniciar_chrome_debug.sh
                </code>
              </p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Título</th>
                    <th>URL</th>
                  </tr>
                </thead>
                <tbody>
                  {debugTabs.tabs.map((tab, i) => (
                    <tr key={i}>
                      <td>{tab.title}</td>
                      <td style={{ fontSize: '12px', color: '#9ca3af' }}>{tab.url}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tabs && (
        <div className="card results-section">
          <div className="results-header">
            <h2>Abas Capturadas ({tabs.total})</h2>
            <div className="header-buttons">
              <button onClick={copyTabsToClipboard} className="btn btn-secondary">
                {copied ? (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Copiado!
                  </>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                      <rect x="8" y="2" width="8" height="4"></rect>
                    </svg>
                    Copiar URLs
                  </>
                )}
              </button>
              <button onClick={handleClearAll} className="btn btn-danger">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                Limpar
              </button>
            </div>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Produto</th>
                  <th>UPC</th>
                  <th>Métodos</th>
                  <th>Links</th>
                </tr>
              </thead>
              <tbody>
                {tabs.tabs.map((tab, i) => (
                  <tr key={i}>
                    <td className="product-title">{tab.product_title || tab.title || 'Sem título'}</td>
                    <td className="upc-cell">
                      {tab.upc ? (
                        <span className="upc-badge">{tab.upc}</span>
                      ) : (
                        <span className="upc-not-found">Não encontrado</span>
                      )}
                    </td>
                    <td className="method-cell">{tab.upc_method}</td>
                    <td className="links-cell">
                      <div className="button-group">
                        <a
                          href={tab.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`link-btn link-btn-supplier ${isButtonClicked(`supplier-${i}`) ? 'clicked' : ''}`}
                          title="Abrir fornecedor"
                          onClick={() => handleButtonClick(`supplier-${i}`)}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                          </svg>
                          Fornecedor
                        </a>
                        {tab.upc && (
                          <a
                            href={buildAmazonSearchUrl(tab.upc)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`link-btn link-btn-upc ${isButtonClicked(`upc-${i}`) ? 'clicked' : ''}`}
                            title="Buscar por UPC na Amazon"
                            onClick={() => handleButtonClick(`upc-${i}`)}
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="11" cy="11" r="8"></circle>
                              <path d="m21 21-4.35-4.35"></path>
                            </svg>
                            UPC
                          </a>
                        )}
                        {tab.product_title && (
                          <a
                            href={buildAmazonSearchUrl(tab.product_title)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`link-btn link-btn-title ${isButtonClicked(`title-${i}`) ? 'clicked' : ''}`}
                            title="Buscar por título na Amazon"
                            onClick={() => handleButtonClick(`title-${i}`)}
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="11" cy="11" r="8"></circle>
                              <path d="m21 21-4.35-4.35"></path>
                            </svg>
                            Título
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="export-section">
            <button
              onClick={() => exportToCSV(tabs.tabs)}
              className="btn btn-secondary"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              Exportar CSV (somente esta captura)
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function exportToCSV(tabs, filename = 'produtos_capturados.csv') {
  const headers = ['Produto', 'UPC', 'Método', 'URL Fornecedor', 'Amazon UPC', 'Amazon Título']
  const rows = (tabs || []).map(tab => [
    tab.product_title || tab.title || 'Sem título',
    tab.upc || '',
    tab.upc_method || '',
    tab.url,
    tab.upc ? `https://www.amazon.com/s?k=${encodeURIComponent(tab.upc)}` : '',
    tab.product_title ? `https://www.amazon.com/s?k=${encodeURIComponent(tab.product_title)}` : ''
  ])

  let csv = '\uFEFF'
  csv += headers.map(h => `"${h}"`).join(',') + '\n'
  rows.forEach(row => {
    csv += row.map(cell => `"${cell}"`).join(',') + '\n'
  })

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  window.URL.revokeObjectURL(url)
}

export default CaptureTabsPage
