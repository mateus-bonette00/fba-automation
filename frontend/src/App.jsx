import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import SellersPage from "./pages/SellersPage";
import ProductsPage from "./pages/ProductsPage";
import CaptureTabsPage from "./pages/CaptureTabsPage";
import SupplierScraperPage from "./pages/SupplierScraperPage";
import AutomationUI from "./pages/AutomationUI";
import "./App.css";

// URL Base do Backend (usa o mesmo host do frontend para funcionar
// tanto em localhost quanto via IP da rede local).
const apiHost = window.location.hostname || "localhost";
window.API_URL = `http://${apiHost}:8001`;

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
          <Route path="/automation" element={<AutomationUI />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
