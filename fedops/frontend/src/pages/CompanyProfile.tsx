import { useState, useEffect } from 'react';

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

  if (loading && !profile && !isEditing) return <div>Loading...</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Company Profile</h1>
        {!isEditing && profile && (
          <button 
            onClick={() => setIsEditing(true)}
            className="bg-primary text-primary-foreground px-4 py-2 rounded"
          >
            Edit Profile
          </button>
        )}
      </div>

      {error && <div className="bg-destructive/10 text-destructive p-4 rounded mb-4">{error}</div>}

      {!profile && !isEditing ? (
        <div className="text-center py-12 bg-muted rounded-lg">
          <p className="mb-4">No company profile found.</p>
          <button 
            onClick={() => setIsEditing(true)}
            className="bg-primary text-primary-foreground px-4 py-2 rounded"
          >
            Create Profile
          </button>
        </div>
      ) : (
        <div className="space-y-8">
            <div className="bg-card border rounded-lg p-6 shadow-sm">
            {isEditing ? (
                <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                    <label className="block text-sm font-medium mb-1">Company Name</label>
                    <input
                        type="text"
                        name="company_name"
                        id="company-name"
                        required
                        value={formData.company_name}
                        onChange={e => setFormData({...formData, company_name: e.target.value})}
                        className="w-full p-2 rounded border bg-background"
                    />
                    </div>
                    <div>
                    <label className="block text-sm font-medium mb-1">UEI</label>
                    <input
                        type="text"
                        name="uei"
                        id="uei"
                        required
                        disabled={!!profile}
                        value={formData.uei}
                        onChange={e => setFormData({...formData, uei: e.target.value})}
                        className="w-full p-2 rounded border bg-background disabled:opacity-50"
                    />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1">Target NAICS Codes (comma separated)</label>
                    <input
                    type="text"
                    name="target_naics"
                    id="target-naics"
                    value={formData.target_naics.join(', ')}
                    onChange={e => handleArrayInput('target_naics', e.target.value)}
                    className="w-full p-2 rounded border bg-background"
                    placeholder="541511, 541512..."
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1">Target Keywords (comma separated)</label>
                    <input
                    type="text"
                    name="target_keywords"
                    id="target-keywords"
                    value={formData.target_keywords.join(', ')}
                    onChange={e => handleArrayInput('target_keywords', e.target.value)}
                    className="w-full p-2 rounded border bg-background"
                    placeholder="software, cloud, ai..."
                    />
                </div>

                <div className="flex gap-4">
                    <button 
                    type="submit" 
                    disabled={loading}
                    className="bg-primary text-primary-foreground px-4 py-2 rounded hover:bg-primary/90"
                    >
                    {loading ? 'Saving...' : 'Save Profile'}
                    </button>
                    <button 
                    type="button" 
                    onClick={() => {
                        setIsEditing(false);
                        if (profile) setFormData(profile);
                    }}
                    className="bg-secondary text-secondary-foreground px-4 py-2 rounded hover:bg-secondary/80"
                    >
                    Cancel
                    </button>
                </div>
                </form>
            ) : (
                <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                    <h3 className="text-sm font-medium text-muted-foreground">Company Name</h3>
                    <p className="text-lg font-semibold">{profile?.company_name}</p>
                    </div>
                    <div>
                    <h3 className="text-sm font-medium text-muted-foreground">UEI</h3>
                    <p className="text-lg font-mono">{profile?.uei}</p>
                    </div>
                </div>

                <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Target NAICS Codes</h3>
                    <div className="flex flex-wrap gap-2">
                    {profile?.target_naics.map(code => (
                        <span key={code} className="bg-secondary px-2 py-1 rounded text-sm font-mono">
                        {code}
                        </span>
                    ))}
                    </div>
                </div>

                <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Target Keywords</h3>
                    <div className="flex flex-wrap gap-2">
                    {profile?.target_keywords.map(kw => (
                        <span key={kw} className="bg-accent px-2 py-1 rounded text-sm">
                        {kw}
                        </span>
                    ))}
                    </div>
                </div>
                </div>
            )}
            </div>

            {/* Contract Documents Section */}
            <div className="bg-card border rounded-lg p-6 shadow-sm">
                <h2 className="text-xl font-semibold mb-4">Contract Documents (SOW/PWS)</h2>
                <p className="text-sm text-muted-foreground mb-4">
                    Documents retrieved from SAM.gov based on recent awards.
                </p>
                
                {docsLoading ? (
                    <div className="py-8 text-center text-muted-foreground">Searching for documents...</div>
                ) : documents.length > 0 ? (
                    <div className="space-y-4">
                        {documents.map((doc, i) => (
                            <div key={i} className="flex items-start justify-between p-4 border rounded hover:bg-accent/10">
                                <div>
                                    <h3 className="font-medium">{doc.title || "Untitled Opportunity"}</h3>
                                    <p className="text-xs text-muted-foreground font-mono mb-1">Solicitation: {doc.solicitation_id}</p>
                                    <p className="text-xs text-muted-foreground">Award ID: {doc.award_id}</p>
                                </div>
                                <a 
                                    href={typeof doc.document_url === 'string' ? doc.document_url : doc.document_url?.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-sm hover:bg-blue-200 flex items-center gap-1"
                                >
                                    <span>Download</span>
                                    <span className="text-xs">↗</span>
                                </a>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="py-8 text-center text-muted-foreground border-2 border-dashed rounded">
                        No documents found for recent awards.
                    </div>
                )}
            </div>
        </div>
      )}
    </div>
  );
}
