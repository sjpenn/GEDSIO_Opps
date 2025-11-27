import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import CompanyProfilePage from './pages/CompanyProfile';
import EntitySearchPage from './pages/EntitySearch';
import OpportunitiesPage from './pages/Opportunities';
import FileManagementPage from './pages/FileManagement';
import AnalysisViewer from './pages/AnalysisViewer';
import PipelinePage from './pages/Pipeline';
import { ThemeProvider } from './components/theme-provider';
import Layout from './components/Layout';
import PageTransition from './components/PageTransition';

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={
              <PageTransition>
                <OpportunitiesPage />
              </PageTransition>
            } />
            <Route path="/opportunities" element={
              <PageTransition>
                <OpportunitiesPage />
              </PageTransition>
            } />
            <Route path="/entities" element={
              <PageTransition>
                <EntitySearchPage />
              </PageTransition>
            } />
            <Route path="/profile" element={
              <PageTransition>
                <CompanyProfilePage />
              </PageTransition>
            } />
            <Route path="/files" element={
              <PageTransition>
                <FileManagementPage />
              </PageTransition>
            } />
            <Route path="/pipeline" element={
              <PageTransition>
                <PipelinePage />
              </PageTransition>
            } />
            <Route path="/analysis/:opportunityId" element={
              <AnalysisViewer />
            } />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  )
}

export default App
