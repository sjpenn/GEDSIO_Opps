import { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ExternalLink, Target, AlertTriangle, Trophy, Lightbulb, RefreshCw, BarChart3, List, DollarSign } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

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

// Copy of Award interface from EntitySearch.tsx
export interface Award {
  "Award ID": string;
  "Recipient Name": string;
  "Description": string;
  "Award Amount": number;
  "Total Obligation"?: number;
  "Base and All Options Value"?: number;
  "Base Exercised Options Val"?: number;
  "Start Date"?: string;
  "End Date"?: string;
  "Current End Date"?: string;
  "Period of Performance Start Date"?: string;
  "Period of Performance Current End Date"?: string;
  "Last Modified Date"?: string;
  "Award Type"?: string;
  "Contract Award Type"?: string;
  "IDV Type"?: string;
  "Contract Pricing"?: string;
  "Type of Set Aside"?: string;
  "Extent Competed"?: string;
  "Awarding Agency": string;
  "Awarding Sub Agency"?: string;
  "Funding Agency"?: string;
  "Funding Sub Agency"?: string;
  "Place of Performance City Name"?: string;
  "Place of Performance State Code"?: string;
  "Place of Performance ZIP Code"?: string;
  "Place of Performance Country Code"?: string;
  "Recipient Address Line 1"?: string;
  "Recipient City Name"?: string;
  "Recipient State Code"?: string;
  "Recipient ZIP Code"?: string;
  "NAICS Code"?: string;
  "NAICS Description"?: string;
  "Product or Service Code"?: string;
  "Product or Service Code Description"?: string;
  "Solicitation ID"?: string;
  "Parent Award ID"?: string;
  "Referenced IDV Agency Identifier"?: string;
  "Contract Award Unique Key"?: string;
  "Recipient UEI"?: string;
  "Recipient DUNS Number"?: string;
  "Sub-Award Count"?: number;
  "Number of Offers Received"?: number;
  award_type?: string;
  "Prime Award ID"?: string;
  "Prime Recipient Name"?: string;
}

interface CompetitorAnalysisProps {
  entityName: string;
  onClose?: () => void;
  awards?: Award[];
}

