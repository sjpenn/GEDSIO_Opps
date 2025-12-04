import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  ArrowLeft, 
  TrendingUp, 
  DollarSign, 
  FileText, 
  Target, 
  AlertTriangle, 
  Users,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Lightbulb,
  AlertCircle,
  Shield,
  Calendar,
  Briefcase,
  History,
  ExternalLink,
  Eye,
  RefreshCw,
  Download
} from 'lucide-react';
import { cn } from "@/lib/utils";
import ShipleyPhaseIndicator from '@/components/ShipleyPhaseIndicator';
import PursuitDecision from '@/components/PursuitDecision';
import DocumentViewer from '@/components/DocumentViewer';

const API_URL = import.meta.env.VITE_API_URL || '';

interface AnalysisData {
  opportunity: {
    id: number;
    title: string;
    description: string;
    notice_id: string;
    department: string;
    sub_tier: string;
    office: string;
    posted_date: string;
    response_deadline: string;
    archive_date: string;
    naics_code: string;
    classification_code: string;
    type_of_set_aside: string;
    place_of_performance: string;
    active: boolean;
    compliance_status: string;
    risk_score: number;
    full_parent_path_name: string | null;
  };
  score: {
    strategic_alignment_score: number;
    financial_viability_score: number;
    contract_risk_score: number;
    internal_capacity_score: number;
    data_integrity_score: number;
    weighted_score: number;
    go_no_go_decision: string;
    details: any;
    created_at: string;
  } | null;
  logs: Array<{
    id: number;
    agent_name: string;
    action: string;
    status: string;
    timestamp: string;
    details: any;
  }>;
}

type TabType = 'overview' | 'solicitation' | 'financial' | 'strategic' | 'risk' | 'security' | 'capacity' | 'personnel' | 'past_performance' | 'logs';

// Helper function to parse department and subtier from fullParentPathName
const parseParentPath = (fullPath: string | null | undefined): { department: string; subTier: string } => {
  if (!fullPath) {
    return { department: 'N/A', subTier: 'N/A' };
  }
  
  // SAM.gov uses period as separator
  // Example: "DEPT OF DEFENSE.DEPT OF THE NAVY"
  const parts = fullPath.split('.').map(p => p.trim()).filter(p => p);
  
  if (parts.length === 0) {
    return { department: 'N/A', subTier: 'N/A' };
  }
  
  return {
    department: parts[0],
    subTier: parts[1] || 'N/A'
  };
};

// Helper component for source badges with clickable document links
// Helper component for source badges with clickable document links
interface SourceDocument {
  filename: string;
  type?: string;
  id?: number;
}

interface SourceLocation {
  filename: string;
  start: number;
  end: number;
  text?: string;
}

function QuoteLink({ 
  location, 
  documents, 
  onLocationClick 
}: { 
  location?: SourceLocation; 
  documents?: SourceDocument[]; 
  onLocationClick?: (doc: SourceDocument, loc: SourceLocation) => void;
}) {
  if (!location || !documents) return null;
  
  const doc = documents.find(d => d.filename === location.filename);
  if (!doc || !onLocationClick) return null;

  return (
    <Badge 
      variant="outline" 
      className="cursor-pointer hover:bg-blue-100 text-[10px] ml-2 px-1.5 py-0 h-5 border-blue-200 text-blue-700"
      onClick={(e) => {
        e.stopPropagation();
        onLocationClick(doc, location);
      }}
      title={`View source in ${doc.filename}`}
    >
      <Eye className="h-3 w-3 mr-1" />
      Source
    </Badge>
  );
}

/**
 * Helper component for source badges with clickable document links.
 * Displays a badge for each source section (e.g., "Section L") and links it to the corresponding document if available.
 */
function SourceBadge({ 
  sources, 
  documents, 
  onDocumentClick 
}: { 
  /** List of source strings (e.g., ["Section L", "Section M"]) */
  sources: string[]; 
  /** List of available source documents to match against */
  documents?: SourceDocument[];
  /** Callback when a clickable badge is clicked */
  onDocumentClick?: (doc: SourceDocument) => void;
}) {
  if (!sources || sources.length === 0) return null;
  
  const handleClick = (doc: SourceDocument) => {
    if (onDocumentClick) {
      onDocumentClick(doc);
    }
  };
  
  return (
    <div className="flex flex-wrap gap-1 mt-1">
      {sources.map((source, i) => {
        const doc = documents?.find(d => d.type?.includes(source.replace('Section ', '')));
        const isClickable = !!doc && !!onDocumentClick;
        
        return (
          <Badge 
            key={i} 
            variant="outline" 
            className={cn(
              "text-xs bg-blue-50 text-blue-700 border-blue-300",
              isClickable && "cursor-pointer hover:bg-blue-100 hover:border-blue-400 transition-colors"
            )}
            onClick={isClickable ? () => handleClick(doc) : undefined}
            title={doc ? `Click to view ${doc.filename}` : source}
          >
            <FileText className="h-3 w-3 mr-1" />
            {source}
            {isClickable && <ExternalLink className="h-3 w-3 ml-1" />}
          </Badge>
        );
      })}
    </div>
  );
}

