import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import {
  ArrowLeft,
  FileText,
  CheckSquare,
  FileCode,
  History,
  DollarSign,
  Package,
  Loader2,
  Save,
  AlertCircle,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

interface Requirement {
  id: number;
  requirement_text: string;
  requirement_type: string;
  source_document_id: number | null;
  source_section: string | null;
  source_location: any;
  priority: string;
  compliance_status: string;
}

interface Artifact {
  id: number;
  artifact_type: string;
  title: string;
  description: string | null;
  source_section: string | null;
  required: boolean;
  status: string;
  file_id: number | null;
}

interface Document {
  id: number;
  filename: string;
  file_type: string | null;
  file_size: number | null;
  parsed_content: string | null;
}

interface Opportunity {
  id: number;
  title: string;
  notice_id: string | null;
  solicitation_number: string | null;
  department: string | null;
  sub_tier: string | null;
  office: string | null;
  description: string | null;
  posted_date: string | null;
  response_deadline: string | null;
  naics_code: string | null;
  type_of_set_aside: string | null;
  place_of_performance: any;
  point_of_contact: any;
}

interface WorkspaceData {
  proposal: {
    id: number;
    opportunity_id: number;
    version: number;
    volumes: any[];
  };
  opportunity: Opportunity | null;
  requirements: Requirement[];
  artifacts: Artifact[];
  documents: Document[];
}

type TabType = 'overview' | 'specification' | 'requirements' | 'sow' | 'past-performance' | 'pricing' | 'artifacts';

export default function ProposalWorkspace() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [workspaceData, setWorkspaceData] = useState<WorkspaceData | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedRequirement, setSelectedRequirement] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkspaceData();
  }, [opportunityId]);

  const fetchWorkspaceData = async () => {
    try {
      setLoading(true);
      // First get the proposal for this opportunity
      const proposalRes = await fetch(`${API_URL}/api/v1/proposals/${opportunityId}`);
      if (!proposalRes.ok) {
        throw new Error('Proposal not found. Please generate a proposal first.');
      }
      const proposalData = await proposalRes.json();
      
      // Then get workspace data
      const workspaceRes = await fetch(`${API_URL}/api/v1/requirements/proposals/${proposalData.id}/workspace`);
      if (!workspaceRes.ok) {
        throw new Error('Failed to load workspace data');
      }
      const data = await workspaceRes.json();
      setWorkspaceData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'overview' as TabType, label: 'Opportunity Overview', icon: AlertCircle },
    { id: 'specification' as TabType, label: 'Proposal Specification', icon: FileText },
    { id: 'requirements' as TabType, label: 'Requirements Matrix', icon: CheckSquare },
    { id: 'sow' as TabType, label: 'SOW/PWS Decomposition', icon: FileCode },
    { id: 'past-performance' as TabType, label: 'Past Performance', icon: History },
    { id: 'pricing' as TabType, label: 'Pricing Requirements', icon: DollarSign },
    { id: 'artifacts' as TabType, label: 'Required Artifacts', icon: Package },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading proposal workspace...</p>
        </div>
      </div>
    );
  }

  if (error || !workspaceData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
            <CardDescription>{error || 'No workspace data found'}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate(`/analysis/${opportunityId}`)} variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Analysis
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="bg-card border-b shadow-sm sticky top-0 z-10">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button 
                onClick={() => navigate(`/analysis/${opportunityId}`)} 
                variant="ghost" 
                size="sm"
                className="gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Analysis
              </Button>
              <Separator orientation="vertical" className="h-8" />
              <div>
                <h1 className="text-2xl font-bold text-foreground">Proposal Workspace</h1>
                <p className="text-sm text-muted-foreground">
                  {workspaceData.opportunity?.title || `Opportunity #${opportunityId}`} • Version {workspaceData.proposal.version}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {workspaceData.opportunity?.response_deadline && (
                <Badge variant="outline" className="text-sm gap-2">
                  <Clock className="h-4 w-4" />
                  Due: {new Date(workspaceData.opportunity.response_deadline).toLocaleDateString()}
                </Badge>
              )}
              <Badge variant="outline" className="text-sm">
                {workspaceData.requirements.length} Requirements
              </Badge>
              <Badge variant="outline" className="text-sm">
                {workspaceData.artifacts.length} Artifacts
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Vertical Tab Navigation */}
        <div className="w-64 bg-card border-r flex-shrink-0">
          <ScrollArea className="h-full">
            <div className="p-4 space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                      activeTab === tab.id
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    <span className="text-left">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </ScrollArea>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          <div className="p-8">
            {activeTab === 'overview' && <OpportunityOverviewTab opportunity={workspaceData.opportunity} />}
            {activeTab === 'specification' && <SpecificationTab proposal={workspaceData.proposal} />}
            {activeTab === 'requirements' && (
              <RequirementsTab 
                proposalId={workspaceData.proposal.id}
                requirements={workspaceData.requirements}
                selectedRequirement={selectedRequirement}
                setSelectedRequirement={setSelectedRequirement}
              />
            )}
            {activeTab === 'sow' && <SOWTab documents={workspaceData.documents} proposalId={workspaceData.proposal.id} />}
            {activeTab === 'past-performance' && (
              <PastPerformanceTab 
                requirements={workspaceData.requirements.filter(r => r.requirement_type === 'PAST_PERFORMANCE')} 
                proposalId={workspaceData.proposal.id}
              />
            )}
            {activeTab === 'pricing' && (
              <PricingTab requirements={workspaceData.requirements.filter(r => r.requirement_type === 'PRICING')} />
            )}
            {activeTab === 'artifacts' && <ArtifactsTab artifacts={workspaceData.artifacts} />}
          </div>
        </div>
      </div>
    </div>
  );
}

