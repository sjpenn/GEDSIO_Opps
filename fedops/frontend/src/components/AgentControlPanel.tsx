import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';

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
    try {
      const scoreRes = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/score`);
      if (scoreRes.ok) {
        setScore(await scoreRes.json());
      }
      
      const logsRes = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/logs`);
      if (logsRes.ok) {
        setLogs(await logsRes.json());
      }
      
      const propRes = await fetch(`${API_URL}/api/v1/proposals/${opportunityId}`);
      if (propRes.ok) {
        const propData = await propRes.json();
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
        await fetchData();
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
      case 'GO': return 'bg-green-500';
      case 'NO_GO': return 'bg-red-500';
      case 'REVIEW': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const activeVolume = proposal?.volumes.find(v => v.id === activeVolumeId);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Agentic Analysis</h3>
        <Button onClick={handleAnalyze} disabled={loading}>
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {score ? 'Re-Analyze' : 'Start Analysis'}
        </Button>
      </div>

      {score && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex justify-between items-center">
              <span>Weighted Score: {score.weighted_score.toFixed(1)}</span>
              <Badge className={getDecisionColor(score.go_no_go_decision)}>
                {score.go_no_go_decision}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>Strategic Alignment: {score.strategic_alignment_score.toFixed(1)}</div>
              <div>Financial Viability: {score.financial_viability_score.toFixed(1)}</div>
              <div>Contract Risk: {score.contract_risk_score.toFixed(1)}</div>
              <div>Internal Capacity: {score.internal_capacity_score.toFixed(1)}</div>
            </div>
            
            {score.go_no_go_decision === 'GO' && (
               <div className="mt-4">
                 <Button onClick={handleGenerateProposal} variant="outline" className="w-full">
                   {proposal ? 'Regenerate Proposal' : 'Generate Proposal Draft'}
                 </Button>
               </div>
            )}
          </CardContent>
        </Card>
      )}
      
      {proposal && (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Proposal Documents</h3>
                <span className="text-xs text-muted-foreground">Version {proposal.version}</span>
            </div>
            
            {/* Volume Tabs */}
            <div className="flex space-x-2 border-b pb-2 overflow-x-auto">
                {proposal.volumes.sort((a, b) => a.order - b.order).map(vol => (
                    <button
                        key={vol.id}
                        onClick={() => setActiveVolumeId(vol.id)}
                        className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                            activeVolumeId === vol.id 
                            ? 'bg-primary text-primary-foreground' 
                            : 'hover:bg-muted text-muted-foreground'
                        }`}
                    >
                        {vol.title}
                    </button>
                ))}
            </div>

            {/* Active Volume Content */}
            {activeVolume && (
                <div className="space-y-3">
                    {activeVolume.blocks.sort((a, b) => a.order - b.order).map(block => (
                        <Card key={block.id}>
                            <CardHeader className="py-3 bg-muted/20">
                                <div className="flex justify-between items-center">
                                    <h5 className="font-medium text-sm">{block.title}</h5>
                                    {editingBlock !== block.id && (
                                        <Button variant="outline" size="sm" onClick={() => startEdit(block)}>Edit</Button>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent className="p-4">
                                {editingBlock === block.id ? (
                                    <div className="space-y-2">
                                        <textarea 
                                            className="w-full min-h-[200px] p-3 border rounded-md font-mono text-sm"
                                            value={editContent}
                                            onChange={(e) => setEditContent(e.target.value)}
                                        />
                                        <div className="flex gap-2 justify-end">
                                            <Button variant="outline" size="sm" onClick={() => setEditingBlock(null)}>Cancel</Button>
                                            <Button size="sm" onClick={() => saveBlock(block.id)}>Save</Button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="whitespace-pre-wrap text-sm">{block.content}</div>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Activity Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[200px] w-full rounded-md border p-4">
            <div className="space-y-2">
              {logs.map((log) => (
                <div key={log.id} className="flex items-start space-x-2 text-sm">
                  {log.status === 'SUCCESS' ? <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" /> : 
                   log.status === 'FAILURE' ? <XCircle className="h-4 w-4 text-red-500 mt-0.5" /> :
                   <Loader2 className="h-4 w-4 animate-spin text-blue-500 mt-0.5" />}
                  <div>
                    <span className="font-semibold">{log.agent_name}:</span> {log.action}
                    <div className="text-xs text-muted-foreground">{new Date(log.timestamp).toLocaleString()}</div>
                  </div>
                </div>
              ))}
              {logs.length === 0 && <div className="text-muted-foreground text-center">No logs yet.</div>}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
