import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Calendar, CheckCircle, Target, FileText, Star, Archive, ArchiveRestore } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { cn } from "@/lib/utils";
import { ShipleyPhaseBadge } from '@/components/ShipleyPhaseIndicator';

interface PipelineItem {
  pipeline: {
    id: number;
    opportunity_id: number;
    status: string;
    stage: string;
    questions_due_date: string | null;
    proposal_due_date: string | null;
    submission_instructions: string | null;
    notes: string | null;
    archived: boolean;
    archived_at: string | null;
    archived_by: string | null;
  };
  opportunity: {
    id: number;
    title: string;
    notice_id: string;
    department: string;
    response_deadline: string;
    type: string;
  };
  proposal: {
    id: number;
    shipley_phase: string;
    capture_manager_id: string | null;
    bid_decision_score: number | null;
  } | null;
  score: {
    weighted_score: number | null;
    go_no_go_decision: string | null;
  } | null;
  display_score: number | null;
  score_source: string | null;
}

// Notice type color mapping
const getNoticeTypeStyle = (type: string): { bg: string; text: string } => {
  const lowerType = type.toLowerCase();
  
  if (lowerType.includes('sources sought') || lowerType.includes('rfi')) {
    return { bg: 'bg-cyan-600', text: 'text-white' };
  } else if (lowerType.includes('presolicitation') || lowerType.includes('pre-solicitation')) {
    return { bg: 'bg-amber-600', text: 'text-white' };
  } else if (lowerType.includes('solicitation') && !lowerType.includes('pre')) {
    return { bg: 'bg-emerald-600', text: 'text-white' };
  } else if (lowerType.includes('award')) {
    return { bg: 'bg-purple-600', text: 'text-white' };
  } else if (lowerType.includes('combined synopsis')) {
    return { bg: 'bg-indigo-600', text: 'text-white' };
  } else {
    return { bg: 'bg-slate-600', text: 'text-white' };
  }
};

