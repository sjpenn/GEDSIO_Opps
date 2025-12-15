import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import CompanyProfilePage from './pages/CompanyProfile';
import EntitySearchPage from './pages/EntitySearch';
import OpportunitiesPage from './pages/Opportunities';
import OpportunityDetail from './pages/OpportunityDetail';
import FileManagementPage from './pages/FileManagement';
import AnalysisViewer from './pages/AnalysisViewer';
import ProposalWorkspace from './pages/ProposalWorkspace';
import PipelinePage from './pages/Pipeline';
import BidDecisionPage from './pages/BidDecision';
import ManualUploadPage from './pages/ManualUpload';
import PartnerTeamsPage from './pages/PartnerTeams';
import { ThemeProvider } from './components/theme-provider';
import Layout from './components/Layout';
import PageTransition from './components/PageTransition';
import AboutPage from './pages/About';
import ResumeManager from './pages/ResumeManager';
import PastPerformancePage from './pages/PastPerformance';
import PastPerformanceDetail from './pages/PastPerformanceDetail';

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={
              <PageTransition>
                <AboutPage />
              </PageTransition>
            } />
            <Route path="/opportunities" element={
              <PageTransition>
                <OpportunitiesPage />
              </PageTransition>
            } />
            <Route path="/opportunities/:opportunityId" element={
              <PageTransition>
                <OpportunityDetail />
              </PageTransition>
            } />
            <Route path="/entities" element={
              <PageTransition>
                <EntitySearchPage />
              </PageTransition>
            } />
            <Route path="/teams" element={
              <PageTransition>
                <PartnerTeamsPage />
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
            <Route path="/upload-opportunity" element={
              <PageTransition>
                <ManualUploadPage />
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
            <Route path="/bid-decision/:opportunityId" element={
              <PageTransition>
                <BidDecisionPage />
              </PageTransition>
            } />
            <Route path="/proposal-workspace/:opportunityId" element={
              <ProposalWorkspace />
            } />
            <Route path="/resumes" element={
              <PageTransition>
                <ResumeManager />
              </PageTransition>
            } />
            <Route path="/past-performance" element={
              <PageTransition>
                <PastPerformancePage />
              </PageTransition>
            } />
            <Route path="/past-performance/:ppId" element={
              <PageTransition>
                <PastPerformanceDetail />
              </PageTransition>
            } />

          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  )
}

export default App
