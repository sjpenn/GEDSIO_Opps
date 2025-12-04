import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { DndContext, closestCenter, PointerSensor, KeyboardSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import CapturePlanningTab from '@/components/CapturePlanningTab';
import ProposalEditor from '@/components/ProposalEditor';
import ReviewsTab from '@/components/ReviewsTab';
import SubmissionTab from '@/components/SubmissionTab';
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
  Sparkles,
  Target,
  ShieldCheck,
  Send,
  GripVertical,
  Plus,
  Pencil,
  Trash2
} from 'lucide-react';
import { cn } from '@/lib/utils';

const API_URL = import.meta.env.VITE_API_URL || '';

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

interface Block {
  id: string;
  title: string;
  content: string;
  order: number;
}

interface Volume {
  id: number;
  title: string;
  order: number;
  blocks: Block[];
}

interface WorkspaceData {
  proposal: {
    id: number;
    opportunity_id: number;
    version: number;
    volumes: Volume[];
  };
  opportunity: Opportunity | null;
  requirements: Requirement[];
  artifacts: Artifact[];
  documents: Document[];
}

type TabType = 'overview' | 'capture' | 'development' | 'specification' | 'requirements' | 'sow' | 'past-performance' | 'pricing' | 'artifacts' | 'reviews' | 'submission' | 'sources-sought';

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
      // Get the proposal for this opportunity from pipeline
      const pipelineRes = await fetch(`${API_URL}/api/v1/pipeline/`);
      if (!pipelineRes.ok) {
        throw new Error('Failed to load pipeline data');
      }
      const pipelineData = await pipelineRes.json();
      const pipelineItem = pipelineData.find((p: any) => p.opportunity.id === parseInt(opportunityId || '0'));
      
      if (!pipelineItem || !pipelineItem.proposal) {
        throw new Error('Proposal not found. Please make a Pursuit Decision first.');
      }
      
      const proposalId = pipelineItem.proposal.id;
      
      // Then get workspace data
      const workspaceRes = await fetch(`${API_URL}/api/v1/requirements/proposals/${proposalId}/workspace`);
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
    { id: 'capture' as TabType, label: 'Capture Planning', icon: Target },
    { id: 'development' as TabType, label: 'Proposal Development', icon: FileText },
    { id: 'specification' as TabType, label: 'Proposal Specification', icon: FileText },
    { id: 'requirements' as TabType, label: 'Requirements Matrix', icon: CheckSquare },
    { id: 'sow' as TabType, label: 'SOW/PWS Decomposition', icon: FileCode },
    { id: 'past-performance' as TabType, label: 'Past Performance', icon: History },
    { id: 'pricing' as TabType, label: 'Pricing Requirements', icon: DollarSign },
    { id: 'artifacts' as TabType, label: 'Required Artifacts', icon: Package },
    { id: 'reviews' as TabType, label: 'Reviews', icon: ShieldCheck },
    { id: 'submission' as TabType, label: 'Submission', icon: Send },
    { id: 'sources-sought' as TabType, label: 'Sources Sought', icon: FileText },
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
            {activeTab === 'capture' && <CapturePlanningTab proposalId={workspaceData.proposal.id} />}
            {activeTab === 'development' && <ProposalEditor proposalId={workspaceData.proposal.id} />}
            {activeTab === 'specification' && <SpecificationTab proposal={workspaceData.proposal} proposalId={workspaceData.proposal.id} />}
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
            {activeTab === 'artifacts' && <ArtifactsTab artifacts={workspaceData.artifacts} proposalId={workspaceData.proposal.id} />}
            {activeTab === 'reviews' && <ReviewsTab proposalId={workspaceData.proposal.id} />}
            {activeTab === 'submission' && <SubmissionTab proposalId={workspaceData.proposal.id} />}
            {activeTab === 'sources-sought' && <SourcesSoughtTab proposalId={workspaceData.proposal.id} />}
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
                {typeof opportunity.place_of_performance === 'string' ? (
                  opportunity.place_of_performance
                ) : (
                  <div className="flex flex-col gap-1">
                    <span className="font-medium">
                      {[
                        opportunity.place_of_performance?.city?.name || opportunity.place_of_performance?.city,
                        opportunity.place_of_performance?.state?.name || opportunity.place_of_performance?.state?.code || opportunity.place_of_performance?.state,
                        opportunity.place_of_performance?.country?.name || opportunity.place_of_performance?.country?.code || opportunity.place_of_performance?.country
                      ].filter(Boolean).join(', ')}
                    </span>
                    {opportunity.place_of_performance?.zip && (
                      <span className="text-xs text-muted-foreground">{opportunity.place_of_performance.zip}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Point of Contact */}
          {opportunity.point_of_contact && (
            <div>
              <h4 className="font-semibold mb-2">Point of Contact</h4>
              <div className="space-y-3">
                {Array.isArray(opportunity.point_of_contact) ? (
                  opportunity.point_of_contact.map((poc: any, i: number) => (
                    <div key={i} className="text-sm bg-muted/30 p-3 rounded-lg border">
                      <div className="font-medium">{poc.fullName || poc.name || 'Unknown Name'}</div>
                      {poc.title && <div className="text-xs text-muted-foreground">{poc.title}</div>}
                      <div className="mt-2 space-y-1">
                        {poc.email && (
                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-muted-foreground">Email:</span>
                            <a href={`mailto:${poc.email}`} className="text-primary hover:underline">{poc.email}</a>
                          </div>
                        )}
                        {poc.phone && (
                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-muted-foreground">Phone:</span>
                            <span>{poc.phone}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : typeof opportunity.point_of_contact === 'object' ? (
                   <div className="text-sm bg-muted/30 p-3 rounded-lg border">
                      <div className="font-medium">{(opportunity.point_of_contact as any).fullName || (opportunity.point_of_contact as any).name}</div>
                      {(opportunity.point_of_contact as any).email && (
                        <div className="text-xs mt-1">{(opportunity.point_of_contact as any).email}</div>
                      )}
                   </div>
                ) : (
                  <div className="text-sm bg-muted/30 p-3 rounded-lg">
                    {String(opportunity.point_of_contact)}
                  </div>
                )}
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
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {opportunity.description.replace(/<[^>]*>?/gm, '')}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Specification Tab Component
function SpecificationTab({ proposal, proposalId }: { proposal: WorkspaceData['proposal'], proposalId: number }) {
  const [volumes, setVolumes] = useState(proposal.volumes);
  const [editingSection, setEditingSection] = useState<{volumeId: number, blockId: string} | null>(null);
  const [sectionTitle, setSectionTitle] = useState('');
  const [addingTo, setAddingTo] = useState<number | null>(null);
  const [newSectionTitle, setNewSectionTitle] = useState('');
  
  useEffect(() => {
    setVolumes(proposal.volumes);
  }, [proposal.volumes]);

  const handleReorder = async (volumeId: number, newBlocks: Block[]) => {
    try {
      const blockOrders = newBlocks.map((block, index) => ({
        id: block.id,
        order: index
      }));
      
      const res = await fetch(`/api/v1/proposal-content/proposals/${proposalId}/volumes/${volumeId}/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ block_orders: blockOrders })
      });
      
      if (res.ok) {
        // Update local state
        setVolumes(prev => prev.map(v => 
          v.id === volumeId ? { ...v, blocks: newBlocks } : v
        ));
      }
    } catch (error) {
      console.error('Reorder failed:', error);
    }
  };
  
  const handleRename = async (volumeId: number, blockId: string) => {
    if (!sectionTitle.trim()) return;
    
    try {
      const res = await fetch(`/api/v1/proposal-content/proposals/${proposalId}/volumes/${volumeId}/sections/${blockId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: sectionTitle })
      });
      
      if (res.ok) {
        // Update local state
        setVolumes(prev => prev.map(v => 
          v.id === volumeId 
            ? { ...v, blocks: v.blocks.map(b => b.id === blockId ? { ...b, title: sectionTitle } : b) }
            : v
        ));
        setEditingSection(null);
        setSectionTitle('');
      }
    } catch (error) {
      console.error('Rename failed:', error);
    }
  };
  
  const handleDelete = async (volumeId: number, blockId: string) => {
    if (!confirm('Delete this section?')) return;
    
    try {
      const res = await fetch(`/api/v1/proposal-content/proposals/${proposalId}/volumes/${volumeId}/sections/${blockId}`, {
        method: 'DELETE'
      });
      
      if (res.ok) {
        // Update local state
        setVolumes(prev => prev.map(v => 
          v.id === volumeId 
            ? { ...v, blocks: v.blocks.filter(b => b.id !== blockId) }
            : v
        ));
      }
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };
  
  const handleAddSection = async (volumeId: number) => {
    if (!newSectionTitle.trim()) return;
    
    try {
      const res = await fetch(`/api/v1/proposal-content/proposals/${proposalId}/volumes/${volumeId}/sections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          title: newSectionTitle,
          content: ''
        })
      });
      
      if (res.ok) {
        const newBlock = await res.json();
        // Update local state
        setVolumes(prev => prev.map(v => 
          v.id === volumeId 
            ? { ...v, blocks: [...v.blocks, newBlock] }
            : v
        ));
        setNewSectionTitle('');
        setAddingTo(null);
      }
    } catch (error) {
      console.error('Add section failed:', error);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle>Proposal Volumes</CardTitle>
          <CardDescription>Structured proposal document outline - drag sections to reorder</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {volumes.map((volume) => (
              <VolumeCard 
                key={volume.id}
                volume={volume}
                onReorder={handleReorder}
                onRename={handleRename}
                onDelete={handleDelete}
                onAddSection={handleAddSection}
                editingSection={editingSection}
                setEditingSection={setEditingSection}
                sectionTitle={sectionTitle}
                setSectionTitle={setSectionTitle}
                addingTo={addingTo}
                setAddingTo={setAddingTo}
                newSectionTitle={newSectionTitle}
                setNewSectionTitle={setNewSectionTitle}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// VolumeCard Props Interface
interface VolumeCardProps {
  volume: Volume;
  onReorder: (volumeId: number, blocks: Block[]) => void;
  onRename: (volumeId: number, blockId: string) => void;
  onDelete: (volumeId: number, blockId: string) => void;
  onAddSection: (volumeId: number) => void;
  editingSection: { volumeId: number; blockId: string } | null;
  setEditingSection: (section: { volumeId: number; blockId: string } | null) => void;
  sectionTitle: string;
  setSectionTitle: (title: string) => void;
  addingTo: number | null;
  setAddingTo: (id: number | null) => void;
  newSectionTitle: string;
  setNewSectionTitle: (title: string) => void;
}

// Volume Card Component with Drag and Drop
function VolumeCard({
  volume,
  onReorder,
  onRename,
  onDelete,
  onAddSection,
  editingSection,
  setEditingSection,
  sectionTitle,
  setSectionTitle,
  addingTo,
  setAddingTo,
  newSectionTitle,
  setNewSectionTitle
}: VolumeCardProps) {
  const [blocks, setBlocks] = useState<Block[]>(volume.blocks);
  
  useEffect(() => {
    setBlocks(volume.blocks);
  }, [volume.blocks]);
  
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: any) => {
    const {active, over} = event;

    if (active.id !== over.id) {
      const oldIndex = blocks.findIndex((b) => b.id === active.id);
      const newIndex = blocks.findIndex((b) => b.id === over.id);
      
      const newBlocks = arrayMove(blocks, oldIndex, newIndex);
      setBlocks(newBlocks);
      onReorder(volume.id, newBlocks);
    }
  };

  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{volume.title}</CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setAddingTo(addingTo === volume.id ? null : volume.id)}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Section
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {addingTo === volume.id && (
          <div className="mb-4 p-3 bg-muted rounded-lg flex gap-2">
            <Input
              placeholder="New section title"
              value={newSectionTitle}
              onChange={(e) => setNewSectionTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  onAddSection(volume.id);
                }
              }}
            />
            <Button onClick={() => onAddSection(volume.id)} size="sm">
              Add
            </Button>
            <Button onClick={() => { setAddingTo(null); setNewSectionTitle(''); }} size="sm" variant="ghost">
              Cancel
            </Button>
          </div>
        )}
        
        <DndContext 
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext 
            items={blocks.map((b) => b.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-2">
              {blocks.map((block) => (
                <SortableSection
                  key={block.id}
                  block={block}
                  editing={editingSection?.volumeId === volume.id && editingSection?.blockId === block.id}
                  onStartEdit={(blockId: string, title: string) => {
                    setEditingSection({ volumeId: volume.id, blockId });
                    setSectionTitle(title);
                  }}
                  onSaveEdit={() => onRename(volume.id, block.id)}
                  onCancelEdit={() => {
                    setEditingSection(null);
                    setSectionTitle('');
                  }}
                  onDelete={() => onDelete(volume.id, block.id)}
                  sectionTitle={sectionTitle}
                  setSectionTitle={setSectionTitle}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </CardContent>
    </Card>
  );
}

// SortableSection Props Interface
interface SortableSectionProps {
  block: Block;
  editing: boolean;
  onStartEdit: (blockId: string, title: string) => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onDelete: () => void;
  sectionTitle: string;
  setSectionTitle: (title: string) => void;
}

// Sortable Section Component
function SortableSection({
  block,
  editing,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onDelete,
  sectionTitle,
  setSectionTitle
}: SortableSectionProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({id: block.id});

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-2 p-2 bg-background border rounded hover:bg-muted transition-colors"
    >
      <div {...attributes} {...listeners} className="cursor-move p-1">
        <GripVertical className="h-4 w-4 text-muted-foreground" />
      </div>
      
      {editing ? (
        <>
          <Input
            value={sectionTitle}
            onChange={(e) => setSectionTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onSaveEdit();
              if (e.key === 'Escape') onCancelEdit();
            }}
            className="flex-1"
            autoFocus
          />
          <Button size="sm" onClick={onSaveEdit}>Save</Button>
          <Button size="sm" variant="ghost" onClick={onCancelEdit}>Cancel</Button>
        </>
      ) : (
        <>
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="flex-1 text-sm">{block.title}</span>
          <Button 
            size="sm" 
            variant="ghost"
            onClick={() => onStartEdit(block.id, block.title)}
          >
            <Pencil className="h-3 w-3" />
          </Button>
          <Button 
            size="sm" 
            variant="ghost"
            onClick={onDelete}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </>
      )}
    </div>
  );
}

// Sources Sought Tab Component
function SourcesSoughtTab({ proposalId }: { proposalId: number }) {
  const [generating, setGenerating] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/proposal-content/proposals/${proposalId}/generate-sources-sought`, {
        method: 'POST',
      });
      
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to generate response');
      }
      
      const data = await res.json();
      setResponse(data.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Sources Sought / RFI Response
          </CardTitle>
          <CardDescription>
            Generate a specialized response for Sources Sought Notices and RFIs, focusing on capabilities and past performance.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {!response && (
            <div className="text-center py-12 bg-muted/30 rounded-lg border border-dashed">
              <h3 className="text-lg font-medium mb-2">Generate Response</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Create a tailored response based on the opportunity details and your company's profile.
              </p>
              <Button onClick={handleGenerate} disabled={generating} size="lg">
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Sources Sought Response
                  </>
                )}
              </Button>
              {error && (
                <div className="mt-4 text-red-600 bg-red-50 p-3 rounded-md inline-block">
                  <AlertTriangle className="h-4 w-4 inline mr-2" />
                  {error}
                </div>
              )}
            </div>
          )}

          {response && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Generated Response</h3>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setResponse(null)}>
                    Regenerate
                  </Button>
                  <Button onClick={() => navigator.clipboard.writeText(response)}>
                    Copy to Clipboard
                  </Button>
                </div>
              </div>
              <div className="bg-muted/30 p-6 rounded-lg border prose max-w-none dark:prose-invert">
                <pre className="whitespace-pre-wrap font-sans">{response}</pre>
              </div>
            </div>
          )}
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
  const [extracting, setExtracting] = useState(false);
  const [extractionMessage, setExtractionMessage] = useState<{type: 'success' | 'error' | 'info', text: string} | null>(null);
  
  const filteredRequirements = filter === 'ALL' 
    ? requirements 
    : requirements.filter(r => r.requirement_type === filter);

  const [matrixData, setMatrixData] = useState<any[]>([]);

  // Calculate counts for each requirement type
  const requirementCounts = useMemo(() => {
    const counts: Record<string, number> = {
      ALL: requirements.length,
      TECHNICAL: 0,
      MANAGEMENT: 0,
      PAST_PERFORMANCE: 0,
      PRICING: 0,
      CERTIFICATION: 0,
      OTHER: 0,
    };
    
    requirements.forEach(req => {
      const type = req.requirement_type;
      if (counts[type] !== undefined) {
        counts[type]++;
      } else {
        counts.OTHER++;
      }
    });
    
    return counts;
  }, [requirements]);

  const requirementTypes = [
    { key: 'ALL', label: 'All', color: 'bg-slate-100 text-slate-700 border-slate-300' },
    { key: 'TECHNICAL', label: 'Technical', color: 'bg-blue-100 text-blue-700 border-blue-300' },
    { key: 'MANAGEMENT', label: 'Management', color: 'bg-purple-100 text-purple-700 border-purple-300' },
    { key: 'PAST_PERFORMANCE', label: 'Past Performance', color: 'bg-green-100 text-green-700 border-green-300' },
    { key: 'PRICING', label: 'Pricing', color: 'bg-orange-100 text-orange-700 border-orange-300' },
    { key: 'CERTIFICATION', label: 'Certification', color: 'bg-red-100 text-red-700 border-red-300' },
    { key: 'OTHER', label: 'Other', color: 'bg-gray-100 text-gray-700 border-gray-300' },
  ];

  const handleGenerateMatrix = async () => {
    setGenerating(true);
    setExtractionMessage(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/proposals/${proposalId}/generate-requirements-matrix`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setMatrixData(data.content);
        setExtractionMessage({type: 'success', text: 'Requirements matrix generated successfully!'});
      } else {
        const errorData = await res.json().catch(() => ({}));
        setExtractionMessage({type: 'error', text: `Failed to generate matrix: ${errorData.detail || errorData.message || 'Unknown error'}`});
      }
    } catch (error) {
      console.error("Generation failed:", error);
      setExtractionMessage({type: 'error', text: 'An error occurred during generation.'});
    } finally {
      setGenerating(false);
    }
  };

  const downloadCSV = () => {
    if (!matrixData || matrixData.length === 0) return;

    const headers = ["ID", "Requirement Summary", "Source", "Proposal Section", "Compliance", "Notes"];
    const csvContent = [
      headers.join(","),
      ...matrixData.map(row => [
        `"${row.id}"`,
        `"${(row.summary || '').replace(/"/g, '""')}"`,
        `"${(row.source || '').replace(/"/g, '""')}"`,
        `"${(row.proposal_section || '').replace(/"/g, '""')}"`,
        `"${(row.compliance || '').replace(/"/g, '""')}"`,
        `"${(row.notes || '').replace(/"/g, '""')}"`
      ].join(","))
    ].join("\n");

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `requirements_matrix_${proposalId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExtractRequirements = async () => {
    setExtracting(true);
    setExtractionMessage(null);
    
    try {
      // Start the extraction
      const res = await fetch(`${API_URL}/api/v1/proposals/${proposalId}/extract-requirements`, {
        method: 'POST'
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        setExtractionMessage({type: 'error', text: `Failed to start extraction: ${errorData.detail || errorData.message || 'Unknown error'}`});
        setExtracting(false);
        return;
      }
      
      const startData = await res.json();
      
      if (startData.status === 'already_running') {
        setExtractionMessage({type: 'info', text: 'Extraction is already in progress. Checking status...'});
      } else {
        setExtractionMessage({type: 'info', text: 'Extraction started. Processing documents...'});
      }
      
      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const progressRes = await fetch(`${API_URL}/api/v1/proposals/${proposalId}/extract-requirements/progress`);
          if (progressRes.ok) {
            const progress = await progressRes.json();
            
            if (progress.status === 'running') {
              // Update message with current progress
              const fileList = progress.filenames.length > 0 
                ? '\n\nProcessed files:\n' + progress.filenames.map((f: string) => `  • ${f}`).join('\n')
                : '';
              
              setExtractionMessage({
                type: 'info',
                text: `Extracting requirements... ${progress.percentage}%\n\nCurrent file: ${progress.current_file || 'Initializing...'}\nProcessed: ${progress.processed_files} / ${progress.total_files} files${fileList}`
              });
            } else if (progress.status === 'completed') {
              clearInterval(pollInterval);
              setExtracting(false);
              
              if (progress.requirements_count > 0) {
                setExtractionMessage({
                  type: 'success',
                  text: `Requirements extraction completed! Found ${progress.requirements_count} requirements and ${progress.artifacts_count} artifacts from ${progress.total_files} document(s). Reloading page...`
                });
                // Reload page to show new requirements
                setTimeout(() => window.location.reload(), 2000);
              } else {
                setExtractionMessage({
                  type: 'error',
                  text: `Extraction completed but found 0 requirements.\n\nProcessed ${progress.total_files} document(s). The documents may not contain standard requirement language, or AI extraction may have failed to identify requirements.`
                });
              }
            } else if (progress.status === 'failed') {
              clearInterval(pollInterval);
              setExtracting(false);
              setExtractionMessage({
                type: 'error',
                text: `Extraction failed: ${progress.error || 'Unknown error'}`
              });
            }
          }
        } catch (error) {
          console.error('Error polling progress:', error);
        }
      }, 2000); // Poll every 2 seconds
      
      // Cleanup interval after 5 minutes (safety timeout)
      setTimeout(() => {
        clearInterval(pollInterval);
        if (extracting) {
          setExtracting(false);
          setExtractionMessage({
            type: 'error',
            text: 'Extraction timed out. Please try again or check the logs.'
          });
        }
      }, 300000); // 5 minutes
      
    } catch (error) {
      console.error("Extraction failed:", error);
      setExtractionMessage({type: 'error', text: 'An error occurred during extraction.'});
      setExtracting(false);
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
                className="gap-2"
              >
                {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 text-purple-500" />}
                Generate Matrix
              </Button>
              <Button 
                onClick={handleExtractRequirements} 
                disabled={extracting} 
                variant="outline"
                size="sm"
                className="gap-2"
              >
                {extracting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileCode className="h-4 w-4" />}
                Re-extract
              </Button>
            </div>
          </div>
          
          {/* Requirement Type Filters */}
          <div className="flex flex-wrap gap-2 mt-4">
            {requirementTypes.map((type) => {
              const count = requirementCounts[type.key] || 0;
              const isActive = filter === type.key;
              
              return (
                <button
                  key={type.key}
                  onClick={() => setFilter(type.key)}
                  className={cn(
                    "inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all",
                    "border hover:shadow-sm",
                    isActive 
                      ? cn(type.color, "shadow-sm ring-2 ring-offset-1", 
                          type.key === 'ALL' ? 'ring-slate-400' :
                          type.key === 'TECHNICAL' ? 'ring-blue-400' :
                          type.key === 'MANAGEMENT' ? 'ring-purple-400' :
                          type.key === 'PAST_PERFORMANCE' ? 'ring-green-400' :
                          type.key === 'PRICING' ? 'ring-orange-400' :
                          type.key === 'CERTIFICATION' ? 'ring-red-400' :
                          'ring-gray-400'
                        )
                      : "bg-background border-border text-muted-foreground hover:bg-muted"
                  )}
                >
                  <span>{type.label}</span>
                  <Badge 
                    variant="secondary" 
                    className={cn(
                      "ml-1 px-1.5 py-0 text-xs font-semibold",
                      isActive ? "bg-white/40" : "bg-muted"
                    )}
                  >
                    {count}
                  </Badge>
                </button>
              );
            })}
          </div>
        </CardHeader>
        <CardContent>
          {extractionMessage && (
            <Card className={cn(
              "mb-4 border-l-4",
              extractionMessage.type === 'success' && "border-l-green-500 bg-green-50 dark:bg-green-950",
              extractionMessage.type === 'error' && "border-l-red-500 bg-red-50 dark:bg-red-950",
              extractionMessage.type === 'info' && "border-l-blue-500 bg-blue-50 dark:bg-blue-950"
            )}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  {extractionMessage.type === 'success' && <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />}
                  {extractionMessage.type === 'error' && <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />}
                  {extractionMessage.type === 'info' && <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />}
                  <p className="text-sm whitespace-pre-line">{extractionMessage.text}</p>
                </div>
              </CardContent>
            </Card>
          )}
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

      {matrixData.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Generated Compliance Matrix</CardTitle>
                <CardDescription>AI-generated compliance matrix based on requirements</CardDescription>
              </div>
              <Button onClick={downloadCSV} variant="outline" size="sm" className="gap-2">
                <FileText className="h-4 w-4" />
                Download CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr className="border-b">
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground w-24">ID</th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Requirement</th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground w-24">Source</th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground w-48">Proposal Section</th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground w-32">Compliance</th>
                      <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {matrixData.map((row, i) => (
                      <tr key={i} className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                        <td className="p-4 align-middle font-mono text-xs">{row.id}</td>
                        <td className="p-4 align-middle">{row.summary}</td>
                        <td className="p-4 align-middle">{row.source}</td>
                        <td className="p-4 align-middle">{row.proposal_section}</td>
                        <td className="p-4 align-middle">
                          <Badge variant={
                            row.compliance === 'Compliant' ? 'default' : 
                            row.compliance === 'Non-Compliant' ? 'destructive' : 'secondary'
                          }>
                            {row.compliance}
                          </Badge>
                        </td>
                        <td className="p-4 align-middle text-muted-foreground">{row.notes}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
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
      console.log('Fetched content:', data);
      if (data.volumes) {
        data.volumes.forEach((v: any) => {
          console.log(`Volume ${v.id} blocks:`, v.blocks);
        });
      }
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
function ArtifactsTab({ artifacts: initialArtifacts, proposalId }: { artifacts: Artifact[], proposalId: number }) {
  const [artifacts, setArtifacts] = useState<Artifact[]>(initialArtifacts);
  const [uploading, setUploading] = useState<number | null>(null);
  
  useEffect(() => {
    setArtifacts(initialArtifacts);
  }, [initialArtifacts]);
  
  const getStatusColor = (status: string) => {
    if (status === 'COMPLETE') return 'bg-green-100 text-green-700 border-green-300';
    if (status === 'IN_PROGRESS') return 'bg-blue-100 text-blue-700 border-blue-300';
    return 'bg-gray-100 text-gray-700 border-gray-300';
  };
  
  const handleFileUpload = async (artifactId: number, file: File) => {
    setUploading(artifactId);
    
    try {
      // Step 1: Upload file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('opportunity_id', String(proposalId)); // Using proposal_id as fallback
      
      const uploadRes = await fetch('/api/v1/files/upload', {
        method: 'POST',
        body: formData
      });
      
      if (!uploadRes.ok) {
        throw new Error('File upload failed');
      }
      
      const uploadData = await uploadRes.json();
      const fileId = uploadData.id;
      
      // Step 2: Update artifact with file_id
      const updateRes = await fetch(`/api/v1/requirements/proposals/${proposalId}/artifacts/${artifactId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'COMPLETE',
          file_id: fileId
        })
      });
      
      if (!updateRes.ok) {
        throw new Error('Artifact update failed');
      }
      
      // Update local state
      setArtifacts(prev => prev.map(art => 
        art.id === artifactId 
          ? { ...art, status: 'COMPLETE', file_id: fileId }
          : art
      ));
      
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setUploading(null);
    }
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
                    <div className="space-y-2 flex-1">
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
                      
                      {/* File Upload Section */}
                      <div className="flex items-center gap-2 mt-3">
                        {art.file_id ? (
                          <div className="flex items-center gap-2 text-sm text-green-600">
                            <FileText className="h-4 w-4" />
                            <span>File attached</span>
                          </div>
                        ) : (
                          <label className="cursor-pointer">
                            <input
                              type="file"
                              className="hidden"
                              onChange={(e) => {
                                const file = e.target.files?.[0];
                                if (file) {
                                  handleFileUpload(art.id, file);
                                }
                              }}
                              disabled={uploading === art.id}
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={uploading === art.id}
                              onClick={(e) => {
                                const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                                input?.click();
                              }}
                            >
                              {uploading === art.id ? (
                                <>
                                  <Clock className="h-4 w-4 mr-2 animate-spin" />
                                  Uploading...
                                </>
                              ) : (
                                <>
                                  <FileText className="h-4 w-4 mr-2" />
                                  Upload File
                                </>
                              )}
                            </Button>
                          </label>
                        )}
                      </div>
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
