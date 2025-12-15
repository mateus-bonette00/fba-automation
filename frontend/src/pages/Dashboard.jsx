import { useEffect, useState } from 'react'
import './Dashboard.css'

function Dashboard() {
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    fetch(`${window.API_URL}/api/health`)
      .then(r => r.json())
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'))
  }, [])

  const features = [
    {
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 2v20h16V2H4z"></path>
          <path d="M8 8h8M8 14h8"></path>
        </svg>
      ),
      title: 'Sellers',
      desc: 'Filtrar e organizar sellers FBA por categoria'
    },
    {
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7"></rect>
          <rect x="14" y="3" width="7" height="7"></rect>
          <rect x="14" y="14" width="7" height="7"></rect>
          <rect x="3" y="14" width="7" height="7"></rect>
        </svg>
      ),
      title: 'Produtos',
      desc: 'Processar e filtrar produtos com dados de vendas'
    },
    {
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="1"></circle>
          <path d="M12 2v6M12 16v6"></path>
          <path d="M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24"></path>
          <path d="M2 12h6M16 12h6"></path>
          <path d="M4.22 19.78l4.24-4.24M15.54 8.46l4.24-4.24"></path>
        </svg>
      ),
      title: 'Capturar',
      desc: 'Capture URLs de suas abas do navegador'
    },
    {
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="1"></circle>
          <path d="M12 1v6m0 6v6"></path>
          <path d="M4.22 4.22l4.24 4.24m5.08 5.08l4.24 4.24"></path>
          <path d="M1 12h6m6 0h6"></path>
          <path d="M4.22 19.78l4.24-4.24m5.08-5.08l4.24-4.24"></path>
        </svg>
      ),
      title: 'Automação',
      desc: 'Pipeline integrado de extração e análise'
    },
  ]

  return (
    <div className="dashboard">
      <div className="hero">
        <h1>FBA Automation</h1>
        <p>Pipeline completo de análise e automação</p>
        <div className="status">
          <span className={`status-dot ${status}`}></span>
          Backend: {status.toUpperCase()}
        </div>
      </div>

      <div className="features-grid">
        {features.map((f, i) => (
          <div key={i} className="feature-card">
            <div className="feature-icon">{f.icon}</div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </div>

      <div className="info-section">
        <h2>Como Começar</h2>
        <ol>
          <li><strong>Sellers:</strong> Faça upload de um CSV de sellers do Keepa e filtre por categoria</li>
          <li><strong>Produtos:</strong> Processe arquivos de produtos com filtros avançados de preço e avaliações</li>
          <li><strong>Capturar:</strong> Conecte ao seu Chrome com DevTools para capturar abas abertas</li>
          <li><strong>Exportar:</strong> Baixe todos os dados processados em formato CSV</li>
        </ol>
      </div>
    </div>
  )
}

export default Dashboard