export default function AnalysisViewer() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<AnalysisData | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [error, setError] = useState<string | null>(null);
  const [generatingProposal, setGeneratingProposal] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<any>(null);
  const [proposalData, setProposalData] = useState<any>(null);
  const [showPursuitDialog, setShowPursuitDialog] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [eligibilityStatus, setEligibilityStatus] = useState<any>(null);
  const [analysisMessage, setAnalysisMessage] = useState<{type: 'info' | 'success' | 'error', text: string} | null>(null);
  
  // Document Viewer State
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<SourceDocument | null>(null);
  const [highlightLocation, setHighlightLocation] = useState<{start: number, end: number} | undefined>(undefined);

  const handleLocationClick = (doc: SourceDocument, loc: SourceLocation) => {
    setSelectedDoc(doc);
    setHighlightLocation({ start: loc.start, end: loc.end });
    setViewerOpen(true);
  };

  const canGenerateProposal = !!data?.score;
  const showPursuitButton = !!proposalData;

  useEffect(() => {
    fetchAnalysisData();
    fetchPipelineStatus();
    fetchProposalData();
    fetchEligibility();
  }, [opportunityId]);

  const fetchEligibility = async () => {
    if (!opportunityId) return;
    try {
      const response = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/eligibility`);
      if (response.ok) {
        const data = await response.json();
        setEligibilityStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch eligibility status:', err);
    }
  };

  const fetchAnalysisData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/analysis`);
      if (!response.ok) {
        throw new Error('Failed to fetch analysis data');
      }
      const analysisData = await response.json();
      setData(analysisData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchPipelineStatus = async () => {
    if (!opportunityId) return;
    try {
      const response = await fetch(`${API_URL}/api/v1/pipeline/${opportunityId}`);
      if (response.ok) {
        const data = await response.json();
        setPipelineStatus(data);
      }
    } catch (err) {
      // Not in pipeline, ignore error
      setPipelineStatus(null);
    }
  };

  const fetchProposalData = async () => {
    if (!opportunityId) return;
    try {
      const response = await fetch(`${API_URL}/api/v1/pipeline/`);
      if (response.ok) {
        const pipelineData = await response.json();
        const item = pipelineData.find((p: any) => p.opportunity.id === parseInt(opportunityId));
        if (item && item.proposal) {
          setProposalData(item.proposal);
        }
      }
    } catch (err) {
      console.error('Failed to fetch proposal data:', err);
    }
  };

  const handleGenerateProposal = async () => {
    if (!opportunityId) return;
    setGeneratingProposal(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/proposals/generate/${opportunityId}`, {
        method: 'POST'
      });
      if (res.ok) {
        // Open workspace in new tab
        window.open(`/proposal-workspace/${opportunityId}`, '_blank');
      } else {
        const errorText = await res.text();
        alert(`Failed to generate proposal: ${errorText}`);
      }
    } catch (error) {
      console.error("Proposal generation failed", error);
      alert("An error occurred while generating the proposal.");
    } finally {
      setGeneratingProposal(false);
    }
  };

  const handleAddToPipeline = async () => {
    if (!opportunityId) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/pipeline/${opportunityId}/watch`, {
        method: 'POST'
      });
      if (res.ok) {
        alert("Opportunity added to pipeline!");
        // Refresh pipeline status to update badge
        await fetchPipelineStatus();
      } else {
        const data = await res.json();
        alert(data.message || "Failed to add to pipeline");
      }
    } catch (err) {
      console.error("Failed to add to pipeline", err);
      alert("An error occurred while adding to pipeline.");
    }
  };

  const handlePursuitDecisionMade = async (decision: 'GO' | 'NO_GO', proposalId?: number) => {
    setShowPursuitDialog(false);
    
    if (decision === 'GO' && proposalId) {
      // Refresh proposal data
      await fetchProposalData();
      alert(`Pursuit decision recorded! Proceeding to Phase 2: Opportunity Assessment. You can now make a Bid/No-Bid decision.`);
    } else {
      alert(`Pursuit decision recorded: ${decision}. This opportunity will remain in Phase 1.`);
    }
  };

  const handleRerunAnalysis = async () => {
    if (!opportunityId) return;
    setReanalyzing(true);
    setAnalysisMessage({
      type: 'info',
      text: 'Running comprehensive analysis...\n\nThis may take 30-60 seconds as AI agents analyze:\n• Solicitation requirements\n• Financial viability\n• Strategic alignment\n• Risk assessment\n• Internal capacity\n• Security requirements'
    });
    
    try {
      const res = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/analyze`, {
        method: 'POST'
      });
      if (res.ok) {
        setAnalysisMessage({
          type: 'success',
          text: 'Analysis completed successfully! Refreshing data...'
        });
        // Refresh all analysis data
        await fetchAnalysisData();
        await fetchEligibility();
        setTimeout(() => setAnalysisMessage(null), 3000);
      } else {
        const errorText = await res.text();
        setAnalysisMessage({
          type: 'error',
          text: `Analysis failed: ${errorText}`
        });
      }
    } catch (error) {
      console.error("Analysis failed", error);
      setAnalysisMessage({
        type: 'error',
        text: 'An error occurred while running analysis. Please try again.'
      });
    } finally {
      setReanalyzing(false);
    }
  };

  const handleExportSummary = () => {
    if (!data) return;
    exportAnalysis('summary');
  };

  const handleExportFull = () => {
    if (!data) return;
    exportAnalysis('full');
  };

  const exportAnalysis = (type: 'summary' | 'full') => {
    if (!data) return;
    
    // Create timestamp in YYYYMMDD_HH:MM:SS format
    const now = new Date();
    const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    
    // Sanitize opportunity title for filename
    const sanitizedTitle = data.opportunity.title
      .replace(/[^a-z0-9]/gi, '_')
      .replace(/_+/g, '_')
      .substring(0, 50);
    
    const baseFilename = `${sanitizedTitle}_${type}_${timestamp}`;
    
    // Create comprehensive export object
    const exportData = {
      exported_at: now.toISOString(),
      opportunity: data.opportunity,
      score: data.score,
      logs: data.logs,
      eligibility: eligibilityStatus
    };
    
    // Generate markdown based on type
    const markdownContent = type === 'summary' 
      ? generateSummaryReport(exportData) 
      : generateFullReport(exportData);
    
    // Export as Markdown
    const mdBlob = new Blob([markdownContent], { type: 'text/markdown' });
    const mdUrl = URL.createObjectURL(mdBlob);
    const mdLink = document.createElement('a');
    mdLink.href = mdUrl;
    mdLink.download = `${baseFilename}.md`;
    document.body.appendChild(mdLink);
    document.body.removeChild(mdLink);
    URL.revokeObjectURL(mdUrl);
    
    // Export as PDF using browser print
    setTimeout(() => {
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
          <!DOCTYPE html>
          <html>
            <head>
              <title>${sanitizedTitle} - ${type === 'summary' ? 'Summary' : 'Full'} Analysis Report</title>
              <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }
                h2 { color: #1e40af; margin-top: 30px; border-bottom: 2px solid #93c5fd; padding-bottom: 5px; }
                h3 { color: #1e3a8a; margin-top: 20px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #2563eb; color: white; }
                .score { font-size: 24px; font-weight: bold; }
                .badge { display: inline-block; padding: 5px 15px; border-radius: 5px; font-weight: bold; margin: 5px 0; }
                .badge-go { background-color: #22c55e; color: white; }
                .badge-no-go { background-color: #ef4444; color: white; }
                .badge-review { background-color: #eab308; color: white; }
                pre { background: #f3f4f6; padding: 15px; border-radius: 5px; overflow-x: auto; }
              </style>
            </head>
            <body>
              ${markdownToHTML(markdownContent)}
            </body>
          </html>
        `);
        printWindow.document.close();
        setTimeout(() => {
          printWindow.print();
        }, 250);
      }
    }, 500);
  };

  const generateSummaryReport = (exportData: any): string => {
    const opp = exportData.opportunity;
    const score = exportData.score;
    
    let md = `# Analysis Summary: ${opp.title}\n\n`;
    md += `**Generated:** ${new Date(exportData.exported_at).toLocaleString()}\n\n`;
    md += `**Notice ID:** ${opp.notice_id}\n\n`;
    md += `---\n\n`;
    
    // Overall Score and Decision
    if (score) {
      md += `## Overall Assessment\n\n`;
      md += `**Score:** ${score.weighted_score.toFixed(1)} / 100\n\n`;
      md += `**Decision:** ${score.go_no_go_decision}\n\n`;
      
      // Executive Summary
      if (score.details?.executive_overview?.executive_summary) {
        md += `### Executive Summary\n\n${score.details.executive_overview.executive_summary}\n\n`;
      }
      
      // Score Breakdown (compact)
      md += `### Score Breakdown\n\n`;
      md += `| Category | Score |\n`;
      md += `|----------|-------|\n`;
      md += `| Strategic Alignment | ${score.strategic_alignment_score.toFixed(1)} |\n`;
      md += `| Financial Viability | ${score.financial_viability_score.toFixed(1)} |\n`;
      md += `| Contract Risk | ${score.contract_risk_score.toFixed(1)} |\n`;
      md += `| Internal Capacity | ${score.internal_capacity_score.toFixed(1)} |\n\n`;
    }
    
    // Key Opportunity Details
    const { department, subTier } = parseParentPath(opp.full_parent_path_name);
    md += `## Key Details\n\n`;
    md += `- **Department:** ${department}\n`;
    md += `- **Sub-Tier:** ${subTier}\n`;
    md += `- **NAICS Code:** ${opp.naics_code || 'N/A'}\n`;
    md += `- **Set-Aside:** ${opp.type_of_set_aside || 'N/A'}\n`;
    md += `- **Response Deadline:** ${opp.response_deadline ? new Date(opp.response_deadline).toLocaleDateString() : 'N/A'}\n\n`;
    
    // Critical Success Factors
    if (score?.details?.executive_overview?.critical_success_factors?.length > 0) {
      md += `## Critical Success Factors\n\n`;
      score.details.executive_overview.critical_success_factors.forEach((factor: string) => {
        md += `- ${factor}\n`;
      });
      md += `\n`;
    }
    
    // Key Recommendations
    if (score?.details?.strategic?.recommendation) {
      md += `## Strategic Recommendation\n\n${score.details.strategic.recommendation}\n\n`;
    }
    
    return md;
  };

  const generateFullReport = (exportData: any): string => {
    return generateMarkdownReport(exportData);
  };

  const generateMarkdownReport = (exportData: any): string => {
    const opp = exportData.opportunity;
    const score = exportData.score;
    const eligibility = exportData.eligibility;
    
    let md = `# Analysis Report: ${opp.title}\n\n`;
    md += `**Generated:** ${new Date(exportData.exported_at).toLocaleString()}\n\n`;
    md += `**Notice ID:** ${opp.notice_id}\n\n`;
    md += `---\n\n`;
    
    // OVERVIEW TAB
    md += `## Overview\n\n`;
    
    // Score Summary
    if (score) {
      md += `### Overall Score: ${score.weighted_score.toFixed(1)} / 100\n\n`;
      md += `**Decision:** ${score.go_no_go_decision}\n\n`;
      
      // Executive Summary
      if (score.details?.executive_overview?.executive_summary) {
        md += `#### Executive Summary\n\n${score.details.executive_overview.executive_summary}\n\n`;
      }
      
      // Mission Alignment
      if (score.details?.executive_overview?.mission_alignment) {
        md += `#### Mission Alignment\n\n${score.details.executive_overview.mission_alignment}\n\n`;
      }
      
      // Critical Success Factors
      if (score.details?.executive_overview?.critical_success_factors?.length > 0) {
        md += `#### Critical Success Factors\n\n`;
        score.details.executive_overview.critical_success_factors.forEach((factor: string) => {
          md += `- ${factor}\n`;
        });
        md += `\n`;
      }
      
      // Score Breakdown
      md += `### Score Breakdown\n\n`;
      md += `| Category | Score |\n`;
      md += `|----------|-------|\n`;
      md += `| Strategic Alignment | ${score.strategic_alignment_score.toFixed(1)} |\n`;
      md += `| Financial Viability | ${score.financial_viability_score.toFixed(1)} |\n`;
      md += `| Contract Risk | ${score.contract_risk_score.toFixed(1)} |\n`;
      md += `| Internal Capacity | ${score.internal_capacity_score.toFixed(1)} |\n`;
      md += `| Data Integrity | ${score.data_integrity_score.toFixed(1)} |\n\n`;
    }
    
    // Parse department and subtier from fullParentPathName
    const { department, subTier } = parseParentPath(opp.full_parent_path_name);
    
    // Opportunity Details
    md += `### Opportunity Details\n\n`;
    md += `- **Department:** ${department}\n`;
    md += `- **Sub-Tier:** ${subTier}\n`;
    md += `- **NAICS Code:** ${opp.naics_code || 'N/A'}\n`;
    md += `- **Set-Aside Type:** ${opp.type_of_set_aside || 'N/A'}\n`;
    md += `- **Posted Date:** ${opp.posted_date ? new Date(opp.posted_date).toLocaleDateString() : 'N/A'}\n`;
    md += `- **Response Deadline:** ${opp.response_deadline ? new Date(opp.response_deadline).toLocaleDateString() : 'N/A'}\n`;
    md += `- **Place of Performance:** ${opp.place_of_performance || 'N/A'}\n\n`;
    
    if (opp.description) {
      md += `#### Description\n\n${opp.description}\n\n`;
    }
    
    // SOLICITATION TAB
    if (score?.details?.solicitation) {
      md += `---\n\n## Solicitation Analysis\n\n`;
      
      if (score.details.solicitation.summary) {
        md += `### Summary\n\n${score.details.solicitation.summary}\n\n`;
      }
      
      if (score.details.solicitation.key_dates?.length > 0) {
        md += `### Key Dates & Milestones\n\n`;
        md += `| Event | Date |\n`;
        md += `|-------|------|\n`;
        score.details.solicitation.key_dates.forEach((item: any) => {
          md += `| ${item.event} | ${item.date} |\n`;
        });
        md += `\n`;
      }
      
      if (score.details.solicitation.key_personnel?.length > 0) {
        md += `### Key Personnel Requirements\n\n`;
        score.details.solicitation.key_personnel.forEach((person: any) => {
          md += `- **${person.role}**${person.is_key ? ' (Key Position)' : ''}\n`;
          md += `  - ${person.requirements}\n`;
        });
        md += `\n`;
      }
      
      if (score.details.solicitation.agency_goals?.length > 0) {
        md += `### Agency Goals\n\n`;
        score.details.solicitation.agency_goals.forEach((goal: string) => {
          md += `- ${goal}\n`;
        });
        md += `\n`;
      }
    }
    
    // FINANCIAL TAB
    if (score?.details?.financial) {
      md += `---\n\n## Financial Viability Analysis\n\n`;
      md += `**Score:** ${score.financial_viability_score.toFixed(1)} / 100\n\n`;
      
      if (score.details.financial.summary) {
        md += `### Analysis Summary\n\n${score.details.financial.summary}\n\n`;
      }
      
      if (score.details.financial.contract_value) {
        md += `### Contract Value\n\n${score.details.financial.contract_value}\n\n`;
      }
      
      if (score.details.financial.pricing_strategy) {
        md += `### Pricing Strategy\n\n${score.details.financial.pricing_strategy}\n\n`;
      }
      
      if (score.details.financial.cost_factors?.length > 0) {
        md += `### Cost Factors\n\n`;
        score.details.financial.cost_factors.forEach((factor: string) => {
          md += `- ${factor}\n`;
        });
        md += `\n`;
      }
    }
    
    // STRATEGIC TAB
    if (score?.details?.strategic) {
      md += `---\n\n## Strategic Alignment\n\n`;
      md += `**Score:** ${score.strategic_alignment_score.toFixed(1)} / 100\n\n`;
      
      if (score.details.strategic.summary) {
        md += `### Analysis Summary\n\n${score.details.strategic.summary}\n\n`;
      }
      
      if (score.details.strategic.alignment_factors?.length > 0) {
        md += `### Alignment Factors\n\n`;
        score.details.strategic.alignment_factors.forEach((factor: string) => {
          md += `- ${factor}\n`;
        });
        md += `\n`;
      }
      
      if (score.details.strategic.competitive_advantages?.length > 0) {
        md += `### Competitive Advantages\n\n`;
        score.details.strategic.competitive_advantages.forEach((advantage: string) => {
          md += `- ${advantage}\n`;
        });
        md += `\n`;
      }
    }
    
    // RISK TAB
    if (score?.details?.risk) {
      md += `---\n\n## Risk Assessment\n\n`;
      md += `**Score:** ${score.contract_risk_score.toFixed(1)} / 100\n\n`;
      
      if (score.details.risk.summary) {
        md += `### Risk Summary\n\n${score.details.risk.summary}\n\n`;
      }
      
      if (score.details.risk.identified_risks?.length > 0) {
        md += `### Identified Risks\n\n`;
        score.details.risk.identified_risks.forEach((risk: any) => {
          md += `- **${risk.type || 'Risk'}** (${risk.severity || 'Unknown'})\n`;
          md += `  - ${risk.description}\n`;
          if (risk.mitigation) {
            md += `  - *Mitigation:* ${risk.mitigation}\n`;
          }
        });
        md += `\n`;
      }
    }
    
    // SECURITY TAB
    if (score?.details?.security) {
      md += `---\n\n## Security Requirements\n\n`;
      
      if (score.details.security.summary) {
        md += `### Security Posture Summary\n\n${score.details.security.summary}\n\n`;
      }
      
      md += `### Clearance Requirements\n\n`;
      md += `- **Facility Clearance (FCL):** ${score.details.security.facility_clearance || 'Not Specified'}\n`;
      md += `- **Personnel Clearance (PCL):** ${score.details.security.personnel_clearance || 'Not Specified'}\n\n`;
      
      if (score.details.security.cybersecurity_requirements?.length > 0) {
        md += `### Cybersecurity Requirements\n\n`;
        score.details.security.cybersecurity_requirements.forEach((req: string) => {
          md += `- ${req}\n`;
        });
        md += `\n`;
      }
      
      if (score.details.security.other_requirements?.length > 0) {
        md += `### Other Security Requirements\n\n`;
        score.details.security.other_requirements.forEach((req: string) => {
          md += `- ${req}\n`;
        });
        md += `\n`;
      }
    }
    
    // CAPACITY TAB
    if (score?.details?.capacity) {
      md += `---\n\n## Capacity Analysis\n\n`;
      md += `**Score:** ${score.internal_capacity_score.toFixed(1)} / 100\n\n`;
      
      if (score.details.capacity.summary) {
        md += `### Analysis Summary\n\n${score.details.capacity.summary}\n\n`;
      }
      
      if (score.details.capacity.resource_requirements?.length > 0) {
        md += `### Resource Requirements\n\n`;
        score.details.capacity.resource_requirements.forEach((req: string) => {
          md += `- ${req}\n`;
        });
        md += `\n`;
      }
      
      if (score.details.capacity.capability_gaps?.length > 0) {
        md += `### Capability Gaps\n\n`;
        score.details.capacity.capability_gaps.forEach((gap: string) => {
          md += `- ${gap}\n`;
        });
        md += `\n`;
      }
    }
    
    // PERSONNEL TAB
    if (score?.details?.personnel) {
      md += `---\n\n## Personnel Requirements\n\n`;
      
      if (score.details.personnel.summary) {
        md += `### Summary\n\n${score.details.personnel.summary}\n\n`;
      }
      
      if (score.details.personnel.key_positions?.length > 0) {
        md += `### Key Positions\n\n`;
        score.details.personnel.key_positions.forEach((position: any) => {
          md += `- **${position.title}**\n`;
          md += `  - ${position.requirements}\n`;
        });
        md += `\n`;
      }
      
      if (score.details.personnel.staffing_plan) {
        md += `### Staffing Plan\n\n${score.details.personnel.staffing_plan}\n\n`;
      }
    }
    
    // PAST PERFORMANCE TAB
    if (score?.details?.past_performance) {
      md += `---\n\n## Past Performance\n\n`;
      
      if (score.details.past_performance.summary) {
        md += `### Summary\n\n${score.details.past_performance.summary}\n\n`;
      }
      
      if (score.details.past_performance.relevant_experience?.length > 0) {
        md += `### Relevant Experience\n\n`;
        score.details.past_performance.relevant_experience.forEach((exp: any) => {
          md += `- **${exp.project || 'Project'}**\n`;
          md += `  - Client: ${exp.client}\n`;
          md += `  - Value: ${exp.value}\n`;
          md += `  - Description: ${exp.description}\n`;
        });
        md += `\n`;
      }
      
      if (score.details.past_performance.requirements?.length > 0) {
        md += `### Past Performance Requirements\n\n`;
        score.details.past_performance.requirements.forEach((req: string) => {
          md += `- ${req}\n`;
        });
        md += `\n`;
      }
    }
    
    // ELIGIBILITY STATUS
    if (eligibility) {
      md += `---\n\n## Eligibility Status\n\n`;
      md += `**Qualified:** ${eligibility.qualified ? 'Yes ✓' : 'No ✗'}\n\n`;
      
      if (eligibility.disqualifiers && eligibility.disqualifiers.length > 0) {
        md += `### Disqualification Reasons\n\n`;
        eligibility.disqualifiers.forEach((dq: any, i: number) => {
          md += `${i + 1}. **${dq.type.replace(/_/g, ' ')}** (${dq.severity})\n`;
          md += `   - **Reason:** ${dq.reason}\n`;
          md += `   - **Required:** ${dq.required}\n`;
          md += `   - **Your Entity:** ${dq.actual}\n\n`;
        });
      }
      
      if (eligibility.entity_info) {
        md += `### Entity Information\n\n`;
        md += `- **Name:** ${eligibility.entity_info.name}\n`;
        md += `- **UEI:** ${eligibility.entity_info.uei}\n\n`;
      }
    }
    
    return md;
  };

  const markdownToHTML = (markdown: string): string => {
    // Simple markdown to HTML conversion for PDF generation
    let html = markdown;
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Tables
    html = html.replace(/\n\|(.+)\|\n\|[-:\s|]+\|\n((?:\|.+\|\n?)*)/g, (_match, header, rows) => {
      const headerCells = header.split('|').filter((c: string) => c.trim()).map((c: string) => `<th>${c.trim()}</th>`).join('');
      const rowsHTML = rows.trim().split('\n').map((row: string) => {
        const cells = row.split('|').filter((c: string) => c.trim()).map((c: string) => `<td>${c.trim()}</td>`).join('');
        return `<tr>${cells}</tr>`;
      }).join('');
      return `<table><thead><tr>${headerCells}</tr></thead><tbody>${rowsHTML}</tbody></table>`;
    });
    
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    html = `<p>${html}</p>`;
    
    // Horizontal rules
    html = html.replace(/<p>---<\/p>/g, '<hr>');
    
    return html;
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'GO': return 'bg-green-500 hover:bg-green-600';
      case 'NO_GO': return 'bg-red-500 hover:bg-red-600';
      case 'REVIEW': return 'bg-yellow-500 hover:bg-yellow-600';
      default: return 'bg-gray-500 hover:bg-gray-600';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: TrendingUp },
    { id: 'solicitation' as TabType, label: 'Solicitation', icon: FileText },
    { id: 'financial' as TabType, label: 'Financial Analysis', icon: DollarSign },
    { id: 'strategic' as TabType, label: 'Strategic Alignment', icon: Target },
    { id: 'risk' as TabType, label: 'Risk Assessment', icon: AlertTriangle },
    { id: 'security' as TabType, label: 'Security', icon: Shield },
    { id: 'capacity' as TabType, label: 'Capacity Analysis', icon: Users },
    { id: 'personnel' as TabType, label: 'Personnel', icon: Briefcase },
    { id: 'past_performance' as TabType, label: 'Past Performance', icon: History },
    { id: 'logs' as TabType, label: 'Activity Logs', icon: Activity },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading analysis data...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
            <CardDescription>{error || 'Failed to load analysis data'}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => window.location.reload()}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { opportunity, score, logs } = data;

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6 p-6 pb-24">
        <div className="flex flex-col gap-6">
          <Button 
            onClick={() => navigate(-1)} 
            variant="ghost" 
            size="sm"
            className="gap-2 w-fit"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-3xl font-bold tracking-tight">Opportunity Analysis</h2>
              <p className="text-muted-foreground mt-1">
                Comprehensive AI-powered analysis of opportunity viability
              </p>
              <div className="flex items-center gap-2 mt-4">
                <h1 className="text-xl font-semibold text-foreground">{opportunity.title}</h1>
                <Badge variant="outline">{opportunity.notice_id}</Badge>
              </div>
            </div>

            <div className="flex gap-4">
              {/* Stack 1: Exports */}
              <div className="flex flex-col gap-2">
                <Button 
                  onClick={handleExportSummary} 
                  variant="outline" 
                  size="sm"
                  className="gap-1.5 text-xs justify-start w-36"
                >
                  <Download className="h-3.5 w-3.5" />
                  Export Summary
                </Button>
                <Button 
                  onClick={handleExportFull} 
                  variant="outline" 
                  size="sm"
                  className="gap-1.5 text-xs justify-start w-36"
                >
                  <FileText className="h-3.5 w-3.5" />
                  Export Full
                </Button>
              </div>

              {/* Stack 2: Proposals */}
              <div className="flex flex-col gap-2">
                <Button 
                  onClick={handleGenerateProposal}
                  disabled={!canGenerateProposal || generatingProposal}
                  variant="default"
                  size="sm"
                  className="gap-1.5 text-xs justify-start w-40"
                >
                  {generatingProposal ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileText className="h-3.5 w-3.5" />}
                  Generate Proposal
                </Button>
                {showPursuitButton && (
                  <Button 
                    onClick={() => setShowPursuitDialog(true)}
                    variant="default"
                    size="sm"
                    className="gap-1.5 text-xs bg-green-600 hover:bg-green-700 justify-start w-40"
                  >
                    <CheckCircle className="h-3.5 w-3.5" />
                    Proposal Decision
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons row */}
          <div className="flex flex-wrap gap-2 items-center">
            {score && (
              <>
                <div className="text-right mr-4">
                  <span className={cn("text-2xl font-bold", getScoreColor(score.weighted_score))}>
                    {score.weighted_score.toFixed(1)}
                  </span>
                  <span className="text-xs text-muted-foreground ml-1">/ 100</span>
                </div>
                <Badge className={cn("text-sm px-3 py-1 mr-2", getDecisionColor(score.go_no_go_decision))}>
                  {score.go_no_go_decision}
                </Badge>
              </>
            )}
            
            {pipelineStatus && (
              <Badge variant="secondary" className="bg-blue-600 hover:bg-blue-700 text-white gap-1 text-xs px-2 py-1 mr-2">
                <Eye className="h-3 w-3" />
                In Pipeline
              </Badge>
            )}

            <Button 
              onClick={handleRerunAnalysis} 
              disabled={reanalyzing}
              variant="outline" 
              size="sm"
              className="gap-1.5 text-xs"
            >
              {reanalyzing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
              Re-Run Analysis
            </Button>

            {!pipelineStatus && (
              <Button onClick={handleAddToPipeline} variant="outline" size="sm" className="gap-1.5 text-xs">
                <Eye className="h-3.5 w-3.5" />
                Add to Pipeline
              </Button>
            )}
          </div>
          
          {/* Shipley Phase Indicator */}
          {proposalData && proposalData.shipley_phase && (
            <div className="mt-4">
              <ShipleyPhaseIndicator currentPhase={proposalData.shipley_phase} showLabels={false} />
            </div>
          )}
        </div>
      </div>

      {/* Eligibility Warning Banner */}
      {eligibilityStatus && !eligibilityStatus.qualified && eligibilityStatus.disqualifiers && eligibilityStatus.disqualifiers.length > 0 && (
        <div className="max-w-7xl mx-auto px-6 pt-4">
          {eligibilityStatus.disqualifiers.map((disqualifier: any, index: number) => (
            <Alert 
              key={index}
              variant={disqualifier.severity === 'CRITICAL' ? 'destructive' : 'default'}
              className={`mb-3 ${disqualifier.severity === 'WARNING' ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/30 text-yellow-900 dark:text-yellow-200' : ''}`}
            >
              <AlertTriangle className="h-5 w-5" />
              <AlertTitle className="font-bold">
                {disqualifier.severity === 'CRITICAL' ? 'Disqualified' : 'Warning'}: {disqualifier.type.replace(/_/g, ' ')}
              </AlertTitle>
              <AlertDescription className="mt-2">
                <p className="font-semibold">{disqualifier.reason}</p>
                <div className="mt-2 text-sm space-y-1">
                  <div><strong>Required:</strong> {disqualifier.required}</div>
                  <div><strong>Your Entity:</strong> {disqualifier.actual}</div>
                </div>
                {eligibilityStatus.entity_info && (
                  <div className="mt-3 pt-3 border-t text-xs opacity-75">
                    <strong>Entity:</strong> {eligibilityStatus.entity_info.name} (UEI: {eligibilityStatus.entity_info.uei})
                  </div>
                )}
              </AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Analysis Progress Message */}
      {analysisMessage && (
        <div className="max-w-7xl mx-auto px-6 pt-4">
          <Card className={cn(
            "border-l-4",
            analysisMessage.type === 'success' && "border-l-green-500 bg-green-50 dark:bg-green-950",
            analysisMessage.type === 'error' && "border-l-red-500 bg-red-50 dark:bg-red-950",
            analysisMessage.type === 'info' && "border-l-blue-500 bg-blue-50 dark:bg-blue-950"
          )}>
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                {analysisMessage.type === 'success' && <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />}
                {analysisMessage.type === 'error' && <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />}
                {analysisMessage.type === 'info' && <Loader2 className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5 animate-spin" />}
                <p className="text-sm whitespace-pre-line">{analysisMessage.text}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Pursuit Decision Dialog */}
      <Dialog open={showPursuitDialog} onOpenChange={setShowPursuitDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Pursuit Decision Gate</DialogTitle>
            <DialogDescription>
              Make a formal decision on whether to pursue this opportunity
            </DialogDescription>
          </DialogHeader>
          <PursuitDecision
            opportunityId={parseInt(opportunityId || '0')}
            opportunityTitle={opportunity.title}
            onDecisionMade={handlePursuitDecisionMade}
          />
        </DialogContent>
      </Dialog>

      {/* Tab Navigation */}
      <div className="bg-card border-b">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                    activeTab === tab.id
                      ? "border-primary text-primary bg-primary/5"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <ScrollArea className="h-[calc(100vh-280px)]">
          {activeTab === 'overview' && <OverviewTab opportunity={opportunity} score={score} />}
          {activeTab === 'solicitation' && <SolicitationTab score={score} />}
          {activeTab === 'financial' && <FinancialTab score={score} />}
          {activeTab === 'strategic' && <StrategicTab score={score} />}
          {activeTab === 'risk' && <RiskTab opportunity={opportunity} score={score} />}
          {activeTab === 'security' && <SecurityTab score={score} opportunityId={data.opportunity.id} />}
          {activeTab === 'capacity' && <CapacityTab score={score} />}
          {activeTab === 'personnel' && <PersonnelTab score={score} documents={data?.score?.details?.source_documents} onLocationClick={handleLocationClick} />}
          {activeTab === 'past_performance' && <PastPerformanceTab score={score} />}
          {activeTab === 'logs' && <LogsTab logs={logs} />}
        </ScrollArea>
      </div>

      {/* Document Viewer */}
      {selectedDoc && (
        <DocumentViewer
          open={viewerOpen}
          onClose={() => setViewerOpen(false)}
          document={selectedDoc}
          opportunityId={opportunityId ? parseInt(opportunityId) : undefined}
          highlightLocation={highlightLocation}
        />
      )}
    </div>
  );
}

// Overview Tab Component
function OverviewTab({ opportunity, score }: { opportunity: AnalysisData['opportunity'], score: AnalysisData['score'] }) {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle>Executive Overview</CardTitle>
          <CardDescription>High-level summary and strategic analysis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {score?.details?.executive_overview?.executive_summary && (
            <div className="bg-primary/5 p-6 rounded-lg border border-primary/20">
              <h4 className="font-semibold mb-3 flex items-center gap-2 text-primary">
                <Briefcase className="h-5 w-5" />
                Executive Summary
              </h4>
              <p className="text-base leading-relaxed text-foreground/90">
                {score.details.executive_overview.executive_summary}
              </p>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {score?.details?.executive_overview?.mission_alignment && (
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <Target className="h-4 w-4 text-blue-600" />
                  Mission Alignment
                </h4>
                <p className="text-sm text-muted-foreground">
                  {score.details.executive_overview.mission_alignment}
                </p>
              </div>
            )}
            
            {score?.details?.executive_overview?.critical_success_factors && (
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  Critical Success Factors
                </h4>
                <ul className="space-y-2">
                  {score.details.executive_overview.critical_success_factors.map((factor: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-green-600 flex-shrink-0" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-muted-foreground mb-1">Department</div>
              <div className="text-base">{parseParentPath(opportunity.full_parent_path_name).department}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground mb-1">Sub-Tier</div>
              <div className="text-base">{parseParentPath(opportunity.full_parent_path_name).subTier}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">NAICS Code</div>
              <div className="text-base font-mono">{opportunity.naics_code || 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Set-Aside Type</div>
              <div className="text-base">{opportunity.type_of_set_aside || 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Posted Date</div>
              <div className="text-base">{opportunity.posted_date ? new Date(opportunity.posted_date).toLocaleDateString() : 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Response Deadline</div>
              <div className="text-base font-semibold text-red-600">
                {opportunity.response_deadline ? new Date(opportunity.response_deadline).toLocaleDateString() : 'N/A'}
              </div>
            </div>
          </div>
          <Separator />
          <div>
            <div className="text-sm font-medium text-muted-foreground mb-2">Description</div>
            <div className="text-sm leading-relaxed">{opportunity.description || 'No description available'}</div>
          </div>
        </CardContent>
      </Card>

      {score && (
        <Card>
          <CardHeader>
            <CardTitle>Score Breakdown</CardTitle>
            <CardDescription>Analysis scores across all dimensions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <ScoreCard title="Strategic Alignment" score={score.strategic_alignment_score} />
              <ScoreCard title="Financial Viability" score={score.financial_viability_score} />
              <ScoreCard title="Contract Risk" score={score.contract_risk_score} />
              <ScoreCard title="Internal Capacity" score={score.internal_capacity_score} />
              <ScoreCard title="Data Integrity" score={score.data_integrity_score} />
              <ScoreCard title="Weighted Score" score={score.weighted_score} highlight />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Solicitation Tab Component
function SolicitationTab({ score }: { score: AnalysisData['score'] }) {
  if (!score) return <NoAnalysisCard />;

  const details = score.details?.solicitation;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-600" />
            Solicitation Analysis
          </CardTitle>
          <CardDescription>Comprehensive summary and key requirements</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {details?.summary && (
            <div className="prose prose-sm max-w-none">
              <h4 className="font-semibold mb-2">Solicitation Summary</h4>
              <p className="text-muted-foreground whitespace-pre-wrap">{details.summary}</p>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {details?.key_dates && details.key_dates.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-orange-600" />
                  Key Dates & Milestones
                </h4>
                <div className="space-y-3">
                  {details.key_dates.map((item: any, i: number) => {
                    // Handle both string and object formats
                    if (typeof item === 'string') {
                      return (
                        <div key={i} className="p-3 bg-muted/30 rounded-lg">
                          <span className="text-sm">{item}</span>
                        </div>
                      );
                    }
                    return (
                      <div key={i} className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                        <span className="text-sm font-medium">{item.event || item.name || item.description || 'Event'}</span>
                        <Badge variant="outline">{item.date || item.deadline || 'TBD'}</Badge>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {details?.key_personnel && details.key_personnel.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Users className="h-4 w-4 text-purple-600" />
                  Key Personnel
                </h4>
                <div className="space-y-3">
                  {details.key_personnel.map((person: any, i: number) => {
                    // Handle both string and object formats
                    if (typeof person === 'string') {
                      return (
                        <div key={i} className="p-3 bg-muted/30 rounded-lg">
                          <span className="text-sm">{person}</span>
                        </div>
                      );
                    }
                    return (
                      <div key={i} className="p-3 bg-muted/30 rounded-lg space-y-1">
                        <div className="flex justify-between items-start">
                          <span className="text-sm font-medium">{person.role || person.title || 'Key Personnel'}</span>
                          {person.is_key && <Badge className="text-[10px] h-5">Key</Badge>}
                        </div>
                        {person.requirements && (
                          <p className="text-xs text-muted-foreground">{person.requirements}</p>
                        )}
                        {person.qualifications && !person.requirements && (
                          <p className="text-xs text-muted-foreground">{person.qualifications}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {details?.agency_goals && details.agency_goals.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3">Agency Goals</h4>
              <div className="flex flex-wrap gap-2">
                {details.agency_goals.map((goal: string, i: number) => (
                  <Badge key={i} variant="secondary" className="px-3 py-1">
                    {goal}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Security Tab Component
function SecurityTab({ score, opportunityId }: { score: AnalysisData['score']; opportunityId?: number }) {
  if (!score) return <NoAnalysisCard />;

  const details = score.details?.security;
  const extractedFrom = details?.extracted_from || [];
  const sourceDocuments = score.details?.extracted_data?.source_documents || [];
  
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<SourceDocument | null>(null);
  
  const handleDocumentClick = (doc: SourceDocument) => {
    setSelectedDocument(doc);
    setViewerOpen(true);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-red-600" />
            Security Requirements
          </CardTitle>
          <CardDescription>Security clearances and cybersecurity compliance</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {details?.summary && (
            <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-blue-600" />
                AI Security Analysis
              </h4>
              <p className="text-sm">{details.summary}</p>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-muted-foreground">Facility Clearance (FCL)</h4>
                  <Badge variant="outline" className="text-xs bg-green-100 text-green-700 border-green-300">
                    <FileText className="h-3 w-3 mr-1" />
                    Extracted
                  </Badge>
                </div>
                <div className="text-lg font-semibold flex items-center gap-2">
                  {details?.facility_clearance !== 'None' && details?.facility_clearance !== 'Not specified' ? (
                    <Shield className="h-4 w-4 text-red-600" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  )}
                  {details?.facility_clearance || 'Not Specified'}
                </div>
                <SourceBadge sources={extractedFrom} documents={sourceDocuments} />
              </div>

              <div className="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-muted-foreground">Personnel Clearance (PCL)</h4>
                  <Badge variant="outline" className="text-xs bg-green-100 text-green-700 border-green-300">
                    <FileText className="h-3 w-4 mr-1" />
                    Extracted
                  </Badge>
                </div>
                <div className="text-lg font-semibold">
                  {details?.personnel_clearance || 'Not Specified'}
                </div>
                <SourceBadge sources={extractedFrom} documents={sourceDocuments} />
              </div>
            </div>

            <div className="space-y-4">
              {details?.cybersecurity_requirements && details.cybersecurity_requirements.length > 0 && (
                <div className="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold flex items-center gap-2">
                      <Shield className="h-4 w-4 text-blue-600" />
                      Cybersecurity Requirements
                    </h4>
                    <Badge variant="outline" className="text-xs bg-green-100 text-green-700 border-green-300">
                      <FileText className="h-3 w-3 mr-1" />
                      Extracted
                    </Badge>
                  </div>
                  <ul className="space-y-2">
                    {details.cybersecurity_requirements.map((req: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <span>{req}</span>
                      </li>
                    ))}
                  </ul>
                  <SourceBadge 
                    sources={extractedFrom} 
                    documents={sourceDocuments}
                    onDocumentClick={handleDocumentClick}
                  />
                </div>
              )}

              {details?.other_requirements && details.other_requirements.length > 0 && (
                <div className="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold">Other Requirements</h4>
                    <Badge variant="outline" className="text-xs bg-green-100 text-green-700 border-green-300">
                      <FileText className="h-3 w-3 mr-1" />
                      Extracted
                    </Badge>
                  </div>
                  <ul className="space-y-2">
                    {details.other_requirements.map((req: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                        <span>{req}</span>
                      </li>
                    ))}
                  </ul>
                  <SourceBadge 
                    sources={extractedFrom} 
                    documents={sourceDocuments}
                    onDocumentClick={handleDocumentClick}
                  />
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
      
      <DocumentViewer
        open={viewerOpen}
        onClose={() => setViewerOpen(false)}
        document={selectedDocument}
        opportunityId={opportunityId}
      />
    </div>
  );
}
function FinancialTab({ score }: { score: AnalysisData['score'] }) {
  if (!score) {
    return <NoAnalysisCard />;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                Financial Viability Analysis
              </CardTitle>
              <CardDescription>Assessment of financial aspects and profitability</CardDescription>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-green-600">{score.financial_viability_score.toFixed(1)}</div>
              <div className="text-xs text-muted-foreground">Score</div>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
             <Button variant="outline" className="gap-2 text-blue-600 hover:text-blue-700">
               <ExternalLink className="h-4 w-4" />
               Price to Win Analysis
             </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {score.details?.financial?.summary && (
            <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-blue-600" />
                AI Analysis Summary
              </h4>
              <p className="text-sm">{score.details.financial.summary}</p>
            </div>
          )}
          
          {score.details?.financial?.insights && score.details.financial.insights.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3">Key Insights</h4>
              <ul className="space-y-2">
                {score.details.financial.insights.map((insight: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Lightbulb className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            {score.details?.financial?.risks && score.details.financial.risks.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Financial Risks</h4>
                <ul className="space-y-2">
                  {score.details.financial.risks.map((risk: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {score.details?.financial?.opportunities && score.details.financial.opportunities.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Opportunities</h4>
                <ul className="space-y-2">
                  {score.details.financial.opportunities.map((opp: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>{opp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          {score.details?.financial?.recommendation && (
            <div className="bg-muted/30 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Recommendation</h4>
              <p className="text-sm">{score.details.financial.recommendation}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Strategic Tab Component
function StrategicTab({ score }: { score: AnalysisData['score'] }) {
  if (!score) {
    return <NoAnalysisCard />;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-blue-600" />
                Strategic Alignment Analysis
              </CardTitle>
              <CardDescription>How well this opportunity aligns with company capabilities</CardDescription>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-blue-600">{score.strategic_alignment_score.toFixed(1)}</div>
              <div className="text-xs text-muted-foreground">Score</div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {score.details?.strategic?.summary && (
            <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-blue-600" />
                AI Analysis Summary
              </h4>
              <p className="text-sm">{score.details.strategic.summary}</p>
            </div>
          )}
          
          {/* NAICS and PSC Match Analysis */}
          <div className="grid md:grid-cols-2 gap-4">
            {score.details?.strategic?.naics_match && (
              <div className="bg-muted/30 p-4 rounded-lg border">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <Target className="h-4 w-4 text-blue-600" />
                  NAICS Code Alignment
                </h4>
                <p className="text-sm text-muted-foreground">{score.details.strategic.naics_match}</p>
              </div>
            )}
            
            {score.details?.strategic?.psc_match && (
              <div className="bg-muted/30 p-4 rounded-lg border">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <Target className="h-4 w-4 text-green-600" />
                  PSC Code Alignment
                </h4>
                <p className="text-sm text-muted-foreground">{score.details.strategic.psc_match}</p>
              </div>
            )}
          </div>
          
          {/* Team Contribution */}
          {score.details?.strategic?.team_contribution && (
            <div className="bg-purple-50 dark:bg-purple-950/30 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Users className="h-4 w-4 text-purple-600" />
                Team Contribution
              </h4>
              <p className="text-sm">{score.details.strategic.team_contribution}</p>
            </div>
          )}
          
          {score.details?.strategic?.capability_matches && score.details.strategic.capability_matches.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3">Capability Matches</h4>
              <ul className="space-y-2">
                {score.details.strategic.capability_matches.map((match: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span>{match}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {score.details?.strategic?.gaps && score.details.strategic.gaps.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3">Capability Gaps</h4>
              <ul className="space-y-2">
                {score.details.strategic.gaps.map((gap: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {score.details?.strategic?.recommendation && (
            <div className="bg-muted/30 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Recommendation</h4>
              <p className="text-sm">{score.details.strategic.recommendation}</p>
            </div>
          )}
        </CardContent>
      </Card>
      {/* Document Viewer removed from here */}
    </div>
  );
}

// Risk Tab Component
function RiskTab({ opportunity, score }: { opportunity: AnalysisData['opportunity'], score: AnalysisData['score'] }) {
  if (!score) {
    return <NoAnalysisCard />;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                Risk Assessment
              </CardTitle>
              <CardDescription>Evaluation of potential risks and compliance status</CardDescription>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-orange-600">{score.contract_risk_score.toFixed(1)}</div>
              <div className="text-xs text-muted-foreground">Risk Score</div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-muted/30 p-4 rounded-lg">
              <div className="text-sm font-medium text-muted-foreground mb-1">Compliance Status</div>
              <div className="text-lg font-semibold">{opportunity.compliance_status || 'Not Assessed'}</div>
            </div>
            <div className="bg-muted/30 p-4 rounded-lg">
              <div className="text-sm font-medium text-muted-foreground mb-1">Risk Score</div>
              <div className="text-lg font-semibold">{opportunity.risk_score?.toFixed(1) || 'N/A'}</div>
            </div>
          </div>
          {score.details?.risk?.summary && (
            <div className="bg-orange-50 dark:bg-orange-950/30 p-4 rounded-lg border border-orange-200 dark:border-orange-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-orange-600" />
                AI Risk Analysis Summary
              </h4>
              <p className="text-sm">{score.details.risk.summary}</p>
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            {score.details?.risk?.high_risks && score.details.risk.high_risks.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3 text-red-600">High Risks</h4>
                <ul className="space-y-3">
                  {score.details.risk.high_risks.map((riskItem: any, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="font-medium">{typeof riskItem === 'string' ? riskItem : riskItem.risk}</div>
                        {typeof riskItem === 'object' && riskItem.mitigation && (
                          <div className="text-xs text-muted-foreground mt-1">
                            <span className="font-medium">Mitigation:</span> {riskItem.mitigation}
                          </div>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {score.details?.risk?.medium_risks && score.details.risk.medium_risks.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3 text-orange-600">Medium Risks</h4>
                <ul className="space-y-3">
                  {score.details.risk.medium_risks.map((riskItem: any, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="font-medium">{typeof riskItem === 'string' ? riskItem : riskItem.risk}</div>
                        {typeof riskItem === 'object' && riskItem.mitigation && (
                          <div className="text-xs text-muted-foreground mt-1">
                            <span className="font-medium">Mitigation:</span> {riskItem.mitigation}
                          </div>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          {score.details?.risk?.mitigation_strategies && score.details.risk.mitigation_strategies.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3">Mitigation Strategies</h4>
              <ul className="space-y-2">
                {score.details.risk.mitigation_strategies.map((strategy: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span>{strategy}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {score.details?.risk?.recommendation && (
            <div className="bg-muted/30 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Recommendation</h4>
              <p className="text-sm">{score.details.risk.recommendation}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Capacity Tab Component
function CapacityTab({ score }: { score: AnalysisData['score'] }) {
  if (!score) {
    return <NoAnalysisCard />;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-purple-600" />
                Internal Capacity Analysis
              </CardTitle>
              <CardDescription>Assessment of team capacity and capability to deliver</CardDescription>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-purple-600">{score.internal_capacity_score.toFixed(1)}</div>
              <div className="text-xs text-muted-foreground">Score</div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {score.details?.capacity?.summary && (
            <div className="bg-purple-50 dark:bg-purple-950/30 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-purple-600" />
                AI Capacity Analysis Summary
              </h4>
              <p className="text-sm">{score.details.capacity.summary}</p>
            </div>
          )}
          
          {/* Entity, Team, and Combined Capacity */}
          <div className="grid md:grid-cols-3 gap-4">
            {score.details?.capacity?.entity_capacity && (
              <div className="bg-muted/30 p-4 rounded-lg border">
                <h4 className="font-semibold mb-2 flex items-center gap-2 text-sm">
                  <Briefcase className="h-4 w-4 text-blue-600" />
                  Primary Entity Capacity
                </h4>
                <p className="text-xs text-muted-foreground">{score.details.capacity.entity_capacity}</p>
              </div>
            )}
            
            {score.details?.capacity?.team_capacity && (
              <div className="bg-muted/30 p-4 rounded-lg border">
                <h4 className="font-semibold mb-2 flex items-center gap-2 text-sm">
                  <Users className="h-4 w-4 text-purple-600" />
                  Team Capacity
                </h4>
                <p className="text-xs text-muted-foreground">{score.details.capacity.team_capacity}</p>
              </div>
            )}
            
            {score.details?.capacity?.combined_capacity && (
              <div className="bg-green-50 dark:bg-green-950/30 p-4 rounded-lg border border-green-200 dark:border-green-800">
                <h4 className="font-semibold mb-2 flex items-center gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  Combined Capacity
                </h4>
                <p className="text-xs text-muted-foreground">{score.details.capacity.combined_capacity}</p>
              </div>
            )}
          </div>
          
          {/* Subcontracting Needs */}
          {score.details?.capacity?.subcontracting_needs && score.details.capacity.subcontracting_needs.length > 0 && (
            <div className="bg-orange-50 dark:bg-orange-950/30 p-4 rounded-lg border border-orange-200 dark:border-orange-800">
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-orange-600" />
                Subcontracting Needs
              </h4>
              <ul className="space-y-2">
                {score.details.capacity.subcontracting_needs.map((need: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-orange-600 flex-shrink-0" />
                    {need}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {score.details?.capacity?.required_skills && score.details.capacity.required_skills.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3">Required Skills</h4>
              <ul className="space-y-2">
                {score.details.capacity.required_skills.map((skill: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Target className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <span>{skill}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            {score.details?.capacity?.available_resources && score.details.capacity.available_resources.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Available Resources</h4>
                <ul className="space-y-2">
                  {score.details.capacity.available_resources.map((resource: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span>{resource}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {score.details?.capacity?.gaps && score.details.capacity.gaps.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Capacity Gaps</h4>
                <ul className="space-y-2">
                  {score.details.capacity.gaps.map((gap: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                      <span>{gap}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          {score.details?.capacity?.staffing_recommendation && (
            <div className="bg-muted/30 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Staffing Recommendation</h4>
              <p className="text-sm">{score.details.capacity.staffing_recommendation}</p>
            </div>
          )}
          
          {score.details?.capacity?.recommendation && (
            <div className="bg-muted/30 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Overall Recommendation</h4>
              <p className="text-sm">{score.details.capacity.recommendation}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Personnel Tab Component
function PersonnelTab({ score, documents, onLocationClick }: { 
  score: AnalysisData['score'];
  documents?: SourceDocument[];
  onLocationClick?: (doc: SourceDocument, loc: SourceLocation) => void;
}) {
  if (!score) return <NoAnalysisCard />;

  const details = score.details?.personnel;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="h-5 w-5 text-indigo-600" />
            Personnel & Staffing Analysis
          </CardTitle>
          <CardDescription>Key personnel, labor categories, and staffing requirements</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {details?.summary && (
            <div className="bg-indigo-50 dark:bg-indigo-950/30 p-4 rounded-lg border border-indigo-200 dark:border-indigo-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-indigo-600" />
                Staffing Summary
              </h4>
              <p className="text-sm">{details.summary}</p>
            </div>
          )}

          {details?.fte_estimate && (
            <div className="bg-muted/30 p-4 rounded-lg border flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-sm">Estimated FTEs</h4>
                <p className="text-xs text-muted-foreground">Based on scope analysis</p>
              </div>
              <div className="text-2xl font-bold text-indigo-600">
                {details.fte_estimate}
              </div>
            </div>
          )}

          {details?.key_personnel && details.key_personnel.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Users className="h-4 w-4 text-indigo-600" />
                Key Personnel
              </h4>
              <div className="grid md:grid-cols-2 gap-4">
                {details.key_personnel.map((person: any, i: number) => {
                  // Handle both string and object formats
                  if (typeof person === 'string') {
                    return (
                      <div key={i} className="p-4 bg-muted/30 rounded-lg border">
                        <div className="flex justify-between items-start">
                          <p className="text-sm">{person}</p>
                          <Badge variant="secondary" className="text-[10px]">Key</Badge>
                        </div>
                      </div>
                    );
                  }
                  return (
                    <div key={i} className="p-4 bg-muted/30 rounded-lg border space-y-2">
                      <div className="flex justify-between items-start">
                        <h5 className="font-semibold text-sm flex items-center">
                          {person.role || person.title || 'Key Personnel'}
                          <QuoteLink location={person.source_location} documents={documents} onLocationClick={onLocationClick} />
                        </h5>
                        <Badge variant="secondary" className="text-[10px]">Key</Badge>
                      </div>
                      <div className="text-xs space-y-1">
                        {person.qualifications && (
                          <p><span className="font-medium text-muted-foreground">Qualifications:</span> {person.qualifications}</p>
                        )}
                        {person.responsibilities && (
                          <p><span className="font-medium text-muted-foreground">Responsibilities:</span> {person.responsibilities}</p>
                        )}
                        {person.description && !person.qualifications && !person.responsibilities && (
                          <p className="text-muted-foreground">{person.description}</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {details?.labor_categories && details.labor_categories.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Labor Categories</h4>
                <div className="space-y-3">
                  {details.labor_categories.map((lcat: any, i: number) => {
                    // Handle both string and object formats
                    if (typeof lcat === 'string') {
                      return (
                        <div key={i} className="p-3 bg-muted/30 rounded-lg">
                          <div className="text-sm">{lcat}</div>
                        </div>
                      );
                    }
                    return (
                      <div key={i} className="p-3 bg-muted/30 rounded-lg">
                        <div className="font-medium text-sm flex items-center">
                          {lcat.title || lcat.name || lcat.category || 'Labor Category'}
                          <QuoteLink location={lcat.source_location} documents={documents} onLocationClick={onLocationClick} />
                        </div>
                        {lcat.requirements && (
                          <div className="text-xs text-muted-foreground mt-1">{lcat.requirements}</div>
                        )}
                        {lcat.description && !lcat.requirements && (
                          <div className="text-xs text-muted-foreground mt-1">{lcat.description}</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {details?.staffing_requirements && details.staffing_requirements.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">General Requirements</h4>
                <ul className="space-y-2">
                  {details.staffing_requirements.map((req: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-indigo-600 mt-0.5 flex-shrink-0" />
                      <span>{req}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Past Performance Tab Component
function PastPerformanceTab({ score }: { score: AnalysisData['score'] }) {
  if (!score) return <NoAnalysisCard />;

  const details = score.details?.past_performance;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-teal-600" />
            Past Performance Analysis
          </CardTitle>
          <CardDescription>Requirements, relevance criteria, and evaluation factors</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {details?.summary && (
            <div className="bg-teal-50 dark:bg-teal-950/30 p-4 rounded-lg border border-teal-200 dark:border-teal-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-teal-600" />
                Requirements Summary
              </h4>
              <p className="text-sm">{details.summary}</p>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {details?.requirements && details.requirements.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Target className="h-4 w-4 text-teal-600" />
                  Specific Requirements
                </h4>
                <ul className="space-y-2">
                  {details.requirements.map((req: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-teal-600 mt-0.5 flex-shrink-0" />
                      <span>{req}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {details?.relevance_criteria && details.relevance_criteria.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Target className="h-4 w-4 text-blue-600" />
                  Relevance Criteria
                </h4>
                <ul className="space-y-2">
                  {details.relevance_criteria.map((crit: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      <span>{crit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {details?.evaluation_factors && details.evaluation_factors.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3">Evaluation Factors</h4>
              <div className="flex flex-wrap gap-2">
                {details.evaluation_factors.map((factor: string, i: number) => (
                  <Badge key={i} variant="outline" className="px-3 py-1 border-teal-200 text-teal-700 bg-teal-50">
                    {factor}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Logs Tab Component
function LogsTab({ logs }: { logs: AnalysisData['logs'] }) {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Activity Timeline
          </CardTitle>
          <CardDescription>Detailed log of all agent activities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {logs.map((log) => (
              <div key={log.id} className="flex items-start gap-4 p-4 bg-muted/30 rounded-lg">
                <div className="mt-1">
                  {log.status === 'SUCCESS' ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : log.status === 'FAILURE' ? (
                    <XCircle className="h-5 w-5 text-red-500" />
                  ) : (
                    <Clock className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{log.agent_name}</span>
                    <span className="text-xs text-muted-foreground font-mono">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">{log.action}</p>
                  {log.details && Object.keys(log.details).length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                        View Details
                      </summary>
                      <pre className="mt-2 bg-muted p-2 rounded text-xs overflow-auto">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
            {logs.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No activity logs recorded yet.
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper Components
function ScoreCard({ title, score, highlight = false }: { title: string; score: number; highlight?: boolean }) {
  const getColor = (s: number) => {
    if (s >= 70) return 'text-green-600';
    if (s >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={cn(
      "p-4 rounded-lg border",
      highlight ? "bg-primary/5 border-primary" : "bg-muted/30"
    )}>
      <div className="text-xs text-muted-foreground uppercase font-medium mb-1">{title}</div>
      <div className={cn("text-2xl font-bold", getColor(score))}>{score.toFixed(1)}</div>
      <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
        <div 
          className={cn("h-full transition-all", getColor(score).replace('text-', 'bg-'))}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

function NoAnalysisCard() {
  return (
    <Card>
      <CardContent className="py-12 text-center">
        <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Analysis Data</h3>
        <p className="text-sm text-muted-foreground">
          Analysis has not been run for this opportunity yet.
        </p>
      </CardContent>
    </Card>
  );
}
