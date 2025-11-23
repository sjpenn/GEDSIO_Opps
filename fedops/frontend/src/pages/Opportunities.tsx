import { useEffect, useState } from 'react'
import type { Opportunity, OpportunityComment } from '../types'
import FileManagementPage from './FileManagement'
import { AgentControlPanel } from '@/components/AgentControlPanel'

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
      if (searchParams.postedFrom) queryParams.append('postedFrom', searchParams.postedFrom);
      if (searchParams.postedTo) queryParams.append('postedTo', searchParams.postedTo);
      queryParams.append('limit', searchParams.limit.toString());
      queryParams.append('skip', searchParams.skip.toString());

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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Opportunities</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <div className="p-4 bg-card rounded-lg border border-border shadow-sm">
            <h3 className="font-semibold mb-4">Filters</h3>
            <form onSubmit={handleSearch} className="space-y-4">
              <div>
                <label htmlFor="keywords" className="block text-sm font-medium mb-1">Keywords</label>
                <input 
                  id="keywords"
                  type="text" 
                  placeholder="Search keywords..."
                  value={searchParams.keywords}
                  onChange={e => setSearchParams(prev => ({ ...prev, keywords: e.target.value }))}
                  className="w-full p-2 rounded border border-input bg-background text-sm"
                />
              </div>

              <div>
                <label htmlFor="naics" className="block text-sm font-medium mb-1">NAICS Code</label>
                <input 
                  id="naics"
                  type="text" 
                  placeholder="e.g. 541511"
                  value={searchParams.naics}
                  onChange={e => setSearchParams(prev => ({ ...prev, naics: e.target.value }))}
                  className="w-full p-2 rounded border border-input bg-background text-sm"
                />
              </div>

              <div>
                <label htmlFor="setAside" className="block text-sm font-medium mb-1">Set Aside</label>
                <input 
                  id="setAside"
                  type="text" 
                  placeholder="e.g. Sba"
                  value={searchParams.setAside}
                  onChange={e => setSearchParams(prev => ({ ...prev, setAside: e.target.value }))}
                  className="w-full p-2 rounded border border-input bg-background text-sm"
                />
              </div>

              <div>
                <label htmlFor="posted-from" className="block text-sm font-medium mb-1">Posted From</label>
                <input 
                  id="posted-from"
                  type="text" 
                  placeholder="MM/DD/YYYY"
                  value={searchParams.postedFrom}
                  onChange={e => setSearchParams(prev => ({ ...prev, postedFrom: e.target.value }))}
                  className="w-full p-2 rounded border border-input bg-background text-sm"
                />
              </div>

              <div>
                <label htmlFor="posted-to" className="block text-sm font-medium mb-1">Posted To</label>
                <input 
                  id="posted-to"
                  type="text" 
                  placeholder="MM/DD/YYYY"
                  value={searchParams.postedTo}
                  onChange={e => setSearchParams(prev => ({ ...prev, postedTo: e.target.value }))}
                  className="w-full p-2 rounded border border-input bg-background text-sm"
                />
              </div>

              <div>
                <label htmlFor="limit" className="block text-sm font-medium mb-1">Items per page</label>
                <select
                  id="limit"
                  value={searchParams.limit}
                  onChange={e => setSearchParams(prev => ({ ...prev, limit: parseInt(e.target.value), skip: 0 }))}
                  className="w-full p-2 rounded border border-input bg-background text-sm"
                >
                  <option value="10">10</option>
                  <option value="20">20</option>
                  <option value="50">50</option>
                </select>
              </div>

              <button type="submit" className="w-full bg-primary text-primary-foreground px-4 py-2 rounded hover:bg-primary/90 transition-colors">
                Apply Filters
              </button>
            </form>
          </div>
        </div>

        {/* Results List */}
        <div className="lg:col-span-3 space-y-4">
          {loading && <div className="text-center py-8">Loading opportunities...</div>}
          {error && <div className="text-center text-destructive py-8">Error: {error}</div>}
          
          {!loading && !error && opportunities.length === 0 && (
             <div className="text-center py-8 text-muted-foreground">No opportunities found. Try adjusting your filters.</div>
          )}

          <div className="grid gap-4">
            {opportunities.map(opp => (
              <div key={opp.id} className="group p-6 rounded-lg border border-border bg-card text-card-foreground shadow-sm hover:shadow-md transition-all">
                <div className="flex justify-between items-start mb-3">
                  <div className="space-y-1">
                    <button 
                      onClick={() => setSelectedOpp(opp)}
                      className="text-lg font-semibold hover:text-primary text-left line-clamp-1"
                    >
                      {opp.title}
                    </button>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="font-mono bg-secondary/50 px-1.5 py-0.5 rounded">{opp.solicitation_number}</span>
                      <span>•</span>
                      <span>{opp.department}</span>
                      {opp.sub_tier && <span>/ {opp.sub_tier}</span>}
                    </div>
                  </div>
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
                    opp.active === 'Yes' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                  }`}>
                    {opp.active === 'Yes' ? 'Active' : 'Inactive'}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-muted-foreground mb-4 bg-muted/30 p-3 rounded-md">
                  <div>
                    <span className="block text-xs font-medium uppercase opacity-70">Type</span>
                    <span className="text-foreground">{opp.type}</span>
                  </div>
                  <div>
                    <span className="block text-xs font-medium uppercase opacity-70">Posted</span>
                    <span className="text-foreground">{new Date(opp.posted_date).toLocaleDateString()}</span>
                  </div>
                  <div>
                    <span className="block text-xs font-medium uppercase opacity-70">Deadline</span>
                    <span className="text-foreground">{opp.response_deadline ? new Date(opp.response_deadline).toLocaleDateString() : 'N/A'}</span>
                  </div>
                  <div>
                    <span className="block text-xs font-medium uppercase opacity-70">Set Aside</span>
                    <span className="text-foreground truncate" title={opp.type_of_set_aside_description}>{opp.type_of_set_aside || 'None'}</span>
                  </div>
                  <div>
                    <span className="block text-xs font-medium uppercase opacity-70">NAICS</span>
                    <span className="text-foreground">{opp.naics_code || 'N/A'}</span>
                  </div>
                </div>

                <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                  {stripHtml(opp.description || '')}
                </p>

                <div className="flex justify-end">
                  <button 
                    onClick={() => setSelectedOpp(opp)}
                    className="text-sm font-medium text-primary hover:underline"
                  >
                    View Details →
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {!loading && opportunities.length > 0 && (
            <div className="flex justify-center items-center gap-4 mt-8 pt-4 border-t border-border">
              <button
                onClick={() => setSearchParams(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
                disabled={currentPage === 1 || loading}
                className="px-4 py-2 rounded border border-input bg-background hover:bg-accent disabled:opacity-50 text-sm"
              >
                Previous
              </button>
              <span className="text-sm font-medium">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setSearchParams(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
                disabled={currentPage >= totalPages || loading}
                className="px-4 py-2 rounded border border-input bg-background hover:bg-accent disabled:opacity-50 text-sm"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Details Modal */}
      {selectedOpp && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-background rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
            <div className="p-6 border-b border-border flex justify-between items-start sticky top-0 bg-background z-10">
              <div>
                <h2 className="text-2xl font-bold pr-8">{selectedOpp.title}</h2>
                <div className="flex gap-2 mt-2">
                   <span className="text-xs font-mono bg-secondary px-2 py-1 rounded">
                    {selectedOpp.solicitation_number}
                  </span>
                  <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded font-medium">
                    {selectedOpp.type}
                  </span>
                </div>
              </div>
              <button 
                onClick={() => setSelectedOpp(null)}
                className="text-muted-foreground hover:text-foreground p-2 hover:bg-accent rounded-full transition-colors"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6 space-y-8">
              {/* Actions Bar */}
              <div className="flex gap-4 mb-6">
                <button
                  onClick={() => setShowFileManager(true)}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
                >
                  <span>📂</span> Manage Files & AI Analysis
                </button>
                <button
                  onClick={handleFindPartners}
                  disabled={loadingPartners}
                  className="bg-secondary text-secondary-foreground px-4 py-2 rounded-lg font-medium hover:bg-secondary/90 transition-colors flex items-center gap-2"
                >
                  <span>🤝</span> {loadingPartners ? 'Searching...' : 'Find Partners'}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-1">
                  <h3 className="text-sm font-medium text-muted-foreground">Department</h3>
                  <p className="font-medium">{selectedOpp.department}</p>
                  {selectedOpp.sub_tier && <p className="text-sm text-muted-foreground">{selectedOpp.sub_tier}</p>}
                  {selectedOpp.office && <p className="text-sm text-muted-foreground">{selectedOpp.office}</p>}
                </div>
                <div className="space-y-1">
                  <h3 className="text-sm font-medium text-muted-foreground">Key Dates</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span>Posted:</span>
                    <span className="font-medium">{new Date(selectedOpp.posted_date).toLocaleDateString()}</span>
                    <span>Due:</span>
                    <span className="font-medium text-destructive">
                      {selectedOpp.response_deadline ? new Date(selectedOpp.response_deadline).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                </div>
                <div className="space-y-1">
                  <h3 className="text-sm font-medium text-muted-foreground">Details</h3>
                  <div className="text-sm space-y-1">
                    <p><span className="opacity-70">NAICS:</span> {selectedOpp.naics_code}</p>
                    <p><span className="opacity-70">Set Aside:</span> {selectedOpp.type_of_set_aside || 'None'}</p>
                    <p><span className="opacity-70">Notice ID:</span> {selectedOpp.notice_id}</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">Description</h3>
                <div className="bg-muted/30 p-4 rounded-lg text-sm leading-relaxed whitespace-pre-wrap border border-border">
                  {selectedOpp.description?.startsWith('http') ? (
                    <a href={selectedOpp.description} target="_blank" rel="noreferrer" className="text-primary hover:underline flex items-center gap-2">
                      View Full Description on SAM.gov ↗
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
                        <div key={i} className="p-3 bg-card border border-border rounded-lg text-sm">
                          <p className="font-medium">{poc.fullName}</p>
                          {poc.title && <p className="text-muted-foreground">{poc.title}</p>}
                          {poc.email && <p className="text-primary hover:underline mt-1">{poc.email}</p>}
                          {poc.phone && <p className="text-muted-foreground">{poc.phone}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {(selectedOpp.links || selectedOpp.resource_links) && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Resources & Links</h3>
                    <div className="flex flex-col gap-2">
                      {selectedOpp.ui_link && (
                        <a href={selectedOpp.ui_link} target="_blank" rel="noreferrer" className="p-3 bg-primary/5 border border-primary/20 rounded-lg text-primary hover:bg-primary/10 transition-colors flex items-center justify-between group">
                          <span className="font-medium">View on SAM.gov</span>
                          <span className="group-hover:translate-x-1 transition-transform">→</span>
                        </a>
                      )}
                      {loadingResources ? (
                        <div className="text-sm text-muted-foreground animate-pulse">Loading resources...</div>
                      ) : (
                        resourceFiles.length > 0 ? (
                          resourceFiles.map((file, i) => (
                            <a key={`res-${i}`} href={file.url} target="_blank" rel="noreferrer" className="p-3 bg-card border border-border rounded-lg hover:border-primary/50 transition-colors text-sm flex flex-col">
                              <span className="font-medium truncate" title={file.filename}>{file.filename}</span>
                              <span className="text-xs text-muted-foreground truncate">{file.url}</span>
                            </a>
                          ))
                        ) : (
                          selectedOpp.resource_links?.map((link: string, i: number) => (
                            <a key={`res-${i}`} href={link} target="_blank" rel="noreferrer" className="p-3 bg-card border border-border rounded-lg hover:border-primary/50 transition-colors text-sm flex flex-col">
                              <span className="font-medium truncate" title={getFilenameFromUrl(link)}>{getFilenameFromUrl(link)}</span>
                              <span className="text-xs text-muted-foreground truncate">{link}</span>
                            </a>
                          ))
                        )
                      )}
                      {selectedOpp.links?.map((link: any, i: number) => (
                        <a key={i} href={link.href} target="_blank" rel="noreferrer" className="p-3 bg-card border border-border rounded-lg hover:border-primary/50 transition-colors text-sm flex flex-col">
                          <span className="font-medium">{link.rel}</span>
                          <span className="text-xs text-muted-foreground truncate">{link.href}</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Agentic Analysis Panel */}
              <div className="border-t border-border pt-6 mt-6">
                <AgentControlPanel opportunityId={selectedOpp.id} />
              </div>

              {/* Comments Section */}
              <div className="border-t border-border pt-6 mt-6">
                <h3 className="text-lg font-semibold mb-4">Team Comments</h3>
                
                <div className="space-y-4 mb-6">
                  {comments.map(comment => (
                    <div key={comment.id} className="bg-muted/30 p-4 rounded-lg border border-border group relative">
                      <p className="text-sm whitespace-pre-wrap">{comment.text}</p>
                      <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
                        <span>{new Date(comment.created_at).toLocaleString()}</span>
                        <button 
                          onClick={() => handleDeleteComment(comment.id)}
                          className="text-destructive opacity-0 group-hover:opacity-100 transition-opacity hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                  {comments.length === 0 && (
                    <p className="text-sm text-muted-foreground italic">No comments yet.</p>
                  )}
                </div>

                <div className="flex gap-2">
                  <textarea
                    value={newComment}
                    onChange={e => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="flex-1 min-h-[80px] p-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                  <button
                    onClick={handleAddComment}
                    disabled={!newComment.trim()}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed h-fit"
                  >
                    Add Note
                  </button>
                </div>
              </div>
            </div>
            
            <div className="p-6 border-t border-border bg-muted/10">
               <details className="text-xs">
                <summary className="cursor-pointer text-muted-foreground hover:text-foreground">View Raw Data</summary>
                <pre className="mt-2 p-4 bg-black/90 text-white rounded overflow-x-auto">
                  {JSON.stringify(selectedOpp.full_response, null, 2)}
                </pre>
              </details>
            </div>
          </div>
        </div>
      )}

      {/* Partner Matches Modal */}
      {showPartnerMatches && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-[60] animate-in fade-in duration-200">
          <div className="bg-background rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
            <div className="p-6 border-b border-border flex justify-between items-start sticky top-0 bg-background z-10">
              <div>
                <h2 className="text-2xl font-bold">Partner Matches</h2>
                <p className="text-sm text-muted-foreground">Based on NAICS: {selectedOpp?.naics_code}</p>
              </div>
              <button 
                onClick={() => setShowPartnerMatches(false)}
                className="text-muted-foreground hover:text-foreground p-2 hover:bg-accent rounded-full transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-4">
               {partnerMatches.length === 0 ? (
                   <div className="text-center py-8 text-muted-foreground">
                       <p>No matches found based on NAICS code.</p>
                       <p className="text-sm mt-2">Try adding more entities with relevant awards to your database.</p>
                   </div>
               ) : (
                   partnerMatches.map((match, i) => (
                       <div key={i} className="p-4 border rounded hover:bg-accent/10 transition-colors">
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
                           <div className="bg-secondary/20 p-2 rounded text-sm">
                               <p><strong>Match Reason:</strong> {match.match_details.reason}</p>
                           </div>
                           <div className="mt-3 flex gap-2">
                               <button className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">View Profile</button>
                               {match.entity.entity_type === 'PARTNER' && <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded border border-green-200">Existing Partner</span>}
                           </div>
                       </div>
                   ))
               )}
            </div>
          </div>
        </div>
      )}

      {/* File Manager Modal */}
      {showFileManager && selectedOpp && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-[60] animate-in fade-in duration-200">
          <div className="bg-background rounded-xl shadow-2xl max-w-6xl w-full h-[90vh] flex flex-col">
            <div className="p-4 border-b border-border flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold">Files & AI Analysis</h2>
                <p className="text-sm text-muted-foreground">For: {selectedOpp.title}</p>
              </div>
              <button 
                onClick={() => setShowFileManager(false)}
                className="text-muted-foreground hover:text-foreground p-2 hover:bg-accent rounded-full transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <FileManagementPage opportunityId={selectedOpp.id} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
