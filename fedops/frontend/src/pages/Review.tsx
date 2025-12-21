import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    CheckCircle,
    XCircle,
    AlertTriangle,
    FileText,
    ThumbsUp,
    ThumbsDown,
    MessageSquare,
    BarChart3,
    RefreshCw,
    ChevronDown,
    ChevronRight
} from "lucide-react";

interface ReviewItem {
    id: string;
    section: string;
    criterion: string;
    status: "pass" | "fail" | "warning" | "pending";
    feedback: string;
    confidence: number;
}

interface ComplianceCheck {
    id: string;
    requirement: string;
    location: string;
    status: "compliant" | "non-compliant" | "partial" | "not-checked";
}

const Review = () => {
    const [activeTab, setActiveTab] = useState("compliance");
    const [expandedSections, setExpandedSections] = useState<string[]>(["technical"]);

    const reviewItems: ReviewItem[] = [
        {
            id: "1",
            section: "Technical Approach",
            criterion: "Addresses all PWS requirements",
            status: "pass",
            feedback: "All PWS items are addressed with clear solutions.",
            confidence: 95,
        },
        {
            id: "2",
            section: "Technical Approach",
            criterion: "Clear methodology presented",
            status: "pass",
            feedback: "Methodology is well-structured and follows industry standards.",
            confidence: 88,
        },
        {
            id: "3",
            section: "Technical Approach",
            criterion: "Risk mitigation plan",
            status: "warning",
            feedback: "Consider adding more detail to cybersecurity risk mitigation.",
            confidence: 72,
        },
        {
            id: "4",
            section: "Management Approach",
            criterion: "Org chart provided",
            status: "fail",
            feedback: "Missing organizational chart requirement from Section L.",
            confidence: 98,
        },
        {
            id: "5",
            section: "Past Performance",
            criterion: "Relevance to current work",
            status: "pass",
            feedback: "All past performance examples are directly relevant.",
            confidence: 91,
        },
    ];

    const complianceChecks: ComplianceCheck[] = [
        { id: "1", requirement: "Font size 12pt Times New Roman", location: "Section L.4.1", status: "compliant" },
        { id: "2", requirement: "Page limit 50 pages", location: "Section L.4.2", status: "partial" },
        { id: "3", requirement: "Single spaced text", location: "Section L.4.1", status: "compliant" },
        { id: "4", requirement: "1-inch margins", location: "Section L.4.1", status: "compliant" },
        { id: "5", requirement: "Table of Contents included", location: "Section L.5.1", status: "non-compliant" },
        { id: "6", requirement: "Executive Summary max 2 pages", location: "Section L.5.2", status: "compliant" },
    ];

    const getStatusIcon = (status: ReviewItem["status"]) => {
        switch (status) {
            case "pass": return <CheckCircle className="h-5 w-5 text-green-500" />;
            case "fail": return <XCircle className="h-5 w-5 text-red-500" />;
            case "warning": return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
            default: return <RefreshCw className="h-5 w-5 text-muted-foreground animate-spin" />;
        }
    };

    const getComplianceStatusBadge = (status: ComplianceCheck["status"]) => {
        const configs = {
            compliant: { label: "Compliant", className: "bg-green-500/20 text-green-400 border-green-500/30" },
            "non-compliant": { label: "Non-Compliant", className: "bg-red-500/20 text-red-400 border-red-500/30" },
            partial: { label: "Partial", className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
            "not-checked": { label: "Not Checked", className: "bg-muted text-muted-foreground" },
        };
        const config = configs[status];
        return <Badge variant="outline" className={config.className}>{config.label}</Badge>;
    };

    const toggleSection = (section: string) => {
        setExpandedSections(prev =>
            prev.includes(section)
                ? prev.filter(s => s !== section)
                : [...prev, section]
        );
    };

    const stats = {
        pass: reviewItems.filter(r => r.status === "pass").length,
        fail: reviewItems.filter(r => r.status === "fail").length,
        warning: reviewItems.filter(r => r.status === "warning").length,
    };

    const groupedReviews = reviewItems.reduce((acc, item) => {
        if (!acc[item.section]) acc[item.section] = [];
        acc[item.section].push(item);
        return acc;
    }, {} as Record<string, ReviewItem[]>);

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Review</h1>
                    <p className="text-muted-foreground mt-2">
                        Check your proposal for compliance and quality against evaluation criteria.
                    </p>
                </div>
                <Button>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Run Full Review
                </Button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-3 rounded-full bg-green-500/20">
                            <CheckCircle className="h-6 w-6 text-green-500" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold">{stats.pass}</p>
                            <p className="text-sm text-muted-foreground">Passing</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-3 rounded-full bg-yellow-500/20">
                            <AlertTriangle className="h-6 w-6 text-yellow-500" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold">{stats.warning}</p>
                            <p className="text-sm text-muted-foreground">Warnings</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-3 rounded-full bg-red-500/20">
                            <XCircle className="h-6 w-6 text-red-500" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold">{stats.fail}</p>
                            <p className="text-sm text-muted-foreground">Issues</p>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-4 flex items-center gap-4">
                        <div className="p-3 rounded-full bg-primary/20">
                            <BarChart3 className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold">82%</p>
                            <p className="text-sm text-muted-foreground">Overall Score</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                    <TabsTrigger value="compliance" className="gap-2">
                        <FileText className="h-4 w-4" />
                        Compliance Check
                    </TabsTrigger>
                    <TabsTrigger value="quality" className="gap-2">
                        <CheckCircle className="h-4 w-4" />
                        Quality Review
                    </TabsTrigger>
                    <TabsTrigger value="feedback" className="gap-2">
                        <MessageSquare className="h-4 w-4" />
                        Feedback
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="compliance" className="mt-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Section L Compliance</CardTitle>
                            <CardDescription>
                                Automated check against solicitation formatting requirements
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {complianceChecks.map((check) => (
                                    <div
                                        key={check.id}
                                        className="flex items-center justify-between p-4 rounded-lg border border-border"
                                    >
                                        <div className="flex items-center gap-4">
                                            {check.status === "compliant" ? (
                                                <CheckCircle className="h-5 w-5 text-green-500" />
                                            ) : check.status === "non-compliant" ? (
                                                <XCircle className="h-5 w-5 text-red-500" />
                                            ) : (
                                                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                                            )}
                                            <div>
                                                <p className="font-medium">{check.requirement}</p>
                                                <p className="text-sm text-muted-foreground">{check.location}</p>
                                            </div>
                                        </div>
                                        {getComplianceStatusBadge(check.status)}
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="quality" className="mt-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Section-by-Section Review</CardTitle>
                            <CardDescription>
                                AI-powered quality check against evaluation criteria
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {Object.entries(groupedReviews).map(([section, items]) => (
                                <div key={section} className="border rounded-lg">
                                    <button
                                        onClick={() => toggleSection(section.toLowerCase())}
                                        className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
                                    >
                                        <div className="flex items-center gap-3">
                                            {expandedSections.includes(section.toLowerCase()) ? (
                                                <ChevronDown className="h-4 w-4" />
                                            ) : (
                                                <ChevronRight className="h-4 w-4" />
                                            )}
                                            <span className="font-semibold">{section}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {items.filter(i => i.status === "pass").length > 0 && (
                                                <Badge variant="outline" className="bg-green-500/20 text-green-400">
                                                    {items.filter(i => i.status === "pass").length} pass
                                                </Badge>
                                            )}
                                            {items.filter(i => i.status === "warning").length > 0 && (
                                                <Badge variant="outline" className="bg-yellow-500/20 text-yellow-400">
                                                    {items.filter(i => i.status === "warning").length} warning
                                                </Badge>
                                            )}
                                            {items.filter(i => i.status === "fail").length > 0 && (
                                                <Badge variant="outline" className="bg-red-500/20 text-red-400">
                                                    {items.filter(i => i.status === "fail").length} issue
                                                </Badge>
                                            )}
                                        </div>
                                    </button>
                                    {expandedSections.includes(section.toLowerCase()) && (
                                        <div className="border-t p-4 space-y-3">
                                            {items.map((item) => (
                                                <div key={item.id} className="flex items-start gap-4 p-3 rounded-lg bg-muted/30">
                                                    {getStatusIcon(item.status)}
                                                    <div className="flex-1">
                                                        <p className="font-medium">{item.criterion}</p>
                                                        <p className="text-sm text-muted-foreground mt-1">{item.feedback}</p>
                                                        <div className="flex items-center gap-4 mt-2">
                                                            <span className="text-xs text-muted-foreground">
                                                                Confidence: {item.confidence}%
                                                            </span>
                                                            <Button variant="ghost" size="sm" className="h-6 text-xs">
                                                                <ThumbsUp className="h-3 w-3 mr-1" /> Agree
                                                            </Button>
                                                            <Button variant="ghost" size="sm" className="h-6 text-xs">
                                                                <ThumbsDown className="h-3 w-3 mr-1" /> Disagree
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="feedback" className="mt-6">
                    <Card>
                        <CardContent className="p-6 text-center">
                            <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                            <h3 className="font-semibold mb-2">Team Feedback</h3>
                            <p className="text-muted-foreground mb-4">
                                Collect and manage feedback from your review team
                            </p>
                            <Button>Start Feedback Session</Button>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default Review;
