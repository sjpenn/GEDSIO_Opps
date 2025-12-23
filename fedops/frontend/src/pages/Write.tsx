import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    GripVertical,
    ChevronDown,
    ChevronRight,
    Plus,
    MoreHorizontal,
    Check,
    User,
    Calendar,
    Grid3x3,
    ArrowLeft,
    Loader2,
    AlertCircle
} from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

type SectionStatus = "preparing" | "writing" | "formal-review" | "ready-to-submit";

interface Section {
    id: string;
    title: string;
    status: SectionStatus;
    owner?: string;
    dueDate?: string;
    wordLimit?: number;
    wordCount: number;
    subsections?: Section[];
    isExpanded?: boolean;
}

interface Volume {
    id: string;
    title: string;
    sections: Section[];
    isExpanded: boolean;
}

const Write = () => {
    const { opportunityId } = useParams<{ opportunityId: string }>();
    const navigate = useNavigate();

    const [volumes, setVolumes] = useState<Volume[]>([]);
    const [loading, setLoading] = useState(false);
    const [opportunity, setOpportunity] = useState<any>(null);

    // Load opportunity details and proposal volumes
    useEffect(() => {
        if (opportunityId) {
            loadOpportunityData();
        } else {
            // No opportunity context - use default/sample data
            setVolumes(getDefaultVolumes());
        }
    }, [opportunityId]);

    const loadOpportunityData = async () => {
        if (!opportunityId) return;

        setLoading(true);
        try {
            // Load opportunity details
            const oppResponse = await fetch(`/api/v1/opportunities/${opportunityId}`);
            if (oppResponse.ok) {
                const oppData = await oppResponse.json();
                setOpportunity(oppData);
            }

            // Load or generate proposal for this opportunity
            const proposalResponse = await fetch(`/api/v1/proposals/generate/${opportunityId}`);
            if (proposalResponse.ok) {
                const proposalData = await proposalResponse.json();
                // Transform proposal data to volumes format if needed
                if (proposalData.volumes && proposalData.volumes.length > 0) {
                    setVolumes(proposalData.volumes.map((vol: any) => ({
                        id: vol.id || `vol-${vol.order}`,
                        title: vol.title,
                        isExpanded: true,
                        sections: vol.sections || []
                    })));
                } else {
                    // No volumes yet, use default structure
                    setVolumes(getDefaultVolumes());
                }
            }
        } catch (error) {
            console.error('Error loading opportunity data:', error);
            // Fall back to default volumes on error
            setVolumes(getDefaultVolumes());
        } finally {
            setLoading(false);
        }
    };

    const getDefaultVolumes = (): Volume[] => {
        return [
            {
                id: "vol-1",
                title: "Volume 1: Technical Proposal",
                isExpanded: true,
                sections: [
                    {
                        id: "toc",
                        title: "Table of Contents",
                        status: "preparing",
                        owner: "JD",
                        dueDate: "3/30/2025",
                        wordCount: 19,
                    },
                    {
                        id: "cover",
                        title: "Cover Page",
                        status: "ready-to-submit",
                        dueDate: "2/7/2025",
                        wordLimit: 1500,
                        wordCount: 2542,
                        isExpanded: false,
                    },
                    {
                        id: "exec-summary",
                        title: "Executive Summary",
                        status: "formal-review",
                        dueDate: "2/28/2025",
                        wordCount: 43,
                    },
                    {
                        id: "background",
                        title: "Background and Introduction",
                        status: "preparing",
                        dueDate: "3/7/2025",
                        wordCount: 100,
                    },
                    {
                        id: "tech-approach",
                        title: "1. Technical Approach",
                        status: "writing",
                        dueDate: "3/28/2025",
                        wordCount: 879,
                        isExpanded: false,
                    },
                    {
                        id: "mgmt-approach",
                        title: "2. Management Approach",
                        status: "writing",
                        dueDate: "3/14/2025",
                        wordCount: 487,
                        isExpanded: false,
                    },
                    {
                        id: "institutional",
                        title: "3. Institutional Capability",
                        status: "preparing",
                        dueDate: "3/16/2025",
                        wordLimit: 1500,
                        wordCount: 433,
                        isExpanded: false,
                    },
                ],
            },
        ];
    };

    const toggleVolume = (volumeId: string) => {
        setVolumes(prev => prev.map(vol =>
            vol.id === volumeId ? { ...vol, isExpanded: !vol.isExpanded } : vol
        ));
    };

    const toggleSection = (volumeId: string, sectionId: string) => {
        setVolumes(prev => prev.map(vol => {
            if (vol.id !== volumeId) return vol;
            return {
                ...vol,
                sections: vol.sections.map(sec =>
                    sec.id === sectionId ? { ...sec, isExpanded: !sec.isExpanded } : sec
                )
            };
        }));
    };

    const updateSectionStatus = (volumeId: string, sectionId: string, status: SectionStatus) => {
        setVolumes(prev => prev.map(vol => {
            if (vol.id !== volumeId) return vol;
            return {
                ...vol,
                sections: vol.sections.map(sec =>
                    sec.id === sectionId ? { ...sec, status } : sec
                )
            };
        }));
    };

    const getStatusConfig = (status: SectionStatus) => {
        const configs = {
            "preparing": {
                label: "Preparing",
                icon: null,
                className: "bg-blue-500/10 text-blue-500 border-blue-500/30"
            },
            "writing": {
                label: "Writing",
                icon: null,
                className: "bg-purple-500/10 text-purple-500 border-purple-500/30"
            },
            "formal-review": {
                label: "Formal Review",
                icon: Check,
                className: "bg-pink-500/10 text-pink-500 border-pink-500/30"
            },
            "ready-to-submit": {
                label: "Ready to Submit",
                icon: Check,
                className: "bg-green-500/10 text-green-500 border-green-500/30"
            },
        };
        return configs[status];
    };

    const renderSection = (volume: Volume, section: Section, depth: number = 0) => {
        const statusConfig = getStatusConfig(section.status);
        const StatusIcon = statusConfig.icon;
        const hasSubsections = section.subsections && section.subsections.length > 0;

        return (
            <div key={section.id}>
                <div
                    className={cn(
                        "grid grid-cols-[auto,2fr,1.5fr,1fr,1fr,1fr,1fr,auto] gap-4 items-center p-3 hover:bg-muted/30 transition-colors border-b border-border/50",
                        depth > 0 && "bg-muted/20"
                    )}
                    style={{ paddingLeft: `${depth * 24 + 12}px` }}
                >
                    {/* Drag Handle */}
                    <div className="flex items-center gap-2">
                        <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab" />
                        {hasSubsections && (
                            <button
                                onClick={() => toggleSection(volume.id, section.id)}
                                className="hover:bg-muted rounded p-0.5"
                            >
                                {section.isExpanded ? (
                                    <ChevronDown className="h-4 w-4" />
                                ) : (
                                    <ChevronRight className="h-4 w-4" />
                                )}
                            </button>
                        )}
                    </div>

                    {/* Title */}
                    <div className="font-medium text-sm">{section.title}</div>

                    {/* Status */}
                    <div>
                        <Select
                            value={section.status}
                            onValueChange={(value) => updateSectionStatus(volume.id, section.id, value as SectionStatus)}
                        >
                            <SelectTrigger className={cn("w-full border", statusConfig.className)}>
                                <SelectValue>
                                    <div className="flex items-center gap-2">
                                        {StatusIcon && <StatusIcon className="h-3.5 w-3.5" />}
                                        {statusConfig.label}
                                    </div>
                                </SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="preparing">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                                        Preparing
                                    </div>
                                </SelectItem>
                                <SelectItem value="writing">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-purple-500" />
                                        Writing
                                    </div>
                                </SelectItem>
                                <SelectItem value="formal-review">
                                    <div className="flex items-center gap-2">
                                        <Check className="h-3.5 w-3.5 text-pink-500" />
                                        Formal Review
                                    </div>
                                </SelectItem>
                                <SelectItem value="ready-to-submit">
                                    <div className="flex items-center gap-2">
                                        <Check className="h-3.5 w-3.5 text-green-500" />
                                        Ready to Submit
                                    </div>
                                </SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Owner */}
                    <div>
                        {section.owner ? (
                            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/20 text-primary text-xs font-medium">
                                {section.owner}
                            </div>
                        ) : (
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                <User className="h-4 w-4 text-muted-foreground" />
                            </Button>
                        )}
                    </div>

                    {/* Due Date */}
                    <div className="text-sm text-muted-foreground">
                        {section.dueDate || (
                            <Button variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground">
                                Add Value
                            </Button>
                        )}
                    </div>

                    {/* Word Limit */}
                    <div className="text-sm text-muted-foreground">
                        {section.wordLimit || (
                            <Button variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground">
                                Add Value
                            </Button>
                        )}
                    </div>

                    {/* Word Count */}
                    <div className="text-sm font-medium">{section.wordCount}</div>

                    {/* Actions */}
                    <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <Plus className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <Grid3x3 className="h-4 w-4" />
                        </Button>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                    <MoreHorizontal className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem>Edit</DropdownMenuItem>
                                <DropdownMenuItem>Duplicate</DropdownMenuItem>
                                <DropdownMenuItem>Move to...</DropdownMenuItem>
                                <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>

                {/* Subsections */}
                {section.isExpanded && section.subsections?.map(subsection =>
                    renderSection(volume, subsection, depth + 1)
                )}
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Page Header with Opportunity Context */}
            <div>
                {opportunityId && opportunity && (
                    <Link
                        to={`/opportunities/${opportunityId}`}
                        className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1 mb-2"
                    >
                        <ArrowLeft className="h-4 w-4" /> Back to {opportunity.title}
                    </Link>
                )}
                <h1 className="text-3xl font-bold">Write</h1>
                <p className="text-muted-foreground mt-2">
                    {opportunityId
                        ? `Organize and write proposal volumes for ${opportunity?.solicitation_number || 'this opportunity'}`
                        : "Organize and write your proposal volumes with section-by-section tracking and collaboration."
                    }
                </p>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <span className="ml-3 text-muted-foreground">Loading proposal volumes...</span>
                </div>
            ) : volumes.length === 0 ? (
                <Card>
                    <CardContent className="p-12 text-center">
                        <AlertCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                        <h3 className="text-lg font-semibold mb-2">No Proposal Volumes</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                            Get started by creating your first proposal volume.
                        </p>
                        <Button onClick={() => setVolumes(getDefaultVolumes())}>
                            <Plus className="h-4 w-4 mr-2" />
                            Create First Volume
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <>
                    {/* Volumes */}
                    {volumes.map(volume => (
                        <Card key={volume.id}>
                            <CardContent className="p-0">
                                {/* Volume Header */}
                                <div className="flex items-center justify-between p-4 border-b">
                                    <div className="flex items-center gap-3">
                                        <button
                                            onClick={() => toggleVolume(volume.id)}
                                            className="hover:bg-muted rounded p-1"
                                        >
                                            {volume.isExpanded ? (
                                                <ChevronDown className="h-5 w-5" />
                                            ) : (
                                                <ChevronRight className="h-5 w-5" />
                                            )}
                                        </button>
                                        <h2 className="text-lg font-semibold">{volume.title}</h2>
                                    </div>
                                    <Button variant="outline" size="sm">
                                        <Plus className="h-4 w-4 mr-2" />
                                        ADD SECTION
                                    </Button>
                                </div>

                                {/* Section Table */}
                                {volume.isExpanded && (
                                    <>
                                        {/* Table Header */}
                                        <div className="grid grid-cols-[auto,2fr,1.5fr,1fr,1fr,1fr,1fr,auto] gap-4 items-center p-3 bg-muted/50 border-b font-medium text-xs text-muted-foreground uppercase tracking-wider">
                                            <div></div>
                                            <div>Title</div>
                                            <div>Status</div>
                                            <div>Owner</div>
                                            <div>Due Date</div>
                                            <div>Word Limit</div>
                                            <div>Word Count</div>
                                            <div>Actions</div>
                                        </div>

                                        {/* Sections */}
                                        {volume.sections.map(section => renderSection(volume, section))}
                                    </>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                    {/* Add Volume Button */}
                    <Button variant="outline" className="w-full border-dashed">
                        <Plus className="h-4 w-4 mr-2" />
                        Add New Volume
                    </Button>
                </>
            )}
        </div>
    );
};

export default Write;
