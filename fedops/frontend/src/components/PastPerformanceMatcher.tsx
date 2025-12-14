import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, CheckCircle, AlertTriangle, Briefcase, FileText, Building2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const API_URL = import.meta.env.VITE_API_URL || '';

interface MatchedProject {
    project_id: string;
    title: string;
    relevance_score: number;
    relevance_rationale: string;
    strengths: string[];
    weaknesses: string[];
}

interface PastPerformanceMatcherProps {
    opportunityId: string;
}

export default function PastPerformanceMatcher({ opportunityId }: PastPerformanceMatcherProps) {
    const [loading, setLoading] = useState(false);
    const [matches, setMatches] = useState<MatchedProject[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [entities, setEntities] = useState<any[]>([]);
    const [selectedEntityUei, setSelectedEntityUei] = useState<string>("");

    useEffect(() => {
        fetchEntities();
    }, []);

    const fetchEntities = async () => {
        try {
            const response = await fetch(`${API_URL}/api/v1/entities/`);
            if (response.ok) {
                const data = await response.json();
                setEntities(data);
                if (data.length > 0) {
                    setSelectedEntityUei(data[0].uei);
                }
            }
        } catch (err) {
            console.error("Failed to fetch entities", err);
        }
    };

    const handleMatch = async () => {
        if (!selectedEntityUei || !opportunityId) return;

        setLoading(true);
        setError(null);
        setMatches([]);

        try {
            const response = await fetch(`${API_URL}/api/v1/past-performance/match`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    opportunity_id: parseInt(opportunityId),
                    entity_uei: selectedEntityUei
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to find matches. Ensure analysis has been run first.');
            }

            const data = await response.json();
            setMatches(data.matches);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred during matching');
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 90) return "bg-green-500";
        if (score >= 70) return "bg-yellow-500";
        return "bg-red-500";
    };

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Building2 className="h-5 w-5" />
                        Find Matching Projects
                    </CardTitle>
                    <CardDescription>
                        Identify the most relevant past performance projects for this opportunity from your internal database.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex gap-4 items-end">
                        <div className="space-y-2 flex-1">
                            <label className="text-sm font-medium">Select Entity</label>
                            <Select value={selectedEntityUei} onValueChange={setSelectedEntityUei}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select an entity..." />
                                </SelectTrigger>
                                <SelectContent>
                                    {entities.map((entity) => (
                                        <SelectItem key={entity.uei} value={entity.uei}>
                                            {entity.legal_business_name} ({entity.uei})
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <Button onClick={handleMatch} disabled={loading || !selectedEntityUei}>
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Analyzing Database...
                                </>
                            ) : (
                                'Find Matches'
                            )}
                        </Button>
                    </div>

                    {error && (
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>Error</AlertTitle>
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}
                </CardContent>
            </Card>

            {matches.length > 0 && (
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        Matched Projects ({matches.length})
                    </h3>
                    <div className="grid gap-4">
                        {matches.map((match, index) => (
                            <Card key={index} className="overflow-hidden">
                                <CardHeader className="bg-gray-50/50 pb-3">
                                    <div className="flex justify-between items-start">
                                        <div className="space-y-1">
                                            <CardTitle className="text-base text-blue-700">{match.title}</CardTitle>
                                            <CardDescription className="flex items-center gap-2">
                                                <FileText className="h-3 w-3" />
                                                Project ID: {match.project_id}
                                            </CardDescription>
                                        </div>
                                        <div className="flex flex-col items-end gap-1 min-w-[100px]">
                                            <span className="text-sm font-bold">{match.relevance_score}% Match</span>
                                            <Progress value={match.relevance_score} className="h-2 w-24" indicatorClassName={getScoreColor(match.relevance_score)} />
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="pt-4 grid gap-4 md:grid-cols-2">
                                    <div className="space-y-2">
                                        <h4 className="font-semibold text-sm">Rationale</h4>
                                        <p className="text-sm text-gray-600 leading-relaxed">
                                            {match.relevance_rationale}
                                        </p>
                                    </div>

                                    <div className="space-y-4">
                                        {match.strengths && match.strengths.length > 0 && (
                                            <div>
                                                <h4 className="font-semibold text-sm text-green-700 mb-2">Strengths</h4>
                                                <ul className="space-y-1">
                                                    {match.strengths.map((str, i) => (
                                                        <li key={i} className="text-xs flex items-center gap-2">
                                                            <CheckCircle className="h-3 w-3 text-green-500" />
                                                            {str}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {match.weaknesses && match.weaknesses.length > 0 && (
                                            <div>
                                                <h4 className="font-semibold text-sm text-amber-700 mb-2">Gaps / Weaknesses</h4>
                                                <ul className="space-y-1">
                                                    {match.weaknesses.map((wk, i) => (
                                                        <li key={i} className="text-xs flex items-center gap-2">
                                                            <AlertTriangle className="h-3 w-3 text-amber-500" />
                                                            {wk}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
