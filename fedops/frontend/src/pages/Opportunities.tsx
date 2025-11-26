import { useEffect, useState } from 'react'
import type { Opportunity, OpportunityComment } from '../types'
import FileManagementPage from './FileManagement'
import { AgentControlPanel } from '@/components/AgentControlPanel'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Search, Filter, ExternalLink, FileText, Users, MessageSquare, Trash2, ChevronLeft, ChevronRight, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedOpp, setSelectedOpp] = useState<Opportunity | null>(null)
  const [resourceFiles, setResourceFiles] = useState<{url: string, filename: string}[]>([])
  const [loadingResources, setLoadingResources] = useState(false)
  const [showFileManager, setShowFileManager] = useState(false)
  const [comments, setComments] = useState<OpportunityComment[]>([])
  const [newComment, setNewComment] = useState('')
  const [partnerMatches, setPartnerMatches] = useState<any[]>([])
  const [loadingPartners, setLoadingPartners] = useState(false)
  const [showPartnerMatches, setShowPartnerMatches] = useState(false)
  
  // Calculate default date range (last 30 days)
  const getDefaultDates = () => {
    const today = new Date()
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)
    
    return {
      from: thirtyDaysAgo,
      to: today
    }
  }
  
  const { from: thirtyDaysAgo, to: today } = getDefaultDates()
  
  // Helper to strip HTML tags
  const stripHtml = (html: string) => {
    if (!html) return ''
    const tmp = document.createElement('DIV')
    tmp.innerHTML = html
    return tmp.textContent || tmp.innerText || ''
  }

  const getFilenameFromUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      const pathname = urlObj.pathname;
      const filename = pathname.substring(pathname.lastIndexOf('/') + 1);
      return filename || url;
    } catch (e) {
      return url;
    }
  };

  const [searchParams, setSearchParams] = useState({
    keywords: '',
    naics: '',
    setAside: '',
    active: 'yes',
    postedFrom: thirtyDaysAgo.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' }),
    postedTo: today.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' }),
    limit: 10,
    skip: 0
  });
  const [total, setTotal] = useState(0);

  const fetchOpportunities = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const queryParams = new URLSearchParams();
      if (searchParams.keywords) queryParams.append('keywords', searchParams.keywords);
      if (searchParams.naics) queryParams.append('naics', searchParams.naics);
      if (searchParams.setAside) queryParams.append('setAside', searchParams.setAside);
      if (searchParams.active) queryParams.append('active', searchParams.active);
      if (searchParams.postedFrom) queryParams.append('postedFrom', searchParams.postedFrom);
      if (searchParams.postedTo) queryParams.append('postedTo', searchParams.postedTo);
      queryParams.append('limit', searchParams.limit.toString());
      queryParams.append('skip', searchParams.skip.toString());

      console.log('Fetching opportunities with params:', queryParams.toString());
      const response = await fetch(`/api/v1/opportunities/?${queryParams.toString()}`);
      if (!response.ok) {
        throw new Error('Failed to fetch opportunities');
      }
      const data = await response.json();
      setOpportunities(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
  }, [searchParams.skip]); // Only auto-fetch on pagination change

  const fetchComments = async (oppId: number) => {
    try {
      const response = await fetch(`/api/v1/opportunities/${oppId}/comments`)
      if (response.ok) {
        const data = await response.json()
        setComments(data)
      }
    } catch (err) {
      console.error('Failed to fetch comments', err)
    }
  }

  const handleAddComment = async () => {
    if (!selectedOpp || !newComment.trim()) return

    try {
      const response = await fetch(`/api/v1/opportunities/${selectedOpp.id}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newComment })
      })

      if (response.ok) {
        setNewComment('')
        fetchComments(selectedOpp.id)
      }
    } catch (err) {
      console.error('Failed to add comment', err)
    }
  }

  const handleDeleteComment = async (commentId: number) => {
    if (!selectedOpp) return
    
    if (!confirm('Are you sure you want to delete this comment?')) return

    try {
      const response = await fetch(`/api/v1/opportunities/${selectedOpp.id}/comments/${commentId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        setComments(prev => prev.filter(c => c.id !== commentId))
      }
    } catch (err) {
      console.error('Failed to delete comment', err)
    }
  }

  const fetchResources = async (oppId: number) => {
    try {
      setLoadingResources(true);
      const response = await fetch(`/api/v1/opportunities/${oppId}/resources`);
      if (response.ok) {
        const data = await response.json();
        setResourceFiles(data);
      }
    } catch (err) {
      console.error('Failed to fetch resources', err);
    } finally {
      setLoadingResources(false);
    }
  };

  useEffect(() => {
    if (selectedOpp) {
      setResourceFiles([]); // Reset
      setComments([]); // Reset comments
      setPartnerMatches([]); // Reset matches
      fetchComments(selectedOpp.id); // Fetch comments
      if (selectedOpp.resource_links && selectedOpp.resource_links.length > 0) {
        fetchResources(selectedOpp.id);
      }
    }
  }, [selectedOpp]);

  const handleFindPartners = async () => {
    if (!selectedOpp) return;
    setLoadingPartners(true);
    try {
      const res = await fetch(`/api/v1/entities/match-opportunity?opportunity_id=${selectedOpp.id}`, {
        method: 'POST'
      });
      const data = await res.json();
      setPartnerMatches(data);
      setShowPartnerMatches(true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingPartners(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams(prev => ({ ...prev, skip: 0 })); // Reset to first page on new search
    fetchOpportunities();
  };

  const totalPages = Math.ceil(total / searchParams.limit);
  const currentPage = (searchParams.skip / searchParams.limit) + 1;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Opportunities</h2>
          <p className="text-muted-foreground">Search and manage federal opportunities.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <Card className="lg:col-span-1 h-fit">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="keywords">Keywords</Label>
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input 
                    id="keywords"
                    placeholder="Search keywords..."
                    value={searchParams.keywords}
                    onChange={e => setSearchParams(prev => ({ ...prev, keywords: e.target.value }))}
                    className="pl-8"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="naics">NAICS Code</Label>
                <Input 
                  id="naics"
                  placeholder="e.g. 541511"
                  value={searchParams.naics}
                  onChange={e => setSearchParams(prev => ({ ...prev, naics: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="setAside">Set Aside</Label>
                <Input 
                  id="setAside"
                  placeholder="e.g. Sba"
                  value={searchParams.setAside}
                  onChange={e => setSearchParams(prev => ({ ...prev, setAside: e.target.value }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="active">Status</Label>
                <Select
                  value={searchParams.active}
                  onValueChange={value => setSearchParams(prev => ({ ...prev, active: value }))}
                >
                  <SelectTrigger id="active">
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="yes">Active Only</SelectItem>
                    <SelectItem value="no">Inactive Only</SelectItem>
                    <SelectItem value="all">All Statuses</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-2">
                  <Label htmlFor="posted-from">Posted From</Label>
                  <Input 
                    id="posted-from"
                    placeholder="MM/DD/YYYY"
                    value={searchParams.postedFrom}
                    onChange={e => setSearchParams(prev => ({ ...prev, postedFrom: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="posted-to">Posted To</Label>
                  <Input 
                    id="posted-to"
                    placeholder="MM/DD/YYYY"
                    value={searchParams.postedTo}
                    onChange={e => setSearchParams(prev => ({ ...prev, postedTo: e.target.value }))}
                  />
                </div>
              </div>
              
              <Button 
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setSearchParams(prev => ({ ...prev, postedFrom: '', postedTo: '' }))}
                className="w-full text-xs"
              >
                Clear Dates
              </Button>

              <div className="space-y-2">
                <Label htmlFor="limit">Items per page</Label>
                <Select
                  value={searchParams.limit.toString()}
                  onValueChange={value => setSearchParams(prev => ({ ...prev, limit: parseInt(value), skip: 0 }))}
                >
                  <SelectTrigger id="limit">
                    <SelectValue placeholder="10" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="20">20</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button type="submit" className="w-full">
                Apply Filters
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results List */}
        <div className="lg:col-span-3 space-y-4">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold">Searching Opportunities...</h3>
                <p className="text-muted-foreground text-sm max-w-md">
                  {searchParams.keywords ? `Searching for "${searchParams.keywords}"` : 'Fetching latest opportunities'}
                </p>
              </div>
            </div>
          )}
          
          {error && (
            <Card className="border-destructive/50 bg-destructive/10">
              <CardContent className="pt-6 text-center text-destructive">
                Error: {error}
              </CardContent>
            </Card>
          )}
          
          {!loading && !error && opportunities.length === 0 && (
             <Card className="border-dashed">
               <CardContent className="py-12 text-center text-muted-foreground">
                 <Search className="h-12 w-12 mx-auto mb-4 opacity-20" />
                 <p>No opportunities found. Try adjusting your filters.</p>
               </CardContent>
             </Card>
          )}

          <div className="grid gap-4">
            {opportunities.map(opp => (
              <Card key={opp.id} className="group hover:shadow-md transition-all duration-200 border-l-4 border-l-primary/0 hover:border-l-primary">
                <CardContent className="p-6">
                  <div className="flex justify-between items-start mb-3 gap-4">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="font-mono text-xs">
                          {opp.solicitation_number}
                        </Badge>
                        <Badge variant={opp.active === 'Yes' ? 'default' : 'secondary'} className={cn("text-xs", opp.active === 'Yes' ? "bg-green-600 hover:bg-green-700" : "")}>
                          {opp.active === 'Yes' ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      <h3 
                        onClick={() => setSelectedOpp(opp)}
                        className="text-lg font-semibold hover:text-primary cursor-pointer line-clamp-1 transition-colors"
                      >
                        {opp.title}
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="font-medium text-foreground">{opp.department}</span>
                        {opp.sub_tier && <span>• {opp.sub_tier}</span>}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-muted-foreground mb-4 bg-muted/30 p-3 rounded-md">
                    <div>
                      <span className="block text-xs font-medium uppercase opacity-70">Type</span>
                      <span className="text-foreground font-medium">{opp.type}</span>
                    </div>
                    <div>
                      <span className="block text-xs font-medium uppercase opacity-70">Posted</span>
                      <span className="text-foreground font-medium">{new Date(opp.posted_date).toLocaleDateString()}</span>
                    </div>
                    <div>
                      <span className="block text-xs font-medium uppercase opacity-70">Deadline</span>
                      <span className={cn("font-medium", opp.response_deadline && new Date(opp.response_deadline) < new Date() ? "text-destructive" : "text-foreground")}>
                        {opp.response_deadline ? new Date(opp.response_deadline).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="block text-xs font-medium uppercase opacity-70">Set Aside</span>
                      <span className="text-foreground font-medium truncate" title={opp.type_of_set_aside_description}>{opp.type_of_set_aside || 'None'}</span>
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                    {stripHtml(opp.description || '')}
                  </p>

                  <div className="flex justify-end">
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setSelectedOpp(opp)}
                      className="text-primary hover:text-primary hover:bg-primary/10"
                    >
                      View Details <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {!loading && opportunities.length > 0 && (
            <div className="flex justify-center items-center gap-4 mt-8 pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSearchParams(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
                disabled={currentPage === 1 || loading}
              >
                <ChevronLeft className="h-4 w-4 mr-1" /> Previous
              </Button>
              <span className="text-sm font-medium text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSearchParams(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
                disabled={currentPage >= totalPages || loading}
              >
                Next <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Details Dialog */}
      <Dialog open={!!selectedOpp} onOpenChange={(open) => !open && setSelectedOpp(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto flex flex-col p-0 gap-0">
          {selectedOpp && (
            <>
              <div className="p-6 border-b sticky top-0 bg-background z-10 flex justify-between items-start">
                <div className="space-y-1 pr-8">
                  <DialogTitle className="text-2xl font-bold leading-tight">{selectedOpp.title}</DialogTitle>
                  <div className="flex flex-wrap gap-2 mt-2">
                     <Badge variant="secondary" className="font-mono">
                      {selectedOpp.solicitation_number}
                    </Badge>
                    <Badge variant="outline" className="text-primary border-primary/20 bg-primary/5">
                      {selectedOpp.type}
                    </Badge>
                  </div>
                </div>
              </div>
              
              <div className="p-6 space-y-8 overflow-y-auto">
                {/* Actions Bar */}
                <div className="flex flex-wrap gap-3">
                  <Button onClick={() => setShowFileManager(true)} className="gap-2">
                    <FileText className="h-4 w-4" /> Manage Files & AI
                  </Button>
                  <Button 
                    variant="secondary" 
                    onClick={handleFindPartners}
                    disabled={loadingPartners}
                    className="gap-2"
                  >
                    {loadingPartners ? <Loader2 className="h-4 w-4 animate-spin" /> : <Users className="h-4 w-4" />}
                    {loadingPartners ? 'Searching...' : 'Find Partners'}
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-muted/30 p-4 rounded-lg border">
                  <div className="space-y-1">
                    <h3 className="text-xs font-semibold uppercase text-muted-foreground">Department</h3>
                    <p className="font-medium text-sm">{selectedOpp.department}</p>
                    {selectedOpp.sub_tier && <p className="text-xs text-muted-foreground">{selectedOpp.sub_tier}</p>}
                    {selectedOpp.office && <p className="text-xs text-muted-foreground">{selectedOpp.office}</p>}
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-xs font-semibold uppercase text-muted-foreground">Key Dates</h3>
                    <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-sm">
                      <span className="text-muted-foreground">Posted:</span>
                      <span className="font-medium">{new Date(selectedOpp.posted_date).toLocaleDateString()}</span>
                      <span className="text-muted-foreground">Due:</span>
                      <span className="font-medium text-destructive">
                        {selectedOpp.response_deadline ? new Date(selectedOpp.response_deadline).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-xs font-semibold uppercase text-muted-foreground">Details</h3>
                    <div className="space-y-1 text-sm">
                      <p><span className="text-muted-foreground">NAICS:</span> {selectedOpp.naics_code}</p>
                      <p><span className="text-muted-foreground">Set Aside:</span> {selectedOpp.type_of_set_aside || 'None'}</p>
                      <p><span className="text-muted-foreground">Notice ID:</span> {selectedOpp.notice_id}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-3">Description</h3>
                  <div className="bg-card p-4 rounded-lg text-sm leading-relaxed whitespace-pre-wrap border shadow-sm">
                    {selectedOpp.description?.startsWith('http') ? (
                      <a href={selectedOpp.description} target="_blank" rel="noreferrer" className="text-primary hover:underline flex items-center gap-2">
                        View Full Description on SAM.gov <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : (
                      selectedOpp.description
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {selectedOpp.point_of_contact && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Points of Contact</h3>
                      <div className="space-y-3">
                        {selectedOpp.point_of_contact.map((poc: any, i: number) => (
                          <Card key={i} className="bg-card">
                            <CardContent className="p-3 text-sm">
                              <p className="font-medium">{poc.fullName}</p>
                              {poc.title && <p className="text-muted-foreground text-xs">{poc.title}</p>}
                              {poc.email && <a href={`mailto:${poc.email}`} className="text-primary hover:underline mt-1 block text-xs">{poc.email}</a>}
                              {poc.phone && <p className="text-muted-foreground text-xs">{poc.phone}</p>}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}

                  {(selectedOpp.links || selectedOpp.resource_links) && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Resources & Links</h3>
                      <div className="flex flex-col gap-2">
                        {selectedOpp.ui_link && (
                          <a href={selectedOpp.ui_link} target="_blank" rel="noreferrer">
                            <Button variant="outline" className="w-full justify-between group">
                              View on SAM.gov
                              <ExternalLink className="h-4 w-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                            </Button>
                          </a>
                        )}
                        {loadingResources ? (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground p-2">
                            <Loader2 className="h-3 w-3 animate-spin" /> Loading resources...
                          </div>
                        ) : (
                          resourceFiles.length > 0 ? (
                            resourceFiles.map((file, i) => (
                              <a key={`res-${i}`} href={file.url} target="_blank" rel="noreferrer" className="block">
                                <Card className="hover:bg-accent transition-colors">
                                  <CardContent className="p-3 flex items-center gap-3">
                                    <FileText className="h-4 w-4 text-muted-foreground" />
                                    <div className="overflow-hidden">
                                      <p className="text-sm font-medium truncate" title={file.filename}>{file.filename}</p>
                                      <p className="text-xs text-muted-foreground truncate">{file.url}</p>
                                    </div>
                                  </CardContent>
                                </Card>
                              </a>
                            ))
                          ) : (
                            selectedOpp.resource_links?.map((link: string, i: number) => (
                              <a key={`res-${i}`} href={link} target="_blank" rel="noreferrer" className="block">
                                <Card className="hover:bg-accent transition-colors">
                                  <CardContent className="p-3 flex items-center gap-3">
                                    <FileText className="h-4 w-4 text-muted-foreground" />
                                    <div className="overflow-hidden">
                                      <p className="text-sm font-medium truncate" title={getFilenameFromUrl(link)}>{getFilenameFromUrl(link)}</p>
                                      <p className="text-xs text-muted-foreground truncate">{link}</p>
                                    </div>
                                  </CardContent>
                                </Card>
                              </a>
                            ))
                          )
                        )}
                        {selectedOpp.links?.map((link: any, i: number) => (
                          <a key={i} href={link.href} target="_blank" rel="noreferrer" className="block">
                            <Card className="hover:bg-accent transition-colors">
                              <CardContent className="p-3">
                                <p className="text-sm font-medium">{link.rel}</p>
                                <p className="text-xs text-muted-foreground truncate">{link.href}</p>
                              </CardContent>
                            </Card>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Agentic Analysis Panel */}
                <div className="border-t pt-6">
                  <AgentControlPanel opportunityId={selectedOpp.id} />
                </div>

                {/* Comments Section */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" /> Team Comments
                  </h3>
                  
                  <div className="space-y-4 mb-6">
                    {comments.map(comment => (
                      <div key={comment.id} className="bg-muted/30 p-4 rounded-lg border group relative">
                        <p className="text-sm whitespace-pre-wrap">{comment.text}</p>
                        <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
                          <span>{new Date(comment.created_at).toLocaleString()}</span>
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleDeleteComment(comment.id)}
                            className="h-6 w-6 text-destructive opacity-0 group-hover:opacity-100 transition-opacity hover:bg-destructive/10"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                    {comments.length === 0 && (
                      <p className="text-sm text-muted-foreground italic">No comments yet.</p>
                    )}
                  </div>

                  <div className="flex gap-2 items-start">
                    <Textarea
                      value={newComment}
                      onChange={e => setNewComment(e.target.value)}
                      placeholder="Add a comment..."
                      className="flex-1"
                    />
                    <Button
                      onClick={handleAddComment}
                      disabled={!newComment.trim()}
                    >
                      Add Note
                    </Button>
                  </div>
                </div>
              </div>
              
              <div className="p-4 border-t bg-muted/10">
                 <details className="text-xs">
                  <summary className="cursor-pointer text-muted-foreground hover:text-foreground">View Raw Data</summary>
                  <pre className="mt-2 p-4 bg-black/90 text-white rounded overflow-x-auto">
                    {JSON.stringify(selectedOpp.full_response, null, 2)}
                  </pre>
                </details>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Partner Matches Dialog */}
      <Dialog open={showPartnerMatches} onOpenChange={setShowPartnerMatches}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Partner Matches</DialogTitle>
            <DialogDescription>Based on NAICS: {selectedOpp?.naics_code}</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
             {partnerMatches.length === 0 ? (
                 <div className="text-center py-8 text-muted-foreground">
                     <p>No matches found based on NAICS code.</p>
                     <p className="text-sm mt-2">Try adding more entities with relevant awards to your database.</p>
                 </div>
             ) : (
                 partnerMatches.map((match, i) => (
                     <Card key={i} className="hover:bg-accent/5 transition-colors">
                         <CardContent className="p-4">
                             <div className="flex justify-between items-start mb-2">
                                 <div>
                                     <h3 className="font-bold text-lg">{match.entity.legal_business_name}</h3>
                                     <p className="text-xs font-mono text-muted-foreground">UEI: {match.entity.uei}</p>
                                 </div>
                                 <div className="text-right">
                                     <div className="text-sm font-medium text-green-600">
                                         ${match.match_details.total_obligation.toLocaleString()}
                                     </div>
                                     <div className="text-xs text-muted-foreground">Total Obligation</div>
                                 </div>
                             </div>
                             <div className="bg-secondary/20 p-2 rounded text-sm mb-3">
                                 <p><strong>Match Reason:</strong> {match.match_details.reason}</p>
                             </div>
                             <div className="flex gap-2">
                                 <Button size="sm" variant="outline" className="h-7 text-xs">View Profile</Button>
                                 {match.entity.entity_type === 'PARTNER' && (
                                   <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200">
                                     Existing Partner
                                   </Badge>
                                 )}
                             </div>
                         </CardContent>
                     </Card>
                 ))
             )}
          </div>
        </DialogContent>
      </Dialog>

      {/* File Manager Dialog */}
      <Dialog open={showFileManager} onOpenChange={setShowFileManager}>
        <DialogContent className="max-w-6xl h-[90vh] flex flex-col p-0 gap-0">
          <div className="p-4 border-b flex justify-between items-center">
            <div>
              <DialogTitle>Files & AI Analysis</DialogTitle>
              <DialogDescription>For: {selectedOpp?.title}</DialogDescription>
            </div>
          </div>
          <div className="flex-1 overflow-hidden p-4">
             {selectedOpp && <FileManagementPage opportunityId={selectedOpp.id} />}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
