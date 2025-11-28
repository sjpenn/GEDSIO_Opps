
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
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
  Eye
} from 'lucide-react';
import { cn } from "@/lib/utils";

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
    naics_code: string;
    type_of_set_aside: string;
    place_of_performance: string;
    compliance_status: string;
    risk_score: number;
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

export default function AnalysisViewer() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<AnalysisData | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [error, setError] = useState<string | null>(null);
  const [generatingProposal, setGeneratingProposal] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<any>(null);

  useEffect(() => {
    fetchAnalysisData();
    fetchPipelineStatus();
  }, [opportunityId]);

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
            <CardDescription>{error || 'No analysis data found'}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate('/opportunities')} variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Opportunities
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { opportunity, score, logs } = data;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button 
                onClick={() => navigate('/opportunities')} 
                variant="ghost" 
                size="sm"
                className="gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
              <Separator orientation="vertical" className="h-8" />
              <div>
                <h1 className="text-2xl font-bold text-foreground">{opportunity.title}</h1>
                <p className="text-sm text-muted-foreground">Notice ID: {opportunity.notice_id}</p>
              </div>
            </div>
            {score && (
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className={cn("text-3xl font-bold", getScoreColor(score.weighted_score))}>
                    {score.weighted_score.toFixed(1)}
                  </div>
                  <div className="text-xs text-muted-foreground">Overall Score</div>
                </div>
                <Badge className={cn("text-lg px-4 py-2", getDecisionColor(score.go_no_go_decision))}>
                  {score.go_no_go_decision}
                </Badge>
                {pipelineStatus && (
                  <Badge variant="secondary" className="bg-blue-600 hover:bg-blue-700 text-white gap-1">
                    <Eye className="h-4 w-4" />
                    In Pipeline
                  </Badge>
                )}
                <Button onClick={handleAddToPipeline} variant="outline" className="gap-2">
                  <Eye className="h-4 w-4" />
                  Add to Pipeline
                </Button>
                <Button onClick={handleGenerateProposal} disabled={generatingProposal} variant="default" className="gap-2">
                  {generatingProposal ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                  Generate Proposal Draft
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

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
          {activeTab === 'security' && <SecurityTab score={score} />}
          {activeTab === 'capacity' && <CapacityTab score={score} />}
          {activeTab === 'personnel' && <PersonnelTab score={score} />}
          {activeTab === 'past_performance' && <PastPerformanceTab score={score} />}
          {activeTab === 'logs' && <LogsTab logs={logs} />}
        </ScrollArea>
      </div>
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm font-medium text-muted-foreground">Department</div>
              <div className="text-base">{opportunity.department || 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Sub-Tier</div>
              <div className="text-base">{opportunity.sub_tier || 'N/A'}</div>
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
                  {details.key_dates.map((item: any, i: number) => (
                    <div key={i} className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                      <span className="text-sm font-medium">{item.event}</span>
                      <Badge variant="outline">{item.date}</Badge>
                    </div>
                  ))}
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
                  {details.key_personnel.map((person: any, i: number) => (
                    <div key={i} className="p-3 bg-muted/30 rounded-lg space-y-1">
                      <div className="flex justify-between items-start">
                        <span className="text-sm font-medium">{person.role}</span>
                        {person.is_key && <Badge className="text-[10px] h-5">Key</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground">{person.requirements}</p>
                    </div>
                  ))}
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
function SecurityTab({ score }: { score: AnalysisData['score'] }) {
  if (!score) return <NoAnalysisCard />;

  const details = score.details?.security;

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
            <div className="bg-red-50 dark:bg-red-950/30 p-4 rounded-lg border border-red-200 dark:border-red-800">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-red-600" />
                Security Posture Summary
              </h4>
              <p className="text-sm">{details.summary}</p>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="p-4 bg-muted/30 rounded-lg border">
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Facility Clearance (FCL)</h4>
                <div className="text-lg font-semibold flex items-center gap-2">
                  {details?.facility_clearance !== 'None' ? (
                    <Shield className="h-4 w-4 text-red-600" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  )}
                  {details?.facility_clearance || 'Not Specified'}
                </div>
              </div>

              <div className="p-4 bg-muted/30 rounded-lg border">
                <h4 className="text-sm font-medium text-muted-foreground mb-1">Personnel Clearance (PCL)</h4>
                <div className="text-lg font-semibold">
                  {details?.personnel_clearance || 'Not Specified'}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              {details?.cybersecurity_requirements && details.cybersecurity_requirements.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Shield className="h-4 w-4 text-blue-600" />
                    Cybersecurity
                  </h4>
                  <ul className="space-y-2">
                    {details.cybersecurity_requirements.map((req: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <span>{req}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {details?.other_requirements && details.other_requirements.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">Other Requirements</h4>
                  <ul className="space-y-2">
                    {details.other_requirements.map((req: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                        <span>{req}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
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
                <ul className="space-y-2">
                  {score.details.risk.high_risks.map((risk: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                      <span>{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {score.details?.risk?.medium_risks && score.details.risk.medium_risks.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3 text-orange-600">Medium Risks</h4>
                <ul className="space-y-2">
                  {score.details.risk.medium_risks.map((risk: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                      <span>{risk}</span>
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
function PersonnelTab({ score }: { score: AnalysisData['score'] }) {
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
                {details.key_personnel.map((person: any, i: number) => (
                  <div key={i} className="p-4 bg-muted/30 rounded-lg border space-y-2">
                    <div className="flex justify-between items-start">
                      <h5 className="font-semibold text-sm">{person.role}</h5>
                      <Badge variant="secondary" className="text-[10px]">Key</Badge>
                    </div>
                    <div className="text-xs space-y-1">
                      <p><span className="font-medium text-muted-foreground">Qualifications:</span> {person.qualifications}</p>
                      <p><span className="font-medium text-muted-foreground">Responsibilities:</span> {person.responsibilities}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {details?.labor_categories && details.labor_categories.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Labor Categories</h4>
                <div className="space-y-3">
                  {details.labor_categories.map((lcat: any, i: number) => (
                    <div key={i} className="p-3 bg-muted/30 rounded-lg">
                      <div className="font-medium text-sm">{lcat.title}</div>
                      <div className="text-xs text-muted-foreground mt-1">{lcat.requirements}</div>
                    </div>
                  ))}
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
