import { useState } from 'react'
import './ProductsPage.css'

function ProductsPage() {
  const [file, setFile] = useState(null)
  const [minPrice, setMinPrice] = useState(10)
  const [maxPrice, setMaxPrice] = useState(50)
  const [maxReviews, setMaxReviews] = useState(130)
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('min_price', minPrice)
      formData.append('max_price', maxPrice)
      formData.append('max_reviews', maxReviews)

      const res = await fetch(`${window.API_URL}/api/products/process-csv`, {
        method: 'POST',
        body: formData
      })

      if (!res.ok) {
        throw new Error('Erro ao processar arquivo')
      }

      const result = await res.json()
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!file) return

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('min_price', minPrice)
      formData.append('max_price', maxPrice)
      formData.append('max_reviews', maxReviews)

      const res = await fetch(`${window.API_URL}/api/products/process-csv`, {
        method: 'POST',
        body: formData
      })

      if (!res.ok) throw new Error('Erro ao baixar')

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'produtos_filtrados.csv'
      a.click()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="products-page">
      <h1>Processamento de Produtos</h1>

      <div className="card filter-section">
        <h2>Filtros e Upload</h2>

        <form onSubmit={handleUpload}>
          <div className="filter-grid">
            <div className="form-group">
              <label>Preço Mínimo (US$)</label>
              <input
                type="number"
                value={minPrice}
                onChange={(e) => setMinPrice(Number(e.target.value))}
                min="0"
                step="0.5"
              />
            </div>

            <div className="form-group">
              <label>Preço Máximo (US$)</label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(Number(e.target.value))}
                min="0"
                step="0.5"
              />
            </div>

            <div className="form-group">
              <label>Máx de Avaliações</label>
              <input
                type="number"
                value={maxReviews}
                onChange={(e) => setMaxReviews(Number(e.target.value))}
                min="0"
                step="10"
              />
            </div>
          </div>

          <div className="input-group">
            <label className="file-input-label">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0])}
              />
              {file ? file.name : 'Escolher arquivo CSV'}
            </label>

            <button type="submit" className="btn btn-primary" disabled={!file || loading}>
              {loading ? (
                <>
                  <span className="loader"></span> Processando...
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="1"></circle>
                    <path d="M12 1v6m0 6v6"></path>
                    <path d="M4.22 4.22l4.24 4.24m5.08 5.08l4.24 4.24"></path>
                    <path d="M1 12h6m6 0h6"></path>
                    <path d="M4.22 19.78l4.24-4.24m5.08-5.08l4.24-4.24"></path>
                  </svg>
                  Processar
                </>
              )}
            </button>

            {data && (
              <button type="button" onClick={handleDownload} className="btn btn-secondary">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Baixar CSV
              </button>
            )}
          </div>
        </form>

        {error && <div className="error-message">{error}</div>}
        {data && (
          <div className="success-message">
            {data.total_processados} produtos processados com sucesso
          </div>
        )}
      </div>

      {data && (
        <div className="card results-section">
          <h2>Resultado ({data.total_processados} produtos)</h2>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Título</th>
                  <th>ASIN</th>
                  <th>Preço</th>
                  <th>Rating</th>
                  <th>Avaliações</th>
                </tr>
              </thead>
              <tbody>
                {data.data.slice(0, 20).map((item, i) => (
                  <tr key={i}>
                    <td className="title-cell">{item.titulo || item.Produto || '-'}</td>
                    <td>{item.asin || '-'}</td>
                    <td>${item.buybox_atual || '-'}</td>
                    <td>{item.rating ? item.rating.toFixed(1) : '-'}</td>
                    <td>{item.avaliacoes || '-'}</td>
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

export default ProductsPage