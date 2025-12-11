import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Loader2, Target, AlertTriangle, List, DollarSign, Users, ExternalLink, 
  RefreshCw, Save, Trash2, ChevronDown, ChevronRight, Bookmark,
  Plane, Shield, Heart, Landmark, Zap, Rocket, GraduationCap, Building2,
  TrendingUp, TrendingDown, Minus, Scale, Wheat
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

// --- Types ---
interface OrgNode {
  name: string;
  title?: string;
  icon_type: string;
  children: OrgNode[];
}

interface LOBItem {
  name: string;
  description: string;
  responsibilities: string[];
  key_programs: string[];
  budget_share?: string;
}

interface BudgetItem {
  division: string;
  amount?: string;
  percentage?: number;
  trend?: string;
}

interface AgencyAnalysisData {
  agency_name: string;
  acronym?: string;
  overview: string;
  strategic_goals: string[];
  budget_outlook: string;
  org_structure: string;
  org_tree?: OrgNode;
  key_bureaus: string[];
  lines_of_business: LOBItem[];
  budget_by_division: BudgetItem[];
  pain_points: string[];
  procurement_priorities: string[];
  citations: { title: string; url: string }[];
  analyzed_at?: string;
}

interface SavedAgency {
  id: number;
  agency_name: string;
  acronym?: string;
  icon_type: string;
  last_refreshed_at?: string;
}

// --- Icon Mapping ---
const getAgencyIcon = (iconType: string) => {
  const icons: Record<string, React.ReactNode> = {
    aviation: <Plane className="h-4 w-4" />,
    military: <Shield className="h-4 w-4" />,
    health: <Heart className="h-4 w-4" />,
    finance: <DollarSign className="h-4 w-4" />,
    legislative: <Landmark className="h-4 w-4" />,
    justice: <Scale className="h-4 w-4" />,
    shield: <Shield className="h-4 w-4" />,
    energy: <Zap className="h-4 w-4" />,
    rocket: <Rocket className="h-4 w-4" />,
    agriculture: <Wheat className="h-4 w-4" />,
    veteran: <Shield className="h-4 w-4" />,
    education: <GraduationCap className="h-4 w-4" />,
    default: <Building2 className="h-4 w-4" />,
    leadership: <Users className="h-4 w-4" />,
  };
  return icons[iconType] || icons.default;
};

const CHART_COLORS = ['#F59E0B', '#3B82F6', '#10B981', '#8B5CF6', '#EC4899', '#06B6D4', '#EF4444', '#84CC16'];