export default function CompetitorAnalysis({ entityName, onClose, awards = [] }: CompetitorAnalysisProps) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<CompetitiveAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [context, setContext] = useState('');
  const [source, setSource] = useState<'cache' | 'fresh' | null>(null);
  const [opportunityCounts, setOpportunityCounts] = useState<Record<string, number>>({});

  // Compute NAICS Stats
  const naicsStats = useMemo(() => {
    if (!awards || awards.length === 0) return [];
    
    // Track stats including last used date
    const stats: Record<string, { code: string, description: string, count: number, value: number, last_used: string }> = {};
    
    awards.forEach(a => {
      const code = a["NAICS Code"] || "Unknown";
      const awardDate = a["Start Date"] || "";
      const description = a["NAICS Description"] || (code === "Unknown" ? "Unclassified / Sub-Awards" : "Unknown Analysis");

      if (!stats[code]) {
        stats[code] = { 
          code, 
          description, 
          count: 0, 
          value: 0,
          last_used: awardDate
        };
      }
      stats[code].count++;
      stats[code].value += a["Award Amount"] || 0;
      
      // Update last active date if newer
      if (awardDate && (!stats[code].last_used || new Date(awardDate) > new Date(stats[code].last_used))) {
        stats[code].last_used = awardDate;
      }
    });
    
    // Sort by Last Used Date Descending (Most Recent First)
    return Object.values(stats).sort((a, b) => {
      const dateA = a.last_used ? new Date(a.last_used).getTime() : 0;
      const dateB = b.last_used ? new Date(b.last_used).getTime() : 0;
      return dateB - dateA;
    });
  }, [awards]);

  // Compute Financial Estimates
  const financialStats = useMemo(() => {
    if (!awards || awards.length === 0) return { ttm: 0, avg3y: 0, avg5y: 0 };

    const now = new Date();
    const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
    const threeYearsAgo = new Date(now.getFullYear() - 3, now.getMonth(), now.getDate());
    const fiveYearsAgo = new Date(now.getFullYear() - 5, now.getMonth(), now.getDate());

    let sum1Y = 0;
    let sum3Y = 0;
    let sum5Y = 0;

    awards.forEach(a => {
      if (!a["Start Date"] || !a["Award Amount"]) return;
      
      const date = new Date(a["Start Date"]);
      const amount = a["Award Amount"];
      
      if (date >= oneYearAgo) {
        sum1Y += amount;
      }
      if (date >= threeYearsAgo) {
        sum3Y += amount;
      }
      if (date >= fiveYearsAgo) {
        sum5Y += amount;
      }
    });

    return {
      ttm: sum1Y,
      avg3y: sum3Y / 3, // Simple average over 3 years
      avg5y: sum5Y / 5  // Simple average over 5 years
    };
  }, [awards]);

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

  useEffect(() => {
    const fetchCounts = async () => {
        const codes = naicsStats.map(s => s.code).filter(c => c !== "Unknown");
        if (codes.length === 0) return;

        try {
            const res = await fetch('/api/v1/opportunities/stats/naics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ naics_codes: codes })
            });
            if (res.ok) {
                const data = await res.json();
                setOpportunityCounts(data);
            }
        } catch (e) {
            console.error("Failed to fetch NAICS stats", e);
        }
    };

    if (naicsStats.length > 0) {
        fetchCounts();
    }
  }, [naicsStats]);

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
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-semibold flex items-center gap-2">
            <Target className="h-5 w-5 text-purple-600" />
            Competitive Analysis: {analysis?.entity_name}
          </h3>
          <div className="flex gap-2 items-center mt-1">
            {source && (
              <Badge variant="outline" className="text-xs">
                {source === 'cache' ? 'Cached Result' : 'Fresh Research'}
              </Badge>
            )}
            <span className="text-xs text-muted-foreground">
              Analyzed: {analysis?.analyzed_at ? new Date(analysis.analyzed_at).toLocaleDateString() : 'N/A'}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => fetchAnalysis(true)}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Update
          </Button>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="detailed">Detailed Analysis</TabsTrigger>
          <TabsTrigger value="naics">NAICS Analysis</TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4 mt-4">
           {/* Financial Profile Card */}
           <Card className="bg-muted/10 border-muted">
              <CardHeader className="pb-2">
                 <CardTitle className="text-sm uppercase tracking-wide text-muted-foreground flex items-center gap-2">
                    <DollarSign className="h-4 w-4" /> Estimated Federal Revenue
                 </CardTitle>
              </CardHeader>
              <CardContent>
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <p className="text-xs text-muted-foreground font-medium mb-1">Last 12 Months</p>
                        <p className="text-2xl font-bold tracking-tight text-primary">
                            ${financialStats.ttm.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </p>
                        <p className="text-[10px] text-muted-foreground mt-1">Sum of awards in past year</p>
                    </div>
                    <div>
                        <p className="text-xs text-muted-foreground font-medium mb-1">3-Year Average</p>
                        <p className="text-2xl font-bold tracking-tight">
                            ${financialStats.avg3y.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </p>
                        <p className="text-[10px] text-muted-foreground mt-1">Avg annual revenue (3y)</p>
                    </div>
                    <div>
                        <p className="text-xs text-muted-foreground font-medium mb-1">5-Year Average</p>
                        <p className="text-2xl font-bold tracking-tight">
                            ${financialStats.avg5y.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </p>
                        <p className="text-[10px] text-muted-foreground mt-1">Avg annual revenue (5y)</p>
                    </div>
                 </div>
              </CardContent>
           </Card>

           {/* Executive Summary */}
           <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <List className="h-4 w-4" /> Executive Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
               <div className="bg-muted/30 p-4 rounded-md">
                 <p className="font-medium text-sm mb-1 text-primary">Overview</p>
                 <p className="text-sm text-muted-foreground leading-relaxed">{analysis?.overview}</p>
                 
                 <p className="font-medium text-sm mt-4 mb-1 text-primary">Market Position</p>
                 <p className="text-sm text-muted-foreground">{analysis?.market_position}</p>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                     <h4 className="text-xs font-semibold uppercase text-green-700 flex items-center gap-1">
                       <Trophy className="h-3 w-3" /> Key Strengths
                     </h4>
                     <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                       {analysis?.strengths.slice(0, 3).map((s, i) => (
                         <li key={i}><span className="text-foreground">{s.description}</span></li>
                       ))}
                     </ul>
                  </div>
                  <div className="space-y-2">
                     <h4 className="text-xs font-semibold uppercase text-red-700 flex items-center gap-1">
                       <AlertTriangle className="h-3 w-3" /> Key Weaknesses
                     </h4>
                     <ul className="list-disc list-inside text-sm space-y-1 text-muted-foreground">
                       {analysis?.weaknesses.slice(0, 3).map((w, i) => (
                         <li key={i}><span className="text-foreground">{w.description}</span></li>
                       ))}
                     </ul>
                  </div>
               </div>

               <div className="pt-2 border-t mt-2">
                 <h4 className="text-xs font-semibold uppercase text-blue-700 mb-2 flex items-center gap-1">
                    <Lightbulb className="h-3 w-3" /> Winning Strategy
                 </h4>
                 {analysis?.how_to_beat_them[0] && (
                    <div className="text-sm bg-blue-50 dark:bg-blue-950/30 p-3 rounded border border-blue-100 dark:border-blue-900">
                      <span className="font-semibold text-blue-800 dark:text-blue-300">Priority: {analysis.how_to_beat_them[0].priority}</span>
                      <p className="mt-1 font-medium">{analysis.how_to_beat_them[0].strategy}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{analysis.how_to_beat_them[0].rationale}</p>
                    </div>
                 )}
               </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Detailed Analysis Tab */}
        <TabsContent value="detailed" className="space-y-4 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strengths */}
            <Card className="border-green-200 dark:border-green-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2 text-green-700 dark:text-green-400">
                  <Trophy className="h-4 w-4" />
                  Strengths
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
                  Weaknesses
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
        </TabsContent>

        {/* NAICS Analysis Tab */}
        <TabsContent value="naics" className="space-y-6 mt-4">
             {naicsStats.length === 0 ? (
                 <div className="text-center py-8 text-muted-foreground border rounded-lg bg-muted/10">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No awards data available for NAICS analysis.</p>
                 </div>
             ) : (
                <>
                  <Card>
                    <CardHeader>
                       <CardTitle className="text-base">Core Competencies via NAICS</CardTitle>
                       <CardDescription>Analysis of recent awards by NAICS code (Sorted by Most Recent)</CardDescription>
                    </CardHeader>
                    <CardContent>
                         <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                            <div className="space-y-2">
                                <h4 className="text-sm font-semibold text-green-700 flex items-center gap-2">
                                   <Trophy className="h-4 w-4" /> Most Recently Active
                                </h4>
                                <p className="text-xs text-muted-foreground">NAICS codes with most recent activity</p>
                                <ul className="space-y-2 mt-2">
                                   {naicsStats.filter(s => s.code !== "Unknown").slice(0, 3).map((stat, i) => (
                                     <li key={i} className="text-sm border-l-2 border-green-500 pl-2">
                                        <div className="flex items-center gap-2">
                                            <p className="font-medium">{stat.code}</p>
                                            {opportunityCounts[stat.code] !== undefined && (
                                                <Badge variant="secondary" className="text-[10px] h-4 px-1 bg-muted-foreground/10 text-muted-foreground" title={`${opportunityCounts[stat.code]} active opportunities`}>
                                                    {opportunityCounts[stat.code]}
                                                </Badge>
                                            )}
                                        </div>
                                        <p className="text-xs truncate" title={stat.description}>{stat.description}</p>
                                        <p className="text-xs font-mono text-muted-foreground">
                                            Last: {stat.last_used ? new Date(stat.last_used).toLocaleDateString() : 'N/A'}
                                        </p>
                                     </li>
                                   ))}
                                   {naicsStats.filter(s => s.code !== "Unknown").length === 0 && (
                                     <li className="text-sm text-muted-foreground italic pl-2">No classified NAICS codes available.</li>
                                   )}
                                </ul>
                            </div>
                            <div className="space-y-2">
                                <h4 className="text-sm font-semibold text-blue-700 flex items-center gap-2">
                                   <BarChart3 className="h-4 w-4" /> Top Revenue Drivers
                                </h4>
                                <p className="text-xs text-muted-foreground">Highest total award value</p>
                                <ul className="space-y-2 mt-2">
                                   {[...naicsStats].sort((a,b) => b.value - a.value).filter(s => s.code !== "Unknown").slice(0, 3).map((stat, i) => (
                                     <li key={i} className="text-sm border-l-2 border-blue-500 pl-2">
                                        <div className="flex items-center gap-2">
                                            <p className="font-medium">{stat.code}</p>
                                            {opportunityCounts[stat.code] !== undefined && (
                                                <Badge variant="secondary" className="text-[10px] h-4 px-1 bg-muted-foreground/10 text-muted-foreground" title={`${opportunityCounts[stat.code]} active opportunities`}>
                                                    {opportunityCounts[stat.code]}
                                                </Badge>
                                            )}
                                        </div>
                                        <p className="text-xs truncate" title={stat.description}>{stat.description}</p>
                                        <p className="text-xs font-mono text-muted-foreground">${stat.value.toLocaleString()}</p>
                                     </li>
                                   ))}
                                   {naicsStats.filter(s => s.code !== "Unknown").length === 0 && (
                                     <li className="text-sm text-muted-foreground italic pl-2">No classified NAICS codes available.</li>
                                   )}
                                </ul>
                            </div>
                         </div>
                    </CardContent>
                  </Card>

                  <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">NAICS Breakdown (Most Recent First)</CardTitle>
                      </CardHeader>
                      <CardContent>
                         <Table>
                             <TableHeader>
                                 <TableRow>
                                     <TableHead>Code</TableHead>
                                     <TableHead>Description</TableHead>
                                     <TableHead>Last Active</TableHead>
                                     <TableHead className="text-right">Count</TableHead>
                                     <TableHead className="text-right">Total Value</TableHead>
                                 </TableRow>
                             </TableHeader>
                             <TableBody>
                                 {naicsStats.slice(0, 10).map((stat) => (
                                     <TableRow key={stat.code}>
                                         <TableCell className="font-mono text-xs font-medium">
                                            <div className="flex items-center gap-2">
                                                {stat.code}
                                                {opportunityCounts[stat.code] !== undefined && (
                                                    <Badge variant="secondary" className="text-[10px] h-4 px-1 bg-muted-foreground/10 text-muted-foreground" title={`${opportunityCounts[stat.code]} active opportunities`}>
                                                        {opportunityCounts[stat.code]}
                                                    </Badge>
                                                )}
                                            </div>
                                         </TableCell>
                                         <TableCell className="text-xs max-w-[200px] truncate" title={stat.description}>{stat.description}</TableCell>
                                         <TableCell className="text-xs">
                                             {stat.last_used ? new Date(stat.last_used).toLocaleDateString() : 'N/A'}
                                         </TableCell>
                                         <TableCell className="text-right text-xs">{stat.count}</TableCell>
                                         <TableCell className="text-right text-xs font-mono text-green-600">${stat.value.toLocaleString()}</TableCell>
                                     </TableRow>
                                 ))}
                             </TableBody>
                         </Table>
                         {naicsStats.length > 10 && (
                             <p className="text-xs text-muted-foreground text-center mt-2">Showing top 10 of {naicsStats.length} NAICS codes</p>
                         )}
                      </CardContent>
                  </Card>
                </>
             )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
