import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Trash2, Save, Loader2 } from 'lucide-react';

interface CapturePlan {
  id: number;
  proposal_id: number;
  win_strategy: string;
  executive_summary_theme: string;
  customer_hot_buttons: { issue: string; impact: string; solution: string }[];
  discriminators: { discriminator: string; proof: string }[];
  key_themes: string[];
  competitor_analysis_summary: string;
  teaming_strategy: string;
  partners: { name: string; role: string; status: string }[];
  action_items: { task: string; owner: string; due: string; status: string }[];
}

interface CapturePlanningTabProps {
  proposalId: number;
}

export default function CapturePlanningTab({ proposalId }: CapturePlanningTabProps) {
  const [plan, setPlan] = useState<CapturePlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadCapturePlan();
  }, [proposalId]);

  const loadCapturePlan = async () => {
    try {
      const res = await fetch(`/api/v1/capture/proposals/${proposalId}`);
      if (res.ok) {
        const data = await res.json();
        // Ensure arrays are initialized
        data.customer_hot_buttons = data.customer_hot_buttons || [];
        data.discriminators = data.discriminators || [];
        data.key_themes = data.key_themes || [];
        data.partners = data.partners || [];
        data.action_items = data.action_items || [];
        setPlan(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const saveCapturePlan = async () => {
    if (!plan) return;
    setSaving(true);
    try {
      await fetch(`/api/v1/capture/proposals/${proposalId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plan)
      });
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const updateField = (field: keyof CapturePlan, value: any) => {
    if (!plan) return;
    setPlan({ ...plan, [field]: value });
  };

  if (loading) return <Loader2 className="animate-spin" />;
  if (!plan) return <div>Failed to load capture plan</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Capture Planning (Phase 3)</h2>
          <p className="text-muted-foreground">Develop win strategy and refine approach</p>
        </div>
        <Button onClick={saveCapturePlan} disabled={saving}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          Save Plan
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strategy Section */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Win Strategy</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Core Win Strategy</Label>
              <Textarea 
                value={plan.win_strategy || ''} 
                onChange={e => updateField('win_strategy', e.target.value)}
                placeholder="Describe the overarching strategy to win this opportunity..."
                className="h-32"
              />
            </div>
            <div>
              <Label>Executive Summary Theme</Label>
              <Textarea 
                value={plan.executive_summary_theme || ''} 
                onChange={e => updateField('executive_summary_theme', e.target.value)}
                placeholder="The main theme that will appear in the Executive Summary..."
              />
            </div>
          </CardContent>
        </Card>

        {/* Hot Buttons */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Customer Hot Buttons</CardTitle>
              <Button variant="outline" size="sm" onClick={() => {
                const newItems = [...plan.customer_hot_buttons, { issue: '', impact: '', solution: '' }];
                updateField('customer_hot_buttons', newItems);
              }}>
                <Plus className="h-4 w-4 mr-2" /> Add Issue
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {plan.customer_hot_buttons.map((item, idx) => (
              <div key={idx} className="grid grid-cols-12 gap-2 items-start border-b pb-4 last:border-0">
                <div className="col-span-3">
                  <Label className="text-xs">Issue</Label>
                  <Input 
                    value={item.issue} 
                    onChange={e => {
                      const newItems = [...plan.customer_hot_buttons];
                      newItems[idx].issue = e.target.value;
                      updateField('customer_hot_buttons', newItems);
                    }}
                  />
                </div>
                <div className="col-span-4">
                  <Label className="text-xs">Impact</Label>
                  <Input 
                    value={item.impact} 
                    onChange={e => {
                      const newItems = [...plan.customer_hot_buttons];
                      newItems[idx].impact = e.target.value;
                      updateField('customer_hot_buttons', newItems);
                    }}
                  />
                </div>
                <div className="col-span-4">
                  <Label className="text-xs">Our Solution</Label>
                  <Input 
                    value={item.solution} 
                    onChange={e => {
                      const newItems = [...plan.customer_hot_buttons];
                      newItems[idx].solution = e.target.value;
                      updateField('customer_hot_buttons', newItems);
                    }}
                  />
                </div>
                <div className="col-span-1 pt-5">
                  <Button variant="ghost" size="sm" onClick={() => {
                    const newItems = plan.customer_hot_buttons.filter((_, i) => i !== idx);
                    updateField('customer_hot_buttons', newItems);
                  }}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
            {plan.customer_hot_buttons.length === 0 && <p className="text-sm text-muted-foreground text-center py-4">No hot buttons added yet.</p>}
          </CardContent>
        </Card>

        {/* Discriminators */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Discriminators</CardTitle>
              <Button variant="outline" size="sm" onClick={() => {
                const newItems = [...plan.discriminators, { discriminator: '', proof: '' }];
                updateField('discriminators', newItems);
              }}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {plan.discriminators.map((item, idx) => (
              <div key={idx} className="space-y-2 border-b pb-2 last:border-0">
                <div className="flex gap-2">
                  <Input 
                    placeholder="Discriminator"
                    value={item.discriminator} 
                    onChange={e => {
                      const newItems = [...plan.discriminators];
                      newItems[idx].discriminator = e.target.value;
                      updateField('discriminators', newItems);
                    }}
                  />
                  <Button variant="ghost" size="sm" onClick={() => {
                    const newItems = plan.discriminators.filter((_, i) => i !== idx);
                    updateField('discriminators', newItems);
                  }}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
                <Input 
                  placeholder="Proof Point"
                  className="text-sm"
                  value={item.proof} 
                  onChange={e => {
                    const newItems = [...plan.discriminators];
                    newItems[idx].proof = e.target.value;
                    updateField('discriminators', newItems);
                  }}
                />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Key Themes */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Key Themes</CardTitle>
              <Button variant="outline" size="sm" onClick={() => {
                const newItems = [...plan.key_themes, ''];
                updateField('key_themes', newItems);
              }}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {plan.key_themes.map((item, idx) => (
              <div key={idx} className="flex gap-2">
                <Input 
                  value={item} 
                  onChange={e => {
                    const newItems = [...plan.key_themes];
                    newItems[idx] = e.target.value;
                    updateField('key_themes', newItems);
                  }}
                />
                <Button variant="ghost" size="sm" onClick={() => {
                  const newItems = plan.key_themes.filter((_, i) => i !== idx);
                  updateField('key_themes', newItems);
                }}>
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Competitor Analysis */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Competitor Analysis Summary</CardTitle>
            <CardDescription>Synthesize insights from the Competitive Intelligence tab</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea 
              value={plan.competitor_analysis_summary || ''} 
              onChange={e => updateField('competitor_analysis_summary', e.target.value)}
              placeholder="Summarize key competitor strengths and weaknesses..."
              className="h-24"
            />
          </CardContent>
        </Card>

        {/* Teaming */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Teaming Strategy</CardTitle>
              <Button variant="outline" size="sm" onClick={() => {
                const newItems = [...plan.partners, { name: '', role: '', status: 'Identified' }];
                updateField('partners', newItems);
              }}>
                <Plus className="h-4 w-4 mr-2" /> Add Partner
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea 
              value={plan.teaming_strategy || ''} 
              onChange={e => updateField('teaming_strategy', e.target.value)}
              placeholder="Describe the teaming approach (e.g., Prime/Sub split, workshare)..."
              className="mb-4"
            />
            <div className="space-y-2">
              {plan.partners.map((item, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                  <div className="col-span-4">
                    <Input 
                      placeholder="Partner Name"
                      value={item.name} 
                      onChange={e => {
                        const newItems = [...plan.partners];
                        newItems[idx].name = e.target.value;
                        updateField('partners', newItems);
                      }}
                    />
                  </div>
                  <div className="col-span-4">
                    <Input 
                      placeholder="Role/Workshare"
                      value={item.role} 
                      onChange={e => {
                        const newItems = [...plan.partners];
                        newItems[idx].role = e.target.value;
                        updateField('partners', newItems);
                      }}
                    />
                  </div>
                  <div className="col-span-3">
                    <Input 
                      placeholder="Status"
                      value={item.status} 
                      onChange={e => {
                        const newItems = [...plan.partners];
                        newItems[idx].status = e.target.value;
                        updateField('partners', newItems);
                      }}
                    />
                  </div>
                  <div className="col-span-1">
                    <Button variant="ghost" size="sm" onClick={() => {
                      const newItems = plan.partners.filter((_, i) => i !== idx);
                      updateField('partners', newItems);
                    }}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
