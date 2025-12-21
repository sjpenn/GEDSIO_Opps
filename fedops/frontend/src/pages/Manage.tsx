import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    FolderKanban,
    Clock,
    Users,
    CheckCircle,
    AlertCircle,
    ArrowRight,
    Plus,
    FileText,
    Calendar
} from "lucide-react";

interface Proposal {
    id: string;
    title: string;
    opportunity: string;
    status: "preparing" | "in-progress" | "review" | "submitted" | "won" | "lost";
    dueDate: string;
    daysRemaining: number;
    owner: string;
    team: string[];
    progress: number;
}

const Manage = () => {
    // Demo data
    const proposals: Proposal[] = [
        {
            id: "1",
            title: "Cloud Migration Services",
            opportunity: "DOD-2024-0001",
            status: "in-progress",
            dueDate: "Jan 15, 2025",
            daysRemaining: 25,
            owner: "John Doe",
            team: ["JD", "AS", "MK"],
            progress: 65,
        },
        {
            id: "2",
            title: "Cybersecurity Assessment",
            opportunity: "DHS-2024-0045",
            status: "review",
            dueDate: "Dec 30, 2024",
            daysRemaining: 9,
            owner: "Sarah Miller",
            team: ["SM", "RJ"],
            progress: 90,
        },
        {
            id: "3",
            title: "Data Analytics Platform",
            opportunity: "VA-2024-0112",
            status: "preparing",
            dueDate: "Feb 1, 2025",
            daysRemaining: 42,
            owner: "Michael Chen",
            team: ["MC", "LP", "AS", "NK"],
            progress: 25,
        },
    ];

    const getStatusBadge = (status: Proposal["status"]) => {
        const configs = {
            preparing: { label: "Preparing", className: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
            "in-progress": { label: "In Progress", className: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
            review: { label: "In Review", className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
            submitted: { label: "Submitted", className: "bg-green-500/20 text-green-400 border-green-500/30" },
            won: { label: "Won", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
            lost: { label: "Lost", className: "bg-red-500/20 text-red-400 border-red-500/30" },
        };
        const config = configs[status];
        return <Badge variant="outline" className={config.className}>{config.label}</Badge>;
    };

    const stats = [
        { label: "Active Proposals", value: "12", icon: FileText, color: "text-blue-400" },
        { label: "Due This Week", value: "3", icon: Clock, color: "text-yellow-400" },
        { label: "In Review", value: "4", icon: CheckCircle, color: "text-green-400" },
        { label: "Needs Attention", value: "2", icon: AlertCircle, color: "text-red-400" },
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
                <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Proposal
                </Button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => {
                    const Icon = stat.icon;
                    return (
                        <Card key={stat.label}>
                            <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                                        <p className="text-2xl font-bold mt-1">{stat.value}</p>
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
                            <Button variant="outline" size="sm">
                                <FolderKanban className="h-4 w-4 mr-2" />
                                Kanban View
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
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
                                            {proposal.opportunity}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <Calendar className="h-3.5 w-3.5" />
                                            Due: {proposal.dueDate}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <Users className="h-3.5 w-3.5" />
                                            {proposal.owner}
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
                                        {proposal.team.slice(0, 3).map((member, idx) => (
                                            <div
                                                key={idx}
                                                className="w-8 h-8 rounded-full bg-primary/20 border-2 border-background flex items-center justify-center text-xs font-medium"
                                            >
                                                {member}
                                            </div>
                                        ))}
                                        {proposal.team.length > 3 && (
                                            <div className="w-8 h-8 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs font-medium">
                                                +{proposal.team.length - 3}
                                            </div>
                                        )}
                                    </div>

                                    <Link to={`/proposal-workspace/${proposal.id}`}>
                                        <Button variant="ghost" size="sm">
                                            <ArrowRight className="h-4 w-4" />
                                        </Button>
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                    <CardContent className="p-6 text-center">
                        <FileText className="h-8 w-8 mx-auto mb-3 text-primary" />
                        <h3 className="font-semibold">Import Opportunity</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            Create a proposal from SAM.gov
                        </p>
                    </CardContent>
                </Card>
                <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                    <CardContent className="p-6 text-center">
                        <Users className="h-8 w-8 mx-auto mb-3 text-primary" />
                        <h3 className="font-semibold">Assign Team</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            Configure team assignments
                        </p>
                    </CardContent>
                </Card>
                <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                    <CardContent className="p-6 text-center">
                        <Calendar className="h-8 w-8 mx-auto mb-3 text-primary" />
                        <h3 className="font-semibold">View Calendar</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            See upcoming deadlines
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Manage;
