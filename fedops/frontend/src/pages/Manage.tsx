import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import {
    FolderKanban,
    Clock,
    Users,
    CheckCircle,
    AlertCircle,
    ArrowRight,
    Plus,
    FileText,
    Calendar,
    Loader2,
    RefreshCw
} from "lucide-react";
import {
    getProposals,
    getProposalStats,
    formatDeadline,
    type Proposal
} from "@/services/proposalService";

const Manage = () => {
    const toastContext = useToast();
    const [proposals, setProposals] = useState<Proposal[]>([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        active: 0,
        dueThisWeek: 0,
        inReview: 0,
        needsAttention: 0
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [proposalData, statsData] = await Promise.all([
                getProposals(),
                getProposalStats()
            ]);

            setProposals(proposalData);

            // Calculate stats
            const now = new Date();
            const oneWeekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

            const dueThisWeek = proposalData.filter(p => {
                if (!p.deadline) return false;
                const deadline = new Date(p.deadline);
                return deadline <= oneWeekFromNow && deadline >= now;
            }).length;

            const inReview = proposalData.filter(p => p.status === 'review').length;
            const needsAttention = proposalData.filter(p => {
                if (!p.deadline) return false;
                const deadline = new Date(p.deadline);
                const daysLeft = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
                return daysLeft <= 3 && daysLeft >= 0;
            }).length;

            setStats({
                active: statsData.active,
                dueThisWeek,
                inReview,
                needsAttention
            });
        } catch (error) {
            console.error("Failed to load proposals:", error);
            toastContext.error("Failed to load proposals");
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status: Proposal["status"]) => {
        const configs = {
            draft: { label: "Draft", className: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
            in_progress: { label: "In Progress", className: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
            review: { label: "In Review", className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
            submitted: { label: "Submitted", className: "bg-green-500/20 text-green-400 border-green-500/30" },
            awarded: { label: "Won", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
        };
        const config = configs[status] || configs.draft;
        return <Badge variant="outline" className={config.className}>{config.label}</Badge>;
    };

    const getTeamInitials = (proposal: Proposal): string[] => {
        if (proposal.team && proposal.team.length > 0) {
            return proposal.team.map(m => m.name?.split(' ').map(n => n[0]).join('') || 'U');
        }
        return ['U']; // Unknown
    };

    const statCards = [
        { label: "Active Proposals", value: stats.active, icon: FileText, color: "text-blue-400" },
        { label: "Due This Week", value: stats.dueThisWeek, icon: Clock, color: "text-yellow-400" },
        { label: "In Review", value: stats.inReview, icon: CheckCircle, color: "text-green-400" },
        { label: "Needs Attention", value: stats.needsAttention, icon: AlertCircle, color: "text-red-400" },
    ];

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Manage</h1>
                    <p className="text-muted-foreground mt-2">
                        Track and manage your proposals from strategy to submission.
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={loadData} disabled={loading}>
                        <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Link to="/opportunities">
                        <Button>
                            <Plus className="h-4 w-4 mr-2" />
                            New Proposal
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {statCards.map((stat) => {
                    const Icon = stat.icon;
                    return (
                        <Card key={stat.label}>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                                        <p className="text-2xl font-bold mt-1">
                                            {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : stat.value}
                                        </p>
                                    </div>
                                    <Icon className={`h-8 w-8 ${stat.color} opacity-80`} />
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {/* Proposals Table */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Active Proposals</CardTitle>
                            <CardDescription>Manage your ongoing proposal efforts</CardDescription>
                        </div>
                        <div className="flex gap-2">
                            <Link to="/pipeline">
                                <Button variant="outline" size="sm">
                                    <FolderKanban className="h-4 w-4 mr-2" />
                                    Kanban View
                                </Button>
                            </Link>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        </div>
                    ) : proposals.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                            <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <p>No active proposals yet</p>
                            <Link to="/opportunities">
                                <Button variant="outline" className="mt-4">
                                    Browse Opportunities
                                </Button>
                            </Link>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {proposals.map((proposal) => (
                                <div
                                    key={proposal.id}
                                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
                                >
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="font-semibold">{proposal.title}</h3>
                                            {getStatusBadge(proposal.status)}
                                        </div>
                                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                            <span className="flex items-center gap-1">
                                                <FileText className="h-3.5 w-3.5" />
                                                OPP-{proposal.opportunity_id}
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <Calendar className="h-3.5 w-3.5" />
                                                {formatDeadline(proposal.deadline)}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Progress */}
                                    <div className="flex items-center gap-4">
                                        <div className="w-32">
                                            <div className="flex items-center justify-between text-xs mb-1">
                                                <span className="text-muted-foreground">Progress</span>
                                                <span className="font-medium">{proposal.progress}%</span>
                                            </div>
                                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-primary rounded-full transition-all duration-500"
                                                    style={{ width: `${proposal.progress}%` }}
                                                />
                                            </div>
                                        </div>

                                        {/* Team Avatars */}
                                        <div className="flex -space-x-2">
                                            {getTeamInitials(proposal).slice(0, 3).map((initials, idx) => (
                                                <div
                                                    key={idx}
                                                    className="w-8 h-8 rounded-full bg-primary/20 border-2 border-background flex items-center justify-center text-xs font-medium"
                                                >
                                                    {initials}
                                                </div>
                                            ))}
                                        </div>

                                        <Link to={`/proposal-workspace/${proposal.opportunity_id}`}>
                                            <Button variant="ghost" size="sm">
                                                <ArrowRight className="h-4 w-4" />
                                            </Button>
                                        </Link>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Link to="/opportunities">
                    <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
                        <CardContent className="p-6 text-center">
                            <FileText className="h-8 w-8 mx-auto mb-3 text-primary" />
                            <h3 className="font-semibold">Browse Opportunities</h3>
                            <p className="text-sm text-muted-foreground mt-1">
                                Find and qualify new opportunities
                            </p>
                        </CardContent>
                    </Card>
                </Link>
                <Link to="/teams">
                    <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
                        <CardContent className="p-6 text-center">
                            <Users className="h-8 w-8 mx-auto mb-3 text-primary" />
                            <h3 className="font-semibold">Manage Teams</h3>
                            <p className="text-sm text-muted-foreground mt-1">
                                Configure team assignments
                            </p>
                        </CardContent>
                    </Card>
                </Link>
                <Link to="/pipeline">
                    <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
                        <CardContent className="p-6 text-center">
                            <Calendar className="h-8 w-8 mx-auto mb-3 text-primary" />
                            <h3 className="font-semibold">View Pipeline</h3>
                            <p className="text-sm text-muted-foreground mt-1">
                                See all proposals in progress
                            </p>
                        </CardContent>
                    </Card>
                </Link>
            </div>
        </div>
    );
};

export default Manage;
