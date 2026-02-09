import { useState, useEffect } from 'react'
import './SellersPage.css'

function SellersPage() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [cacheId, setCacheId] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [total, setTotal] = useState(0)

  // Filtros
  const [sellerFilter, setSellerFilter] = useState('')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [minBsr, setMinBsr] = useState('')
  const [maxBsr, setMaxBsr] = useState('')
  const [maxFbaSellers, setMaxFbaSellers] = useState('')
  const [excludeAmazon, setExcludeAmazon] = useState(false)
  const [onlyWithUpc, setOnlyWithUpc] = useState(false)  // NOVO: filtro para produtos com UPC
  const [availableSellers, setAvailableSellers] = useState([])

  const loadProducts = async (page = 1) => {
    if (!cacheId) return

    setLoading(true)
    setError(null)

    try {
      let url = `${window.API_URL}/api/sellers/get-products/${cacheId}?page=${page}&per_page=200`

      // Adicionar filtros se preenchidos
      if (sellerFilter) {
        url += `&seller=${encodeURIComponent(sellerFilter)}`
      }
      if (minPrice) {
        url += `&min_price=${minPrice}`
      }
      if (maxPrice) {
        url += `&max_price=${maxPrice}`
      }
      if (minBsr) {
        url += `&min_bsr=${minBsr}`
      }
      if (maxBsr) {
        url += `&max_bsr=${maxBsr}`
      }
      if (maxFbaSellers) {
        url += `&max_fba_sellers=${maxFbaSellers}`
      }
      if (excludeAmazon) {
        url += `&exclude_amazon=true`
      }
      if (onlyWithUpc) {
        url += `&only_with_upc=true`
      }

      const res = await fetch(url)

      if (!res.ok) {
        throw new Error('Erro ao carregar produtos')
      }

      const result = await res.json()
      setData(result)
      setCurrentPage(result.page)
      setTotalPages(result.total_pages)
      setTotal(result.total)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadSellers = async () => {
    if (!cacheId) return

    try {
      const res = await fetch(`${window.API_URL}/api/sellers/get-sellers-list/${cacheId}`)
      if (res.ok) {
        const result = await res.json()
        setAvailableSellers(result.sellers || [])
      }
    } catch (err) {
      console.error('Erro ao carregar sellers:', err)
    }
  }

  // Recarregar produtos quando os filtros mudarem
  useEffect(() => {
    if (cacheId) {
      loadProducts(1)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sellerFilter, minPrice, maxPrice, minBsr, maxBsr, maxFbaSellers, excludeAmazon, onlyWithUpc])

  const applyFilters = () => {
    setCurrentPage(1)
    loadProducts(1)
  }

  const clearFilters = () => {
    setSellerFilter('')
    setMinPrice('')
    setMaxPrice('')
    setMinBsr('')
    setMaxBsr('')
    setMaxFbaSellers('')
    setExcludeAmazon(false)
    setOnlyWithUpc(false)
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (files.length === 0) return

    setLoading(true)
    setError(null)
    setData(null)

    try {
      const formData = new FormData()

      // Adicionar todos os arquivos ao FormData
      files.forEach(file => {
        formData.append('files', file)
      })

      const res = await fetch(`${window.API_URL}/api/sellers/upload-csv`, {
        method: 'POST',
        body: formData
      })

      if (!res.ok) {
        throw new Error('Erro ao processar arquivo')
      }

      const result = await res.json()
      setCacheId(result.cache_id)
      setTotal(result.total)
      setCurrentPage(1)

      // Carregar primeira página
      const productsRes = await fetch(`${window.API_URL}/api/sellers/get-products/${result.cache_id}?page=1&per_page=200`)

      if (!productsRes.ok) {
        throw new Error('Erro ao carregar produtos')
      }

      const productsData = await productsRes.json()
      setData(productsData)
      setTotalPages(productsData.total_pages)

      // Carregar lista de sellers disponíveis
      const sellersRes = await fetch(`${window.API_URL}/api/sellers/get-sellers-list/${result.cache_id}`)
      if (sellersRes.ok) {
        const sellersData = await sellersRes.json()
        setAvailableSellers(sellersData.sellers || [])
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (files.length === 0) return

    try {
      const formData = new FormData()

      // Adicionar todos os arquivos ao FormData
      files.forEach(file => {
        formData.append('files', file)
      })

      const res = await fetch(`${window.API_URL}/api/sellers/download-filtered`, {
        method: 'POST',
        body: formData
      })

      if (!res.ok) throw new Error('Erro ao baixar')

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'sellers_filtrado.csv'
      a.click()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDownloadFiltered = async () => {
    if (!cacheId) return

    try {
      let url = `${window.API_URL}/api/sellers/download-filtered-csv/${cacheId}?`

      // Adicionar filtros se preenchidos
      if (sellerFilter) {
        url += `&seller=${encodeURIComponent(sellerFilter)}`
      }
      if (minPrice) {
        url += `&min_price=${minPrice}`
      }
      if (maxPrice) {
        url += `&max_price=${maxPrice}`
      }
      if (minBsr) {
        url += `&min_bsr=${minBsr}`
      }
      if (maxBsr) {
        url += `&max_bsr=${maxBsr}`
      }
      if (maxFbaSellers) {
        url += `&max_fba_sellers=${maxFbaSellers}`
      }
      if (excludeAmazon) {
        url += `&exclude_amazon=true`
      }
      if (onlyWithUpc) {
        url += `&only_with_upc=true`
      }

      const res = await fetch(url)

      if (!res.ok) throw new Error('Erro ao baixar CSV filtrado')

      const blob = await res.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = 'produtos_filtrados.csv'
      a.click()
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="sellers-page">
      <h1>Processamento de Sellers</h1>
      
      <div className="card upload-section">
        <h2>Upload & Filtro</h2>
        
        <form onSubmit={handleUpload}>
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
                multiple
                onChange={(e) => setFiles(Array.from(e.target.files || []))}
              />
              {files.length > 0 ? `${files.length} arquivo(s) selecionado(s)` : 'Escolher arquivo(s) CSV'}
            </label>

            <button type="submit" className="btn btn-primary" disabled={files.length === 0 || loading}>
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

        {files.length > 0 && (
          <div className="files-list">
            <h3>Arquivos selecionados:</h3>
            <ul>
              {files.map((file, idx) => (
                <li key={idx}>{file.name}</li>
              ))}
            </ul>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
        {data && (
          <div className="success-message">
            {total} produtos encontrados (todas as categorias)
          </div>
        )}
      </div>

      {data && (
        <>
          {/* Seção de Filtros */}
          <div className="card filters-section">
            <h2>Filtros</h2>
            <div className="filters-grid">
              <div className="filter-group">
                <label htmlFor="seller-filter">Seller</label>
                <select
                  id="seller-filter"
                  value={sellerFilter}
                  onChange={(e) => setSellerFilter(e.target.value)}
                  className="filter-input"
                >
                  <option value="">Todos os sellers</option>
                  {availableSellers.map((seller, idx) => (
                    <option key={idx} value={seller}>{seller}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label htmlFor="min-price">Preço Mínimo ($)</label>
                <input
                  id="min-price"
                  type="number"
                  step="0.01"
                  min="0"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  placeholder="0.00"
                  className="filter-input"
                />
              </div>

              <div className="filter-group">
                <label htmlFor="max-price">Preço Máximo ($)</label>
                <input
                  id="max-price"
                  type="number"
                  step="0.01"
                  min="0"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  placeholder="999.99"
                  className="filter-input"
                />
              </div>

              <div className="filter-group">
                <label htmlFor="min-bsr">BSR Mínimo</label>
                <input
                  id="min-bsr"
                  type="number"
                  min="1"
                  value={minBsr}
                  onChange={(e) => setMinBsr(e.target.value)}
                  placeholder="Ex: 1"
                  className="filter-input"
                  title="BSR mínimo. Quanto menor o BSR, melhor o produto vende."
                />
              </div>

              <div className="filter-group">
                <label htmlFor="max-bsr">BSR Máximo</label>
                <input
                  id="max-bsr"
                  type="number"
                  min="1"
                  value={maxBsr}
                  onChange={(e) => setMaxBsr(e.target.value)}
                  placeholder="Ex: 50000"
                  className="filter-input"
                  title="BSR máximo. Quanto menor o BSR, melhor o produto vende. Ex: 50000 = produtos até rank 50000"
                />
              </div>

              <div className="filter-group">
                <label htmlFor="max-fba-sellers">Máx. FBA Sellers (pouca concorrência)</label>
                <input
                  id="max-fba-sellers"
                  type="number"
                  min="0"
                  value={maxFbaSellers}
                  onChange={(e) => setMaxFbaSellers(e.target.value)}
                  placeholder="Ex: 3"
                  className="filter-input"
                  title="Produtos com poucos vendedores FBA (menos concorrência). Ex: 3 = máximo 3 sellers FBA"
                />
              </div>

              <div className="filter-group">
                <label htmlFor="exclude-amazon" className="checkbox-label">
                  <input
                    id="exclude-amazon"
                    type="checkbox"
                    checked={excludeAmazon}
                    onChange={(e) => setExcludeAmazon(e.target.checked)}
                    className="filter-checkbox"
                  />
                  Excluir produtos vendidos pela Amazon
                </label>
              </div>

              <div className="filter-group">
                <label htmlFor="only-with-upc" className="checkbox-label">
                  <input
                    id="only-with-upc"
                    type="checkbox"
                    checked={onlyWithUpc}
                    onChange={(e) => setOnlyWithUpc(e.target.checked)}
                    className="filter-checkbox"
                  />
                  Apenas produtos com UPC
                </label>
              </div>

              <div className="filter-actions">
                <button
                  onClick={clearFilters}
                  className="btn btn-secondary"
                  disabled={!sellerFilter && !minPrice && !maxPrice && !minBsr && !maxBsr && !maxFbaSellers && !excludeAmazon && !onlyWithUpc}
                >
                  Limpar Filtros
                </button>
              </div>
            </div>
          </div>

          {/* Seção de Resultados */}
          <div className="card results-section">
            <div className="results-header">
              <div>
                <h2>Produtos ({data.data.length} de {total} exibidos)</h2>
                <button
                  onClick={handleDownloadFiltered}
                  className="btn btn-success"
                  style={{ marginTop: '10px' }}
                  title="Baixar CSV dos produtos filtrados com links"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                  </svg>
                  Baixar CSV Filtrado com Links
                </button>
              </div>

              {/* Controles de Paginação */}
              <div className="pagination-controls">
                <button
                  onClick={() => loadProducts(1)}
                  disabled={currentPage === 1 || loading}
                  className="btn-pagination"
                  title="Primeira página"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="11 17 6 12 11 7"></polyline>
                    <polyline points="18 17 13 12 18 7"></polyline>
                  </svg>
                </button>

                <button
                  onClick={() => loadProducts(currentPage - 1)}
                  disabled={currentPage === 1 || loading}
                  className="btn-pagination"
                  title="Página anterior"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="15 18 9 12 15 6"></polyline>
                  </svg>
                </button>

                <span className="page-info">
                  Página {currentPage} de {totalPages}
                </span>

                <button
                  onClick={() => loadProducts(currentPage + 1)}
                  disabled={currentPage === totalPages || loading}
                  className="btn-pagination"
                  title="Próxima página"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </button>

                <button
                  onClick={() => loadProducts(totalPages)}
                  disabled={currentPage === totalPages || loading}
                  className="btn-pagination"
                  title="Última página"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="13 17 18 12 13 7"></polyline>
                    <polyline points="6 17 11 12 6 7"></polyline>
                  </svg>
                </button>
              </div>
            </div>

            <div className="products-grid">
            {data.data.map((product, i) => (
              <div key={i} className="product-card">
                <div className="product-image">
                  {product.image ? (
                    <img src={product.image} alt={product.title || 'Produto'} />
                  ) : (
                    <div className="no-image">Sem imagem</div>
                  )}
                </div>
                <div className="product-info">
                  <h3 className="product-title">{product.title || 'Sem título'}</h3>

                  {/* Informações de Preço e Seller */}
                  <div className="product-details">
                    {product.price && (
                      <div className="product-price">
                        <strong>Preço:</strong> ${product.price.toFixed(2)}
                      </div>
                    )}
                    {product.seller && (
                      <div className="product-seller">
                        <strong>Seller:</strong> {product.seller}
                      </div>
                    )}
                  </div>

                  {/* Links de Ação */}
                  <div className="product-actions">
                    {product.asin && (
                      <a
                        href={`https://www.amazon.com/dp/${product.asin}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="amazon-link"
                        title="Abrir produto na Amazon"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                          <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                          <line x1="12" y1="22.08" x2="12" y2="12"></line>
                        </svg>
                        Amazon
                      </a>
                    )}

                    {product.title && (
                      <a
                        href={`https://www.google.com/search?q=${encodeURIComponent(product.title)}&gl=us&hl=es`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="google-title-link"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="11" cy="11" r="8"></circle>
                          <path d="m21 21-4.35-4.35"></path>
                        </svg>
                        Google (Título)
                      </a>
                    )}

                    {product.upc && (
                      <a
                        href={`https://www.google.com/search?q=${product.upc}&gl=us&hl=es`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="google-upc-link"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 3h18v18H3V3z"></path>
                          <path d="M7 7v10M11 7v10M15 7v10M19 7v10"></path>
                        </svg>
                        Google (UPC)
                      </a>
                    )}

                    {!product.upc && !product.asin && !product.title && (
                      <p className="no-links">Sem links disponíveis</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        </>
      )}
    </div>
  )
}

export default SellersPage