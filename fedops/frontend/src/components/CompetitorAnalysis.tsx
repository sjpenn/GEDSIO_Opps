import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ExternalLink, Target, AlertTriangle, Trophy, Lightbulb, RefreshCw } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";

interface Citation {
  title: string;
  url: string;
  snippet?: string;
  date?: string;
}

interface Strength {
  description: string;
  evidence?: string;
  source_index?: number;
}

interface Weakness {
  description: string;
  evidence?: string;
  source_index?: number;
}

interface Strategy {
  strategy: string;
  rationale: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
}

interface CompetitiveAnalysis {
  id?: number;
  entity_name: string;
  entity_uei?: string;
  overview: string;
  market_position: string;
  strengths: Strength[];
  weaknesses: Weakness[];
  key_differentiators: string[];
  how_to_beat_them: Strategy[];
  citations: Citation[];
  analyzed_at: string;
  model_used?: string;
}

interface CompetitorAnalysisProps {
  entityName: string;
  onClose?: () => void;
}

export default function CompetitorAnalysis({ entityName, onClose }: CompetitorAnalysisProps) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<CompetitiveAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [context, setContext] = useState('');
  const [source, setSource] = useState<'cache' | 'fresh' | null>(null);

  const fetchAnalysis = async (forceRefresh = false) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/v1/competitive_intel/competitors/${encodeURIComponent(entityName)}/research`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            context: context || undefined,
            force_refresh: forceRefresh
          })
        }
      );
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to fetch analysis');
      }
      
      const data = await response.json();
      setAnalysis(data.analysis);
      setSource(data.source);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const priorityColors = {
    HIGH: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    LOW: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  };

  if (!analysis && !loading) {
    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Competitive Analysis
          </CardTitle>
          <CardDescription>
            Research "{entityName}" to generate a competitive intelligence report
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Additional Context (optional)</label>
            <Textarea
              placeholder="e.g., defense contractor, IT modernization, cloud services..."
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={2}
            />
          </div>
          
          {error && (
            <div className="text-red-600 text-sm bg-red-50 dark:bg-red-950 p-3 rounded-md">
              {error}
            </div>
          )}
          
          <Button onClick={() => fetchAnalysis()} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Researching...
              </>
            ) : (
              <>
                <Target className="mr-2 h-4 w-4" />
                Research Competitor
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className="mt-4">
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Researching {entityName}...</p>
            <p className="text-xs text-muted-foreground">This may take 15-30 seconds</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4 mt-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Target className="h-5 w-5" />
            Competitive Analysis: {analysis?.entity_name}
          </h3>
          {source && (
            <Badge variant="outline" className="mt-1">
              {source === 'cache' ? 'From Cache' : 'Fresh Research'}
            </Badge>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => fetchAnalysis(true)}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </div>

      {/* Overview */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{analysis?.overview}</p>
          <p className="text-sm mt-2"><strong>Market Position:</strong> {analysis?.market_position}</p>
        </CardContent>
      </Card>

      {/* Strengths & Weaknesses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Strengths */}
        <Card className="border-green-200 dark:border-green-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2 text-green-700 dark:text-green-400">
              <Trophy className="h-4 w-4" />
              Strengths ({analysis?.strengths.length || 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {analysis?.strengths.map((s, i) => (
                <li key={i} className="text-sm">
                  <p className="font-medium">{s.description}</p>
                  {s.evidence && (
                    <p className="text-xs text-muted-foreground mt-1">{s.evidence}</p>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Weaknesses */}
        <Card className="border-red-200 dark:border-red-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2 text-red-700 dark:text-red-400">
              <AlertTriangle className="h-4 w-4" />
              Weaknesses ({analysis?.weaknesses.length || 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {analysis?.weaknesses.map((w, i) => (
                <li key={i} className="text-sm">
                  <p className="font-medium">{w.description}</p>
                  {w.evidence && (
                    <p className="text-xs text-muted-foreground mt-1">{w.evidence}</p>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Key Differentiators */}
      {analysis?.key_differentiators && analysis.key_differentiators.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Key Differentiators</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {analysis.key_differentiators.map((d, i) => (
                <Badge key={i} variant="secondary">{d}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* How to Beat Them */}
      <Card className="border-blue-200 dark:border-blue-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2 text-blue-700 dark:text-blue-400">
            <Lightbulb className="h-4 w-4" />
            Strategies to Win Against Them
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-4">
            {analysis?.how_to_beat_them.map((s, i) => (
              <li key={i} className="border-b border-border pb-3 last:border-0 last:pb-0">
                <div className="flex items-start gap-2">
                  <Badge className={priorityColors[s.priority] || priorityColors.MEDIUM}>
                    {s.priority}
                  </Badge>
                  <div>
                    <p className="font-medium text-sm">{s.strategy}</p>
                    <p className="text-xs text-muted-foreground mt-1">{s.rationale}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Citations */}
      {analysis?.citations && analysis.citations.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Research Sources ({analysis.citations.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {analysis.citations.map((c, i) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="text-muted-foreground">[{i + 1}]</span>
                  <div className="flex-1">
                    <a 
                      href={c.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline flex items-center gap-1"
                    >
                      {c.title}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                    {c.snippet && (
                      <p className="text-xs text-muted-foreground mt-0.5">{c.snippet}</p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Metadata */}
      <p className="text-xs text-muted-foreground text-right">
        Analyzed at: {analysis?.analyzed_at ? new Date(analysis.analyzed_at).toLocaleString() : 'N/A'}
        {analysis?.model_used && ` | Model: ${analysis.model_used}`}
      </p>
    </div>
  );
}
