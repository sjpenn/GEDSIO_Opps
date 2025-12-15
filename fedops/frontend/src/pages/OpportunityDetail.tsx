import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import type { Opportunity, OpportunityComment } from '../types';
import { AgentControlPanel } from '@/components/AgentControlPanel';
import DocumentSlideout from '@/components/DocumentSlideout';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
    ArrowLeft,
    Users,
    MessageSquare,
    Trash2,
    Loader2,
    Eye,
    FileText,
    ExternalLink,
    Calendar,
    Building,
    Hash,
    Clock
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || '';

export default function OpportunityDetail() {
    const { opportunityId } = useParams<{ opportunityId: string }>();
    const navigate = useNavigate();

    const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Resources
    const [resourceFiles, setResourceFiles] = useState<{ url: string, filename: string, id?: number }[]>([]);
    const [loadingResources, setLoadingResources] = useState(false);

    // Comments
    const [comments, setComments] = useState<OpportunityComment[]>([]);
    const [newComment, setNewComment] = useState('');
    const [submittingComment, setSubmittingComment] = useState(false);

    // Partners
    const [loadingPartners, setLoadingPartners] = useState(false);

    // Pipeline
    const [pipelineItems, setPipelineItems] = useState<any[]>([]);

    // Document Slideout
    const [slideoutOpen, setSlideoutOpen] = useState(false);
    const [slideoutDocument, setSlideoutDocument] = useState<{ filename: string; id?: number; type?: string } | null>(null);

    // Helper to strip HTML tags
    const stripHtml = (html: string) => {
        if (!html) return '';
        const tmp = document.createElement('DIV');
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || '';
    };

    const getFilenameFromUrl = (url: string) => {
        try {
            const urlObj = new URL(url);
            const pathname = urlObj.pathname;
            const filename = pathname.substring(pathname.lastIndexOf('/') + 1);
            return filename || url;
        } catch (e) {
            return url;
        }
    };

    // Fetch opportunity details
    useEffect(() => {
        const fetchOpportunity = async () => {
            if (!opportunityId) return;

            setLoading(true);
            setError(null);

            try {
                const response = await fetch(`${API_URL}/api/v1/opportunities/${opportunityId}`);
                if (!response.ok) throw new Error('Failed to fetch opportunity');
                const data = await response.json();
                setOpportunity(data);

                // Fetch resources
                fetchResources(data);

                // Fetch comments
                fetchComments(parseInt(opportunityId));

                // Fetch pipeline status
                fetchPipelineData();
            } catch (err) {
                console.error('Error fetching opportunity:', err);
                setError('Failed to load opportunity details');
            } finally {
                setLoading(false);
            }
        };

        fetchOpportunity();
    }, [opportunityId]);

    const fetchResources = async (opp: Opportunity) => {
        if (!opp.resource_links && !opp.resource_files) return;

        setLoadingResources(true);
        try {
            const response = await fetch(`${API_URL}/api/v1/opportunities/${opp.id}/resources`);
            if (response.ok) {
                const data = await response.json();
                setResourceFiles(data);
            }
        } catch (err) {
            console.error('Error fetching resources:', err);
        } finally {
            setLoadingResources(false);
        }
    };

    const fetchComments = async (oppId: number) => {
        try {
            const response = await fetch(`${API_URL}/api/v1/opportunities/${oppId}/comments`);
            if (response.ok) {
                const data = await response.json();
                setComments(data);
            }
        } catch (err) {
            console.error('Error fetching comments:', err);
        }
    };

    const fetchPipelineData = async () => {
        try {
            const response = await fetch(`${API_URL}/api/v1/pipeline/`);
            if (response.ok) {
                const data = await response.json();
                setPipelineItems(data);
            }
        } catch (err) {
            console.error('Failed to fetch pipeline data', err);
        }
    };

    const isInPipeline = (oppId: number) => {
        return pipelineItems.find(item => item.pipeline?.opportunity_id === oppId);
    };

    const handleAddComment = async () => {
        if (!newComment.trim() || !opportunity) return;

        setSubmittingComment(true);
        try {
            const response = await fetch(`${API_URL}/api/v1/opportunities/${opportunity.id}/comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: newComment })
            });
            if (response.ok) {
                const comment = await response.json();
                setComments(prev => [...prev, comment]);
                setNewComment('');
            }
        } catch (err) {
            console.error('Error adding comment:', err);
        } finally {
            setSubmittingComment(false);
        }
    };

    const handleDeleteComment = async (commentId: number) => {
        if (!opportunity) return;

        try {
            const response = await fetch(`${API_URL}/api/v1/opportunities/${opportunity.id}/comments/${commentId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                setComments(prev => prev.filter(c => c.id !== commentId));
            }
        } catch (err) {
            console.error('Error deleting comment:', err);
        }
    };

    const handleFindPartners = async () => {
        if (!opportunity) return;

        setLoadingPartners(true);
        try {
            // Navigate to partners page with opportunity context
            navigate(`/teams?opportunityId=${opportunity.id}`);
        } finally {
            setLoadingPartners(false);
        }
    };

    const handleWatchOpportunity = async () => {
        if (!opportunity) return;

        try {
            const response = await fetch(`${API_URL}/api/v1/pipeline/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    opportunity_id: opportunity.id,
                    stage: 'watching',
                    priority: 'medium'
                })
            });
            if (response.ok) {
                fetchPipelineData();
            }
        } catch (err) {
            console.error('Error watching opportunity:', err);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (error || !opportunity) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
                <p className="text-destructive">{error || 'Opportunity not found'}</p>
                <Button variant="outline" onClick={() => navigate('/opportunities')}>
                    <ArrowLeft className="h-4 w-4 mr-2" /> Back to Opportunities
                </Button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <div className="sticky top-0 z-10 bg-background border-b">
                <div className="container max-w-6xl mx-auto px-4 py-4">
                    <div className="flex items-start justify-between gap-4">
                        <div className="space-y-2">
                            <Link to="/opportunities" className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1">
                                <ArrowLeft className="h-4 w-4" /> Back to Opportunities
                            </Link>
                            <h1 className="text-2xl font-bold leading-tight">{opportunity.title}</h1>
                            <div className="flex flex-wrap gap-2">
                                <Badge variant="secondary" className="font-mono">
                                    {opportunity.solicitation_number}
                                </Badge>
                                <Badge variant="outline" className="text-primary border-primary/20 bg-primary/5">
                                    {opportunity.type}
                                </Badge>
                                {isInPipeline(opportunity.id) && (
                                    <Badge variant="secondary" className="bg-blue-600 hover:bg-blue-700 text-white gap-1">
                                        <Eye className="h-3 w-3" />
                                        In Pipeline
                                    </Badge>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="container max-w-6xl mx-auto px-4 py-6 space-y-8">
                {/* Actions Bar */}
                <div className="flex flex-wrap gap-3">
                    <Button onClick={handleFindPartners} disabled={loadingPartners} className="gap-2">
                        {loadingPartners ? <Loader2 className="h-4 w-4 animate-spin" /> : <Users className="h-4 w-4" />}
                        Find Partners
                    </Button>
                    <Button variant="default" onClick={() => navigate(`/teams?opportunityId=${opportunity.id}`)} className="gap-2">
                        <Users className="h-4 w-4" /> Build Team
                    </Button>
                    <Button variant="outline" onClick={handleWatchOpportunity} className="gap-2">
                        <Eye className="h-4 w-4" /> Watch Opportunity
                    </Button>
                </div>

                {/* Key Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-muted/30 p-6 rounded-lg border">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground">
                            <Building className="h-3 w-3" /> Department
                        </div>
                        <p className="font-medium">{opportunity.department}</p>
                        {opportunity.sub_tier && <p className="text-sm text-muted-foreground">{opportunity.sub_tier}</p>}
                        {opportunity.office && <p className="text-sm text-muted-foreground">{opportunity.office}</p>}
                    </div>
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground">
                            <Calendar className="h-3 w-3" /> Key Dates
                        </div>
                        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-sm">
                            <span className="text-muted-foreground">Posted:</span>
                            <span className="font-medium">{new Date(opportunity.posted_date).toLocaleDateString()}</span>
                            <span className="text-muted-foreground">Due:</span>
                            <span className="font-medium text-destructive">
                                {opportunity.response_deadline ? new Date(opportunity.response_deadline).toLocaleDateString() : 'N/A'}
                            </span>
                        </div>
                    </div>
                    <div className="space-y-1">
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground">
                            <Hash className="h-3 w-3" /> Details
                        </div>
                        <div className="space-y-1 text-sm">
                            <p><span className="text-muted-foreground">NAICS:</span> {opportunity.naics_code}</p>
                            <p><span className="text-muted-foreground">Set Aside:</span> {opportunity.type_of_set_aside || 'None'}</p>
                            <p><span className="text-muted-foreground">Notice ID:</span> {opportunity.notice_id}</p>
                        </div>
                    </div>
                </div>

                {/* Description */}
                <div>
                    <h2 className="text-lg font-semibold mb-3">Description</h2>
                    <div className="bg-card p-4 rounded-lg text-sm leading-relaxed whitespace-pre-wrap border shadow-sm">
                        {opportunity.description ? stripHtml(opportunity.description) : 'No description available.'}
                    </div>
                </div>

                {/* Two Column: Contacts & Resources */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Points of Contact */}
                    {opportunity.point_of_contact && (
                        <div>
                            <h2 className="text-lg font-semibold mb-3">Points of Contact</h2>
                            <div className="space-y-3">
                                {opportunity.point_of_contact.map((poc: any, i: number) => (
                                    <Card key={i} className="bg-card">
                                        <CardContent className="p-3 text-sm">
                                            <p className="font-medium">{poc.fullName}</p>
                                            {poc.title && <p className="text-muted-foreground text-xs">{poc.title}</p>}
                                            {poc.email && <a href={`mailto:${poc.email}`} className="text-primary hover:underline mt-1 block text-xs">{poc.email}</a>}
                                            {poc.phone && <p className="text-muted-foreground text-xs">{poc.phone}</p>}
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Resources & Links */}
                    <div>
                        <h2 className="text-lg font-semibold mb-3">Resources & Links</h2>
                        <div className="flex flex-col gap-2">
                            {opportunity.ui_link && (
                                <a href={opportunity.ui_link} target="_blank" rel="noreferrer">
                                    <Button variant="outline" className="w-full justify-between group">
                                        View on SAM.gov
                                        <ExternalLink className="h-4 w-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                                    </Button>
                                </a>
                            )}

                            {loadingResources ? (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground p-2">
                                    <Loader2 className="h-3 w-3 animate-spin" /> Loading resources...
                                </div>
                            ) : (
                                resourceFiles.length > 0 ? (
                                    resourceFiles.map((file, i) => (
                                        <Card
                                            key={`res-${i}`}
                                            className="hover:bg-accent transition-colors cursor-pointer group"
                                            onClick={() => {
                                                setSlideoutDocument({ filename: file.filename, id: file.id });
                                                setSlideoutOpen(true);
                                            }}
                                        >
                                            <CardContent className="p-3 flex items-center justify-between gap-3">
                                                <div className="flex items-center gap-3 min-w-0">
                                                    <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                                                    <div className="overflow-hidden">
                                                        <p className="text-sm font-medium truncate group-hover:text-primary transition-colors" title={file.filename}>{file.filename}</p>
                                                        <p className="text-xs text-muted-foreground truncate">Click to preview</p>
                                                    </div>
                                                </div>
                                                <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                                            </CardContent>
                                        </Card>
                                    ))
                                ) : opportunity.resource_links?.map((link: string, i: number) => (
                                    <Card
                                        key={`res-${i}`}
                                        className="hover:bg-accent transition-colors cursor-pointer group"
                                        onClick={() => {
                                            setSlideoutDocument({ filename: getFilenameFromUrl(link) });
                                            setSlideoutOpen(true);
                                        }}
                                    >
                                        <CardContent className="p-3 flex items-center justify-between gap-3">
                                            <div className="flex items-center gap-3 min-w-0">
                                                <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                                                <div className="overflow-hidden">
                                                    <p className="text-sm font-medium truncate group-hover:text-primary transition-colors" title={getFilenameFromUrl(link)}>{getFilenameFromUrl(link)}</p>
                                                    <p className="text-xs text-muted-foreground truncate">Click to preview</p>
                                                </div>
                                            </div>
                                            <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                                        </CardContent>
                                    </Card>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Agent Control Panel */}
                <div className="border-t pt-6">
                    <AgentControlPanel key={opportunity.id} opportunityId={opportunity.id} />
                </div>

                {/* Comments Section */}
                <div className="border-t pt-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <MessageSquare className="h-5 w-5" /> Team Comments
                    </h2>

                    <div className="space-y-4 mb-6">
                        {comments.map(comment => (
                            <div key={comment.id} className="bg-muted/30 p-4 rounded-lg border group relative">
                                <p className="text-sm whitespace-pre-wrap">{comment.text}</p>
                                <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
                                    <span>{new Date(comment.created_at).toLocaleString()}</span>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => handleDeleteComment(comment.id)}
                                        className="h-6 w-6 text-destructive opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive/10"
                                    >
                                        <Trash2 className="h-3 w-3" />
                                    </Button>
                                </div>
                            </div>
                        ))}
                        {comments.length === 0 && (
                            <p className="text-sm text-muted-foreground italic">No comments yet.</p>
                        )}
                    </div>

                    <div className="flex gap-2 items-start">
                        <Textarea
                            placeholder="Add a comment..."
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            className="min-h-[80px] flex-1"
                        />
                        <Button
                            onClick={handleAddComment}
                            disabled={!newComment.trim() || submittingComment}
                            className="shrink-0"
                        >
                            {submittingComment ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Post'}
                        </Button>
                    </div>
                </div>
            </div>

            {/* Document Slideout */}
            <DocumentSlideout
                isOpen={slideoutOpen}
                onClose={() => setSlideoutOpen(false)}
                document={slideoutDocument}
                opportunityId={opportunity.id}
            />
        </div>
    );
}
