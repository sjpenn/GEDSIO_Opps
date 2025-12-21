import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
    FileSearch,
    FolderKanban,
    PenTool,
    Search,
    CheckCircle,
    Plug
} from "lucide-react";

interface TabItem {
    path: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
}

const TabNavigation = () => {
    const location = useLocation();

    const tabs: TabItem[] = [
        { path: "/qualify-extract", label: "Qualify & Extract", icon: FileSearch },
        { path: "/manage", label: "Manage", icon: FolderKanban },
        { path: "/write", label: "Write", icon: PenTool },
        { path: "/research", label: "Research", icon: Search },
        { path: "/review", label: "Review", icon: CheckCircle },
        { path: "/integrations", label: "Integrations", icon: Plug },
    ];

    const isTabActive = (path: string) => {
        if (path === "/") return location.pathname === path;
        return location.pathname.startsWith(path);
    };

    return (
        <nav className="border-b border-border bg-card/50 backdrop-blur-sm">
            <div className="flex items-center gap-1 px-4 overflow-x-auto scrollbar-hide">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = isTabActive(tab.path);

                    return (
                        <Link
                            key={tab.path}
                            to={tab.path}
                            className={cn(
                                "flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all duration-200 relative whitespace-nowrap",
                                "hover:text-foreground",
                                isActive
                                    ? "text-primary"
                                    : "text-muted-foreground"
                            )}
                        >
                            <Icon className={cn(
                                "h-4 w-4 transition-colors",
                                isActive ? "text-primary" : "text-muted-foreground"
                            )} />
                            <span>{tab.label}</span>
                            {isActive && (
                                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-t-full" />
                            )}
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
};

export default TabNavigation;
