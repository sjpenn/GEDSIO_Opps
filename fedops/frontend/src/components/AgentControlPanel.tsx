
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, CheckCircle, XCircle, Play, FileText, Edit2, Save, X, Activity, Clock, ExternalLink } from 'lucide-react';
import { cn } from "@/lib/utils"

interface AgentControlPanelProps {
  opportunityId: number;
}

interface ScoreData {
  weighted_score: number;
  go_no_go_decision: string;
  strategic_alignment_score: number;
  financial_viability_score: number;
  contract_risk_score: number;
  internal_capacity_score: number;
  data_integrity_score: number;
}

interface LogEntry {
  id: number;
  agent_name: string;
  action: string;
  status: string;
  timestamp: string;
  details: any;
}

interface Block {
  id: string;
  title: string;
  content: string;
  order: number;
}

interface ProposalVolume {
  id: number;
  title: string;
  order: number;
  blocks: Block[];
}

interface Proposal {
  id: number;
  volumes: ProposalVolume[];
  version: number;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export function AgentControlPanel({ opportunityId }: AgentControlPanelProps) {
  const [loading, setLoading] = useState(false);
  const [score, setScore] = useState<ScoreData | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [activeVolumeId, setActiveVolumeId] = useState<number | null>(null);
  const [editingBlock, setEditingBlock] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");

  const fetchData = async () => {
    console.log('Fetching agent data for opportunity:', opportunityId);
    try {
      const scoreRes = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/score`);
      if (scoreRes.ok) {
        const scoreData = await scoreRes.json();
        console.log('Score data received:', scoreData);
        console.log('Setting score state with:', {
          weighted_score: scoreData.weighted_score,
          go_no_go_decision: scoreData.go_no_go_decision
        });
        setScore(scoreData);
        console.log('Score state updated');
      } else {
        console.log('Score not found (404 is normal if analysis not run yet)');
        setScore(null);
      }
      
      const logsRes = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/logs`);
      if (logsRes.ok) {
        const logsData = await logsRes.json();
        console.log('Logs data received:', logsData.length, 'entries');
        setLogs(logsData);
      }
      
      const propRes = await fetch(`${API_URL}/api/v1/proposals/${opportunityId}`);
      if (propRes.ok) {
        const propData = await propRes.json();
        console.log('Proposal data received');
        setProposal(propData);
        if (propData.volumes && propData.volumes.length > 0 && !activeVolumeId) {
            setActiveVolumeId(propData.volumes[0].id);
        }
      }
    } catch (error) {
      console.error("Failed to fetch agent data", error);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opportunityId]);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/analyze`, {
        method: 'POST'
      });
      if (!response.ok) {
        const errorData = await response.text();
        console.error("Analysis failed:", response.status, errorData);
        alert(`Analysis failed: ${response.status} - ${errorData}`);
      } else {
        // Give the backend a moment to commit all changes
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchData();
        alert('Analysis completed successfully! Scroll up to see the results card above.');
      }
    } catch (error) {
      console.error("Analysis failed", error);
      alert(`Analysis failed: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateProposal = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/proposals/generate/${opportunityId}`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setProposal(data.proposal);
        if (data.proposal.volumes && data.proposal.volumes.length > 0) {
            setActiveVolumeId(data.proposal.volumes[0].id);
        }
      } else {
        alert("Failed to generate proposal. Ensure decision is GO.");
      }
    } catch (error) {
      console.error("Proposal generation failed", error);
    }
  };

  const startEdit = (block: Block) => {
    setEditingBlock(block.id);
    setEditContent(block.content);
  };

  const saveBlock = async (blockId: string) => {
    if (!proposal || !activeVolumeId) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/proposals/${proposal.id}/volumes/${activeVolumeId}/blocks/${blockId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: editContent })
      });
      
      if (res.ok) {
        const data = await res.json();
        // Update local state
        const updatedVolumes = proposal.volumes.map(vol => {
            if (vol.id === activeVolumeId) {
                return { ...vol, blocks: data.blocks };
            }
            return vol;
        });
        setProposal({ ...proposal, volumes: updatedVolumes });
        setEditingBlock(null);
      }
    } catch (error) {
      console.error("Failed to save block", error);
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

  const activeVolume = proposal?.volumes.find(v => v.id === activeVolumeId);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">Agentic Analysis</h3>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={() => window.open(`/analysis/${opportunityId}`, '_blank')}
            variant="outline"
            disabled={!score}
            className="gap-2"
          >
            <ExternalLink className="h-4 w-4" />
            View Full Analysis
          </Button>
          <Button onClick={handleAnalyze} disabled={loading} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {score ? 'Re-Analyze Opportunity' : 'Start Analysis'}
          </Button>
        </div>
      </div>

      {score && (
        <Card className="border-l-4 border-l-primary">
          <CardHeader className="pb-4">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-xl">Analysis Results</CardTitle>
                <CardDescription>AI-driven assessment of this opportunity.</CardDescription>
              </div>
              <div className="flex flex-col items-end gap-1">
                <Badge className={cn("text-sm px-3 py-1", getDecisionColor(score.go_no_go_decision))}>
                  {score.go_no_go_decision}
                </Badge>
                <span className="text-xs text-muted-foreground font-mono">
                  Score: {score.weighted_score.toFixed(1)}/100
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-muted/30 p-3 rounded-lg border">
                <div className="text-xs text-muted-foreground uppercase font-medium mb-1">Strategic Alignment</div>
                <div className="text-lg font-bold">{score.strategic_alignment_score.toFixed(1)}</div>
              </div>
              <div className="bg-muted/30 p-3 rounded-lg border">
                <div className="text-xs text-muted-foreground uppercase font-medium mb-1">Financial Viability</div>
                <div className="text-lg font-bold">{score.financial_viability_score.toFixed(1)}</div>
              </div>
              <div className="bg-muted/30 p-3 rounded-lg border">
                <div className="text-xs text-muted-foreground uppercase font-medium mb-1">Contract Risk</div>
                <div className="text-lg font-bold">{score.contract_risk_score.toFixed(1)}</div>
              </div>
              <div className="bg-muted/30 p-3 rounded-lg border">
                <div className="text-xs text-muted-foreground uppercase font-medium mb-1">Internal Capacity</div>
                <div className="text-lg font-bold">{score.internal_capacity_score.toFixed(1)}</div>
              </div>
            </div>
            
            {score.go_no_go_decision === 'GO' && (
               <Button onClick={handleGenerateProposal} variant="secondary" className="w-full gap-2">
                 <FileText className="h-4 w-4" />
                 {proposal ? 'Regenerate Proposal Draft' : 'Generate Proposal Draft'}
               </Button>
            )}
          </CardContent>
        </Card>
      )}
      
      {proposal && (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <FileText className="h-5 w-5" /> Proposal Documents
                </h3>
                <Badge variant="outline">Version {proposal.version}</Badge>
            </div>
            
            <Card>
              <CardHeader className="pb-0">
                <div className="flex space-x-1 overflow-x-auto pb-2">
                    {proposal.volumes.sort((a, b) => a.order - b.order).map(vol => (
                        <Button
                            key={vol.id}
                            variant={activeVolumeId === vol.id ? "default" : "ghost"}
                            size="sm"
                            onClick={() => setActiveVolumeId(vol.id)}
                            className="rounded-b-none border-b-2 border-transparent data-[state=active]:border-primary"
                            data-state={activeVolumeId === vol.id ? "active" : "inactive"}
                        >
                            {vol.title}
                        </Button>
                    ))}
                </div>
              </CardHeader>
              <CardContent className="p-6 bg-muted/10 min-h-[400px]">
                {activeVolume && (
                    <div className="space-y-4">
                        {activeVolume.blocks.sort((a, b) => a.order - b.order).map(block => (
                            <Card key={block.id} className="shadow-sm">
                                <CardHeader className="py-3 px-4 bg-muted/30 flex flex-row items-center justify-between space-y-0">
                                    <h5 className="font-semibold text-sm">{block.title}</h5>
                                    {editingBlock !== block.id && (
                                        <Button variant="ghost" size="sm" onClick={() => startEdit(block)} className="h-8 w-8 p-0">
                                          <Edit2 className="h-4 w-4" />
                                        </Button>
                                    )}
                                </CardHeader>
                                <CardContent className="p-4">
                                    {editingBlock === block.id ? (
                                        <div className="space-y-3">
                                            <Textarea 
                                                className="min-h-[200px] font-mono text-sm leading-relaxed"
                                                value={editContent}
                                                onChange={(e) => setEditContent(e.target.value)}
                                            />
                                            <div className="flex gap-2 justify-end">
                                                <Button variant="ghost" size="sm" onClick={() => setEditingBlock(null)} className="gap-1">
                                                  <X className="h-4 w-4" /> Cancel
                                                </Button>
                                                <Button size="sm" onClick={() => saveBlock(block.id)} className="gap-1">
                                                  <Save className="h-4 w-4" /> Save Changes
                                                </Button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                                          {block.content || <span className="italic opacity-50">No content generated yet.</span>}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
              </CardContent>
            </Card>
        </div>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium uppercase text-muted-foreground">Activity Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[200px] w-full rounded-md border bg-muted/10 p-4">
            <div className="space-y-3">
              {logs.map((log) => (
                <div key={log.id} className="flex items-start gap-3 text-sm group">
                  <div className="mt-0.5">
                    {log.status === 'SUCCESS' ? <CheckCircle className="h-4 w-4 text-green-500" /> : 
                     log.status === 'FAILURE' ? <XCircle className="h-4 w-4 text-red-500" /> :
                     loading ? <Loader2 className="h-4 w-4 animate-spin text-blue-500" /> : 
                     <Clock className="h-4 w-4 text-muted-foreground" />}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex justify-between">
                      <span className="font-semibold text-foreground">{log.agent_name}</span>
                      <span className="text-xs text-muted-foreground font-mono">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-muted-foreground">{log.action}</p>
                  </div>
                </div>
              ))}
              {logs.length === 0 && (
                <div className="text-muted-foreground text-center py-8 text-sm italic">
                  No activity logs recorded yet.
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
