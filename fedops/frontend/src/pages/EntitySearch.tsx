import { useState, useMemo, useEffect, Fragment } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loader2, Search, Building2, DollarSign, Calendar, FileText, ExternalLink, X, Settings, Sliders, RefreshCw, Target, History } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PartnerProfile } from "@/components/PartnerProfile";
import CompetitorAnalysis from "@/components/CompetitorAnalysis";
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

// Map imports removed for stability
// import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
// import 'leaflet/dist/leaflet.css';
// import L from 'leaflet';

interface Entity {
  uei: string;
  legal_business_name: string;
  entity_type?: string;
  is_primary?: boolean;
  similarity_score?: number; // Fuzzy match similarity score (0.0-1.0)
  last_synced_at?: string;
}

interface Award {
  // Basic Information
  "Award ID": string;
  "Recipient Name": string;
  "Description": string;
  
  // Financial Fields
  "Award Amount": number;
  "Total Obligation"?: number;
  "Base and All Options Value"?: number;
  "Base Exercised Options Val"?: number;
  
  // Date Fields
  "Start Date"?: string;
  "End Date"?: string;
  "Current End Date"?: string;
  "Period of Performance Start Date"?: string;
  "Period of Performance Current End Date"?: string;
  "Last Modified Date"?: string;
  
  // Contract Details
  "Award Type"?: string;
  "Contract Award Type"?: string;
  "IDV Type"?: string;
  "Contract Pricing"?: string;
  "Type of Set Aside"?: string;
  "Extent Competed"?: string;
  
  // Agency Information
  "Awarding Agency": string;
  "Awarding Sub Agency"?: string;
  "Funding Agency"?: string;
  "Funding Sub Agency"?: string;
  
  // Location
  "Place of Performance City Name"?: string;
  "Place of Performance State Code"?: string;
  "Place of Performance ZIP Code"?: string;
  "Place of Performance Country Code"?: string;
  "Recipient Address Line 1"?: string;
  "Recipient City Name"?: string;
  "Recipient State Code"?: string;
  "Recipient ZIP Code"?: string;
  
  // Classification
  "NAICS Code"?: string;
  "NAICS Description"?: string;
  "Product or Service Code"?: string;
  "Product or Service Code Description"?: string;
  
  // Identifiers
  "Solicitation ID"?: string;
  "Parent Award ID"?: string;
  "Referenced IDV Agency Identifier"?: string;
  "Contract Award Unique Key"?: string;
  "Recipient UEI"?: string;
  "Recipient DUNS Number"?: string;
  
  // Additional Details
  "Sub-Award Count"?: number;
  "Number of Offers Received"?: number;
  
  // Award Type (Prime or Sub)
  award_type?: string;
  
  // Prime Award Information (for sub-awards)
  "Prime Award ID"?: string;
  "Prime Recipient Name"?: string;
}

