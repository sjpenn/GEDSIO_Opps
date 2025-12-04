import { Link, useLocation } from "react-router-dom";
import { Moon, Sun, LayoutDashboard, Search, FileText, Building2, Kanban, Users, Info } from "lucide-react";
import { useTheme } from "./theme-provider";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";

const Layout = ({ children }: { children: React.ReactNode }) => {
  const { theme, setTheme } = useTheme();
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Opportunities", icon: LayoutDashboard },
    { path: "/pipeline", label: "Pipeline", icon: Kanban },
    { path: "/entities", label: "Entity Search", icon: Search },
    { path: "/teams", label: "Partner Teams", icon: Users },
    { path: "/profile", label: "Company Profile", icon: Building2 },
    { path: "/files", label: "Files & AI", icon: FileText },
    { path: "/about", label: "About", icon: Info },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r bg-card hidden md:flex flex-col">
        <div className="p-6 border-b">
          <h1 className="text-2xl font-bold text-primary tracking-tight">FedOps</h1>
          <p className="text-xs text-muted-foreground mt-1">Government Opportunity Intelligence</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || (item.path !== "/" && location.pathname.startsWith(item.path));
            
            return (
              <Link key={item.path} to={item.path}>
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

        <div className="p-4 border-t">
          <div className="flex items-center justify-between px-3 py-2 bg-muted/50 rounded-lg">
            <span className="text-sm font-medium">Theme</span>
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
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Mobile Header (visible only on small screens) */}
        <header className="md:hidden border-b bg-card p-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">FedOps</h1>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </header>

        <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 md:p-8">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
