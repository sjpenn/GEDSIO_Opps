import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, CheckCircle, XCircle, Play, FileText, Activity, Clock, ExternalLink } from 'lucide-react';
import { cn } from "@/lib/utils"
import { useToast } from '@/components/ui/toast';

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

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function AgentControlPanel({ opportunityId }: AgentControlPanelProps) {
  const [loading, setLoading] = useState(false);
  const [score, setScore] = useState<ScoreData | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [analysisStartTime, setAnalysisStartTime] = useState<number | null>(null);
  const toast = useToast();

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
    } catch (error) {
      console.error("Failed to fetch agent data", error);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opportunityId]);

  useEffect(() => {
    let interval: any;
    if (loading) {
      const pollLogs = async () => {
        try {
          const logsRes = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/logs`);
          if (logsRes.ok) {
            const logsData: LogEntry[] = await logsRes.json();
            setLogs(logsData);

            // Check for completion if we initiated a new analysis
            if (analysisStartTime) {
              const relevantLogs = logsData.filter(l => new Date(l.timestamp).getTime() > analysisStartTime);
              const completionLog = relevantLogs.find(l => l.action === 'END_WORKFLOW' && l.status === 'SUCCESS');
              const errorLog = relevantLogs.find(l => l.status === 'FAILURE' && (l.action === 'WORKFLOW_ERROR' || l.action === 'ANALYSIS_FAILED'));

              if (completionLog) {
                setLoading(false);
                setAnalysisStartTime(null);
                await fetchData(); // Refresh scores
                toast.success('Analysis completed successfully! Results updated.');
              } else if (errorLog) {
                setLoading(false);
                setAnalysisStartTime(null);
                const errMsg = typeof errorLog.details === 'object' ? errorLog.details.error : errorLog.details;
                toast.error(`Analysis failed: ${errMsg || 'Unknown error'}`);
              }
            }
          }
        } catch (e) {
          console.error("Error polling logs", e);
        }
      };

      pollLogs();
      interval = setInterval(pollLogs, 2000);
    }
    return () => clearInterval(interval);
  }, [loading, opportunityId, analysisStartTime]);

  const handleAnalyze = async () => {
    setLoading(true);
    setAnalysisStartTime(Date.now()); // Mark start time to track new logs

    try {
      const response = await fetch(`${API_URL}/api/v1/agents/opportunities/${opportunityId}/analyze`, {
        method: 'POST'
      });

      if (response.status === 202) {
        // Async analysis started. 
        // We keep loading=true and let the polling useEffect handle completion detection.
        console.log("Analysis started in background (202 Accepted)");
        return;
      }

      if (!response.ok) {
        setLoading(false);
        setAnalysisStartTime(null);
        const errorData = await response.text();
        console.error("Analysis failed:", response.status, errorData);
        toast.error(`Analysis failed: ${response.status} - ${errorData}`);
      } else {
        // Legacy synchronous 200 OK support
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchData();
        setLoading(false);
        setAnalysisStartTime(null);
        toast.success('Analysis completed successfully!');
      }
    } catch (error) {
      console.error("Analysis request failed", error);
      setLoading(false);
      setAnalysisStartTime(null);
      toast.error(`Analysis failed: ${error}`);
    }
  };

  const handleOpenProposalWorkspace = () => {
    window.open(`/proposal-workspace/${opportunityId}`, '_blank');
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'GO': return 'bg-green-500 hover:bg-green-600';
      case 'NO_GO': return 'bg-red-500 hover:bg-red-600';
      case 'REVIEW': return 'bg-yellow-500 hover:bg-yellow-600';
      default: return 'bg-gray-500 hover:bg-gray-600';
    }
  };

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

            <Button onClick={handleOpenProposalWorkspace} variant="secondary" className="w-full gap-2">
              <FileText className="h-4 w-4" />
              Open Proposal Workspace
            </Button>
          </CardContent>
        </Card>
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
                  {loading ? (
                    <div className="flex flex-col items-center gap-2">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                      <span>Initializing analysis agents... this may take 2-3 minutes.</span>
                    </div>
                  ) : (
                    "No activity logs recorded yet."
                  )}
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