export default function EntitySearchPage() {
  console.log('EntitySearchPage rendered');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [awards, setAwards] = useState<Award[]>([]);
  const [awardsLoading, setAwardsLoading] = useState(false);
  const [selectedAward, setSelectedAward] = useState<Award | null>(null);
  const [solicitationDocs, setSolicitationDocs] = useState<any[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [viewProfile, setViewProfile] = useState(false);
  const [showCompetitorAnalysis, setShowCompetitorAnalysis] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [recentEntities, setRecentEntities] = useState<Entity[]>([]);

  const fetchRecentEntities = async () => {
    try {
      const res = await fetch('/api/v1/entities/recent?limit=25');
      if (res.ok) {
        const data = await res.json();
        setRecentEntities(data);
      }
    } catch (e) {
      console.error("Failed to fetch recent entities", e);
    }
  };

  useEffect(() => {
    fetchRecentEntities();
  }, [results, selectedEntity]); // Refresh when results change or entity selected/updated

  const handleRefresh = async (uei: string) => {
    setRefreshing(true);
    try {
      const res = await fetch(`/api/v1/entities/${uei}/refresh`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSelectedEntity(updated);
        // Update in results list too
        setResults(results.map(r => r.uei === uei ? updated : r));
        fetchRecentEntities(); // Refresh recent list as timestamp changed
      }
    } catch (err) {
      console.error("Refresh failed", err);
    } finally {
      setRefreshing(false);
    }
  };
  
  // Search Settings
  const [showSettings, setShowSettings] = useState(false);
  const [minSimilarity, setMinSimilarity] = useState(0.5);
  const [usePhonetic, setUsePhonetic] = useState(true);
  const [useAbbreviations, setUseAbbreviations] = useState(true);
  const [useTypos, setUseTypos] = useState(true);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('entitySearchSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setMinSimilarity(parsed.minSimilarity ?? 0.5);
        setUsePhonetic(parsed.usePhonetic ?? true);
        setUseAbbreviations(parsed.useAbbreviations ?? true);
        setUseTypos(parsed.useTypos ?? true);
      } catch (e) {
        console.error("Failed to load settings", e);
      }
    }
  }, []);

  // Save settings to localStorage when changed
  useEffect(() => {
    localStorage.setItem('entitySearchSettings', JSON.stringify({
      minSimilarity,
      usePhonetic,
      useAbbreviations,
      useTypos
    }));
  }, [minSimilarity, usePhonetic, useAbbreviations, useTypos]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    
    setLoading(true);
    setError(null);
    setHasSearched(true);
    setResults([]); // Clear previous results
    try {
      const params = new URLSearchParams({
        q: query,
        fuzzy: 'true',
        min_similarity: minSimilarity.toString(),
        use_phonetic: usePhonetic.toString(),
        use_abbreviations: useAbbreviations.toString(),
        use_typos: useTypos.toString()
      });
      
      const res = await fetch(`/api/v1/entities/search?${params.toString()}`);
      if (!res.ok) {
        if (res.status === 429) {
          throw new Error("Rate limit exceeded. Please wait a moment and try again.");
        }
        throw new Error(`Search failed: ${res.statusText}`);
      }
      const data = await res.json();
      console.log("Search results:", data);
      
      if (Array.isArray(data)) {
        setResults(data);
      } else {
        console.error("Search results is not an array:", data);
        setResults([]);
        // You might want to set an error state here to display to the user
      }
    } catch (err) {
      console.error("Error searching entities:", err);
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEntity = async (entity: Entity, type: 'PARTNER' | 'COMPETITOR') => {
    try {
      const res = await fetch('/api/v1/entities/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uei: entity.uei,
          legal_business_name: entity.legal_business_name,
          entity_type: type
        })
      });
      if (res.ok) {
        // Update results
        setResults(results.map(r => r.uei === entity.uei ? { ...r, entity_type: type } : r));
        // Update selectedEntity if it matches
        if (selectedEntity && selectedEntity.uei === entity.uei) {
            setSelectedEntity({ ...selectedEntity, entity_type: type });
        }
        fetchRecentEntities();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSetPrimary = async (uei: string) => {
    try {
      const res = await fetch(`/api/v1/entities/${uei}/primary`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_primary: true })
      });
      if (res.ok) {
        if (selectedEntity && selectedEntity.uei === uei) {
             setSelectedEntity({...selectedEntity, is_primary: true});
        }
        setResults(results.map(r => r.uei === uei ? {...r, is_primary: true} : {...r, is_primary: false}));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAwards = async (uei: string) => {
    setAwardsLoading(true);
    try {
      const res = await fetch(`/api/v1/entities/${uei}/awards`);
      if (!res.ok) {
        console.error('Failed to fetch awards:', res.statusText);
        setAwards([]);
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        // Sort by Start Date descending
        const sortedData = data.sort((a: any, b: any) => {
          const dateA = a["Start Date"] ? new Date(a["Start Date"]).getTime() : 0;
          const dateB = b["Start Date"] ? new Date(b["Start Date"]).getTime() : 0;
          return dateB - dateA;
        });
        setAwards(sortedData);
      } else {
        console.error('Awards data is not an array:', data);
        setAwards([]);
      }
    } catch (err) {
      console.error(err);
      setAwards([]);
    } finally {
      setAwardsLoading(false);
    }
  };

  const fetchSolicitationDocuments = async (uei: string) => {
    setDocsLoading(true);
    try {
      const res = await fetch(`/api/v1/entities/${uei}/contract-documents`);
      if (!res.ok) {
        console.error('Failed to fetch solicitation documents:', res.statusText);
        setSolicitationDocs([]);
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setSolicitationDocs(data);
      } else {
        console.error('Solicitation documents data is not an array:', data);
        setSolicitationDocs([]);
      }
    } catch (err) {
      console.error('Error fetching solicitation documents:', err);
      setSolicitationDocs([]);
    } finally {
      setDocsLoading(false);
    }
  };

  // Prepare Chart Data
  const chartData = useMemo(() => {
    if (!Array.isArray(awards)) return [];
    
    const agencyMap: Record<string, number> = {};
    awards.forEach(award => {
      if (!award) return;
      const agency = award["Awarding Agency"] || "Unknown";
      agencyMap[agency] = (agencyMap[agency] || 0) + (award["Award Amount"] || 0);
    });
    const data = Object.entries(agencyMap)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10); // Top 10 agencies

    console.log('Chart Data for Recharts:', data);
    return data;
  }, [awards]);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Entity Search</h2>
          <p className="text-muted-foreground">Search and manage federal contractors and partners.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-auto min-h-[600px]">
        {/* Search Section */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Search SAM.gov</CardTitle>
                  <CardDescription>Find entities by name or UEI</CardDescription>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={() => setShowSettings(!showSettings)}
                  className={cn("h-8 w-8", showSettings && "bg-accent text-accent-foreground")}
                  title="Search Settings"
                >
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 flex-1 flex flex-col">
              {showSettings && (
                <div className="p-4 bg-muted/30 rounded-lg border mb-4 space-y-4 animate-in slide-in-from-top-2">
                  <div className="flex items-center gap-2 mb-2">
                    <Sliders className="h-4 w-4 text-primary" />
                    <h4 className="font-medium text-sm">Search Settings</h4>
                  </div>

                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <Label>Similarity Threshold</Label>
                      <span className="text-muted-foreground">{(minSimilarity * 100).toFixed(0)}%</span>
                    </div>
                    <input 
                      type="range" 
                      min="0" 
                      max="1" 
                      step="0.05"
                      value={minSimilarity}
                      onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
                      className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label className="text-xs cursor-pointer" htmlFor="phonetic">Phonetic Matching</Label>
                    <input 
                      id="phonetic"
                      type="checkbox"
                      checked={usePhonetic}
                      onChange={(e) => setUsePhonetic(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label className="text-xs cursor-pointer" htmlFor="abbrev">Abbreviations</Label>
                    <input 
                      id="abbrev"
                      type="checkbox"
                      checked={useAbbreviations}
                      onChange={(e) => setUseAbbreviations(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label className="text-xs cursor-pointer" htmlFor="typos">Typo Tolerance</Label>
                    <input 
                      id="typos"
                      type="checkbox"
                      checked={useTypos}
                      onChange={(e) => setUseTypos(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                  </div>
                </div>
              )}

              <form onSubmit={handleSearch} className="flex gap-2">
                <Input
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Company Name..."
                  className="flex-1"
                />
                <Button type="submit" disabled={loading} size="icon">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                </Button>
              </form>

              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2 mt-4 flex-1">
                {hasSearched && results.length === 0 && !loading && (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>No results found.</p>
                  </div>
                )}
                
                {hasSearched ? (
                    // Search Results
                    results.map((entity, i) => {
                      // Calculate match quality based on similarity score
                      const getMatchQuality = (score?: number) => {
                        if (!score || score >= 0.95) return { label: 'Exact Match', color: 'bg-green-600 hover:bg-green-700', show: score && score >= 0.95 };
                        if (score >= 0.80) return { label: 'High Match', color: 'bg-blue-600 hover:bg-blue-700', show: true };
                        if (score >= 0.60) return { label: 'Medium Match', color: 'bg-yellow-600 hover:bg-yellow-700', show: true };
                        return { label: 'Low Match', color: 'bg-orange-600 hover:bg-orange-700', show: true };
                      };
                      
                      const matchQuality = getMatchQuality(entity.similarity_score);
                      
                      return (
                        <div 
                          key={`${i}-${entity.uei}`} 
                          className={cn(
                            "p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md",
                            selectedEntity?.uei === entity.uei 
                              ? "bg-primary/5 border-primary shadow-sm" 
                              : "bg-card hover:bg-accent/50"
                          )}
                          onClick={() => {
                            setSelectedEntity(entity);
                            fetchAwards(entity.uei);
                            fetchSolicitationDocuments(entity.uei);
                          }}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h3 className="font-semibold text-sm line-clamp-2">{entity.legal_business_name || 'Unknown Name'}</h3>
                            {entity.similarity_score !== undefined && matchQuality.show && (
                              <Badge variant="secondary" className="text-[10px] px-1.5 h-5 ml-2 shrink-0" title={`Similarity: ${(entity.similarity_score * 100).toFixed(0)}%`}>
                                {(entity.similarity_score * 100).toFixed(0)}%
                              </Badge>
                            )}
                          </div>
                          
                          <div className="flex flex-wrap gap-1 mb-3">
                            {entity.is_primary && <Badge variant="default" className="bg-blue-600 hover:bg-blue-700">Primary</Badge>}
                            {entity.entity_type === 'PARTNER' && <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">Partner</Badge>}
                            {entity.entity_type === 'COMPETITOR' && <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50">Competitor</Badge>}
                            {entity.similarity_score !== undefined && matchQuality.show && (
                              <Badge variant="outline" className={`text-white border-0 ${matchQuality.color}`}>
                                {matchQuality.label}
                              </Badge>
                            )}
                          </div>

                          <p className="text-xs font-mono text-muted-foreground mb-3 flex items-center gap-1">
                            <Building2 className="h-3 w-3" /> {entity.uei}
                          </p>
                          
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => { e.stopPropagation(); handleAddEntity(entity, 'PARTNER'); }}
                              className="h-7 text-xs flex-1 bg-green-50 text-green-700 hover:bg-green-100 hover:text-green-800"
                            >
                              + Partner
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => { e.stopPropagation(); handleAddEntity(entity, 'COMPETITOR'); }}
                              className="h-7 text-xs flex-1 bg-red-50 text-red-700 hover:bg-red-100 hover:text-red-800"
                            >
                              + Competitor
                            </Button>
                          </div>
                        </div>
                      );
                    })
                ) : (
                    // Recent Entities
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground border-b pb-2">
                            <History className="h-4 w-4" />
                            <span>Recent Searches</span>
                        </div>
                        {recentEntities.length === 0 ? (
                            <p className="text-xs text-muted-foreground italic p-2">No recent searches</p>
                        ) : (
                            recentEntities.map((entity, i) => (
                                <div 
                                    key={`recent-${i}-${entity.uei}`}
                                    className={cn(
                                        "p-3 border rounded-md cursor-pointer transition-colors hover:bg-accent/50",
                                        selectedEntity?.uei === entity.uei && "bg-primary/5 border-primary"
                                    )}
                                    onClick={() => {
                                        setSelectedEntity(entity);
                                        fetchAwards(entity.uei);
                                        fetchSolicitationDocuments(entity.uei);
                                    }}
                                >
                                    <div className="flex justify-between items-start">
                                        <h3 className="font-medium text-sm truncate pr-2">{entity.legal_business_name}</h3>
                                        <Building2 className="h-3 w-3 text-muted-foreground shrink-0 mt-0.5" />
                                    </div>
                                    <p className="text-[10px] font-mono text-muted-foreground mt-1">UEI: {entity.uei}</p>
                                    <div className="flex gap-1 mt-2">
                                        {entity.is_primary && <Badge variant="secondary" className="text-[10px] h-4 px-1">Primary</Badge>}
                                        {entity.entity_type === 'PARTNER' && <Badge variant="outline" className="text-[10px] h-4 px-1 text-green-600 border-green-200">Partner</Badge>}
                                        {entity.entity_type === 'COMPETITOR' && <Badge variant="outline" className="text-[10px] h-4 px-1 text-red-600 border-red-200">Competitor</Badge>}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Details Section */}
        <div className="lg:col-span-3 space-y-6">
          {error && (
            <div className="p-4 rounded-md bg-destructive/10 text-destructive border border-destructive/20 flex items-center gap-2">
              <X className="h-4 w-4" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground bg-muted/10 rounded-lg border border-dashed">
              <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary" />
              <p>Searching for entities...</p>
            </div>
          ) : null}
          {selectedEntity ? (
            <div className="space-y-6 animate-in slide-in-from-right-4 duration-500">
              <Card>
                <CardHeader className="pb-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <CardTitle className="text-2xl">{selectedEntity.legal_business_name}</CardTitle>
                        {selectedEntity.is_primary && <Badge className="bg-blue-600">Primary Entity</Badge>}
                        {selectedEntity.entity_type === 'PARTNER' && <Badge className="bg-green-600">Partner</Badge>}
                        {selectedEntity.entity_type === 'COMPETITOR' && <Badge variant="destructive">Competitor</Badge>}
                      </div>
                      <CardDescription className="font-mono flex items-center gap-2">
                        UEI: {selectedEntity.uei}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        variant="outline"
                        size="sm"
                        onClick={() => setViewProfile(!viewProfile)}
                        className={cn("border-primary/20 hover:bg-primary/5", viewProfile && "bg-primary/10")}
                      >
                        {viewProfile ? <FileText className="h-4 w-4 mr-2" /> : <Building2 className="h-4 w-4 mr-2" />}
                        {viewProfile ? "View Awards" : "Full Profile"}
                      </Button>
                      <Button 
                        variant="outline"
                        size="sm"
                        onClick={() => handleRefresh(selectedEntity.uei)}
                        disabled={refreshing}
                        className="border-primary/20 hover:bg-primary/5"
                      >
                        <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
                        Refresh Data
                      </Button>
                      <Button 
                        variant="outline"
                        size="sm"
                        onClick={() => setShowCompetitorAnalysis(!showCompetitorAnalysis)}
                        className={cn(
                          "text-purple-600 border-purple-200 hover:bg-purple-50",
                          showCompetitorAnalysis && "bg-purple-100"
                        )}
                      >
                        <Target className="h-4 w-4 mr-2" />
                        {showCompetitorAnalysis ? "Hide Analysis" : "Research Competitor"}
                      </Button>
                      {!selectedEntity.is_primary && (
                          <Button 
                              variant="outline"
                              size="sm"
                              onClick={() => handleSetPrimary(selectedEntity.uei)}
                              className="text-blue-600 border-blue-200 hover:bg-blue-50"
                          >
                              Set as Primary
                          </Button>
                      )}
                      <Button 
                          variant="ghost"
                          size="icon"
                          onClick={() => setSelectedEntity(null)}
                      >
                          <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent>
                  {/* Competitive Analysis Section */}
                  {showCompetitorAnalysis && (
                     <CompetitorAnalysis 
                        entityName={selectedEntity.legal_business_name} 
                        onClose={() => setShowCompetitorAnalysis(false)}
                        awards={awards}
                     />
                  )}

                  {viewProfile ? (
                    <PartnerProfile entity={selectedEntity} />
                  ) : awardsLoading ? (
                    <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                      <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary" />
                      <p>Loading awards data...</p>
                    </div>
                  ) : awards.length > 0 ? (
                    <div className="space-y-8">
                      
                      {/* Charts Row */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <Card className="shadow-none border-muted">
                          <CardHeader>
                            <CardTitle className="text-base">Spending by Agency</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="h-[300px] w-full min-w-0">
                              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0} debounce={50}>
                                <BarChart data={chartData} layout="vertical" margin={{ left: 40, right: 20 }}>
                                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#334155" />
                                  <XAxis 
                                    type="number" 
                                    tickFormatter={(val) => `$${(val/1000000).toFixed(0)}M`} 
                                    fontSize={12}
                                    axisLine={{ stroke: '#334155' }}
                                    tickLine={{ stroke: '#334155' }}
                                    tick={{ fill: '#E2E8F0' }}
                                  />
                                  <YAxis 
                                    type="category" 
                                    dataKey="name" 
                                    width={140} 
                                    fontSize={11}
                                    axisLine={{ stroke: '#334155' }}
                                    tickLine={{ stroke: '#334155' }}
                                    tick={{ fill: '#E2E8F0' }}
                                  />
                                  <Tooltip 
                                    formatter={(val: number) => [`$${val.toLocaleString()}`, 'Amount']}
                                    contentStyle={{ 
                                      borderRadius: '8px', 
                                      border: '1px solid #334155', 
                                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                                      backgroundColor: '#1E293B',
                                      color: '#F8FAFC'
                                    }}
                                    itemStyle={{ color: '#F59E0B' }}
                                    cursor={{ fill: 'rgba(148, 163, 184, 0.1)' }}
                                  />
                                  <Bar dataKey="value" fill="#F59E0B" radius={[0, 4, 4, 0]} barSize={20} />
                                </BarChart>
                              </ResponsiveContainer>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Stats Cards */}
                        <div className="grid grid-cols-1 gap-4">
                          <Card className="bg-primary/5 border-primary/10 shadow-none">
                            <CardContent className="p-6 flex flex-col justify-center h-full">
                              <div className="space-y-1">
                                <p className="text-sm font-medium text-muted-foreground">Total Award Value</p>
                                <p className="text-3xl font-bold text-primary">
                                  ${awards.reduce((acc, curr) => acc + (curr["Award Amount"] || 0), 0).toLocaleString()}
                                </p>
                              </div>
                            </CardContent>
                          </Card>
                          <Card className="bg-secondary/20 border-secondary/20 shadow-none">
                            <CardContent className="p-6 flex flex-col justify-center h-full">
                              <div className="space-y-1">
                                <p className="text-sm font-medium text-muted-foreground">Total Awards</p>
                                <p className="text-3xl font-bold">
                                  {awards.length}
                                </p>
                              </div>
                            </CardContent>
                          </Card>
                        </div>
                      </div>

                      {/* Awards List */}
                      <div>
                        <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
                          <FileText className="h-5 w-5" /> Recent Awards ({awards.length})
                        </h3>
                        <div className="rounded-md border">
                          <div className="relative w-full overflow-auto max-h-[600px]">
                            <table className="w-full caption-bottom text-sm">
                              <thead className="[&_tr]:border-b sticky top-0 bg-background z-10">
                                <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Type</th>
                                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Award ID</th>
                                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Date</th>
                                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Agency</th>
                                  <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Description</th>
                                  <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Amount</th>
                                </tr>
                              </thead>
                              <tbody className="[&_tr:last-child]:border-0">
                                {awards.map((award, i) => (
                                  <Fragment key={`${i}-${award["Award ID"]}`}>
                                    <tr 
                                      className={cn(
                                        "border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted cursor-pointer",
                                        selectedAward?.["Award ID"] === award["Award ID"] && "bg-muted/50"
                                      )}
                                      onClick={() => setSelectedAward(selectedAward?.["Award ID"] === award["Award ID"] ? null : award)}
                                    >
                                      <td className="p-4">
                                        <Badge variant={award.award_type === "Sub" ? "secondary" : "default"}>
                                          {award.award_type || "Prime"}
                                        </Badge>
                                      </td>
                                      <td className="p-4 font-mono text-primary font-medium text-xs">
                                        {award["Award ID"]}
                                      </td>
                                      <td className="p-4 text-sm">
                                        {award["Start Date"] ? new Date(award["Start Date"]).toLocaleDateString() : "N/A"}
                                      </td>
                                      <td className="p-4 text-sm">{award["Awarding Agency"]}</td>
                                      <td className="p-4 max-w-[200px] truncate text-sm" title={award["Description"]}>{award["Description"]}</td>
                                      <td className="p-4 text-right font-mono text-green-600 font-medium text-sm">
                                        ${award["Award Amount"]?.toLocaleString()}
                                      </td>
                                    </tr>
                                    {selectedAward?.["Award ID"] === award["Award ID"] && (
                                      <tr>
                                        <td colSpan={6} className="p-0 bg-muted/10">
                                          <div className="p-6 border-b animate-in slide-in-from-top-2 duration-200">
                                            <div className="flex justify-between items-start mb-6">

                                              <h4 className="text-xl font-bold flex items-center gap-2">
                                                <FileText className="h-5 w-5 text-primary" /> Award Details
                                              </h4>
                                              <Button 
                                                variant="ghost" 
                                                size="sm"
                                                onClick={(e) => { e.stopPropagation(); setSelectedAward(null); }}
                                              >
                                                <X className="h-4 w-4 mr-2" /> Close
                                              </Button>
                                            </div>

                                            <div className="space-y-6">
                                              {/* Header Section */}
                                              <Card>
                                                <CardContent className="p-4">
                                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                                    <div>
                                                      <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Award ID</p>
                                                      <p className="font-mono text-sm font-medium">{award["Award ID"]}</p>
                                                    </div>
                                                    <div>
                                                      <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Recipient</p>
                                                      <p className="text-sm font-medium">{award["Recipient Name"]}</p>
                                                    </div>
                                                    <div>
                                                      <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Award Amount</p>
                                                      <p className="text-lg font-bold text-green-600">${award["Award Amount"]?.toLocaleString()}</p>
                                                    </div>
                                                  </div>
                                                  <div className="mt-4 pt-4 border-t">
                                                    <p className="text-xs text-muted-foreground font-medium uppercase mb-1">Description</p>
                                                    <p className="text-sm leading-relaxed">{award["Description"]}</p>
                                                  </div>
                                                </CardContent>
                                              </Card>

                                              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                {/* Financial Information */}
                                                <div className="space-y-3">
                                                  <h5 className="font-semibold text-sm flex items-center gap-2">
                                                    <DollarSign className="h-4 w-4" /> Financial Information
                                                  </h5>
                                                  <Card>
                                                    <CardContent className="p-4 grid gap-4">
                                                      {award["Total Obligation"] && (
                                                        <div>
                                                          <p className="text-xs text-muted-foreground font-medium mb-1">Total Obligation</p>
                                                          <p className="text-sm font-mono">${award["Total Obligation"]?.toLocaleString()}</p>
                                                        </div>
                                                      )}
                                                      {award["Base and All Options Value"] && (
                                                        <div>
                                                          <p className="text-xs text-muted-foreground font-medium mb-1">Base and All Options Value</p>
                                                          <p className="text-sm font-mono">${award["Base and All Options Value"]?.toLocaleString()}</p>
                                                        </div>
                                                      )}
                                                    </CardContent>
                                                  </Card>
                                                </div>

                                                {/* Timeline Information */}
                                                <div className="space-y-3">
                                                  <h5 className="font-semibold text-sm flex items-center gap-2">
                                                    <Calendar className="h-4 w-4" /> Timeline
                                                  </h5>
                                                  <Card>
                                                    <CardContent className="p-4 grid grid-cols-2 gap-4">
                                                      {award["Start Date"] && (
                                                        <div>
                                                          <p className="text-xs text-muted-foreground font-medium mb-1">Start Date</p>
                                                          <p className="text-sm">{award["Start Date"]}</p>
                                                        </div>
                                                      )}
                                                      {award["End Date"] && (
                                                        <div>
                                                          <p className="text-xs text-muted-foreground font-medium mb-1">End Date</p>
                                                          <p className="text-sm">{award["End Date"]}</p>
                                                        </div>
                                                      )}
                                                    </CardContent>
                                                  </Card>
                                                </div>
                                              </div>

                                              {/* Solicitation Documents */}
                                              {award["Solicitation ID"] && (
                                                <div className="space-y-3">
                                                  <h5 className="font-semibold text-sm flex items-center gap-2">
                                                    <FileText className="h-4 w-4" /> Solicitation Documents
                                                  </h5>
                                                  {docsLoading ? (
                                                    <div className="flex items-center gap-2 text-sm text-muted-foreground p-4 border rounded-lg bg-card">
                                                      <Loader2 className="h-4 w-4 animate-spin" /> Loading documents...
                                                    </div>
                                                  ) : (
                                                    <div className="grid gap-2">
                                                      {solicitationDocs.filter(doc => doc.solicitation_id === award["Solicitation ID"]).length > 0 ? (
                                                        solicitationDocs
                                                          .filter(doc => doc.solicitation_id === award["Solicitation ID"])
                                                          .map((doc, idx) => (
                                                            <div key={idx} className="flex justify-between items-center p-3 text-sm bg-muted/20 border rounded-lg hover:bg-muted/40 transition-colors">
                                                              <div className="flex items-start gap-3">
                                                                <FileText className="h-4 w-4 mt-1 text-primary" />
                                                                <div>
                                                                  <p className="font-medium">{doc.document_filename || "Document"}</p>
                                                                  <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                                                                    <Badge variant="outline" className="text-[10px] h-4 px-1">{doc.document_type || "File"}</Badge>
                                                                    <span>{doc.opportunity_title}</span>
                                                                  </div>
                                                                </div>
                                                              </div>
                                                              <a href={doc.document_url} target="_blank" rel="noopener noreferrer">
                                                                <Button size="sm" variant="ghost">Download</Button>
                                                              </a>
                                                            </div>
                                                          ))
                                                      ) : (
                                                        <p className="text-sm text-muted-foreground italic">No public documents found.</p>
                                                      )}
                                                    </div>
                                                  )}
                                                </div>
                                              )}
                                            </div>
                                          </div>
                                        </td>
                                      </tr>
                                    )}
                                    </Fragment>
                                  ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
                      <Search className="h-10 w-10 mx-auto mb-4 opacity-50" />
                      <h3 className="text-lg font-medium mb-2">Select an entity to view details</h3>
                      <p>Full profile, awards history, and documents will appear here.</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
             <div className="h-full flex flex-col items-center justify-center p-12 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/5">
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                  <Search className="h-8 w-8 opacity-50" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Select an Entity</h3>
                <p className="max-w-md text-center">
                  Search for companies or organizations using the sidebar to view their federal awards, contracts, and documents.
                </p>
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
