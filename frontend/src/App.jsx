import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import SellersPage from './pages/SellersPage'
import ProductsPage from './pages/ProductsPage'
import CaptureTabsPage from './pages/CaptureTabsPage'
import SupplierScraperPage from './pages/SupplierScraperPage'
import './App.css'

// URL Base do Backend
window.API_URL = 'http://localhost:8001'

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sellers" element={<SellersPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/capture" element={<CaptureTabsPage />} />
          <Route path="/supplier-scraper" element={<SupplierScraperPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App