// --- Org Tree Component ---
function OrgTreeNode({ node, level = 0 }: { node: OrgNode; level?: number }) {
  const [expanded, setExpanded] = useState(level < 2);
  const hasChildren = node.children && node.children.length > 0;
  
  return (
    <div className="select-none">
      <div 
        className={`flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors hover:bg-primary/10 ${level === 0 ? 'bg-primary/5' : ''}`}
        style={{ marginLeft: level * 16 }}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {hasChildren ? (
          expanded ? <ChevronDown className="h-3 w-3 text-muted-foreground" /> : <ChevronRight className="h-3 w-3 text-muted-foreground" />
        ) : <span className="w-3" />}
        <span className="text-primary">{getAgencyIcon(node.icon_type)}</span>
        <span className={`text-sm ${level === 0 ? 'font-semibold' : 'font-medium'}`}>{node.name}</span>
        {node.title && <span className="text-xs text-muted-foreground ml-1">({node.title})</span>}
      </div>
      {expanded && hasChildren && (
        <div className="border-l border-primary/20 ml-4">
          {node.children.map((child, i) => (
            <OrgTreeNode key={i} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

// --- Trend Icon ---
function TrendIcon({ trend }: { trend?: string }) {
  if (trend === 'increasing') return <TrendingUp className="h-3 w-3 text-green-500" />;
  if (trend === 'decreasing') return <TrendingDown className="h-3 w-3 text-red-500" />;
  return <Minus className="h-3 w-3 text-muted-foreground" />;
}

// --- Main Component ---
export default function AgencyAnalysis() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [analysis, setAnalysis] = useState<AgencyAnalysisData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedAgencies, setSavedAgencies] = useState<SavedAgency[]>([]);

  // Fetch saved agencies on mount
  useEffect(() => {
    fetchSavedAgencies();
  }, []);

  const fetchSavedAgencies = async () => {
    try {
      const res = await fetch('/api/v1/agency_intel/saved');
      if (res.ok) {
        setSavedAgencies(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch saved agencies:', err);
    }
  };

  const handleResearch = async () => {
    if (!query) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/agency_intel/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agency_name: query })
      });
      if (!res.ok) throw new Error('Failed to fetch agency research');
      setAnalysis(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!analysis) return;
    setSaving(true);
    try {
      const res = await fetch(`/api/v1/agency_intel/save/${encodeURIComponent(analysis.agency_name)}`, { method: 'POST' });
      if (res.ok) {
        fetchSavedAgencies();
      }
    } catch (err) {
      console.error('Failed to save:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleLoadSaved = async (saved: SavedAgency) => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/agency_intel/saved/${saved.id}`);
      if (res.ok) {
        const data = await res.json();
        setAnalysis(data);
        setQuery(data.agency_name);
      }
    } catch (err) {
      console.error('Failed to load:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`/api/v1/agency_intel/saved/${id}`, { method: 'DELETE' });
      fetchSavedAgencies();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  // Prepare budget chart data
  const budgetChartData = analysis?.budget_by_division?.filter(b => b.percentage).map(b => ({
    name: b.division,
    value: b.percentage || 0,
    amount: b.amount
  })) || [];

  return (
    <div className="flex gap-6">
      {/* Saved Searches Sidebar */}
      <div className="w-64 shrink-0">
        <Card className="sticky top-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Bookmark className="h-4 w-4 text-primary" /> Saved Agencies
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 max-h-[400px] overflow-y-auto">
            {savedAgencies.length === 0 ? (
              <p className="text-xs text-muted-foreground italic py-2">No saved agencies yet</p>
            ) : (
              savedAgencies.map(saved => (
                <div 
                  key={saved.id}
                  className="flex items-center justify-between p-2 rounded-md cursor-pointer hover:bg-accent/50 group"
                  onClick={() => handleLoadSaved(saved)}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-primary">{getAgencyIcon(saved.icon_type)}</span>
                    <span className="text-sm font-medium truncate">{saved.acronym || saved.agency_name}</span>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-6 w-6 opacity-0 group-hover:opacity-100"
                    onClick={(e) => handleDelete(saved.id, e)}
                  >
                    <Trash2 className="h-3 w-3 text-destructive" />
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Search */}
        <div className="flex gap-2">
          <input 
            className="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="e.g. Department of Veterans Affairs"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleResearch()}
          />
          <Button onClick={handleResearch} disabled={loading || !query}>
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Target className="mr-2 h-4 w-4" />}
            Research
          </Button>
        </div>

        {error && (
          <div className="text-red-600 text-sm bg-red-50 dark:bg-red-950 p-3 rounded-md">
            {error}
          </div>
        )}

        {analysis && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  {analysis.agency_name}
                  {analysis.acronym && <Badge variant="outline">{analysis.acronym}</Badge>}
                </h2>
                <p className="text-muted-foreground mt-1 max-w-3xl">{analysis.overview}</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleSave} disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                  Save
                </Button>
                <Button variant="outline" size="sm" onClick={handleResearch} disabled={loading}>
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>

            {/* Org Tree & Budget Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Org Chart Tree */}
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Users className="h-4 w-4 text-primary" /> Organization Chart
                    </CardTitle>
                    {analysis.analyzed_at && (
                      <span className="text-[10px] text-muted-foreground">As of {new Date(analysis.analyzed_at).toLocaleDateString()}</span>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {analysis.org_tree ? (
                    <OrgTreeNode node={analysis.org_tree} />
                  ) : (
                    <div>
                      <p className="text-sm mb-3 leading-relaxed">{analysis.org_structure}</p>
                      {analysis.key_bureaus.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {analysis.key_bureaus.map((bureau, i) => (
                            <Badge key={i} variant="outline" className="text-xs">{bureau}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Budget Chart */}
              {budgetChartData.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base flex items-center gap-2 text-green-700 dark:text-green-400">
                        <DollarSign className="h-4 w-4" /> Budget by Division
                      </CardTitle>
                      {analysis.analyzed_at && (
                        <span className="text-[10px] text-muted-foreground">As of {new Date(analysis.analyzed_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[200px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={budgetChartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={40}
                            outerRadius={80}
                            paddingAngle={2}
                            dataKey="value"
                            label={({ name, value }) => `${name}: ${value}%`}
                            labelLine={false}
                          >
                            {budgetChartData.map((_, index) => (
                              <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip 
                            formatter={(value: number, name: string, props: any) => [`${value}% (${props.payload.amount || 'N/A'})`, name]}
                            contentStyle={{ backgroundColor: '#1E293B', border: 'none', borderRadius: '8px' }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    {/* Budget table */}
                    <div className="mt-4 space-y-1">
                      {analysis.budget_by_division.map((b, i) => (
                        <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-muted last:border-0">
                          <span className="font-medium">{b.division}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">{b.amount}</span>
                            <TrendIcon trend={b.trend} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Lines of Business */}
            {analysis.lines_of_business.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2 text-purple-700 dark:text-purple-400">
                    <List className="h-4 w-4" /> Lines of Business
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysis.lines_of_business.map((lob, i) => (
                      <div key={i} className="p-4 border rounded-lg bg-muted/30">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold text-sm">{lob.name}</h4>
                          {lob.budget_share && <Badge variant="secondary" className="text-xs">{lob.budget_share}</Badge>}
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">{lob.description}</p>
                        {lob.responsibilities.length > 0 && (
                          <div className="mb-2">
                            <span className="text-[10px] uppercase text-muted-foreground font-semibold">Responsibilities:</span>
                            <ul className="text-xs mt-1 space-y-0.5">
                              {lob.responsibilities.slice(0, 3).map((r, j) => (
                                <li key={j} className="flex gap-1"><span className="text-primary">•</span>{r}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {lob.key_programs.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {lob.key_programs.slice(0, 3).map((p, j) => (
                              <Badge key={j} variant="outline" className="text-[10px]">{p}</Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Goals, Pain Points, Priorities Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Strategic Goals */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2 text-blue-700 dark:text-blue-400">
                    <Target className="h-4 w-4" /> Strategic Goals
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {analysis.strategic_goals.map((goal, i) => (
                      <li key={i} className="text-sm flex gap-2"><span className="text-blue-500">•</span>{goal}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Pain Points */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2 text-red-700 dark:text-red-400">
                    <AlertTriangle className="h-4 w-4" /> Challenges
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {analysis.pain_points.map((point, i) => (
                      <li key={i} className="text-sm flex gap-2"><span className="text-red-500">•</span>{point}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* Procurement Priorities */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2 text-green-700 dark:text-green-400">
                    <List className="h-4 w-4" /> Procurement Priorities
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {analysis.procurement_priorities.map((item, i) => (
                      <li key={i} className="text-sm flex gap-2"><Badge variant="secondary" className="text-[10px]">Priority</Badge>{item}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>

            {/* Budget Outlook */}
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2 text-green-700 dark:text-green-400">
                    <DollarSign className="h-4 w-4" /> Budget Outlook
                  </CardTitle>
                  {analysis.analyzed_at && (
                    <span className="text-[10px] text-muted-foreground">As of {new Date(analysis.analyzed_at).toLocaleDateString()}</span>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed">{analysis.budget_outlook}</p>
              </CardContent>
            </Card>
           
            {/* Citations */}
            {analysis.citations?.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Sources</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1">
                    {analysis.citations.map((c, i) => (
                      <li key={i} className="text-xs flex items-center gap-2">
                        <span className="text-muted-foreground">[{i + 1}]</span>
                        <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline flex items-center gap-1">
                          {c.title} <ExternalLink className="h-3 w-3" />
                        </a>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
