import { useState, useEffect } from 'react';
import { Loader2, Building2, Target, Key, FileText, Download, Edit2, Save, Search, Upload, Link as LinkIcon, ExternalLink, Trash2, Check, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface CompanyProfile {
  uei: string;
  company_name: string;
  entity_uei?: string;
  target_naics: string[];
  target_keywords: string[];
  target_set_asides: string[];
  logo_url?: string;
}

interface Entity {
  uei: string;
  legal_business_name: string;
  cage_code?: string;
  similarity_score?: number;
  logo_url?: string;
}

interface ProfileDocument {
  id: number;
  company_uei: string;
  document_type: string;
  title: string;
  description?: string;
  file_path: string;
  file_size?: number;
  created_at: string;
}

interface ProfileLink {
  id: number;
  company_uei: string;
  link_type: string;
  title: string;
  url: string;
  description?: string;
  created_at: string;
}

export default function CompanyProfilePage() {
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Form state
  const [formData, setFormData] = useState<CompanyProfile>({
    uei: '',
    company_name: '',
    target_naics: [],
    target_keywords: [],
    target_set_asides: []
  });

  // Entity search state
  const [showEntitySearch, setShowEntitySearch] = useState(false);
  const [entitySearchQuery, setEntitySearchQuery] = useState('');
  const [entitySearchResults, setEntitySearchResults] = useState<Entity[]>([]);
  const [entitySearchLoading, setEntitySearchLoading] = useState(false);
  const [showSwitchDialog, setShowSwitchDialog] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);

  // Documents state
  const [documents, setDocuments] = useState<ProfileDocument[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadType, setUploadType] = useState('Capability');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploading, setUploading] = useState(false);

  // Links state
  const [links, setLinks] = useState<ProfileLink[]>([]);
  const [linksLoading, setLinksLoading] = useState(false);
  const [showAddLink, setShowAddLink] = useState(false);
  const [newLink, setNewLink] = useState({
    link_type: 'SOW',
    title: '',
    url: '',
    description: ''
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  useEffect(() => {
    if (profile?.uei) {
      fetchDocuments();
      fetchLinks();
    }
  }, [profile]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/company/');
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          const profileData = data[0];
          
          // Fetch entity details to get logo
          try {
            const entityRes = await fetch(`/api/v1/entities/primary`);
            if (entityRes.ok) {
              const entityData = await entityRes.json();
              if (entityData && entityData.logo_url) {
                profileData.logo_url = entityData.logo_url;
              }
            }
          } catch (e) {
            console.error("Failed to fetch entity logo", e);
          }
          
          setProfile(profileData);
          setFormData(profileData);
        }
      }
    } catch (err) {
      setError('Failed to fetch profile');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async () => {
    if (!profile?.uei) return;
    setDocsLoading(true);
    try {
      const res = await fetch(`/api/v1/company/${profile.uei}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error('Failed to fetch documents', err);
    } finally {
      setDocsLoading(false);
    }
  };

  const fetchLinks = async () => {
    if (!profile?.uei) return;
    setLinksLoading(true);
    try {
      const res = await fetch(`/api/v1/company/${profile.uei}/links`);
      if (res.ok) {
        const data = await res.json();
        setLinks(data);
      }
    } catch (err) {
      console.error('Failed to fetch links', err);
    } finally {
      setLinksLoading(false);
    }
  };

  const searchEntities = async () => {
    if (!entitySearchQuery.trim()) return;
    
    setEntitySearchLoading(true);
    try {
      const res = await fetch(`/api/v1/entities/search?q=${encodeURIComponent(entitySearchQuery)}`);
      if (res.ok) {
        const data = await res.json();
        setEntitySearchResults(data);
      }
    } catch (err) {
      setError('Failed to search entities');
    } finally {
      setEntitySearchLoading(false);
    }
  };

  const setEntityAsProfile = async (entity: Entity) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/company/set-entity/${entity.uei}`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        setFormData(data);
        setShowEntitySearch(false);
        setSuccess('Company profile set successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Failed to set entity as profile');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const switchEntity = async () => {
    if (!selectedEntity || !profile) return;
    
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/company/${profile.uei}/switch-entity/${selectedEntity.uei}`, {
        method: 'PUT'
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        setFormData(data);
        setShowSwitchDialog(false);
        setShowEntitySearch(false);
        setSuccess('Company profile switched successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Failed to switch entity');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadDocument = async () => {
    if (!uploadFile || !profile) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('document_type', uploadType);
      formData.append('title', uploadTitle);
      formData.append('description', uploadDescription);
      
      const res = await fetch(`/api/v1/company/${profile.uei}/documents`, {
        method: 'POST',
        body: formData
      });
      
      if (res.ok) {
        setUploadFile(null);
        setUploadTitle('');
        setUploadDescription('');
        fetchDocuments();
        setSuccess('Document uploaded successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Failed to upload document');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const deleteDocument = async (docId: number) => {
    if (!profile) return;
    
    try {
      const res = await fetch(`/api/v1/company/${profile.uei}/documents/${docId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchDocuments();
        setSuccess('Document deleted successfully!');
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      setError('Failed to delete document');
    }
  };

  const handleAddLink = async () => {
    if (!profile || !newLink.title || !newLink.url) return;
    
    try {
      const res = await fetch(`/api/v1/company/${profile.uei}/links`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newLink, company_uei: profile.uei })
      });
      
      if (res.ok) {
        setNewLink({ link_type: 'SOW', title: '', url: '', description: '' });
        setShowAddLink(false);
        fetchLinks();
        setSuccess('Link added successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Failed to add link');
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const deleteLink = async (linkId: number) => {
    if (!profile) return;
    
    try {
      const res = await fetch(`/api/v1/company/${profile.uei}/links/${linkId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchLinks();
        setSuccess('Link deleted successfully!');
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      setError('Failed to delete link');
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0] || !profile) return;
    
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/entities/${profile.uei}/logo`, {
        method: 'POST',
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        setProfile(prev => prev ? ({...prev, logo_url: data.logo_url}) : null);
        setSuccess('Logo uploaded successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Failed to upload logo');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const method = profile ? 'PUT' : 'POST';
      const url = profile ? `/api/v1/company/${profile.uei}` : '/api/v1/company/';
      
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!res.ok) throw new Error('Failed to save profile');
      
      const savedProfile = await res.json();
      setProfile(savedProfile);
      setIsEditing(false);
      setSuccess('Profile updated successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleArrayInput = (field: keyof CompanyProfile, value: string) => {
    const array = value.split(',').map(s => s.trim()).filter(Boolean);
    setFormData(prev => ({ ...prev, [field]: array }));
  };

  if (loading && !profile && !isEditing) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh]">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Loading company profile...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Company Profile</h2>
          <p className="text-muted-foreground">Manage your company details, documents, and links.</p>
        </div>
        {!isEditing && profile && (
          <div className="flex gap-2">
            <Button onClick={() => setShowEntitySearch(true)} variant="outline" className="gap-2">
              <Search className="h-4 w-4" /> Change Entity
            </Button>
            <Button onClick={() => setIsEditing(true)} className="gap-2">
              <Edit2 className="h-4 w-4" /> Edit Profile
            </Button>
          </div>
        )}
      </div>

      {/* Success/Error Messages */}
      {success && (
        <Alert className="border-green-500/50 bg-green-500/10">
          <Check className="h-4 w-4 text-green-500" />
          <AlertDescription className="text-green-700">{success}</AlertDescription>
        </Alert>
      )}
      
      {error && (
        <Alert className="border-destructive/50 bg-destructive/10">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <AlertDescription className="text-destructive">{error}</AlertDescription>
        </Alert>
      )}

      {/* Entity Search Section */}
      {(!profile || showEntitySearch) && (
        <Card className="border-dashed border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5 text-primary" />
              {profile ? 'Change Company Entity' : 'Select Company Entity'}
            </CardTitle>
            <CardDescription>
              Search for your company on SAM.gov to set up your profile.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Enter company name..."
                value={entitySearchQuery}
                onChange={(e) => setEntitySearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchEntities()}
              />
              <Button onClick={searchEntities} disabled={entitySearchLoading}>
                {entitySearchLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                Search
              </Button>
            </div>

            {entitySearchResults.length > 0 && (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {entitySearchResults.map((entity) => (
                  <div
                    key={entity.uei}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/30 transition-colors"
                  >
                    <div>
                      <h4 className="font-semibold">{entity.legal_business_name}</h4>
                      <div className="flex gap-2 mt-1">
                        <Badge variant="outline" className="font-mono text-xs">{entity.uei}</Badge>
                        {entity.cage_code && <Badge variant="secondary" className="font-mono text-xs">CAGE: {entity.cage_code}</Badge>}
                        {entity.similarity_score && (
                          <Badge variant="secondary" className="text-xs">
                            Match: {(entity.similarity_score * 100).toFixed(0)}%
                          </Badge>
                        )}
                      </div>
                    </div>
                    <Button
                      onClick={() => {
                        if (profile) {
                          setSelectedEntity(entity);
                          setShowSwitchDialog(true);
                        } else {
                          setEntityAsProfile(entity);
                        }
                      }}
                      size="sm"
                    >
                      {profile ? 'Switch to This' : 'Select'}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
          {profile && (
            <CardFooter className="border-t">
              <Button variant="ghost" onClick={() => setShowEntitySearch(false)}>
                Cancel
              </Button>
            </CardFooter>
          )}
        </Card>
      )}

      {profile && !showEntitySearch && (
        <div className="grid gap-6">
          {/* Main Profile Card */}
          <Card className={cn("transition-all duration-300", isEditing ? "ring-2 ring-primary/20" : "")}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                {isEditing ? 'Edit Company Details' : 'Company Details'}
              </CardTitle>
              <CardDescription>
                Basic information about your company.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <form id="profile-form" onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="company-name">Company Name</Label>
                      <Input
                        id="company-name"
                        required
                        value={formData.company_name}
                        onChange={e => setFormData({...formData, company_name: e.target.value})}
                        placeholder="e.g. Acme Corp"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="uei">UEI (Unique Entity ID)</Label>
                      <Input
                        id="uei"
                        required
                        disabled={!!profile}
                        value={formData.uei}
                        onChange={e => setFormData({...formData, uei: e.target.value})}
                        placeholder="e.g. ABC123DEF456"
                        className="font-mono"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="target-naics">Target NAICS Codes</Label>
                    <Input
                      id="target-naics"
                      value={formData.target_naics.join(', ')}
                      onChange={e => handleArrayInput('target_naics', e.target.value)}
                      placeholder="e.g. 541511, 541512 (comma separated)"
                    />
                    <p className="text-xs text-muted-foreground">Enter codes separated by commas.</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="target-keywords">Target Keywords</Label>
                    <Textarea
                      id="target-keywords"
                      value={formData.target_keywords.join(', ')}
                      onChange={e => handleArrayInput('target_keywords', e.target.value)}
                      placeholder="e.g. software development, cloud computing, artificial intelligence"
                      className="min-h-[80px]"
                    />
                    <p className="text-xs text-muted-foreground">Enter keywords separated by commas.</p>
                  </div>
                </form>
              ) : (
                <div className="space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="flex items-start gap-4">
                      {profile?.logo_url ? (
                        <div className="relative group shrink-0">
                          <img 
                            src={profile.logo_url} 
                            alt="Company Logo" 
                            className="h-16 w-16 object-contain rounded border bg-white"
                          />
                          <label 
                            htmlFor="logo-upload" 
                            className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded cursor-pointer"
                          >
                            <Upload className="h-4 w-4 text-white" />
                          </label>
                        </div>
                      ) : (
                        <label 
                          htmlFor="logo-upload"
                          className="h-16 w-16 flex shrink-0 items-center justify-center rounded border border-dashed bg-muted hover:bg-muted/80 cursor-pointer transition-colors"
                          title="Upload Logo"
                        >
                          <Upload className="h-6 w-6 text-muted-foreground" />
                        </label>
                      )}
                      <input 
                        id="logo-upload" 
                        type="file" 
                        accept="image/*" 
                        className="hidden" 
                        onChange={handleLogoUpload}
                        disabled={loading}
                      />
                      
                      <div>
                        <h3 className="text-sm font-medium text-muted-foreground uppercase mb-1">Company Name</h3>
                        <p className="text-2xl font-bold tracking-tight">{profile?.company_name}</p>
                      </div>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-muted-foreground uppercase mb-1">UEI</h3>
                      <p className="text-xl font-mono bg-muted/50 inline-block px-2 py-1 rounded">{profile?.uei}</p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground uppercase mb-3 flex items-center gap-2">
                      <Target className="h-4 w-4" /> Target NAICS Codes
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {profile?.target_naics && profile.target_naics.length > 0 ? (
                        profile?.target_naics.map(code => (
                          <Badge key={code} variant="secondary" className="font-mono text-sm px-3 py-1">
                            {code}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-muted-foreground italic text-sm">No NAICS codes defined.</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground uppercase mb-3 flex items-center gap-2">
                      <Key className="h-4 w-4" /> Target Keywords
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {profile?.target_keywords && profile.target_keywords.length > 0 ? (
                        profile?.target_keywords.map(kw => (
                          <Badge key={kw} variant="outline" className="text-sm px-3 py-1 bg-background">
                            {kw}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-muted-foreground italic text-sm">No keywords defined.</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
            {isEditing && (
              <CardFooter className="flex justify-end gap-3 border-t bg-muted/10 p-4">
                <Button 
                  variant="ghost" 
                  onClick={() => {
                    setIsEditing(false);
                    if (profile) setFormData(profile);
                  }}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  form="profile-form"
                  disabled={loading}
                  className="gap-2"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  Save Changes
                </Button>
              </CardFooter>
            )}
          </Card>

          {/* Document Upload Section */}
          {!isEditing && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5 text-primary" />
                  Company Documents
                </CardTitle>
                <CardDescription>
                  Upload capability statements, past performance, and other documents.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Upload Form */}
                <div className="border-2 border-dashed rounded-lg p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="doc-file">Select File</Label>
                      <Input
                        id="doc-file"
                        type="file"
                        onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="doc-type">Document Type</Label>
                      <Select value={uploadType} onValueChange={setUploadType}>
                        <SelectTrigger id="doc-type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Capability">Capability Statement</SelectItem>
                          <SelectItem value="PastPerformance">Past Performance</SelectItem>
                          <SelectItem value="SOW">SOW/PWS</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="doc-title">Title</Label>
                    <Input
                      id="doc-title"
                      value={uploadTitle}
                      onChange={(e) => setUploadTitle(e.target.value)}
                      placeholder="e.g. 2024 Capability Statement"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="doc-desc">Description (Optional)</Label>
                    <Textarea
                      id="doc-desc"
                      value={uploadDescription}
                      onChange={(e) => setUploadDescription(e.target.value)}
                      placeholder="Brief description of the document"
                      className="min-h-[60px]"
                    />
                  </div>
                  <Button
                    onClick={handleUploadDocument}
                    disabled={!uploadFile || !uploadTitle || uploading}
                    className="gap-2"
                  >
                    {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                    Upload Document
                  </Button>
                </div>

                {/* Documents List */}
                {docsLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : documents.length > 0 ? (
                  <div className="space-y-2">
                    <h4 className="font-semibold text-sm text-muted-foreground uppercase">Uploaded Documents</h4>
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/30 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <FileText className="h-5 w-5 text-primary mt-0.5" />
                          <div>
                            <h5 className="font-medium">{doc.title}</h5>
                            {doc.description && (
                              <p className="text-sm text-muted-foreground">{doc.description}</p>
                            )}
                            <div className="flex gap-2 mt-1">
                              <Badge variant="secondary" className="text-xs">{doc.document_type}</Badge>
                              {doc.file_size && (
                                <span className="text-xs text-muted-foreground">
                                  {(doc.file_size / 1024).toFixed(0)} KB
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" asChild>
                            <a href={`/${doc.file_path}`} download>
                              <Download className="h-4 w-4" />
                            </a>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteDocument(doc.id)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="h-10 w-10 mx-auto opacity-20 mb-2" />
                    <p>No documents uploaded yet.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Links Section */}
          {!isEditing && (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <LinkIcon className="h-5 w-5 text-primary" />
                      External Links
                    </CardTitle>
                    <CardDescription>
                      SOW/PWS links, capability statements, and other external resources.
                    </CardDescription>
                  </div>
                  <Button onClick={() => setShowAddLink(true)} size="sm" className="gap-2">
                    <LinkIcon className="h-4 w-4" /> Add Link
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {linksLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : links.length > 0 ? (
                  <div className="space-y-2">
                    {links.map((link) => (
                      <div
                        key={link.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/30 transition-colors"
                      >
                        <div>
                          <h5 className="font-medium">{link.title}</h5>
                          {link.description && (
                            <p className="text-sm text-muted-foreground">{link.description}</p>
                          )}
                          <div className="flex gap-2 mt-1">
                            <Badge variant="secondary" className="text-xs">{link.link_type}</Badge>
                            <a
                              href={link.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary hover:underline flex items-center gap-1"
                            >
                              {link.url.substring(0, 50)}...
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteLink(link.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <LinkIcon className="h-10 w-10 mx-auto opacity-20 mb-2" />
                    <p>No links added yet.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Switch Entity Dialog */}
      <Dialog open={showSwitchDialog} onOpenChange={setShowSwitchDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Switch Company Entity?</DialogTitle>
            <DialogDescription>
              Are you sure you want to switch your company profile to <strong>{selectedEntity?.legal_business_name}</strong>?
              This will update your company information.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowSwitchDialog(false)}>
              Cancel
            </Button>
            <Button onClick={switchEntity} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Confirm Switch
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Link Dialog */}
      <Dialog open={showAddLink} onOpenChange={setShowAddLink}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add External Link</DialogTitle>
            <DialogDescription>
              Add a link to an external resource like SOW/PWS or capability statement.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="link-type">Link Type</Label>
              <Select value={newLink.link_type} onValueChange={(v) => setNewLink({...newLink, link_type: v})}>
                <SelectTrigger id="link-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SOW">SOW</SelectItem>
                  <SelectItem value="PWS">PWS</SelectItem>
                  <SelectItem value="Capability">Capability Statement</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="link-title">Title</Label>
              <Input
                id="link-title"
                value={newLink.title}
                onChange={(e) => setNewLink({...newLink, title: e.target.value})}
                placeholder="e.g. Company Capability Statement"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="link-url">URL</Label>
              <Input
                id="link-url"
                type="url"
                value={newLink.url}
                onChange={(e) => setNewLink({...newLink, url: e.target.value})}
                placeholder="https://..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="link-desc">Description (Optional)</Label>
              <Textarea
                id="link-desc"
                value={newLink.description}
                onChange={(e) => setNewLink({...newLink, description: e.target.value})}
                placeholder="Brief description"
                className="min-h-[60px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowAddLink(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddLink} disabled={!newLink.title || !newLink.url}>
              Add Link
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