// Opportunity Overview Tab Component
function OpportunityOverviewTab({ opportunity }: { opportunity: Opportunity | null }) {
  if (!opportunity) {
    return (
      <div className="space-y-6 animate-in fade-in duration-500">
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No opportunity details available.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Key Information Card */}
      <Card className="border-l-4 border-l-primary">
        <CardHeader>
          <CardTitle className="text-xl">{opportunity.title}</CardTitle>
          <CardDescription className="flex items-center gap-4 flex-wrap mt-2">
            {opportunity.notice_id && (
              <span className="flex items-center gap-1">
                <strong>Notice ID:</strong> {opportunity.notice_id}
              </span>
            )}
            {opportunity.solicitation_number && (
              <span className="flex items-center gap-1">
                <strong>Solicitation:</strong> {opportunity.solicitation_number}
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Critical Dates */}
          <div className="grid md:grid-cols-2 gap-4 p-4 bg-muted/30 rounded-lg">
            <div>
              <div className="text-sm font-medium text-muted-foreground mb-1">Posted Date</div>
              <div className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4" />
                {opportunity.posted_date ? new Date(opportunity.posted_date).toLocaleDateString() : 'Not specified'}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground mb-1">Response Deadline</div>
              <div className="text-base font-semibold text-red-600 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                {opportunity.response_deadline ? new Date(opportunity.response_deadline).toLocaleDateString() : 'Not specified'}
              </div>
            </div>
          </div>

          {/* Agency Information */}
          <div>
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600" />
              Agency Information
            </h4>
            <div className="grid md:grid-cols-2 gap-4">
              {opportunity.department && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Department</div>
                  <div className="text-base">{opportunity.department}</div>
                </div>
              )}
              {opportunity.sub_tier && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Sub-Tier</div>
                  <div className="text-base">{opportunity.sub_tier}</div>
                </div>
              )}
              {opportunity.office && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Office</div>
                  <div className="text-base">{opportunity.office}</div>
                </div>
              )}
            </div>
          </div>

          {/* Contract Details */}
          <div>
            <h4 className="font-semibold mb-3">Contract Details</h4>
            <div className="grid md:grid-cols-2 gap-4">
              {opportunity.naics_code && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground">NAICS Code</div>
                  <div className="text-base font-mono">{opportunity.naics_code}</div>
                </div>
              )}
              {opportunity.type_of_set_aside && (
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Set-Aside Type</div>
                  <Badge variant="outline" className="mt-1">{opportunity.type_of_set_aside}</Badge>
                </div>
              )}
            </div>
          </div>

          {/* Place of Performance */}
          {opportunity.place_of_performance && (
            <div>
              <h4 className="font-semibold mb-2">Place of Performance</h4>
              <div className="text-sm bg-muted/30 p-3 rounded-lg">
                {typeof opportunity.place_of_performance === 'string' 
                  ? opportunity.place_of_performance 
                  : JSON.stringify(opportunity.place_of_performance, null, 2)}
              </div>
            </div>
          )}

          {/* Point of Contact */}
          {opportunity.point_of_contact && (
            <div>
              <h4 className="font-semibold mb-2">Point of Contact</h4>
              <div className="text-sm bg-muted/30 p-3 rounded-lg">
                {typeof opportunity.point_of_contact === 'string' 
                  ? opportunity.point_of_contact 
                  : JSON.stringify(opportunity.point_of_contact, null, 2)}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Description Card */}
      {opportunity.description && (
        <Card>
          <CardHeader>
            <CardTitle>Description</CardTitle>
            <CardDescription>Full opportunity description from solicitation</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] w-full">
              <div className="text-sm leading-relaxed whitespace-pre-wrap">{opportunity.description}</div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Specification Tab Component
function SpecificationTab({ proposal }: { proposal: WorkspaceData['proposal'] }) {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle>Proposal Volumes</CardTitle>
          <CardDescription>Structured proposal document outline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {proposal.volumes.map((volume) => (
              <Card key={volume.id} className="border-l-4 border-l-primary">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{volume.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {volume.blocks.map((block: any) => (
                      <div key={block.id} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <FileText className="h-4 w-4" />
                        <span>{block.title}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Requirements Tab Component
function RequirementsTab({ 
  proposalId,
  requirements,
  selectedRequirement,
  setSelectedRequirement
}: { 
  proposalId: number;
  requirements: Requirement[];
  selectedRequirement: number | null;
  setSelectedRequirement: (id: number | null) => void;
}) {
  const [filter, setFilter] = useState<string>('ALL');
  const [generating, setGenerating] = useState(false);
  
  const filteredRequirements = filter === 'ALL' 
    ? requirements 
    : requirements.filter(r => r.requirement_type === filter);

  const [matrixContent, setMatrixContent] = useState<string>('');

  const handleGenerateMatrix = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/proposals/${proposalId}/generate-requirements-matrix`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setMatrixContent(data.content);
        // alert("Requirements Matrix generated successfully!");
      } else {
        alert("Failed to generate matrix.");
      }
    } catch (error) {
      console.error("Generation failed:", error);
      alert("An error occurred during generation.");
    } finally {
      setGenerating(false);
    }
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      TECHNICAL: 'bg-blue-100 text-blue-700 border-blue-300',
      MANAGEMENT: 'bg-purple-100 text-purple-700 border-purple-300',
      PAST_PERFORMANCE: 'bg-green-100 text-green-700 border-green-300',
      PRICING: 'bg-orange-100 text-orange-700 border-orange-300',
      CERTIFICATION: 'bg-red-100 text-red-700 border-red-300',
      OTHER: 'bg-gray-100 text-gray-700 border-gray-300',
    };
    return colors[type] || colors.OTHER;
  };

  const getPriorityIcon = (priority: string) => {
    if (priority === 'MANDATORY') return <AlertTriangle className="h-4 w-4 text-red-600" />;
    if (priority === 'IMPORTANT') return <AlertCircle className="h-4 w-4 text-yellow-600" />;
    return <Clock className="h-4 w-4 text-gray-600" />;
  };

  const getStatusIcon = (status: string) => {
    if (status === 'COMPLETE') return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    if (status === 'IN_PROGRESS') return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
    return <Clock className="h-5 w-5 text-gray-400" />;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Requirements Matrix</CardTitle>
              <CardDescription>All extracted requirements from solicitation documents</CardDescription>
            </div>
            <div className="flex gap-2 items-center">
              <Button 
                onClick={handleGenerateMatrix} 
                disabled={generating} 
                variant="secondary"
                size="sm"
                className="mr-2 gap-2"
              >
                {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 text-purple-500" />}
                Generate Matrix
              </Button>
              <div className="h-6 w-px bg-border mx-1" />
              <Button
                variant={filter === 'ALL' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('ALL')}
              >
                All ({requirements.length})
              </Button>
              <Button
                variant={filter === 'TECHNICAL' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('TECHNICAL')}
              >
                Technical
              </Button>
              <Button
                variant={filter === 'MANAGEMENT' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('MANAGEMENT')}
              >
                Management
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredRequirements.map((req) => (
              <Card 
                key={req.id}
                className={cn(
                  "cursor-pointer transition-all hover:shadow-md",
                  selectedRequirement === req.id && "ring-2 ring-primary"
                )}
                onClick={() => setSelectedRequirement(req.id === selectedRequirement ? null : req.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      {getStatusIcon(req.compliance_status)}
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge className={cn("text-xs", getTypeColor(req.requirement_type))}>
                          {req.requirement_type}
                        </Badge>
                        <div className="flex items-center gap-1">
                          {getPriorityIcon(req.priority)}
                          <span className="text-xs text-muted-foreground">{req.priority}</span>
                        </div>
                        {req.source_section && (
                          <Badge variant="outline" className="text-xs">
                            {req.source_section}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm leading-relaxed">{req.requirement_text}</p>
                      {selectedRequirement === req.id && (
                        <div className="mt-4 pt-4 border-t">
                          <RequirementResponse requirementId={req.id} proposalId={proposalId} />
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {filteredRequirements.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No requirements found for this filter.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {matrixContent && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Compliance Matrix</CardTitle>
            <CardDescription>AI-generated compliance matrix based on requirements</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea 
              value={matrixContent} 
              readOnly 
              className="min-h-[400px] font-mono text-sm"
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Requirement Response Component
function RequirementResponse({ requirementId, proposalId }: { requirementId: number; proposalId: number }) {
  const [responseText, setResponseText] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch(`${API_URL}/api/v1/requirements/proposals/${proposalId}/requirements/${requirementId}/response`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response_text: responseText })
      });
    } catch (error) {
      console.error('Failed to save response:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium">Proposal Response</label>
      <Textarea
        value={responseText}
        onChange={(e) => setResponseText(e.target.value)}
        placeholder="Enter your response to this requirement..."
        className="min-h-[150px]"
      />
      <Button onClick={handleSave} disabled={saving} size="sm" className="gap-2">
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        Save Response
      </Button>
    </div>
  );
}

// SOW Tab Component
function SOWTab({ documents, proposalId }: { documents: Document[]; proposalId: number }) {
  const [generating, setGenerating] = useState(false);

  const [sowContent, setSowContent] = useState<string>('');

  const handleGenerateSOW = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/proposals/${proposalId}/generate-sow-decomposition`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setSowContent(data.content);
        // alert("SOW Decomposition generated successfully!");
      } else {
        alert("Failed to generate SOW decomposition.");
      }
    } catch (error) {
      console.error("Generation failed:", error);
      alert("An error occurred during generation.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>SOW/PWS Documents</CardTitle>
              <CardDescription>Source documents with extracted sections</CardDescription>
            </div>
            <Button 
              onClick={handleGenerateSOW} 
              disabled={generating} 
              variant="secondary"
              size="sm"
              className="gap-2"
            >
              {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 text-purple-500" />}
              Generate SOW Analysis
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {documents.map((doc) => (
              <Card key={doc.id} className="border-l-4 border-l-blue-500">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    {doc.filename}
                  </CardTitle>
                  <CardDescription>
                    {doc.file_type} • {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'Unknown size'}
                  </CardDescription>
                </CardHeader>
                {doc.parsed_content && (
                  <CardContent>
                    <ScrollArea className="h-[400px] w-full rounded-md border bg-muted/30 p-4">
                      <pre className="text-sm whitespace-pre-wrap">{doc.parsed_content.substring(0, 5000)}...</pre>
                    </ScrollArea>
                  </CardContent>
                )}
              </Card>
            ))}
            {documents.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No documents available.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {sowContent && (
        <Card>
          <CardHeader>
            <CardTitle>SOW Decomposition Analysis</CardTitle>
            <CardDescription>AI-generated analysis of the Statement of Work</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea 
              value={sowContent} 
              readOnly 
              className="min-h-[500px] font-mono text-sm"
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Past Performance Tab Component
function PastPerformanceTab({ requirements, proposalId }: { requirements: Requirement[]; proposalId: number }) {
  const [generatingVolume, setGeneratingVolume] = useState(false);
  const [generatingPPQs, setGeneratingPPQs] = useState(false);

  const [volumeContent, setVolumeContent] = useState<string>('');
  const [ppqContent, setPpqContent] = useState<string>('');

  const handleGenerateVolume = async () => {
    setGeneratingVolume(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/proposals/${proposalId}/generate-past-performance`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setVolumeContent(data.content);
        // alert("Past Performance Volume generated successfully!");
      } else {
        alert("Failed to generate volume.");
      }
    } catch (error) {
      console.error("Generation failed:", error);
      alert("An error occurred during generation.");
    } finally {
      setGeneratingVolume(false);
    }
  };

  const handleGeneratePPQs = async () => {
    setGeneratingPPQs(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/proposals/${proposalId}/generate-ppqs`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setPpqContent(data.content);
        // alert("PPQs generated successfully!");
      } else {
        alert("Failed to generate PPQs.");
      }
    } catch (error) {
      console.error("Generation failed:", error);
      alert("An error occurred during generation.");
    } finally {
      setGeneratingPPQs(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Past Performance Requirements</CardTitle>
              <CardDescription>Requirements related to past performance and references</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={handleGenerateVolume} 
                disabled={generatingVolume} 
                variant="secondary"
                size="sm"
                className="gap-2"
              >
                {generatingVolume ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 text-purple-500" />}
                Generate Volume
              </Button>
              <Button 
                onClick={handleGeneratePPQs} 
                disabled={generatingPPQs} 
                variant="outline"
                size="sm"
                className="gap-2"
              >
                {generatingPPQs ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                Generate PPQs
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {requirements.map((req) => (
              <Card key={req.id} className="border-l-4 border-l-green-500">
                <CardContent className="p-4">
                  <p className="text-sm leading-relaxed">{req.requirement_text}</p>
                  {req.source_section && (
                    <Badge variant="outline" className="mt-2 text-xs">
                      {req.source_section}
                    </Badge>
                  )}
                </CardContent>
              </Card>
            ))}
            {requirements.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No past performance requirements found.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {volumeContent && (
        <Card>
          <CardHeader>
            <CardTitle>Generated Past Performance Volume</CardTitle>
            <CardDescription>AI-generated volume with case studies</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea 
              value={volumeContent} 
              readOnly 
              className="min-h-[500px] font-mono text-sm"
            />
          </CardContent>
        </Card>
      )}

      {ppqContent && (
        <Card>
          <CardHeader>
            <CardTitle>Generated PPQ Responses</CardTitle>
            <CardDescription>AI-generated responses for Past Performance Questionnaires</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea 
              value={ppqContent} 
              readOnly 
              className="min-h-[500px] font-mono text-sm"
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Pricing Tab Component
function PricingTab({ requirements }: { requirements: Requirement[] }) {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle>Pricing Requirements</CardTitle>
          <CardDescription>Requirements related to pricing and cost proposals</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {requirements.map((req) => (
              <Card key={req.id} className="border-l-4 border-l-orange-500">
                <CardContent className="p-4">
                  <p className="text-sm leading-relaxed">{req.requirement_text}</p>
                  {req.source_section && (
                    <Badge variant="outline" className="mt-2 text-xs">
                      {req.source_section}
                    </Badge>
                  )}
                </CardContent>
              </Card>
            ))}
            {requirements.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <DollarSign className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No pricing requirements found.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Artifacts Tab Component
function ArtifactsTab({ artifacts }: { artifacts: Artifact[] }) {
  const getStatusColor = (status: string) => {
    if (status === 'COMPLETE') return 'bg-green-100 text-green-700 border-green-300';
    if (status === 'IN_PROGRESS') return 'bg-blue-100 text-blue-700 border-blue-300';
    return 'bg-gray-100 text-gray-700 border-gray-300';
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle>Required Artifacts</CardTitle>
          <CardDescription>Forms, certifications, and deliverables required for submission</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {artifacts.map((art) => (
              <Card key={art.id} className={cn("border-l-4", art.required ? "border-l-red-500" : "border-l-gray-300")}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold">{art.title}</h4>
                        {art.required && (
                          <Badge variant="destructive" className="text-xs">Required</Badge>
                        )}
                      </div>
                      {art.description && (
                        <p className="text-sm text-muted-foreground">{art.description}</p>
                      )}
                      {art.source_section && (
                        <Badge variant="outline" className="text-xs">
                          {art.source_section}
                        </Badge>
                      )}
                    </div>
                    <Badge className={cn("text-xs", getStatusColor(art.status))}>
                      {art.status.replace('_', ' ')}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
            {artifacts.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No required artifacts found.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
