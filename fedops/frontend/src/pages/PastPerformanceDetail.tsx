
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft,
    Download,
    Loader2,
    FileText,
    Calendar,
    CheckCircle,
    AlertCircle,
    Clock // Added Clock icon import
} from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
// import { toast } from 'sonner';
const toast = {
    success: (msg: string) => console.log('Success:', msg),
    error: (msg: string) => console.error('Error:', msg)
};
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

import type { PastPerformance } from '../types';

export default function PastPerformanceDetail() {
    const { ppId } = useParams<{ ppId: string }>();
    const navigate = useNavigate();
    const [pp, setPp] = useState<PastPerformance | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (ppId) {
            loadPastPerformance(ppId);
        }
    }, [ppId]);


    const loadPastPerformance = async (id: string) => {
        setLoading(true);
        try {
            const response = await fetch(`/api/v1/company/past-performance/${id}`);
            if (!response.ok) {
                const err = await response.json().catch(() => ({ detail: 'Failed to load past performance' }));
                throw new Error(err.detail || 'Failed to load past performance');
            }
            const data = await response.json();
            setPp(data);
        } catch (err: any) {
            console.error('Failed to load past performance:', err);
            setError(err.message || 'Failed to load past performance');
            toast.error('Failed to load past performance');
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async (format: 'json' | 'text' | 'markdown') => {
        if (!pp) return;
        try {
            const response = await fetch(`/api/v1/company/past-performance/${pp.id}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    format,
                    include_metadata: true
                })
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            const result = await response.json();

            const blob = new Blob([typeof result.content === 'string' ? result.content : JSON.stringify(result.content, null, 2)], {
                type: format === 'json' ? 'application/json' : 'text/plain'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `past-performance-${pp.id}.${format === 'markdown' ? 'md' : format === 'json' ? 'json' : 'txt'}`;
            a.click();
            URL.revokeObjectURL(url);
            toast.success(`Exported as ${format.toUpperCase()}`);
        } catch (err: any) {
            console.error('Failed to export:', err);
            toast.error('Failed to export past performance');
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'DRAFT': return 'bg-gray-500';
            case 'IN_PROGRESS': return 'bg-blue-500';
            case 'COMPLETE': return 'bg-green-500';
            case 'APPROVED': return 'bg-purple-500';
            default: return 'bg-gray-500';
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh]">
                <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                <p className="text-muted-foreground">Loading past performance...</p>
            </div>
        );
    }

    if (error || !pp) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
                <div className="bg-destructive/10 p-3 rounded-full">
                    <AlertCircle className="h-6 w-6 text-destructive" />
                </div>
                <h2 className="text-xl font-semibold">Error Loading Record</h2>
                <p className="text-muted-foreground">{error || 'Past Performance not found'}</p>
                <Button onClick={() => navigate(-1)} variant="outline">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Go Back
                </Button>
            </div>
        );
    }

    // Helper to safely render content potentially containing markdown or newlines
    const renderContent = (content: any) => {
        if (!content) return <span className="text-muted-foreground italic">No content generated</span>;
        if (typeof content === 'string') {
            return <div className="whitespace-pre-wrap font-sans text-sm">{content}</div>;
        }
        return <pre className="text-xs overflow-auto bg-muted p-2 rounded">{JSON.stringify(content, null, 2)}</pre>;
    };

    return (
        <div className="container max-w-5xl py-8 space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="space-y-1">
                    <div className="flex items-center gap-2 text-muted-foreground mb-2">
                        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="-ml-3 h-8">
                            <ArrowLeft className="mr-2 h-4 w-4" />
                            Back
                        </Button>
                        <span>/</span>
                        <span>Past Performance</span>
                        <span>/</span>
                        <span className="text-foreground font-medium">{pp.id}</span>
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight">{pp.title}</h1>
                    <div className="flex items-center gap-3 pt-1">
                        <Badge className={getStatusColor(pp.status)}>
                            {pp.status}
                        </Badge>
                        <span className="flex items-center text-sm text-muted-foreground">
                            <Calendar className="mr-1 h-3 w-3" />
                            Created {new Date(pp.created_at).toLocaleDateString()}
                        </span>
                        {pp.updated_at && (
                            <span className="flex items-center text-sm text-muted-foreground">
                                <Clock className="mr-1 h-3 w-3" />
                                Updated {new Date(pp.updated_at).toLocaleDateString()}
                            </span>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Select onValueChange={(val) => handleExport(val as any)}>
                        <SelectTrigger className="w-[140px]">
                            <Download className="mr-2 h-4 w-4" />
                            <SelectValue placeholder="Export" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="json">JSON</SelectItem>
                            <SelectItem value="text">Text</SelectItem>
                            <SelectItem value="markdown">Markdown</SelectItem>
                        </SelectContent>
                    </Select>
                    {/* Future: Add Edit Button */}
                </div>
            </div>

            {/* Content */}
            <div className="grid gap-6">
                {Object.entries(pp.questionnaire_data || {}).length === 0 ? (
                    <Card>
                        <CardContent className="py-8 text-center text-muted-foreground">
                            No questionnaire data available.
                        </CardContent>
                    </Card>
                ) : (
                    Object.entries(pp.questionnaire_data).map(([sectionKey, sectionData]: [string, any]) => (
                        <Card key={sectionKey} className="overflow-hidden">
                            <CardHeader className="bg-muted/30 border-b">
                                <div className="flex justify-between items-center">
                                    <CardTitle className="text-lg font-semibold capitalize">
                                        {sectionKey.replace(/_/g, ' ')}
                                    </CardTitle>
                                    {sectionData.generated && (
                                        <Badge variant="secondary" className="text-xs font-normal">
                                            <CheckCircle className="mr-1 h-3 w-3 text-green-500" />
                                            AI Generated
                                        </Badge>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent className="p-6">
                                {renderContent(sectionData.content)}
                                {sectionData.model_used && (
                                    <div className="mt-4 pt-4 border-t text-xs text-muted-foreground flex items-center justify-end">
                                        Generated by {sectionData.model_used}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
}
