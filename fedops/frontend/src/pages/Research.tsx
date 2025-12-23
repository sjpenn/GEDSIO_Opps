import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import {
    Search,
    Globe,
    BookOpen,
    Building2,
    Users,
    FileText,
    ExternalLink,
    Sparkles,
    Clock,
    ArrowRight,
    Loader2,
    ArrowLeft
} from "lucide-react";
import {
    unifiedSearch,
    truncateContent,
    type SearchResult
} from "@/services/researchService";

interface DisplayResult {
    id: string;
    title: string;
    source: "internal" | "web" | "sam.gov";
    snippet: string;
    date: string;
    relevance: number;
    filename?: string;
}

const Research = () => {
    const { opportunityId } = useParams<{ opportunityId: string }>();
    const toastContext = useToast();
    const [query, setQuery] = useState("");
    const [isSearching, setIsSearching] = useState(false);
    const [results, setResults] = useState<DisplayResult[]>([]);
    const [hasSearched, setHasSearched] = useState(false);
    const [opportunity, setOpportunity] = useState<any>(null);
    const [sources, setSources] = useState({
        library: true,
        web: true,
        sam: true
    });

    const [recentSearches, setRecentSearches] = useState<string[]>([
        "Cybersecurity compliance requirements NIST 800-53",
        "Department of Defense cloud migration best practices",
        "Federal contractor past performance requirements",
    ]);

    // Load opportunity details if we have an ID
    useEffect(() => {
        if (opportunityId) {
            loadOpportunityData();
        }
    }, [opportunityId]);

    const quickResearchCards = [
        { icon: Building2, title: "Agency Research", description: "Research government agencies" },
        { icon: Users, title: "Competitor Analysis", description: "Analyze competitors" },
        { icon: FileText, title: "Past Contracts", description: "Search FPDS data" },
        { icon: Globe, title: "Market Intelligence", description: "Industry trends" },
    ];

    const loadOpportunityData = async () => {
        if (!opportunityId) return;

        try {
            const response = await fetch(`/api/v1/opportunities/${opportunityId}`);
            if (response.ok) {
                const oppData = await response.json();
                setOpportunity(oppData);
            }
        } catch (error) {
            console.error('Error loading opportunity:', error);
        }
    };

    const handleSearch = async () => {
        if (!query.trim()) return;

        setIsSearching(true);
        setHasSearched(true);

        try {
            const searchResults = await unifiedSearch(query, sources);

            // Combine and transform results
            const combinedResults: DisplayResult[] = [];

            // Add library results
            searchResults.library.forEach((result: SearchResult, idx: number) => {
                combinedResults.push({
                    id: `lib-${idx}`,
                    title: result.filename || `Document ${idx + 1}`,
                    source: "internal",
                    snippet: truncateContent(result.content, 200),
                    date: "Library",
                    relevance: Math.round(result.score * 100),
                    filename: result.filename
                });
            });

            // Add SAM.gov results
            searchResults.sam.forEach((result: any, idx: number) => {
                combinedResults.push({
                    id: `sam-${idx}`,
                    title: result.title || result.name || `Opportunity ${idx + 1}`,
                    source: "sam.gov",
                    snippet: result.description || result.synopsis || "",
                    date: result.posted_date || "SAM.gov",
                    relevance: 80 - (idx * 5) // Decreasing relevance by order
                });
            });

            // Sort by relevance
            combinedResults.sort((a, b) => b.relevance - a.relevance);

            setResults(combinedResults);

            // Add to recent searches if not already there
            if (!recentSearches.includes(query)) {
                setRecentSearches(prev => [query, ...prev.slice(0, 4)]);
            }

            if (combinedResults.length === 0) {
                toastContext.info("No results found. Try different keywords.");
            }
        } catch (error) {
            console.error("Search failed:", error);
            toastContext.error("Search failed. Please try again.");
        } finally {
            setIsSearching(false);
        }
    };

    const toggleSource = (source: keyof typeof sources) => {
        setSources(prev => ({ ...prev, [source]: !prev[source] }));
    };

    const getSourceIcon = (source: DisplayResult["source"]) => {
        switch (source) {
            case "internal": return BookOpen;
            case "web": return Globe;
            case "sam.gov": return Building2;
            default: return FileText;
        }
    };

    const getSourceBadge = (source: DisplayResult["source"]) => {
        const configs = {
            internal: { label: "Library", className: "bg-purple-500/20 text-purple-400" },
            web: { label: "Web", className: "bg-blue-500/20 text-blue-400" },
            "sam.gov": { label: "SAM.gov", className: "bg-green-500/20 text-green-400" },
        };
        const config = configs[source];
        return <Badge variant="outline" className={config.className}>{config.label}</Badge>;
    };

    const getRelevanceColor = (relevance: number) => {
        if (relevance >= 80) return "text-green-400";
        if (relevance >= 60) return "text-yellow-400";
        return "text-muted-foreground";
    };

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                {opportunityId && opportunity && (
                    <Link
                        to={`/opportunities/${opportunityId}`}
                        className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1 mb-2"
                    >
                        <ArrowLeft className="h-4 w-4" /> Back to {opportunity.title}
                    </Link>
                )}
                <h1 className="text-3xl font-bold">Research</h1>
                <p className="text-muted-foreground mt-2">
                    {opportunityId
                        ? `Query your library and the web to gather intelligence for ${opportunity?.solicitation_number || 'this opportunity'}.`
                        : "Query your library and the web to gather intelligence for your proposals."
                    }
                </p>
            </div>

            {/* Search Section */}
            <Card>
                <CardContent className="p-6">
                    <div className="flex gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                                placeholder="Ask a question or search for information..."
                                className="w-full pl-12 pr-4 py-4 rounded-lg border border-border bg-background text-lg focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                        <Button size="lg" onClick={handleSearch} disabled={isSearching || !query.trim()}>
                            {isSearching ? (
                                <>
                                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                                    Searching...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="h-5 w-5 mr-2" />
                                    Research
                                </>
                            )}
                        </Button>
                    </div>

                    {/* Source Toggles */}
                    <div className="flex items-center gap-4 mt-4">
                        <span className="text-sm text-muted-foreground">Search in:</span>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={sources.library}
                                onChange={() => toggleSource('library')}
                                className="rounded"
                            />
                            <BookOpen className="h-4 w-4" />
                            <span className="text-sm">Library</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={sources.web}
                                onChange={() => toggleSource('web')}
                                className="rounded"
                            />
                            <Globe className="h-4 w-4" />
                            <span className="text-sm">Web</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={sources.sam}
                                onChange={() => toggleSource('sam')}
                                className="rounded"
                            />
                            <Building2 className="h-4 w-4" />
                            <span className="text-sm">SAM.gov</span>
                        </label>
                    </div>

                    {/* Recent Searches */}
                    {!query && (
                        <div className="mt-6">
                            <h3 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                                <Clock className="h-4 w-4" />
                                Recent Searches
                            </h3>
                            <div className="flex flex-wrap gap-2">
                                {recentSearches.map((search, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => setQuery(search)}
                                        className="px-3 py-1.5 rounded-full bg-muted hover:bg-muted/80 text-sm transition-colors"
                                    >
                                        {search}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Results */}
                <div className="lg:col-span-2">
                    <Card>
                        <CardHeader>
                            <CardTitle>Research Results</CardTitle>
                            <CardDescription>
                                {hasSearched
                                    ? `${results.length} results found across all sources`
                                    : "Enter a search query to find relevant information"
                                }
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {isSearching ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                </div>
                            ) : results.length === 0 && hasSearched ? (
                                <div className="text-center py-12 text-muted-foreground">
                                    <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>No results found</p>
                                    <p className="text-sm mt-1">Try different keywords or enable more sources</p>
                                </div>
                            ) : results.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground">
                                    <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>Enter a search query above to get started</p>
                                </div>
                            ) : (
                                results.map((result) => {
                                    const Icon = getSourceIcon(result.source);
                                    return (
                                        <div
                                            key={result.id}
                                            className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
                                        >
                                            <div className="flex items-start justify-between mb-2">
                                                <div className="flex items-center gap-2">
                                                    <Icon className="h-4 w-4 text-muted-foreground" />
                                                    <h3 className="font-semibold">{result.title}</h3>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {getSourceBadge(result.source)}
                                                    <span className={`text-xs ${getRelevanceColor(result.relevance)}`}>
                                                        {result.relevance}% match
                                                    </span>
                                                </div>
                                            </div>
                                            <p className="text-sm text-muted-foreground mb-3">
                                                {result.snippet}
                                            </p>
                                            <div className="flex items-center gap-3">
                                                <Button variant="outline" size="sm">
                                                    View Full
                                                    <ExternalLink className="h-3 w-3 ml-2" />
                                                </Button>
                                                <Button variant="ghost" size="sm">
                                                    Add to Proposal
                                                </Button>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Quick Research Cards */}
                <div className="space-y-4">
                    <h3 className="font-semibold">Quick Research</h3>
                    {quickResearchCards.map((card) => {
                        const Icon = card.icon;
                        return (
                            <Card key={card.title} className="hover:border-primary/50 transition-colors cursor-pointer">
                                <CardContent className="p-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-lg bg-primary/10">
                                                <Icon className="h-5 w-5 text-primary" />
                                            </div>
                                            <div>
                                                <h4 className="font-medium">{card.title}</h4>
                                                <p className="text-xs text-muted-foreground">{card.description}</p>
                                            </div>
                                        </div>
                                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}

                    <Card className="bg-primary/5 border-primary/20">
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3 mb-3">
                                <Sparkles className="h-5 w-5 text-primary" />
                                <h4 className="font-semibold">AI Pursuit Plan</h4>
                            </div>
                            <p className="text-sm text-muted-foreground mb-3">
                                Generate a comprehensive pursuit plan based on your research.
                            </p>
                            <Button className="w-full">
                                Generate Plan
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default Research;
