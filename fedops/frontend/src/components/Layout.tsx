import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Moon, Sun, LayoutDashboard, Search, FileText, Building2, Kanban, Users, Info, Menu, Award } from "lucide-react";
import { Slideout } from "./ui/slideout";
import { useTheme } from "./theme-provider";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import TabNavigation from "./TabNavigation";

const Layout = ({ children }: { children: React.ReactNode }) => {
  const { theme, setTheme } = useTheme();
  const location = useLocation();

  // Legacy navigation items for slideout menu
  const navItems = [
    { path: "/opportunities", label: "Opportunities", icon: LayoutDashboard },
    { path: "/pipeline", label: "Pipeline", icon: Kanban },
    { path: "/entities", label: "Entity Search", icon: Search },
    { path: "/teams", label: "Partner Teams", icon: Users },
    { path: "/past-performance", label: "Past Performance", icon: Award },
    { path: "/profile", label: "Company Profile", icon: Building2 },
    { path: "/resumes", label: "Resume Manager", icon: FileText },
    { path: "/files", label: "Files & AI", icon: FileText },
    { path: "/", label: "About", icon: Info },
  ];

  const [isNavOpen, setIsNavOpen] = useState(false);
  const [isLocalLLM, setIsLocalLLM] = useState(false);

  useEffect(() => {
    fetch('/api/v1/config')
      .then(res => res.json())
      .then(data => setIsLocalLLM(data.provider === 'local'))
      .catch(console.error);
  }, []);

  const toggleLocalLLM = async (checked: boolean) => {
    const newProvider = checked ? 'local' : 'openrouter';
    try {
      const res = await fetch('/api/v1/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: newProvider })
      });
      if (res.ok) {
        setIsLocalLLM(checked);
      }
    } catch (err) {
      console.error("Failed to switch provider", err);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Legacy Navigation Slideout */}
      <Slideout
        isOpen={isNavOpen}
        onClose={() => setIsNavOpen(false)}
        title="More Options"
        width="max-w-xs"
        side="left"
      >
        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || (item.path !== "/" && location.pathname.startsWith(item.path));

            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsNavOpen(false)}
              >
                <div className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md transition-all duration-200 group",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-md"
                    : "hover:bg-muted text-muted-foreground hover:text-foreground"
                )}>
                  <Icon className={cn("h-4 w-4", isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground")} />
                  <span className="font-medium">{item.label}</span>
                </div>
              </Link>
            );
          })}
        </nav>
      </Slideout>

      {/* Main Content - Full Page */}
      <main className="flex flex-col h-screen overflow-hidden">
        {/* Header with branding and controls */}
        <header className="border-b bg-card">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsNavOpen(true)}
              >
                <Menu className="h-5 w-5" />
                <span className="sr-only">Open menu</span>
              </Button>
              <Link to="/qualify-extract" className="flex items-center gap-2">
                <span className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                  FedOps Pro
                </span>
              </Link>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch
                  id="llm-mode"
                  checked={isLocalLLM}
                  onCheckedChange={toggleLocalLLM}
                />
                <Label htmlFor="llm-mode" className="text-sm font-medium">Local LLM</Label>
              </div>

              <Button
                variant="ghost"
                size="icon"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="h-8 w-8 rounded-full"
              >
                <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                <span className="sr-only">Toggle theme</span>
              </Button>
            </div>
          </div>

          {/* Tab Navigation */}
          <TabNavigation />
        </header>

        <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 md:p-8">
          <div className="w-full">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
