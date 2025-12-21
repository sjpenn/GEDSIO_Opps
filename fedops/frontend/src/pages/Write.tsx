import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Sparkles,
    BookOpen,
    Lightbulb,
    ChevronRight,
    MessageSquare,
    History,
    Wand2
} from "lucide-react";

interface Section {
    id: string;
    title: string;
    status: "not-started" | "drafting" | "review" | "complete";
    wordCount: number;
    targetWords: number;
}

const Write = () => {
    const [activeSection, setActiveSection] = useState<string | null>(null);
    const [content, setContent] = useState("");

    const sections: Section[] = [
        { id: "exec-summary", title: "Executive Summary", status: "complete", wordCount: 850, targetWords: 1000 },
        { id: "technical", title: "Technical Approach", status: "drafting", wordCount: 2100, targetWords: 5000 },
        { id: "management", title: "Management Approach", status: "not-started", wordCount: 0, targetWords: 3000 },
        { id: "past-perf", title: "Past Performance", status: "review", wordCount: 1500, targetWords: 1500 },
        { id: "pricing", title: "Pricing Volume", status: "not-started", wordCount: 0, targetWords: 500 },
    ];

    const getStatusBadge = (status: Section["status"]) => {
        const configs = {
            "not-started": { label: "Not Started", className: "bg-muted text-muted-foreground" },
            drafting: { label: "Drafting", className: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
            review: { label: "In Review", className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
            complete: { label: "Complete", className: "bg-green-500/20 text-green-400 border-green-500/30" },
        };
        const config = configs[status];
        return <Badge variant="outline" className={config.className}>{config.label}</Badge>;
    };

    const aiTools = [
        { id: "ideate", label: "Ideate", icon: Lightbulb, description: "Generate ideas and outlines" },
        { id: "improve", label: "Improve", icon: Wand2, description: "Enhance your writing" },
        { id: "sources", label: "Source Finder", icon: BookOpen, description: "Find relevant sources" },
        { id: "chat", label: "Ask AI", icon: MessageSquare, description: "Get writing assistance" },
    ];

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold">Write</h1>
                <p className="text-muted-foreground mt-2">
                    AI-powered proposal writing with intelligent assistance and source verification.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Left Sidebar - Sections */}
                <div className="lg:col-span-1">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg">Proposal Sections</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            {sections.map((section) => (
                                <button
                                    key={section.id}
                                    onClick={() => setActiveSection(section.id)}
                                    className={`w-full text-left p-3 rounded-lg transition-colors ${activeSection === section.id
                                        ? "bg-primary/20 border border-primary/50"
                                        : "hover:bg-muted"
                                        }`}
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="font-medium text-sm">{section.title}</span>
                                        <ChevronRight className={`h-4 w-4 transition-transform ${activeSection === section.id ? "rotate-90" : ""
                                            }`} />
                                    </div>
                                    <div className="flex items-center justify-between">
                                        {getStatusBadge(section.status)}
                                        <span className="text-xs text-muted-foreground">
                                            {section.wordCount}/{section.targetWords}
                                        </span>
                                    </div>
                                    <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-primary rounded-full"
                                            style={{ width: `${Math.min((section.wordCount / section.targetWords) * 100, 100)}%` }}
                                        />
                                    </div>
                                </button>
                            ))}
                        </CardContent>
                    </Card>
                </div>

                {/* Center - Editor */}
                <div className="lg:col-span-2">
                    <Card className="h-[600px] flex flex-col">
                        <CardHeader className="pb-3 border-b">
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle>Technical Approach</CardTitle>
                                    <CardDescription>Section 2 of 5 • 2,100 / 5,000 words</CardDescription>
                                </div>
                                <div className="flex gap-2">
                                    <Button variant="outline" size="sm">
                                        <History className="h-4 w-4 mr-2" />
                                        History
                                    </Button>
                                    <Button size="sm">
                                        Save Draft
                                    </Button>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="flex-1 p-0">
                            <textarea
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                placeholder="Start writing your technical approach here...

The AI assistant on the right can help you:
• Generate outlines and ideas
• Improve your writing style
• Find relevant sources from your library
• Answer questions about requirements"
                                className="w-full h-full p-6 bg-transparent resize-none focus:outline-none text-foreground placeholder:text-muted-foreground"
                            />
                        </CardContent>
                    </Card>
                </div>

                {/* Right Sidebar - AI Assistance */}
                <div className="lg:col-span-1">
                    <Card className="h-[600px] flex flex-col">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Sparkles className="h-5 w-5 text-primary" />
                                AI Assistant
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 flex flex-col">
                            <Tabs defaultValue="tools" className="flex-1 flex flex-col">
                                <TabsList className="grid w-full grid-cols-2">
                                    <TabsTrigger value="tools">Tools</TabsTrigger>
                                    <TabsTrigger value="chat">Chat</TabsTrigger>
                                </TabsList>

                                <TabsContent value="tools" className="flex-1 mt-4 space-y-3">
                                    {aiTools.map((tool) => {
                                        const Icon = tool.icon;
                                        return (
                                            <button
                                                key={tool.id}
                                                className="w-full p-3 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 transition-colors text-left"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 rounded-lg bg-primary/10">
                                                        <Icon className="h-4 w-4 text-primary" />
                                                    </div>
                                                    <div>
                                                        <p className="font-medium text-sm">{tool.label}</p>
                                                        <p className="text-xs text-muted-foreground">{tool.description}</p>
                                                    </div>
                                                </div>
                                            </button>
                                        );
                                    })}

                                    <div className="pt-4 border-t mt-4">
                                        <h4 className="text-sm font-medium mb-3">Quick Actions</h4>
                                        <div className="flex flex-wrap gap-2">
                                            <Button variant="outline" size="sm">Expand</Button>
                                            <Button variant="outline" size="sm">Condense</Button>
                                            <Button variant="outline" size="sm">Formalize</Button>
                                            <Button variant="outline" size="sm">Simplify</Button>
                                        </div>
                                    </div>
                                </TabsContent>

                                <TabsContent value="chat" className="flex-1 mt-4 flex flex-col">
                                    <div className="flex-1 border rounded-lg p-4 bg-muted/30 mb-3">
                                        <p className="text-sm text-muted-foreground text-center">
                                            Ask me anything about your proposal...
                                        </p>
                                    </div>
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            placeholder="Type a message..."
                                            className="flex-1 px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                        />
                                        <Button size="sm">
                                            <MessageSquare className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default Write;
