import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
    Plug,
    Cloud,
    FileText,
    Zap,
    Building2,
    ExternalLink,
    CheckCircle,
    XCircle,
    Settings,
    RefreshCw
} from "lucide-react";

interface Integration {
    id: string;
    name: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    status: "connected" | "disconnected" | "error";
    category: "storage" | "automation" | "data" | "other";
    lastSync?: string;
}

const Integrations = () => {
    const integrations: Integration[] = [
        {
            id: "sharepoint",
            name: "SharePoint",
            description: "Sync documents and proposals with Microsoft SharePoint",
            icon: Cloud,
            status: "connected",
            category: "storage",
            lastSync: "2 hours ago",
        },
        {
            id: "onedrive",
            name: "OneDrive",
            description: "Access and store files in Microsoft OneDrive",
            icon: Cloud,
            status: "disconnected",
            category: "storage",
        },
        {
            id: "google-drive",
            name: "Google Drive",
            description: "Connect your Google Drive for document access",
            icon: Cloud,
            status: "disconnected",
            category: "storage",
        },
        {
            id: "zapier",
            name: "Zapier",
            description: "Automate workflows with 5,000+ apps",
            icon: Zap,
            status: "connected",
            category: "automation",
            lastSync: "5 mins ago",
        },
        {
            id: "sam-gov",
            name: "SAM.gov",
            description: "Automatic opportunity import from SAM.gov",
            icon: Building2,
            status: "connected",
            category: "data",
            lastSync: "1 hour ago",
        },
        {
            id: "fpds",
            name: "FPDS",
            description: "Federal contract data for research",
            icon: FileText,
            status: "connected",
            category: "data",
            lastSync: "30 mins ago",
        },
    ];

    const getStatusBadge = (status: Integration["status"]) => {
        const configs = {
            connected: {
                label: "Connected",
                className: "bg-green-500/20 text-green-400 border-green-500/30",
                icon: CheckCircle
            },
            disconnected: {
                label: "Not Connected",
                className: "bg-muted text-muted-foreground",
                icon: XCircle
            },
            error: {
                label: "Error",
                className: "bg-red-500/20 text-red-400 border-red-500/30",
                icon: XCircle
            },
        };
        const config = configs[status];
        const Icon = config.icon;
        return (
            <Badge variant="outline" className={config.className}>
                <Icon className="h-3 w-3 mr-1" />
                {config.label}
            </Badge>
        );
    };

    const storageIntegrations = integrations.filter(i => i.category === "storage");
    const automationIntegrations = integrations.filter(i => i.category === "automation");
    const dataIntegrations = integrations.filter(i => i.category === "data");

    const renderIntegrationCard = (integration: Integration) => {
        const Icon = integration.icon;
        return (
            <Card key={integration.id} className="hover:border-primary/50 transition-colors">
                <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-lg bg-primary/10">
                                <Icon className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h3 className="font-semibold">{integration.name}</h3>
                                <p className="text-sm text-muted-foreground">{integration.description}</p>
                            </div>
                        </div>
                        <Switch checked={integration.status === "connected"} />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {getStatusBadge(integration.status)}
                            {integration.lastSync && (
                                <span className="text-xs text-muted-foreground">
                                    Last sync: {integration.lastSync}
                                </span>
                            )}
                        </div>
                        <div className="flex gap-2">
                            {integration.status === "connected" && (
                                <Button variant="ghost" size="sm">
                                    <RefreshCw className="h-4 w-4" />
                                </Button>
                            )}
                            <Button variant="ghost" size="sm">
                                <Settings className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        );
    };

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold">Integrations</h1>
                <p className="text-muted-foreground mt-2">
                    Connect external services to streamline your proposal workflow.
                </p>
            </div>

            {/* Storage Integrations */}
            <div className="space-y-4">
                <div className="flex items-center gap-2">
                    <Cloud className="h-5 w-5 text-muted-foreground" />
                    <h2 className="text-xl font-semibold">Cloud Storage</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {storageIntegrations.map(renderIntegrationCard)}
                </div>
            </div>

            {/* Data Integrations */}
            <div className="space-y-4">
                <div className="flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-muted-foreground" />
                    <h2 className="text-xl font-semibold">Government Data</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {dataIntegrations.map(renderIntegrationCard)}
                </div>
            </div>

            {/* Automation Integrations */}
            <div className="space-y-4">
                <div className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-muted-foreground" />
                    <h2 className="text-xl font-semibold">Automation</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {automationIntegrations.map(renderIntegrationCard)}
                </div>
            </div>

            {/* API Access */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Plug className="h-5 w-5" />
                        API Access
                    </CardTitle>
                    <CardDescription>
                        Use our API to build custom integrations
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                        <div>
                            <p className="font-medium">API Key</p>
                            <p className="text-sm text-muted-foreground font-mono">
                                fedops_sk_••••••••••••••••••••
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm">
                                Regenerate
                            </Button>
                            <Button variant="outline" size="sm">
                                View Docs
                                <ExternalLink className="h-3 w-3 ml-2" />
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default Integrations;
