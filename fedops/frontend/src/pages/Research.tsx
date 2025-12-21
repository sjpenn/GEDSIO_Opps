import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
    ArrowRight
} from "lucide-react";

interface ResearchResult {
    id: string;
    title: string;
    source: "internal" | "web" | "sam.gov";
    snippet: string;
    date: string;
    relevance: number;
}

const Research = () => {
    const [query, setQuery] = useState("");
    const [isSearching, setIsSearching] = useState(false);

    const recentSearches = [
        "Cybersecurity compliance requirements NIST 800-53",
        "Department of Defense cloud migration best practices",
        "Federal contractor past performance requirements",
    ];

    const sampleResults: ResearchResult[] = [
        {
            id: "1",
            title: "NIST 800-53 Security Controls Framework",
            source: "internal",
            snippet: "Comprehensive security controls for federal information systems including access control, audit and accountability, and system protection requirements...",
            date: "Library",
            relevance: 95,
        },
        {
            id: "2",
            title: "DoD Cloud Computing Security Requirements Guide",
            source: "internal",
            snippet: "Security requirements for cloud computing implementations within the Department of Defense, including FedRAMP and DoD IL requirements...",
            date: "Library",
            relevance: 88,
        },
        {
            id: "3",
            title: "Federal Acquisition Regulation Part 15",
            source: "web",
            snippet: "Contracting by negotiation procedures, source selection, and evaluation factors for competitive proposals...",
            date: "2024",
            relevance: 82,
        },
    ];

    const quickResearchCards = [
        { icon: Building2, title: "Agency Research", description: "Research government agencies" },
        { icon: Users, title: "Competitor Analysis", description: "Analyze competitors" },
        { icon: FileText, title: "Past Contracts", description: "Search FPDS data" },
        { icon: Globe, title: "Market Intelligence", description: "Industry trends" },
    ];

    const handleSearch = () => {
        if (!query.trim()) return;
        setIsSearching(true);
        // Simulate search
        setTimeout(() => setIsSearching(false), 1000);
    };

    const getSourceIcon = (source: ResearchResult["source"]) => {
        switch (source) {
            case "internal": return BookOpen;
            case "web": return Globe;
            case "sam.gov": return Building2;
            default: return FileText;
        }
    };

    const getSourceBadge = (source: ResearchResult["source"]) => {
        const configs = {
            internal: { label: "Library", className: "bg-purple-500/20 text-purple-400" },
            web: { label: "Web", className: "bg-blue-500/20 text-blue-400" },
            "sam.gov": { label: "SAM.gov", className: "bg-green-500/20 text-green-400" },
        };
        const config = configs[source];
        return <Badge variant="outline" className={config.className}>{config.label}</Badge>;
    };

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold">Research</h1>
                <p className="text-muted-foreground mt-2">
                    Query your library and the web to gather intelligence for your proposals.
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
                        <Button size="lg" onClick={handleSearch} disabled={isSearching}>
                            <Sparkles className="h-5 w-5 mr-2" />
                            {isSearching ? "Searching..." : "Research"}
                        </Button>
                    </div>

                    {/* Source Toggles */}
                    <div className="flex items-center gap-4 mt-4">
                        <span className="text-sm text-muted-foreground">Search in:</span>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" defaultChecked className="rounded" />
                            <BookOpen className="h-4 w-4" />
                            <span className="text-sm">Library</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" defaultChecked className="rounded" />
                            <Globe className="h-4 w-4" />
                            <span className="text-sm">Web</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" defaultChecked className="rounded" />
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
                                {sampleResults.length} results found across all sources
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {sampleResults.map((result) => {
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
                                                <span className="text-xs text-muted-foreground">
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
                            })}
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
