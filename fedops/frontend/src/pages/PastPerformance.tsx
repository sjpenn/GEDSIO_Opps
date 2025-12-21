import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Loader2, Plus, FileText, Download, Trash2, Edit, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  pastPerformanceService,
  type PastPerformance,
  type QuestionnaireTemplate
} from '@/services/pastPerformanceService';
import { useToast } from '@/components/ui/toast';

export default function PastPerformancePage() {
  const toast = useToast();
  const [searchParams] = useSearchParams();
  const entityUei = searchParams.get('entity');

  const [pastPerformances, setPastPerformances] = useState<PastPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPP, setSelectedPP] = useState<PastPerformance | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [template, setTemplate] = useState<QuestionnaireTemplate | null>(null);

  // Create form state
  const [createForm, setCreateForm] = useState({
    entity_uei: entityUei || '',
    title: '',
    award_id: '',
    opportunity_id: ''
  });

  useEffect(() => {
    loadTemplate();
    if (entityUei) {
      loadPastPerformances(entityUei);
    } else {
      loadAllPastPerformances();
    }
  }, [entityUei]);

  const loadTemplate = async () => {
    try {
      const tmpl = await pastPerformanceService.getTemplate();
      setTemplate(tmpl);
    } catch (error) {
      console.error('Failed to load template:', error);
    }
  };

  const loadPastPerformances = async (uei: string) => {
    setLoading(true);
    try {
      const data = await pastPerformanceService.listByEntity(uei);
      setPastPerformances(data);
    } catch (error) {
      console.error('Failed to load past performances:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAllPastPerformances = async () => {
    setLoading(true);
    try {
      const data = await pastPerformanceService.listAll();
      setPastPerformances(data);
    } catch (error) {
      console.error('Failed to load past performances:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const newPP = await pastPerformanceService.create({
        entity_uei: createForm.entity_uei,
        title: createForm.title,
        award_id: createForm.award_id || undefined,
        opportunity_id: createForm.opportunity_id ? parseInt(createForm.opportunity_id) : undefined
      });

      setPastPerformances([newPP, ...pastPerformances]);
      setShowCreateDialog(false);
      setCreateForm({ entity_uei: entityUei || '', title: '', award_id: '', opportunity_id: '' });

      // Open editor for new past performance
      setSelectedPP(newPP);
      setShowEditor(true);
    } catch (error: any) {
      toast.error(error.message || 'Failed to create past performance');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this past performance?')) return;

    try {
      await pastPerformanceService.delete(id);
      setPastPerformances(pastPerformances.filter(pp => pp.id !== id));
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete past performance');
    }
  };

  const handleExport = async (id: number, format: 'json' | 'text' | 'markdown') => {
    try {
      const result = await pastPerformanceService.export(id, { format, include_metadata: true });

      // Download the exported content
      const blob = new Blob([typeof result.content === 'string' ? result.content : JSON.stringify(result.content, null, 2)], {
        type: format === 'json' ? 'application/json' : 'text/plain'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `past-performance-${id}.${format === 'markdown' ? 'md' : format === 'json' ? 'json' : 'txt'}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error: any) {
      toast.error(error.message || 'Failed to export past performance');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT': return 'bg-gray-500';
      case 'IN_PROGRESS': return 'bg-blue-500';
      case 'COMPLETE': return 'bg-green-500';
      case 'APPROVED': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  if (showEditor && selectedPP) {
    return (
      <PastPerformanceEditor
        pastPerformance={selectedPP}
        template={template}
        onClose={() => {
          setShowEditor(false);
          setSelectedPP(null);
          if (entityUei) {
            loadPastPerformances(entityUei);
          } else {
            loadAllPastPerformances();
          }
        }}
        onUpdate={(updated) => {
          setPastPerformances(pastPerformances.map(pp => pp.id === updated.id ? updated : pp));
          setSelectedPP(updated);
        }}
      />
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Past Performance</h2>
          <p className="text-muted-foreground">
            Manage past performance questionnaires for proposals
          </p>
        </div>

        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Past Performance
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Past Performance</DialogTitle>
              <DialogDescription>
                Create a new past performance questionnaire
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div>
                <Label htmlFor="entity_uei">Entity UEI *</Label>
                <Input
                  id="entity_uei"
                  value={createForm.entity_uei}
                  onChange={(e) => setCreateForm({ ...createForm, entity_uei: e.target.value })}
                  placeholder="Enter UEI"
                />
              </div>

              <div>
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  value={createForm.title}
                  onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                  placeholder="e.g., IT Infrastructure Support for DoD"
                />
              </div>

              <div>
                <Label htmlFor="award_id">Award ID (Optional)</Label>
                <Input
                  id="award_id"
                  value={createForm.award_id}
                  onChange={(e) => setCreateForm({ ...createForm, award_id: e.target.value })}
                  placeholder="Link to an award"
                />
              </div>

              <div>
                <Label htmlFor="opportunity_id">Opportunity ID (Optional)</Label>
                <Input
                  id="opportunity_id"
                  type="number"
                  value={createForm.opportunity_id}
                  onChange={(e) => setCreateForm({ ...createForm, opportunity_id: e.target.value })}
                  placeholder="Link to an opportunity"
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={!createForm.entity_uei || !createForm.title}>
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : pastPerformances.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Past Performances</h3>
            <p className="text-muted-foreground mb-4">
              Create your first past performance questionnaire to get started
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Past Performance
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {pastPerformances.map((pp) => (
            <Card key={pp.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-xl">{pp.title}</CardTitle>
                      <Badge className={getStatusColor(pp.status)}>
                        {pp.status}
                      </Badge>
                    </div>
                    <CardDescription className="font-mono text-xs">
                      UEI: {pp.entity_uei}
                      {pp.award_id && ` • Award: ${pp.award_id}`}
                    </CardDescription>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedPP(pp);
                        setShowEditor(true);
                      }}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>

                    <Select onValueChange={(format) => handleExport(pp.id, format as any)}>
                      <SelectTrigger className="w-[140px] h-9">
                        <Download className="h-4 w-4 mr-2" />
                        <SelectValue placeholder="Export" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="json">JSON</SelectItem>
                        <SelectItem value="text">Text</SelectItem>
                        <SelectItem value="markdown">Markdown</SelectItem>
                      </SelectContent>
                    </Select>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(pp.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                <div className="text-sm text-muted-foreground">
                  Created: {new Date(pp.created_at).toLocaleDateString()}
                  {pp.updated_at !== pp.created_at && ` • Updated: ${new Date(pp.updated_at).toLocaleDateString()}`}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// Editor Component (simplified inline version)
function PastPerformanceEditor({
  pastPerformance,
  template,
  onClose,
  onUpdate
}: {
  pastPerformance: PastPerformance;
  template: QuestionnaireTemplate | null;
  onClose: () => void;
  onUpdate: (updated: PastPerformance) => void;
}) {
  const toast = useToast();
  const [data, setData] = useState(pastPerformance.questionnaire_data);
  const [generating, setGenerating] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const sections = template ? Object.keys(template.sections) : Object.keys(data);

  const handleGenerate = async (sectionName: string) => {
    setGenerating(sectionName);
    try {
      const result = await pastPerformanceService.generateSection(pastPerformance.id, {
        section_name: sectionName,
        force_regenerate: true
      });

      // Update local data
      setData({
        ...data,
        [sectionName]: {
          content: result.content,
          generated: true,
          last_generated_at: result.generated_at,
          model_used: result.model_used
        }
      });

      // Save to backend
      await handleSave({
        ...data,
        [sectionName]: {
          content: result.content,
          generated: true,
          last_generated_at: result.generated_at,
          model_used: result.model_used
        }
      });
    } catch (error: any) {
      toast.error(error.message || 'Failed to generate content');
    } finally {
      setGenerating(null);
    }
  };

  const handleSave = async (updatedData?: any) => {
    setSaving(true);
    try {
      const updated = await pastPerformanceService.update(pastPerformance.id, {
        questionnaire_data: updatedData || data
      });
      onUpdate(updated);
    } catch (error: any) {
      toast.error(error.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold">{pastPerformance.title}</h2>
          <p className="text-muted-foreground">Edit past performance questionnaire</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => handleSave()} disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Save
          </Button>
          <Button variant="outline" onClick={onClose}>Close</Button>
        </div>
      </div>

      <div className="space-y-6">
        {sections.map((sectionName) => {
          const sectionInfo = template?.sections[sectionName];
          const sectionData = data[sectionName] || { content: '', generated: false };

          return (
            <Card key={sectionName}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{sectionInfo?.title || sectionName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</CardTitle>
                    {sectionInfo?.description && (
                      <CardDescription>{sectionInfo.description}</CardDescription>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleGenerate(sectionName)}
                    disabled={generating === sectionName}
                  >
                    {generating === sectionName ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Sparkles className="h-4 w-4 mr-2" />
                    )}
                    Generate
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={sectionData.content}
                  onChange={(e) => setData({
                    ...data,
                    [sectionName]: { ...sectionData, content: e.target.value }
                  })}
                  placeholder={sectionInfo?.prompt_hint || 'Enter content...'}
                  rows={8}
                  className="font-sans"
                />
                {sectionData.generated && (
                  <p className="text-xs text-muted-foreground mt-2">
                    AI Generated • {sectionData.model_used}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
