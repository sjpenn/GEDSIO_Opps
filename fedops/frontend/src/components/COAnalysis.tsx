import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Lightbulb, BarChart3, User, Briefcase, GraduationCap, ExternalLink, ChevronRight, Search, ArrowLeft } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface COResearch {
  co_name: string;
  agency?: string;
  overview: string;
  career_history: string[];
  education?: string;
  awarding_patterns?: string;
  preferred_vehicles: string[];
  citations: any[];
}

interface MiniAward {
  "Award ID": string;
  "Recipient Name": string;
  "Award Amount": number;
  "Start Date": string;
  "Description": string;
  "Awarding Agency": string;
}

interface MatchResult {
  name: string;
  agency: string;
  office?: string;
  role?: string;
  match_reason?: string;
  location?: string;
  overview?: string;
}

export default function COAnalysis() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  
  // State for flow
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<MatchResult | null>(null);
  const [analysis, setAnalysis] = useState<COResearch | null>(null);
  const [awards, setAwards] = useState<MiniAward[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query) return;
    setLoading(true);
    setError(null);
    setMatches([]);
    setSelectedMatch(null);
    setAnalysis(null);
    setAwards([]);

    try {
        console.log('[COAnalysis] Searching for:', query);
        const res = await fetch(`/api/v1/co_intel/search?q=${encodeURIComponent(query)}`);
        console.log('[COAnalysis] Response status:', res.status, res.statusText);
        
        if (!res.ok) throw new Error('Search failed');
        const data = await res.json();
        console.log('[COAnalysis] Response data:', data);
        console.log('[COAnalysis] Has matches?', data && data.matches);
        console.log('[COAnalysis] Matches length:', data?.matches?.length);
        
        if (data && data.matches && data.matches.length > 0) {
            console.log('[COAnalysis] Setting matches:', data.matches);
            setMatches(data.matches);
        } else {
            console.log('[COAnalysis] No matches found in response');
            setError('No potential matches found. Try a different name or agency.');
        }

    } catch (err) {
        console.error('[COAnalysis] Search error:', err);
        setError(err instanceof Error ? err.message : 'An error occurred during search');
    } finally {
        setLoading(false);
    }
  };

  const handleSelectMatch = async (match: MatchResult) => {
    setSelectedMatch(match);
    setLoading(true);
    setError(null);
    
    // Use the specific name and agency from the match for better research
    const researchQuery = {
        co_name: match.name,
        agency: match.agency
    };

    try {
      // Parallel fetch for deep research and award trends
      const researchPromise = fetch('/api/v1/co_intel/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(researchQuery)
      }).then(res => {
          if (!res.ok) throw new Error('Research failed');
          return res.json();
      });

      // Use the name for award search
      const awardsPromise = fetch(`/api/v1/co_intel/awards?q=${encodeURIComponent(match.name)}&limit=50`)
        .then(res => {
            if (!res.ok) return []; 
            return res.json();
        });

      const [researchData, awardsData] = await Promise.all([researchPromise, awardsPromise]);
      
      setAnalysis(researchData);
      setAwards(awardsData);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during detailed research');
    } finally {
      setLoading(false);
    }
  };

  const resetSearch = () => {
    setMatches([]);
    setSelectedMatch(null);
    setAnalysis(null);
    setAwards([]);
    setError(null);
  };

  // Prepare chart data from awards
  const agencyData = awards.length > 0 ? Object.entries(awards.reduce((acc, curr) => {
      const agency = curr["Awarding Agency"] || "Unknown";
      acc[agency] = (acc[agency] || 0) + (curr["Award Amount"] || 0);
      return acc;
  }, {} as Record<string, number>))
  .map(([name, value]) => ({ name, value }))
  .sort((a,b) => b.value - a.value)
  .slice(0, 5) : [];

  return (
    <div className="space-y-6">
            {/* Search Input Area */}
      {!selectedMatch && (
        <div className="space-y-4">
             <div className="flex gap-4 items-end">
                <div className="flex-1">
                <label className="text-sm font-medium mb-2 block">Search Contracting Professional</label>
                <div className="flex gap-2">
                    <input 
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="e.g. 'Contracting Officers at NASA' or 'Marvin Horne'"
                    value={query}
                    autoComplete="off"
                    name="co_search_query"
                    id="co_search_input"
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <Button onClick={handleSearch} disabled={loading || !query}>
                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                    Find Matches
                    </Button>
                </div>
                </div>
            </div>
            
            {/* Initial Hints */}
            {!matches.length && !loading && !error && (
                <div className="text-sm text-muted-foreground bg-muted/20 p-4 rounded-md border border-dashed">
                    <p className="font-medium mb-1">Search Tips:</p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                        <li><strong>Agency-based:</strong> "Contracting Officers at NASA" or "Head of Contracting at DOD"</li>
                        <li><strong>Specific names:</strong> "Marvin Horne" or "Nipa Shah" (must be real federal COs)</li>
                        <li><strong>Office-based:</strong> "Procurement Officers at NAVAIR"</li>
                    </ul>
                    <p className="text-[10px] mt-2 italic">Note: Generic names like "John Smith" won't return results unless they're actual federal contracting professionals.</p>
                </div>
            )}
        </div>
      )}

      {error && (
        <div className="text-red-600 text-sm bg-red-50 dark:bg-red-950 p-3 rounded-md flex justify-between items-center">
          <span>{error}</span>
          {selectedMatch && <Button variant="ghost" size="sm" onClick={() => setError(null)}>Dismiss</Button>}
        </div>
      )}

      {loading && !selectedMatch && (
        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary" />
            <p>Searching federal directories...</p>
        </div>
      )}

      {/* Match Selection List */}
      {!selectedMatch && matches.length > 0 && (
        <div className="space-y-4">
            <h3 className="text-sm font-medium text-muted-foreground">Potential Matches</h3>
            <div className="grid grid-cols-1 gap-3">
                {matches.map((match, i) => (
                    <Card key={i} className="hover:bg-muted/50 cursor-pointer transition-colors" onClick={() => handleSelectMatch(match)}>
                        <CardContent className="p-4 flex justify-between items-center">
                            <div>
                                <h4 className="font-semibold text-base">{match.name}</h4>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge variant="secondary" className="text-xs">{match.agency}</Badge>
                                    {match.office && <span className="text-xs text-muted-foreground border-l pl-2">{match.office}</span>}
                                </div>
                                <p className="text-xs text-muted-foreground mt-2">{match.match_reason}</p>
                            </div>
                            <ChevronRight className="h-5 w-5 text-muted-foreground" />
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
      )}

      {/* Deep Analysis View */}
      {selectedMatch && (
         <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <Button variant="ghost" size="sm" onClick={resetSearch} className="pl-0 hover:pl-2 transition-all">
                <ArrowLeft className="h-4 w-4 mr-1" /> Back to Search results
            </Button>
            
            {loading ? (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary" />
                    <p>Analyzing {selectedMatch.name} at {selectedMatch.agency}...</p>
                </div>
            ) : analysis && (
                <div className="space-y-6">
                    <div className="flex justify-between items-start">
                        <div>
                        <h2 className="text-2xl font-bold flex items-center gap-2">
                            {analysis.co_name}
                            {analysis.agency && <Badge variant="outline">{analysis.agency}</Badge>}
                        </h2>
                        <p className="text-muted-foreground mt-1 max-w-3xl">{analysis.overview}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-6">
                            {/* Background */}
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-base flex items-center gap-2">
                                        <User className="h-4 w-4" /> Professional Background
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {analysis.education && (
                                        <div className="flex gap-2 items-start text-sm">
                                            <GraduationCap className="h-4 w-4 text-muted-foreground mt-0.5" />
                                            <div>
                                                <span className="font-semibold block">Education</span>
                                                <span className="text-muted-foreground">{analysis.education}</span>
                                            </div>
                                        </div>
                                    )}
                                    <div>
                                        <div className="flex gap-2 items-center text-sm font-semibold mb-2">
                                            <Briefcase className="h-4 w-4 text-muted-foreground" /> Career History
                                        </div>
                                        <ul className="space-y-1 ml-6 list-disc text-sm text-muted-foreground">
                                            {analysis.career_history.map((role, i) => (
                                                <li key={i}>{role}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </CardContent>
                            </Card>
                            
                            {/* Preferences */}
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-base flex items-center gap-2 text-purple-700 dark:text-purple-400">
                                        <Lightbulb className="h-4 w-4" /> Awarding Patterns
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm mb-4 leading-relaxed">{analysis.awarding_patterns || "No specific patterns identified."}</p>
                                    
                                    {analysis.preferred_vehicles.length > 0 && (
                                        <div>
                                            <h4 className="text-xs font-semibold text-muted-foreground mb-2">Preferred Vehicles</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {analysis.preferred_vehicles.map((v, i) => (
                                                    <Badge key={i} variant="secondary" className="text-xs">{v}</Badge>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>

                        <div className="space-y-6">
                            {/* Award Trends */}
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-base flex items-center gap-2">
                                        <BarChart3 className="h-4 w-4" /> Associated Awards Output
                                    </CardTitle>
                                    <CardDescription>Based on keyword matches in federal award descriptions</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {awards.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center h-[200px] text-muted-foreground border border-dashed rounded-md bg-muted/10">
                                            <p>No direct award matches found.</p>
                                        </div>
                                    ) : (
                                        <>
                                            <div className="h-[200px] w-full min-h-[200px]">
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <BarChart data={agencyData} layout="vertical" margin={{ left: 0, right: 20 }}>
                                                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#334155" />
                                                        <XAxis type="number" hide />
                                                        <YAxis type="category" dataKey="name" width={100} tick={{fontSize: 10}} interval={0} />
                                                        <Tooltip 
                                                            formatter={(val: number) => [`$${(val/1000000).toFixed(1)}M`, 'Total Value']}
                                                            contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#F8FAFC' }}
                                                        />
                                                        <Bar dataKey="value" fill="#3B82F6" radius={[0, 4, 4, 0]} barSize={20} />
                                                    </BarChart>
                                                </ResponsiveContainer>
                                            </div>
                                            <div className="mt-4 space-y-2">
                                                <p className="text-xs font-medium text-muted-foreground">Recent Awards (Sample)</p>
                                                <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1">
                                                    {awards.slice(0, 5).map((a, i) => (
                                                        <div key={i} className="text-xs border p-2 rounded bg-muted/20">
                                                            <div className="flex justify-between font-medium">
                                                                <span className="truncate max-w-[180px]" title={a["Recipient Name"]}>{a["Recipient Name"]}</span>
                                                                <span className="text-green-600">${a["Award Amount"]?.toLocaleString()}</span>
                                                            </div>
                                                            <p className="text-[10px] text-muted-foreground truncate" title={a["Description"]}>{a["Description"]}</p>
                                                            <div className="flex justify-between mt-1 text-[10px] text-muted-foreground">
                                                                <span>{a["Awarding Agency"]}</span>
                                                                <span>{a["Start Date"]}</span>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </CardContent>
                            </Card>
                            
                            {/* Citations */}
                            {analysis.citations && analysis.citations.length > 0 && (
                                <Card>
                                    <CardHeader className="pb-2">
                                    <CardTitle className="text-base">Sources</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                    <ul className="space-y-1">
                                        {analysis.citations.map((c, i) => (
                                        <li key={i} className="text-xs flex items-center gap-2">
                                            <span className="text-muted-foreground">[{i + 1}]</span>
                                            <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underlin flex items-center gap-1">
                                            {c.title} <ExternalLink className="h-3 w-3" />
                                            </a>
                                        </li>
                                        ))}
                                    </ul>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
      )}
    </div>
  );
}
