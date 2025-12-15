import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import './Navbar.css'

function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  const navLinks = [
    { path: '/', label: 'Dashboard' },
    { path: '/sellers', label: 'Sellers' },
    { path: '/products', label: 'Produtos' },
    { path: '/capture', label: 'Capturar' },
    { path: '/supplier-scraper', label: 'Fornecedor' },
  ]

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <div className="brand-icon">⚡</div>
          FBA Automation
        </Link>

        <button 
          className="mobile-menu-btn"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          )}
        </button>

        <ul className={`nav-links ${isOpen ? 'active' : ''}`}>
          {navLinks.map(({ path, label }) => (
            <li key={path}>
              <Link 
                to={path}
                className={`nav-link ${isActive(path) ? 'active' : ''}`}
                onClick={() => setIsOpen(false)}
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  )
}

export default Navbar