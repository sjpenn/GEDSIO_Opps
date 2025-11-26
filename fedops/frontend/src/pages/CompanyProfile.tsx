import { useState, useEffect } from 'react';
import { Loader2, Building2, Target, Key, FileText, Download, Edit2, Save, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

interface CompanyProfile {
  uei: string;
  company_name: string;
  target_naics: string[];
  target_keywords: string[];
  target_set_asides: string[];
}

export default function CompanyProfilePage() {
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Form state
  const [formData, setFormData] = useState<CompanyProfile>({
    uei: '',
    company_name: '',
    target_naics: [],
    target_keywords: [],
    target_set_asides: []
  });

  const [documents, setDocuments] = useState<any[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  useEffect(() => {
    if (profile?.uei) {
        fetchDocuments(profile.uei);
    }
  }, [profile]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/company/');
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setProfile(data[0]);
          setFormData(data[0]);
        }
      }
    } catch (err) {
      setError('Failed to fetch profile');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async (uei: string) => {
    setDocsLoading(true);
    try {
        const res = await fetch(`/api/v1/entities/${uei}/contract-documents`);
        if (res.ok) {
            const data = await res.json();
            setDocuments(data);
        }
    } catch (err) {
        console.error("Failed to fetch documents", err);
    } finally {
        setDocsLoading(false);
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
    <div className="space-y-6 animate-in fade-in duration-500 max-w-5xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Company Profile</h2>
          <p className="text-muted-foreground">Manage your company details and targeting preferences.</p>
        </div>
        {!isEditing && profile && (
          <Button onClick={() => setIsEditing(true)} className="gap-2">
            <Edit2 className="h-4 w-4" /> Edit Profile
          </Button>
        )}
      </div>

      {error && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardContent className="pt-6 text-destructive flex items-center gap-2">
            <X className="h-5 w-5" /> {error}
          </CardContent>
        </Card>
      )}

      {!profile && !isEditing ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="bg-primary/10 p-4 rounded-full mb-4">
              <Building2 className="h-12 w-12 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No Company Profile Found</h3>
            <p className="text-muted-foreground max-w-md mb-6">
              Create a profile to start tracking opportunities, managing documents, and finding partners.
            </p>
            <Button onClick={() => setIsEditing(true)} size="lg">
              Create Profile
            </Button>
          </CardContent>
        </Card>
      ) : (
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
                    <div>
                      <h3 className="text-sm font-medium text-muted-foreground uppercase mb-1">Company Name</h3>
                      <p className="text-2xl font-bold tracking-tight">{profile?.company_name}</p>
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

          {/* Contract Documents Section */}
          {!isEditing && (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-primary" /> Contract Documents
                    </CardTitle>
                    <CardDescription>
                      SOW/PWS documents retrieved from SAM.gov based on recent awards.
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="ml-auto">
                    {documents.length} Documents
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {docsLoading ? (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin mb-2" />
                    <p>Searching for documents...</p>
                  </div>
                ) : documents.length > 0 ? (
                  <div className="grid gap-3">
                    {documents.map((doc, i) => (
                      <div 
                        key={i} 
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/30 transition-colors group bg-card"
                      >
                        <div className="flex items-start gap-4">
                          <div className="p-2 bg-primary/10 rounded mt-1">
                            <FileText className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <h4 className="font-medium text-base group-hover:text-primary transition-colors">
                              {doc.title || "Untitled Opportunity"}
                            </h4>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-sm text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">SOL: {doc.solicitation_id}</span>
                              </span>
                              <span className="flex items-center gap-1">
                                <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">AWARD: {doc.award_id}</span>
                              </span>
                            </div>
                          </div>
                        </div>
                        <Button variant="outline" size="sm" asChild className="gap-2 ml-4 shrink-0">
                          <a 
                            href={typeof doc.document_url === 'string' ? doc.document_url : doc.document_url?.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                          >
                            <Download className="h-4 w-4" /> Download
                          </a>
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/5">
                    <FileText className="h-10 w-10 opacity-20 mb-3" />
                    <p>No documents found for recent awards.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
