import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import CompanyProfilePage from './pages/CompanyProfile';
import EntitySearchPage from './pages/EntitySearch';
import OpportunitiesPage from './pages/Opportunities';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background text-foreground flex flex-col">
        <header className="border-b bg-card shadow-sm">
          <div className="px-6 py-4">
            <h1 className="text-3xl font-bold text-primary mb-2">FedOps Opportunities</h1>
            <p className="text-muted-foreground mb-4">Search and view opportunities from SAM.gov</p>
            
            <nav className="flex gap-6">
              <Link to="/" className="text-primary hover:underline font-medium">Opportunities</Link>
              <Link to="/entities" className="text-primary hover:underline font-medium">Entity Search</Link>
              <Link to="/profile" className="text-primary hover:underline font-medium">Company Profile</Link>
            </nav>
          </div>
        </header>

        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<OpportunitiesPage />} />
            <Route path="/opportunities" element={<OpportunitiesPage />} />
            <Route path="/entities" element={<EntitySearchPage />} />
            <Route path="/profile" element={<CompanyProfilePage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
