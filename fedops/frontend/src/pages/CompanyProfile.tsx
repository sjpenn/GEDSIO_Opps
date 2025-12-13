import React, { useState, useEffect, useCallback } from 'react';
import {
  Building2,
  MapPin,
  Globe,
  Users,
  Calendar,
  FileText,
  AlertCircle,
  Loader2,
  Trash2,
  Download,
  CheckCircle,
  Clock,
  ExternalLink,
  Plus,
  RefreshCw,
  Sparkles,
  Search,
  Edit2,
  Check,
  Upload,
  Target,
  Key,
  Save,
  Link as LinkIcon
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useNavigate } from 'react-router-dom';

// import { toast } from 'sonner';
const toast = {
  success: (msg: string) => console.log('Success:', msg),
  error: (msg: string) => console.error('Error:', msg),
  info: (msg: string) => console.log('Info:', msg),
  warning: (msg: string) => console.warn('Warning:', msg)
};
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { BulkUploadDropzone } from '../components/ui/BulkUploadDropzone';
import type { CompanyProfile, CompanyProfileDocument, CompanyProfileLink, Entity, PastPerformance, ContractDocument } from '../types';
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { Alert, AlertDescription } from "@/components/ui/alert"




export default function CompanyProfilePage() {
  const navigate = useNavigate();
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
  const [documents, setDocuments] = useState<CompanyProfileDocument[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [filesToUpload, setFilesToUpload] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  // Unused single upload state removed
  // const [uploadFile, setUploadFile] = useState<File | null>(null);
  // ...


  // Links state
  const [links, setLinks] = useState<CompanyProfileLink[]>([]);
  const [linksLoading, setLinksLoading] = useState(false);
  const [showAddLink, setShowAddLink] = useState(false);
  const [newLink, setNewLink] = useState({
    link_type: 'SOW',
    title: '',
    url: '',
    description: ''
  });

  // SOW Scan State
  const [contractDocuments, setContractDocuments] = useState<ContractDocument[]>([]);
  const [scanningSOWs, setScanningSOWs] = useState(false);
  const [sowScanComplete, setSowScanComplete] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleBulkUpload = async () => {
    if (!profile?.uei || filesToUpload.length === 0) return;

    setUploading(true);
    try {
      const formData = new FormData();
      filesToUpload.forEach((file) => {
        formData.append('files', file);
      });

      const res = await fetch(`/api/v1/company/${profile.uei}/documents/bulk`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        setSuccess(`Successfully uploaded ${filesToUpload.length} documents for processing.`);
        setFilesToUpload([]);
        fetchDocuments();
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to upload documents');
      }
    } catch (e) {
      console.error(e);
      setError('Error uploading documents');
    } finally {
      setUploading(false);
    }
  };

  // ... (keeping existing useEffects)

  const scanForSOWs = async () => {
    if (!profile?.uei) return;

    setScanningSOWs(true);
    setSowScanComplete(false);
    try {
      const res = await fetch(`/api/v1/entities/${profile.uei}/contract-documents`);
      if (res.ok) {
        const data = await res.json();
        setContractDocuments(data);
        setSowScanComplete(true);
      } else {
        setError('Failed to scan for SOWs');
      }
    } catch (e) {
      console.error("SOW scan error", e);
      setError('Error scanning for SOWs');
    } finally {
      setScanningSOWs(false);
    }
  };

  useEffect(() => {
    if (profile?.uei) {
      fetchDocuments();
      fetchLinks();
    }
  }, [profile]);

  const [suggestedEntity, setSuggestedEntity] = useState<Entity | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (file: File | null) => {
    setFile(file);
    setError(null);
  };
  const fetchProfile = async () => {
    setLoading(true);
    try {
      // 1. Fetch all profiles to get the first one's UEI
      const listRes = await fetch('/api/v1/company/');
      let profileData = null;

      if (listRes.ok) {
        const data = await listRes.json();
        if (data && data.length > 0) {
          const firstProfile = data[0];

          // 2. Fetch the FULL profile with past_performances using the UEI
          const profileRes = await fetch(`/api/v1/company/${firstProfile.uei}`);
          if (profileRes.ok) {
            profileData = await profileRes.json();
            setProfile(profileData);
            setFormData(profileData);
          }
        }
      }

      // 3. Fetch Primary Entity (always, to check if we can suggest or enrich)
      try {
        const entityRes = await fetch(`/api/v1/entities/primary`);
        if (entityRes.ok) {
          const entityData = await entityRes.json();

          if (entityData) {
            // Case A: Profile exists - enrich with logo if missing
            if (profileData && !profileData.logo_url && entityData.logo_url) {
              setProfile(prev => prev ? ({ ...prev, logo_url: entityData.logo_url }) : null);
            }

            // Case B: No Profile - suggest this entity
            if (!profileData) {
              setSuggestedEntity(entityData);
            }
          }
        }
      } catch (e) {
        console.error("Failed to fetch entity info", e);
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

  // Poll for document updates if any are processing
  useEffect(() => {
    const processingDocs = documents.some((doc: CompanyProfileDocument) => doc.status === 'PROCESSING');
    if (processingDocs) {
      const interval = setInterval(fetchDocuments, 5000);
      return () => clearInterval(interval);
    }
  }, [documents, profile?.uei]);

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

  const handleReanalyze = async (docId: number) => {
    if (!profile) return;
    try {
      const res = await fetch(`/api/v1/company/${profile.uei}/documents/${docId}/reanalyze`, {
        method: 'POST',
      });
      if (res.ok) {
        setSuccess('Document re-analysis triggered!');
        fetchDocuments();
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to reanalyze document');
      }
    } catch (err) {
      console.error(err);
      setError('Failed to trigger re-analysis');
    }
  };

  // Map of docId -> boolean for tracking generation status
  const [generating, setGenerating] = useState<Record<number, boolean>>({});

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev: CompanyProfile) => ({
      ...prev,
      [name]: value
    }));
  };
  const handleGeneratePP = async (docId: number) => {
    if (!profile?.uei) return;

    setGenerating(prev => ({ ...prev, [docId]: true }));
    try {
      const res = await fetch(`/api/v1/company/${profile.uei}/documents/${docId}/generate-pp`, {
        method: 'POST',
      });

      if (res.ok) {
        setSuccess('Past Performance generation started successfully. This may take a moment.');
        // Brief delay before refresh to allow backend to initialize the task/record
        setTimeout(fetchProfile, 2000);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to generate Past Performance');
      }
    } catch (err: any) {
      console.error("Fetch Error:", err);
      setError(`Failed to generate Past Performance: ${err.message}`);
    } finally {
      setGenerating(prev => ({ ...prev, [docId]: false }));
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
        setProfile(prev => prev ? ({ ...prev, logo_url: data.logo_url }) : null);
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

            {/* Suggestion Card */}
            {suggestedEntity && !entitySearchQuery && (
              <div className="mb-6 p-4 border border-blue-200 bg-blue-50/50 rounded-lg animate-in slide-in-from-top-2">
                <div className="flex items-start gap-4">
                  {suggestedEntity.logo_url ? (
                    <img src={suggestedEntity.logo_url} alt="Logo" className="h-12 w-12 object-contain bg-white rounded border" />
                  ) : (
                    <div className="h-12 w-12 bg-blue-100 rounded flex items-center justify-center text-blue-600">
                      <Building2 className="h-6 w-6" />
                    </div>
                  )}
                  <div className="flex-1">
                    <h3 className="font-semibold text-blue-900">Found Primary Entity: {suggestedEntity.legal_business_name}</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      We found a primary entity configured in your system. Would you like to use this for your company profile?
                    </p>
                    <div className="flex gap-2 mt-3">
                      <Button
                        size="sm"
                        onClick={() => setEntityAsProfile(suggestedEntity)}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        Yes, Use {suggestedEntity.legal_business_name}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setSuggestedEntity(null)}
                        className="text-blue-700 hover:text-blue-900 hover:bg-blue-100"
                      >
                        No, Search for Another
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}
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
                        onChange={e => setFormData({ ...formData, company_name: e.target.value })}
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
                        onChange={e => setFormData({ ...formData, uei: e.target.value })}
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

          {/* Awards Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Contracts & Awards
              </CardTitle>
              <CardDescription>
                Recent Prime and Sub-Awards fetched from USASpending.gov
              </CardDescription>
            </CardHeader>
            <CardContent>
              {profile?.awards && profile.awards.length > 0 ? (
                <div className="max-h-[600px] overflow-y-auto border rounded-lg">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-muted/50 text-xs uppercase sticky top-0 z-10">
                      <tr>
                        <th className="px-4 py-3 font-medium text-muted-foreground rounded-tl-lg">Award ID</th>
                        <th className="px-4 py-3 font-medium text-muted-foreground">Type</th>
                        <th className="px-4 py-3 font-medium text-muted-foreground">Date</th>
                        <th className="px-4 py-3 font-medium text-muted-foreground">Agency</th>
                        <th className="px-4 py-3 font-medium text-muted-foreground">Value</th>
                        <th className="px-4 py-3 font-medium text-muted-foreground rounded-tr-lg">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {profile.awards.slice(0, 50).map((award) => ( // Show max 50 for now
                        <tr key={award.award_id} className="hover:bg-muted/30 transition-colors group">
                          <td className="px-4 py-3 font-mono font-medium">
                            {award.award_id}
                            {award.solicitation_id && (
                              <div className="flex items-center gap-1 mt-1 text-xs text-blue-600">
                                <LinkIcon className="h-3 w-3" />
                                <span title="Linked Solicitation">{award.solicitation_id}</span>
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant={award.award_type === 'Prime' ? 'default' : 'secondary'} className="text-[10px] px-2 h-5">
                              {award.award_type}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                            {award.award_date ? new Date(award.award_date).toLocaleDateString() : '-'}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground max-w-[150px] truncate" title={award.awarding_agency || ''}>
                            {award.awarding_agency || '-'}
                          </td>
                          <td className="px-4 py-3 font-medium text-green-700 whitespace-nowrap">
                            {award.total_obligation ?
                              new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(award.total_obligation)
                              : '-'}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground max-w-[300px]">
                            <p className="truncate group-hover:whitespace-normal group-hover:break-words group-hover:bg-popover group-hover:p-2 group-hover:absolute group-hover:z-10 group-hover:shadow-lg group-hover:border group-hover:rounded-md group-hover:max-w-md">
                              {award.description}
                            </p>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  No awards found for this entity.
                </div>
              )}
            </CardContent>
          </Card>

          {/* SOW / Contract Documents Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Contract Documents (SOW/PWS)
              </CardTitle>
              <CardDescription>
                Scan SAM.gov for Statements of Work linked to these awards.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!contractDocuments.length && !scanningSOWs && !sowScanComplete ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">
                    Scanning for documents involves checking SAM.gov for each solicitation linked to the awards above.
                    This process may take a minute.
                  </p>
                  <Button onClick={scanForSOWs} className="gap-2">
                    <Search className="h-4 w-4" /> Scan for Documents
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {scanningSOWs && (
                    <div className="flex items-center justify-center p-8 text-muted-foreground gap-2 animate-pulse">
                      <Loader2 className="h-5 w-5 animate-spin" /> Scanning related solicitations...
                    </div>
                  )}

                  {!scanningSOWs && contractDocuments.length === 0 && sowScanComplete && (
                    <div className="text-center py-8 text-muted-foreground">
                      No documents found linked to the recent awards.
                    </div>
                  )}

                  {contractDocuments.length > 0 && (
                    <div className="max-h-[600px] overflow-y-auto border rounded-lg">
                      <table className="w-full text-sm text-left">
                        <thead className="bg-muted/50 text-xs uppercase sticky top-0 z-10">
                          <tr>
                            <th className="px-4 py-3 font-medium text-muted-foreground">Type</th>
                            <th className="px-4 py-3 font-medium text-muted-foreground">Filename</th>
                            <th className="px-4 py-3 font-medium text-muted-foreground">Solicitation</th>
                            <th className="px-4 py-3 font-medium text-muted-foreground">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {contractDocuments.map((doc, idx) => (
                            <tr key={idx} className="hover:bg-muted/30">
                              <td className="px-4 py-3">
                                <Badge variant="outline" className={cn(
                                  "font-mono text-xs",
                                  doc.document_type === 'SOW' || doc.document_type === 'PWS' ? "bg-green-50 text-green-700 border-green-200" : ""
                                )}>
                                  {doc.document_type}
                                </Badge>
                              </td>
                              <td className="px-4 py-3 font-medium">
                                <div className="flex items-center gap-2">
                                  <FileText className="h-4 w-4 text-muted-foreground" />
                                  <span className="truncate max-w-[300px]" title={doc.document_filename}>
                                    {doc.document_filename}
                                  </span>
                                </div>
                              </td>
                              <td className="px-4 py-3 text-muted-foreground">
                                {doc.solicitation_id}
                              </td>
                              <td className="px-4 py-3">
                                <a
                                  href={doc.document_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1 text-blue-600 hover:underline text-xs"
                                >
                                  <Download className="h-3 w-3" /> Download
                                </a>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>


          {/* Document Upload Section */}
          {
            !isEditing && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Upload className="h-5 w-5 text-primary" />
                      Company Documents
                    </CardTitle>
                    <Button variant="ghost" size="sm" onClick={fetchDocuments} title="Refresh List">
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                  <CardDescription>
                    Upload capability statements, past performance, and other documents.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Upload Form */}
                  <div className="space-y-4">
                    <BulkUploadDropzone
                      files={filesToUpload}
                      onFilesChange={setFilesToUpload}
                    />

                    {filesToUpload.length > 0 && (
                      <div className="space-y-2">
                        {/* Classification Preview (simulated for immediate feedback / can be enhanced later) */}
                        <div className="bg-muted/30 p-4 rounded-lg border text-sm text-muted-foreground">
                          <p>Ready to upload {filesToUpload.length} file(s). We will automatically classify these documents.</p>
                        </div>

                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            onClick={() => setFilesToUpload([])}
                            disabled={uploading}
                          >
                            Clear
                          </Button>
                          <Button
                            onClick={handleBulkUpload}
                            disabled={uploading}
                            className="gap-2"
                          >
                            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                            Upload {filesToUpload.length} Documents
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>


                  {/* Documents List */}
                  {docsLoading ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                  ) : documents.length > 0 ? (
                    <div className="space-y-2">
                      <h4 className="font-semibold text-sm text-muted-foreground uppercase">Uploaded Documents</h4>
                      <div className="max-h-[500px] overflow-y-auto space-y-2 pr-2">
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
                              <Button
                                variant="ghost"
                                size="sm"
                                title="Reanalyze Document"
                                onClick={() => handleReanalyze(doc.id)}
                              >
                                <RefreshCw className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                title="Generate Past Performance"
                                onClick={() => handleGeneratePP(doc.id)}
                                disabled={generating[doc.id]}
                              >
                                {generating[doc.id] ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Sparkles className="h-4 w-4 text-amber-500" />
                                )}
                              </Button>
                              <a
                                href={`/uploads/${doc.file_path.split('/').pop()}`}
                                download
                                className="inline-flex items-center justify-center h-9 w-9 rounded-md hover:bg-accent transition-colors"
                                title="Download"
                              >
                                <Download className="h-4 w-4" />
                              </a>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => deleteDocument(doc.id)}
                                title="Delete"
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <FileText className="h-10 w-10 mx-auto opacity-20 mb-2" />
                      <p>No documents uploaded yet.</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          }

          {/* Links Section */}
          {
            !isEditing && (
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
            )
          }

          {/* Past Performance Section */}
          {!isEditing && profile?.past_performances && profile.past_performances.length > 0 && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-amber-500" />
                  Generated Past Performance
                </CardTitle>
                <CardDescription>
                  AI-generated past performance records from uploaded documents.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {profile.past_performances.map((pp) => (
                    <div key={pp.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-semibold">{pp.title}</h4>
                          <Badge variant="outline" className="mt-1">{pp.status}</Badge>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/past-performance/${pp.id}`)}
                        >
                          View Details
                        </Button>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Generated on {new Date(pp.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )
      }

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
              <Select value={newLink.link_type} onValueChange={(v) => setNewLink({ ...newLink, link_type: v })}>
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
                onChange={(e) => setNewLink({ ...newLink, title: e.target.value })}
                placeholder="e.g. Company Capability Statement"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="link-url">URL</Label>
              <Input
                id="link-url"
                type="url"
                value={newLink.url}
                onChange={(e) => setNewLink({ ...newLink, url: e.target.value })}
                placeholder="https://..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="link-desc">Description (Optional)</Label>
              <Textarea
                id="link-desc"
                value={newLink.description}
                onChange={(e) => setNewLink({ ...newLink, description: e.target.value })}
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
    </div >
  );
}
