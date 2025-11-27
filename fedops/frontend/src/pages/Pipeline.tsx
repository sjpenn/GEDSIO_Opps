import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, ArrowRight, Calendar, FileText, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from "@/lib/utils";

interface PipelineItem {
  pipeline: {
    id: number;
    opportunity_id: number;
    status: string;
    stage: string;
    questions_due_date: string | null;
    proposal_due_date: string | null;
    submission_instructions: string | null;
    notes: string | null;
  };
  opportunity: {
    id: number;
    title: string;
    notice_id: string;
    department: string;
    response_deadline: string;
  };
}

const STAGES = {
  'QUALIFICATION': { label: 'Qualification', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  'PROPOSAL_DEV': { label: 'Proposal Dev', color: 'bg-purple-100 text-purple-800 border-purple-200' },
  'REVIEW': { label: 'Review', color: 'bg-orange-100 text-orange-800 border-orange-200' },
  'SUBMISSION': { label: 'Submission', color: 'bg-green-100 text-green-800 border-green-200' }
};

export default function PipelinePage() {
  const [items, setItems] = useState<PipelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPipeline();
  }, []);

  const fetchPipeline = async () => {
    try {
      const res = await fetch('/api/v1/pipeline/');
      if (res.ok) {
        const data = await res.json();
        setItems(data);
      }
    } catch (error) {
      console.error("Failed to fetch pipeline", error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysRemaining = (dateStr: string | null) => {
    if (!dateStr) return null;
    const due = new Date(dateStr);
    const now = new Date();
    const diff = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 p-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Pipeline Dashboard</h2>
        <p className="text-muted-foreground">Track and manage your active opportunities.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Object.entries(STAGES).map(([stageKey, stageConfig]) => (
          <div key={stageKey} className="space-y-4">
            <div className={cn("p-3 rounded-lg border font-semibold text-center", stageConfig.color)}>
              {stageConfig.label}
              <Badge variant="secondary" className="ml-2 bg-white/50 text-inherit border-0">
                {items.filter(i => i.pipeline.stage === stageKey).length}
              </Badge>
            </div>
            
            <ScrollArea className="h-[calc(100vh-250px)]">
              <div className="space-y-3 pr-4">
                {items
                  .filter(i => i.pipeline.stage === stageKey)
                  .map(item => {
                    const daysLeft = getDaysRemaining(item.pipeline.proposal_due_date || item.opportunity.response_deadline);
                    return (
                      <Card 
                        key={item.pipeline.id} 
                        className="cursor-pointer hover:shadow-md transition-all border-l-4 border-l-primary/0 hover:border-l-primary"
                        onClick={() => navigate(`/analysis/${item.opportunity.id}`)}
                      >
                        <CardContent className="p-4 space-y-3">
                          <div>
                            <div className="flex justify-between items-start mb-1">
                              <Badge variant="outline" className="text-[10px] font-mono">
                                {item.opportunity.notice_id}
                              </Badge>
                              {daysLeft !== null && (
                                <Badge variant={daysLeft < 5 ? "destructive" : "secondary"} className="text-[10px]">
                                  {daysLeft} days left
                                </Badge>
                              )}
                            </div>
                            <h4 className="font-semibold text-sm line-clamp-2" title={item.opportunity.title}>
                              {item.opportunity.title}
                            </h4>
                            <p className="text-xs text-muted-foreground mt-1">{item.opportunity.department}</p>
                          </div>
                          
                          <div className="pt-2 border-t flex justify-between items-center text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(item.pipeline.proposal_due_date || item.opportunity.response_deadline).toLocaleDateString()}
                            </div>
                            {item.pipeline.status === 'GO' && <CheckCircle className="h-3 w-3 text-green-500" />}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                  
                {items.filter(i => i.pipeline.stage === stageKey).length === 0 && (
                  <div className="text-center py-8 text-muted-foreground text-sm border-2 border-dashed rounded-lg">
                    No items
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        ))}
      </div>
    </div>
  );
}
