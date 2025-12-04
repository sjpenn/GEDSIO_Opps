import { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  Plus,
  Trash2,
  Save,
  Download,
  Sparkles,
  Loader2,
  FileText,
  GripVertical
} from 'lucide-react';
import { cn } from '@/lib/utils';

const API_URL = import.meta.env.VITE_API_URL || '';

interface Block {
  id: string;
  title: string;
  content: string;
  order: number;
  page_limit?: number;
  page_limit_source?: string;
}

interface Volume {
  id: number;
  title: string;
  order: number;
  blocks: Block[];
}

interface ProposalContent {
  proposal: {
    id: number;
    opportunity_id: number;
    version: number;
    shipley_phase: string;
  };
  volumes: Volume[];
}

interface ProposalEditorProps {
  proposalId: number;
}

export default function ProposalEditor({ proposalId }: ProposalEditorProps) {
  const [content, setContent] = useState<ProposalContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [selectedVolume, setSelectedVolume] = useState<number | null>(null);
  const [selectedBlock, setSelectedBlock] = useState<string | null>(null);
  const [editingBlock, setEditingBlock] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [newSectionTitle, setNewSectionTitle] = useState('');
  const autoSaveTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    fetchContent();
  }, [proposalId]);

  const fetchContent = async (background = false) => {
    try {
      if (!background) setLoading(true);
      const response = await fetch(`${API_URL}/api/v1/proposal-content/proposals/${proposalId}/content`);
      if (!response.ok) throw new Error('Failed to fetch content');
      const data = await response.json();
      console.log('ProposalEditor fetched content:', data);
      setContent(data);
      
      // Select first volume by default
      if (data.volumes.length > 0 && !selectedVolume) {
        setSelectedVolume(data.volumes[0].id);
      }
    } catch (error) {
      console.error('Error fetching content:', error);
    } finally {
      if (!background) setLoading(false);
    }
  };

  const handleAddSection = async () => {
    if (!selectedVolume || !newSectionTitle.trim()) return;

    try {
      const response = await fetch(
        `${API_URL}/api/v1/proposal-content/proposals/${proposalId}/volumes/${selectedVolume}/sections`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: newSectionTitle,
            content: '',
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to create section');

      setNewSectionTitle('');
      await fetchContent(true);
    } catch (error) {
      console.error('Error creating section:', error);
    }
  };

  const handleUpdateSection = async (volumeId: number, blockId: string, updates: Partial<Block>) => {
    try {
      setSaving(true);
      const response = await fetch(
        `${API_URL}/api/v1/proposal-content/proposals/${proposalId}/volumes/${volumeId}/sections/${blockId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        }
      );

      if (!response.ok) throw new Error('Failed to update section');

      const updatedSection = await response.json();

      // Use functional setState to avoid stale closures
      setContent(prevContent => {
        if (!prevContent) return prevContent;
        
        const newContent = JSON.parse(JSON.stringify(prevContent));
        const volume = newContent.volumes.find((v: any) => v.id === volumeId);
        
        if (volume) {
          const blockIndex = volume.blocks.findIndex((b: Block) => String(b.id).trim() === String(blockId).trim());
          if (blockIndex !== -1) {
            volume.blocks[blockIndex] = updatedSection;
          }
        }
        
        return newContent;
      });
    } catch (error) {
      console.error('Error updating section:', error);
      await fetchContent(true); 
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteSection = async (volumeId: number, blockId: string) => {
    if (!confirm('Are you sure you want to delete this section?')) return;

    try {
      const response = await fetch(
        `${API_URL}/api/v1/proposal-content/proposals/${proposalId}/volumes/${volumeId}/sections/${blockId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) throw new Error('Failed to delete section');

      await fetchContent();
      if (selectedBlock === blockId) {
        setSelectedBlock(null);
      }
    } catch (error) {
      console.error('Error deleting section:', error);
    }
  };

  const handleGenerateContent = async (volumeId: number, blockId: string) => {
    try {
      setGenerating(blockId);
      const response = await fetch(
        `${API_URL}/api/v1/proposal-content/proposals/${proposalId}/volumes/${volumeId}/sections/${blockId}/generate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({}),
        }
      );

      if (!response.ok) throw new Error('Failed to generate content');

      const data = await response.json();
      
      // Update the block with generated content
      await handleUpdateSection(volumeId, blockId, { content: data.content });
    } catch (error) {
      console.error('Error generating content:', error);
    } finally {
      setGenerating(null);
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await fetch(
        `${API_URL}/api/v1/proposal-content/proposals/${proposalId}/export`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ format: 'markdown' }),
        }
      );

      if (!response.ok) throw new Error('Failed to export');

      const data = await response.json();
      alert(`Proposal exported successfully to: ${data.filepath}`);
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Failed to export proposal');
    } finally {
      setExporting(false);
    }
  };

  const startEdit = (block: Block) => {
    setEditingBlock(block.id);
    setEditContent(block.content);
    setSelectedBlock(block.id);
  };

  const saveEdit = async (volumeId: number, blockId: string) => {
    await handleUpdateSection(volumeId, blockId, { content: editContent });
    setEditingBlock(null);
  };

  const cancelEdit = () => {
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
    setEditingBlock(null);
    setEditContent('');
  };

  // Auto-save with debouncing
  const handleContentChange = useCallback((newContent: string, volumeId: number, blockId: string) => {
    setEditContent(newContent);
    
    // Clear existing timeout
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
    
    // Set new timeout for auto-save (2 seconds after user stops typing)
    autoSaveTimeoutRef.current = setTimeout(async () => {
      await handleUpdateSection(volumeId, blockId, { content: newContent });
    }, 2000);
  }, []);

  // Helper function to calculate page limit based on section type
  const calculatePageLimit = (block: Block): number => {
    // Use database value if available
    if (block.page_limit !== undefined && block.page_limit !== null) {
      return block.page_limit;
    }
    
    // Fallback to heuristic
    const title = block.title.toLowerCase();
    
    // Default page limits based on common section types
    // Cover materials (typically 1 page each)
    if (title.includes('title page') || title.includes('cover page')) return 1;
    if (title.includes('cover letter') || title.includes('transmittal letter')) return 1;
    if (title.includes('table of contents') || title.includes('toc')) return 1;
    
    // Executive materials (short)
    if (title.includes('executive summary')) return 2;
    
    // Technical sections (longer)
    if (title.includes('technical approach') || title.includes('technical solution')) return 15;
    if (title.includes('management') || title.includes('management approach')) return 10;
    
    // Experience and qualifications
    if (title.includes('past performance')) return 5;
    if (title.includes('staffing') || title.includes('key personnel')) return 8;
    if (title.includes('corporate experience') || title.includes('company background')) return 3;
    
    // Quality and process
    if (title.includes('quality assurance') || title.includes('qa')) return 5;
    if (title.includes('transition') || title.includes('phase-in')) return 3;
    
    // Pricing (typically short)
    if (title.includes('pricing') || title.includes('cost') || title.includes('price volume')) return 3;
    
    // Default for other sections (reduced from 5 to 3)
    return 3;
  };

  // Helper function to estimate pages from content
  const estimatePages = (content: string): number => {
    if (!content) return 0;
    
    // Rough estimate: ~500 words per page, ~5 chars per word
    const charCount = content.length;
    const estimatedPages = Math.ceil(charCount / 2500);
    
    return estimatedPages;
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!content) {
    return (
      <div className="text-center p-12 text-muted-foreground">
        No content found
      </div>
    );
  }

  const currentVolume = content.volumes.find(v => v.id === selectedVolume);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Proposal Development</h2>
          <p className="text-sm text-muted-foreground">
            Phase 4: Create and edit proposal content
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleExport}
            disabled={exporting}
            variant="outline"
            className="gap-2"
          >
            {exporting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Export
          </Button>
          <Badge variant="outline">Version {content.proposal.version}</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Volume Navigator */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Volumes</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[600px]">
              <div className="space-y-2">
                {content.volumes.map((volume) => (
                  <button
                    key={volume.id}
                    onClick={() => setSelectedVolume(volume.id)}
                    className={cn(
                      "w-full text-left px-3 py-2 rounded-md text-sm transition-colors",
                      selectedVolume === volume.id
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                    )}
                  >
                    <div className="font-medium">{volume.title}</div>
                    <div className="text-xs opacity-70">
                      {volume.blocks.length} sections
                    </div>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Content Editor */}
        <div className="lg:col-span-3 space-y-4">
          {currentVolume && (
            <>
              {/* Add Section */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex gap-2">
                    <Input
                      placeholder="New section title..."
                      value={newSectionTitle}
                      onChange={(e) => setNewSectionTitle(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddSection()}
                    />
                    <Button onClick={handleAddSection} className="gap-2">
                      <Plus className="h-4 w-4" />
                      Add Section
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Sections */}
              {currentVolume.blocks
                .sort((a, b) => a.order - b.order)
                .map((block) => (
                  <Card key={block.id} className={cn(
                    "transition-all",
                    selectedBlock === block.id && "ring-2 ring-primary"
                  )}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <GripVertical className="h-4 w-4 text-muted-foreground" />
                          <CardTitle className="text-base">{block.title}</CardTitle>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Badge 
                                  variant={block.page_limit_source ? "default" : "outline"} 
                                  className="text-xs cursor-help"
                                >
                                  Page Limit: {calculatePageLimit(block)} pages
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                {block.page_limit_source ? (
                                  <p className="text-sm">Source: {block.page_limit_source}</p>
                                ) : (
                                  <p className="text-sm">Estimated page limit (not from solicitation)</p>
                                )}
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            id={`generate-btn-${block.id}`}
                            size="sm"
                            variant="ghost"
                            onClick={() => handleGenerateContent(currentVolume.id, block.id)}
                            disabled={generating === block.id}
                            className="gap-2"
                          >
                            {generating === block.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Sparkles className="h-4 w-4" />
                            )}
                            Generate
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteSection(currentVolume.id, block.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {editingBlock === block.id ? (
                        <div className="space-y-3">
                          <Textarea
                            value={editContent}
                            onChange={(e) => handleContentChange(e.target.value, currentVolume.id, block.id)}
                            className="min-h-[300px] font-mono text-sm"
                          />
                          <div className="flex items-center justify-between">
                            <div className="text-xs text-muted-foreground">
                              {estimatePages(editContent)} / {calculatePageLimit(block)} pages
                            </div>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={cancelEdit}
                              >
                                Cancel
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => saveEdit(currentVolume.id, block.id)}
                                disabled={saving}
                                className="gap-2"
                              >
                                {saving ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Save className="h-4 w-4" />
                                )}
                                Save
                              </Button>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <div
                            onClick={() => startEdit(block)}
                            className="min-h-[100px] p-4 rounded-md bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
                          >
                            {block.content ? (
                              <div className="prose prose-sm max-w-none dark:prose-invert">
                                <pre className="whitespace-pre-wrap text-sm leading-relaxed">
                                  {block.content}
                                </pre>
                              </div>
                            ) : (
                              <div className="text-sm text-muted-foreground italic">
                                Click to add content or use Generate button
                              </div>
                            )}
                          </div>
                          {block.content && (
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <span>{estimatePages(block.content)} / {calculatePageLimit(block)} pages</span>
                              <span>{block.content.length} characters</span>
                              <span>{block.content.split(/\s+/).length} words</span>
                            </div>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}

              {currentVolume.blocks.length === 0 && (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No sections yet. Add your first section above.</p>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
