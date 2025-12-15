import { useState } from 'react'
import './SupplierScraperPage.css'

function SupplierScraperPage() {
  const [supplierUrl, setSupplierUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [products, setProducts] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState('')

  const handleScrape = async () => {
    if (!supplierUrl.trim()) {
      setError('Por favor, insira uma URL válida')
      return
    }

    if (!supplierUrl.startsWith('http')) {
      setError('URL deve começar com http:// ou https://')
      return
    }

    setLoading(true)
    setError(null)
    setProducts(null)
    setProgress('Iniciando scraping...')

    try {
      const res = await fetch(`${window.API_URL}/api/supplier/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          supplier_url: supplierUrl
        })
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || 'Erro ao fazer scraping')
      }

      const result = await res.json()
      setProducts(result)
      setProgress('')
    } catch (err) {
      setError(err.message)
      setProgress('')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadCSV = async () => {
    if (!supplierUrl.trim()) {
      return
    }

    setLoading(true)
    setError(null)
    setProgress('Gerando CSV...')

    try {
      const res = await fetch(`${window.API_URL}/api/supplier/scrape-and-download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          supplier_url: supplierUrl
        })
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || 'Erro ao gerar CSV')
      }

      // Download do CSV
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url

      // Extrai nome do arquivo do header ou usa padrão
      const contentDisposition = res.headers.get('content-disposition')
      let filename = 'produtos_fornecedor.csv'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }

      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      setProgress('')
    } catch (err) {
      setError(err.message)
      setProgress('')
    } finally {
      setLoading(false)
    }
  }

  const exportCurrentToCSV = () => {
    if (!products || !products.products) return

    const headers = ['Nome do Produto', 'UPC', 'Link Fornecedor', 'Amazon (Busca por UPC)', 'Amazon (Busca por Nome)']
    const rows = products.products.map(p => [
      p.nome || '',
      p.upc || 'Não encontrado',
      p.link_fornecedor || '',
      p.amazon_upc || 'N/A',
      p.amazon_nome || ''
    ])

    let csv = '\uFEFF' // UTF-8 BOM para Excel
    csv += headers.map(h => `"${h}"`).join(',') + '\n'
    rows.forEach(row => {
      csv += row.map(cell => `"${cell}"`).join(',') + '\n'
    })

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    a.download = `produtos_fornecedor_${timestamp}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const handleClear = () => {
    setProducts(null)
    setError(null)
    setProgress('')
  }

  return (
    <div className="supplier-scraper-page">
      <div className="page-header">
        <h1>Extrator de Produtos do Fornecedor</h1>
        <p className="subtitle">
          Extraia automaticamente produtos de uma categoria/seção do fornecedor com UPCs e links da Amazon
        </p>
      </div>

      <div className="card info-section">
        <h2>Como Funciona</h2>
        <div className="info-steps">
          <div className="info-step">
            <span className="step-icon">1</span>
            <div>
              <h4>Cole a URL da Categoria</h4>
              <p>Insira o link da seção ou categoria do fornecedor</p>
            </div>
          </div>
          <div className="info-step">
            <span className="step-icon">2</span>
            <div>
              <h4>Scraping Automático</h4>
              <p>O sistema varre todas as páginas e extrai os produtos</p>
            </div>
          </div>
          <div className="info-step">
            <span className="step-icon">3</span>
            <div>
              <h4>Exportar CSV</h4>
              <p>Baixe o CSV com produtos, UPCs e links da Amazon</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card scrape-section">
        <h2>Extrair Produtos</h2>

        <div className="form-group">
          <label>URL da Categoria/Seção do Fornecedor</label>
          <input
            type="text"
            value={supplierUrl}
            onChange={(e) => setSupplierUrl(e.target.value)}
            placeholder="https://fornecedor.com/categoria/produtos"
            disabled={loading}
            className="url-input"
          />
          <small className="help-text">
            Cole aqui a URL completa da página de categoria ou seção do fornecedor
          </small>
        </div>

        <div className="button-group">
          <button
            onClick={handleScrape}
            disabled={loading || !supplierUrl.trim()}
            className="btn btn-primary"
          >
            {loading && progress.includes('Iniciando') ? (
              <>
                <span className="loader"></span> Extraindo...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
                Extrair Produtos
              </>
            )}
          </button>

          <button
            onClick={handleDownloadCSV}
            disabled={loading || !supplierUrl.trim()}
            className="btn btn-success"
          >
            {loading && progress.includes('CSV') ? (
              <>
                <span className="loader"></span> Gerando CSV...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Baixar CSV Direto
              </>
            )}
          </button>
        </div>

        {progress && (
          <div className="progress-message">
            <span className="loader-small"></span>
            {progress}
          </div>
        )}

        {error && (
          <div className="error-message">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            {error}
          </div>
        )}
      </div>

      {products && products.products && products.products.length > 0 && (
        <div className="card results-section">
          <div className="results-header">
            <div>
              <h2>Produtos Encontrados ({products.total})</h2>
              <p className="results-info">
                {products.pages_scraped} página(s) varrida(s) •
                {' '}{products.products.filter(p => p.upc).length} produto(s) com UPC
              </p>
            </div>
            <div className="header-buttons">
              <button
                onClick={exportCurrentToCSV}
                className="btn btn-success"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Exportar CSV
              </button>
              <button
                onClick={handleClear}
                className="btn btn-danger"
              >
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
                  <th style={{width: '30%'}}>Nome do Produto</th>
                  <th style={{width: '120px'}}>UPC</th>
                  <th style={{width: '15%'}}>Fornecedor</th>
                  <th style={{width: '15%'}}>Amazon (UPC)</th>
                  <th style={{width: '15%'}}>Amazon (Nome)</th>
                </tr>
              </thead>
              <tbody>
                {products.products.map((product, i) => (
                  <tr key={i}>
                    <td className="product-name">{product.nome || 'Sem título'}</td>
                    <td className="upc-cell">
                      {product.upc ? (
                        <span className="upc-badge">{product.upc}</span>
                      ) : (
                        <span className="upc-not-found">-</span>
                      )}
                    </td>
                    <td className="link-cell">
                      <a
                        href={product.link_fornecedor}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-btn link-btn-supplier"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                          <polyline points="15 3 21 3 21 9"></polyline>
                          <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                        Abrir
                      </a>
                    </td>
                    <td className="link-cell">
                      {product.amazon_upc ? (
                        <a
                          href={product.amazon_upc}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="link-btn link-btn-amazon"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                          </svg>
                          Buscar
                        </a>
                      ) : (
                        <span className="text-muted">N/A</span>
                      )}
                    </td>
                    <td className="link-cell">
                      {product.amazon_nome ? (
                        <a
                          href={product.amazon_nome}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="link-btn link-btn-amazon"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                          </svg>
                          Buscar
                        </a>
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default SupplierScraperPage