const STAGES = {
  'QUALIFICATION': { label: 'Qualification', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  'PROPOSAL_DEV': { label: 'Proposal Dev', color: 'bg-purple-100 text-purple-800 border-purple-200' },
  'REVIEW': { label: 'Review', color: 'bg-orange-100 text-orange-800 border-orange-200' },
  'SUBMISSION': { label: 'Submission', color: 'bg-green-100 text-green-800 border-green-200' }
};

export default function PipelinePage() {
  const [items, setItems] = useState<PipelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showArchived, setShowArchived] = useState(false);
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPipeline();
  }, []);

  const fetchPipeline = async () => {
    try {
      const endpoint = showArchived ? '/api/v1/pipeline/archived' : '/api/v1/pipeline/';
      const res = await fetch(endpoint);
      if (res.ok) {
        const data = await res.json();
        setItems(data);
      }
    } catch (error) {
      console.error("Failed to fetch pipeline", error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysRemaining = (dateStr: string | null) => {
    if (!dateStr) return null;
    const due = new Date(dateStr);
    const now = new Date();
    const diff = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const handleArchive = async (opportunityId: number) => {
    try {
      const res = await fetch(`/api/v1/pipeline/${opportunityId}/archive`, { method: 'POST' });
      if (res.ok) {
        fetchPipeline();
      }
    } catch (error) {
      console.error("Failed to archive", error);
    }
  };

  const handleUnarchive = async (opportunityId: number) => {
    try {
      const res = await fetch(`/api/v1/pipeline/${opportunityId}/unarchive`, { method: 'POST' });
      if (res.ok) {
        fetchPipeline();
      }
    } catch (error) {
      console.error("Failed to unarchive", error);
    }
  };

  const handleRerunAnalysis = async (opportunityId: number) => {
    setAnalyzingId(opportunityId);
    try {
      const res = await fetch(`/api/v1/agents/opportunities/${opportunityId}/analyze`, { 
        method: 'POST' 
      });
      if (res.ok) {
        await fetchPipeline(); // Refresh to get updated scores
        alert('Analysis completed successfully!');
      } else {
        const errorText = await res.text();
        alert(`Analysis failed: ${errorText}`);
      }
    } catch (error) {
      console.error("Failed to run analysis", error);
      alert("An error occurred while running analysis.");
    } finally {
      setAnalyzingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Pipeline Dashboard</h2>
          <p className="text-muted-foreground">Track and manage your active opportunities.</p>
        </div>
        <Button 
          variant={showArchived ? "default" : "outline"}
          onClick={() => {
            setShowArchived(!showArchived);
            setLoading(true);
          }}
        >
          {showArchived ? <ArchiveRestore className="h-4 w-4 mr-2" /> : <Archive className="h-4 w-4 mr-2" />}
          {showArchived ? 'Show Active' : 'Show Archived'}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Object.entries(STAGES).map(([stageKey, stageConfig]) => (
          <div key={stageKey} className="space-y-4">
            <div className={cn("p-3 rounded-lg border font-semibold text-center", stageConfig.color)}>
              {stageConfig.label}
              <Badge variant="secondary" className="ml-2 bg-white/50 text-inherit border-0">
                {items.filter(i => i.pipeline.stage === stageKey).length}
              </Badge>
            </div>
            
            <div className="space-y-3">
              {items
                .filter(i => i.pipeline.stage === stageKey)
                .map(item => {
                  const daysLeft = getDaysRemaining(item.pipeline.proposal_due_date || item.opportunity.response_deadline);
                  const noticeStyle = getNoticeTypeStyle(item.opportunity.type);
                  return (
                    <Card 
                      key={item.pipeline.id} 
                      className="transition-all border-l-4 border-l-primary/20 hover:border-l-primary hover:shadow-md cursor-pointer overflow-hidden"
                    >
                      {/* Notice Type Bar */}
                      <div className={cn("px-2 py-0.5 text-[10px] font-semibold text-center", noticeStyle.bg, noticeStyle.text)}>
                        {item.opportunity.type}
                      </div>
                      
                      <CardContent className="p-4 space-y-3">
                        <div className="min-w-0">
                          <div className="flex justify-between items-start gap-2 mb-1">
                            <Badge variant="outline" className="text-[10px] font-mono truncate max-w-[60%]" title={item.opportunity.notice_id}>
                              {item.opportunity.notice_id}
                            </Badge>
                            {daysLeft !== null && (
                              <Badge variant={daysLeft < 5 ? "destructive" : "secondary"} className="text-[10px] shrink-0">
                                {daysLeft} days left
                              </Badge>
                            )}
                          </div>
                          <h4 className="font-semibold text-sm line-clamp-2 break-words" title={item.opportunity.title}>
                            <Link 
                              to={`/opportunities/${item.opportunity.id}`}
                              className="hover:underline hover:text-primary transition-colors"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {item.opportunity.title}
                            </Link>
                          </h4>
                          <p className="text-xs text-muted-foreground mt-1 truncate">{item.opportunity.department}</p>
                        </div>
                        
                        {/* Shipley Phase Indicator */}
                        {item.proposal && item.proposal.shipley_phase && (
                          <div className="flex items-center gap-2 min-w-0">
                            <Target className="h-3 w-3 text-blue-600 shrink-0" />
                            <div className="min-w-0 overflow-hidden">
                              <ShipleyPhaseBadge currentPhase={item.proposal.shipley_phase} />
                            </div>
                          </div>
                        )}
                        
                        {/* Display Score - prioritizes bid decision score */}
                        {item.display_score !== null && (
                          <div className="flex items-center gap-2">
                            <Star className="h-3 w-3 text-amber-500 fill-amber-500 shrink-0" />
                            <Badge 
                              variant={
                                item.display_score >= 70 ? "default" : 
                                item.display_score >= 50 ? "secondary" : 
                                "destructive"
                              }
                              className="text-[10px]"
                              title={item.score_source === 'bid_decision' ? 'Official Bid Decision Score' : 'Automated Analysis Score'}
                            >
                              {item.score_source === 'bid_decision' ? '✓ ' : ''}Score: {item.display_score.toFixed(1)}
                            </Badge>
                          </div>
                        )}
                        
                        <div className="pt-2 border-t flex justify-between items-center text-xs text-muted-foreground min-w-0">
                          <div className="flex items-center gap-1 min-w-0">
                            <Calendar className="h-3 w-3 shrink-0" />
                            <span className="truncate">
                              {new Date(item.pipeline.proposal_due_date || item.opportunity.response_deadline).toLocaleDateString()}
                            </span>
                          </div>
                          {item.pipeline.status === 'GO' && <CheckCircle className="h-3 w-3 text-green-500 shrink-0" />}
                        </div>
                        
                        {/* Action Buttons */}
                        <div className="flex flex-col gap-2 pt-2">
                          {!showArchived && (
                            <>
                              <Button 
                                size="sm" 
                                variant="default" 
                                className="w-full text-xs"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleRerunAnalysis(item.opportunity.id);
                                }}
                                disabled={analyzingId === item.opportunity.id}
                              >
                                {analyzingId === item.opportunity.id ? (
                                  <>
                                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                    Analyzing...
                                  </>
                                ) : (
                                  'Re-Run Analysis'
                                )}
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="w-full text-xs"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/analysis/${item.opportunity.id}`);
                                }}
                              >
                                View Analysis
                              </Button>
                              {(!item.proposal || item.proposal.shipley_phase === 'PHASE_1_LONG_TERM_POSITIONING' || item.proposal.shipley_phase === 'PHASE_2_OPPORTUNITY_ASSESSMENT') && (
                                <Button 
                                  size="sm" 
                                  className="w-full text-xs bg-blue-600 hover:bg-blue-700"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    navigate(`/bid-decision/${item.opportunity.id}`);
                                  }}
                                >
                                  <Target className="h-3 w-3 mr-1" />
                                  Bid Decision
                                </Button>
                              )}
                              {item.proposal && item.proposal.id && (
                                <Button 
                                  asChild
                                  size="sm" 
                                  variant="default"
                                  className="w-full text-xs"
                                >
                                  <Link to={`/proposal-workspace/${item.opportunity.id}`}>
                                    <FileText className="h-3 w-3 mr-1" />
                                    Open Proposal
                                  </Link>
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                className="w-full text-xs text-muted-foreground hover:text-foreground"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleArchive(item.opportunity.id);
                                }}
                              >
                                <Archive className="h-3 w-3 mr-1" />
                                Archive
                              </Button>
                            </>
                          )}
                          {showArchived && (
                            <Button
                              size="sm"
                              variant="default"
                              className="w-full text-xs"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleUnarchive(item.opportunity.id);
                              }}
                            >
                              <ArchiveRestore className="h-3 w-3 mr-1" />
                              Restore
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
                
              {items.filter(i => i.pipeline.stage === stageKey).length === 0 && (
                <div className="text-center py-8 text-muted-foreground text-sm border-2 border-dashed rounded-lg">
                  No items
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
