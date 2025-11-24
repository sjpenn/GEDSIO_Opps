import { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loader2 } from 'lucide-react';
// Map imports removed for stability
// import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
// import 'leaflet/dist/leaflet.css';
// import L from 'leaflet';

interface Entity {
  uei: string;
  legal_business_name: string;
  entity_type?: string;
  is_primary?: boolean;
}

interface Award {
  // Basic Information
  "Award ID": string;
  "Recipient Name": string;
  "Description": string;
  
  // Financial Fields
  "Award Amount": number;
  "Total Obligation"?: number;
  "Base and All Options Value"?: number;
  "Base Exercised Options Val"?: number;
  
  // Date Fields
  "Start Date"?: string;
  "End Date"?: string;
  "Current End Date"?: string;
  "Period of Performance Start Date"?: string;
  "Period of Performance Current End Date"?: string;
  "Last Modified Date"?: string;
  
  // Contract Details
  "Award Type"?: string;
  "Contract Award Type"?: string;
  "IDV Type"?: string;
  "Contract Pricing"?: string;
  "Type of Set Aside"?: string;
  "Extent Competed"?: string;
  
  // Agency Information
  "Awarding Agency": string;
  "Awarding Sub Agency"?: string;
  "Funding Agency"?: string;
  "Funding Sub Agency"?: string;
  
  // Location
  "Place of Performance City Name"?: string;
  "Place of Performance State Code"?: string;
  "Place of Performance ZIP Code"?: string;
  "Place of Performance Country Code"?: string;
  "Recipient Address Line 1"?: string;
  "Recipient City Name"?: string;
  "Recipient State Code"?: string;
  "Recipient ZIP Code"?: string;
  
  // Classification
  "NAICS Code"?: string;
  "NAICS Description"?: string;
  "Product or Service Code"?: string;
  "Product or Service Code Description"?: string;
  
  // Identifiers
  "Solicitation ID"?: string;
  "Parent Award ID"?: string;
  "Referenced IDV Agency Identifier"?: string;
  "Contract Award Unique Key"?: string;
  "Recipient UEI"?: string;
  "Recipient DUNS Number"?: string;
  
  // Additional Details
  "Sub-Award Count"?: number;
  "Number of Offers Received"?: number;
}

export default function EntitySearchPage() {
  console.log('EntitySearchPage rendered');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [awards, setAwards] = useState<Award[]>([]);
  const [awardsLoading, setAwardsLoading] = useState(false);
  const [selectedAward, setSelectedAward] = useState<Award | null>(null);
  const [solicitationDocs, setSolicitationDocs] = useState<any[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    
    setLoading(true);
    setHasSearched(true);
    setResults([]); // Clear previous results
    try {
      const res = await fetch(`/api/v1/entities/search?q=${encodeURIComponent(query)}`);
      if (!res.ok) {
        throw new Error(`Search failed: ${res.statusText}`);
      }
      const data = await res.json();
      console.log("Search results:", data);
      
      if (Array.isArray(data)) {
        setResults(data);
      } else {
        console.error("Search results is not an array:", data);
        setResults([]);
        // You might want to set an error state here to display to the user
      }
    } catch (err) {
      console.error("Error searching entities:", err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEntity = async (entity: Entity, type: 'PARTNER' | 'COMPETITOR') => {
    try {
      const res = await fetch('/api/v1/entities/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          uei: entity.uei,
          legal_business_name: entity.legal_business_name,
          entity_type: type
        })
      });
      if (res.ok) {
        alert(`Added ${entity.legal_business_name} as ${type}`);
        // Update results
        setResults(results.map(r => r.uei === entity.uei ? { ...r, entity_type: type } : r));
        // Update selectedEntity if it matches
        if (selectedEntity && selectedEntity.uei === entity.uei) {
            setSelectedEntity({ ...selectedEntity, entity_type: type });
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSetPrimary = async (uei: string) => {
    try {
      const res = await fetch(`/api/v1/entities/${uei}/primary`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_primary: true })
      });
      if (res.ok) {
        alert('Set as Primary Entity');
        if (selectedEntity && selectedEntity.uei === uei) {
             setSelectedEntity({...selectedEntity, is_primary: true});
        }
        setResults(results.map(r => r.uei === uei ? {...r, is_primary: true} : {...r, is_primary: false}));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAwards = async (uei: string) => {
    setAwardsLoading(true);
    try {
      const res = await fetch(`/api/v1/entities/${uei}/awards`);
      if (!res.ok) {
        console.error('Failed to fetch awards:', res.statusText);
        setAwards([]);
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setAwards(data);
      } else {
        console.error('Awards data is not an array:', data);
        setAwards([]);
      }
    } catch (err) {
      console.error(err);
      setAwards([]);
    } finally {
      setAwardsLoading(false);
    }
  };

  const fetchSolicitationDocuments = async (uei: string) => {
    setDocsLoading(true);
    try {
      const res = await fetch(`/api/v1/entities/${uei}/contract-documents`);
      if (!res.ok) {
        console.error('Failed to fetch solicitation documents:', res.statusText);
        setSolicitationDocs([]);
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setSolicitationDocs(data);
      } else {
        console.error('Solicitation documents data is not an array:', data);
        setSolicitationDocs([]);
      }
    } catch (err) {
      console.error('Error fetching solicitation documents:', err);
      setSolicitationDocs([]);
    } finally {
      setDocsLoading(false);
    }
  };

  // Prepare Chart Data
  const chartData = useMemo(() => {
    if (!Array.isArray(awards)) return [];
    
    const agencyMap: Record<string, number> = {};
    awards.forEach(award => {
      if (!award) return;
      const agency = award["Awarding Agency"] || "Unknown";
      agencyMap[agency] = (agencyMap[agency] || 0) + (award["Award Amount"] || 0);
    });
    return Object.entries(agencyMap)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10); // Top 10 agencies
  }, [awards]);

  return (
    <div className="h-full p-6">
      <h1 className="text-3xl font-bold mb-6">Entity Search & Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-auto min-h-[600px]">
        {/* Search Section */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-card p-6 rounded-lg border shadow-sm">
            <h2 className="text-xl font-semibold mb-4">Search SAM.gov</h2>
            <form onSubmit={handleSearch} className="flex gap-2 mb-4">
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Company Name..."
                className="flex-1 p-2 rounded border bg-background"
              />
              <button 
                type="submit" 
                disabled={loading}
                className="bg-primary text-primary-foreground px-4 py-2 rounded flex items-center justify-center min-w-[80px]"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
              </button>
            </form>

            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {hasSearched && results.length === 0 && !loading && (
                <p className="text-muted-foreground text-sm">No results found.</p>
              )}
              
              {results.map((entity, i) => (
                <div 
                  key={entity.uei || i} 
                  className={`p-4 border rounded cursor-pointer transition-colors ${selectedEntity?.uei === entity.uei ? 'bg-accent/50 border-primary' : 'bg-background hover:bg-accent/50'}`}
                  onClick={() => {
                    setSelectedEntity(entity);
                    fetchAwards(entity.uei);
                    fetchSolicitationDocuments(entity.uei);
                  }}
                >
                  <div className="flex justify-between items-start">
                    <h3 className="font-bold text-sm mb-1">{entity.legal_business_name || 'Unknown Name'}</h3>
                    <div className="flex gap-1">
                        {entity.is_primary && <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">Primary</span>}
                        {entity.entity_type === 'PARTNER' && <span className="text-xs bg-green-100 text-green-800 px-1 rounded">Partner</span>}
                        {entity.entity_type === 'COMPETITOR' && <span className="text-xs bg-red-100 text-red-800 px-1 rounded">Competitor</span>}
                    </div>
                  </div>
                  <p className="text-xs font-mono text-muted-foreground mb-2">UEI: {entity.uei}</p>
                  
                  <div className="flex flex-wrap gap-2 mt-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAddEntity(entity, 'PARTNER'); }}
                      className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200"
                    >
                      + Partner
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAddEntity(entity, 'COMPETITOR'); }}
                      className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200"
                    >
                      + Competitor
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Details Section */}
        <div className="lg:col-span-3 space-y-8">
          {selectedEntity ? (
            <>
              <div className="bg-card p-6 rounded-lg border shadow-sm">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-2xl font-bold">{selectedEntity.legal_business_name}</h2>
                      {selectedEntity.is_primary && <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">Primary Entity</span>}
                      {selectedEntity.entity_type === 'PARTNER' && <span className="bg-green-600 text-white text-xs px-2 py-1 rounded-full">Partner</span>}
                      {selectedEntity.entity_type === 'COMPETITOR' && <span className="bg-red-600 text-white text-xs px-2 py-1 rounded-full">Competitor</span>}
                    </div>
                    <p className="text-muted-foreground font-mono">UEI: {selectedEntity.uei}</p>
                  </div>
                  <div className="flex gap-2">
                    {!selectedEntity.is_primary && (
                        <button 
                            onClick={() => handleSetPrimary(selectedEntity.uei)}
                            className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 text-sm"
                        >
                            Set as Primary
                        </button>
                    )}
                    <button 
                        onClick={() => setSelectedEntity(null)}
                        className="text-muted-foreground hover:text-foreground"
                    >
                        Close
                    </button>
                  </div>
                </div>

                {awardsLoading ? (
                  <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin mb-2" />
                    <p>Loading awards data...</p>
                  </div>
                ) : awards.length > 0 ? (
                  <div className="space-y-8">
                    
                    {/* Charts & Map Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      {/* Chart */}
                      <div className="border rounded p-4">
                        <h3 className="font-semibold mb-4">Spending by Agency</h3>
                        <div style={{ width: '100%', height: '300px' }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} layout="vertical" margin={{ left: 40 }}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis type="number" tickFormatter={(val) => `$${(val/1000000).toFixed(0)}M`} />
                              <YAxis type="category" dataKey="name" width={150} style={{ fontSize: '10px' }} />
                              <Tooltip formatter={(val: number) => `$${val.toLocaleString()}`} />
                              <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      {/* Map - Disabled for stability */}
                      {/* 
                      <div className="border rounded p-4">
                        <h3 className="font-semibold mb-4">Award Locations</h3>
                        <div className="h-[300px] rounded overflow-hidden relative z-0">
                           <MapContainer center={[39.8283, -98.5795]} zoom={3} style={{ height: '100%', width: '100%' }}>
                            <TileLayer
                              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            />
                            {mapMarkers.map((marker, idx) => (
                              <Marker key={idx} position={marker.position}>
                                <Popup>
                                  <div className="text-xs">
                                    <strong>{marker["Awarding Agency"]}</strong><br/>
                                    {marker["Place of Performance City Name"]}, {marker["Place of Performance State Code"]}<br/>
                                    ${marker["Award Amount"]?.toLocaleString()}
                                  </div>
                                </Popup>
                              </Marker>
                            ))}
                          </MapContainer>
                        </div>
                      </div>
                      */}
                    </div>

                    {/* Table */}
                    <div>
                      <h3 className="font-semibold mb-4">Recent Awards</h3>
                      <div className="border rounded overflow-hidden">
                        <table className="w-full text-sm text-left">
                          <thead className="bg-muted/50 text-muted-foreground font-medium border-b">
                            <tr>
                              <th className="p-3">Award ID</th>
                              <th className="p-3">Agency</th>
                              <th className="p-3">Description</th>
                              <th className="p-3">Location</th>
                              <th className="p-3 text-right">Amount</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {awards.map((award, i) => (
                              <>
                                <tr key={i} className={`hover:bg-muted/20 ${selectedAward?.["Award ID"] === award["Award ID"] ? 'bg-accent/50' : ''}`}>
                                  <td className="p-3 font-mono">
                                    <button 
                                      onClick={() => setSelectedAward(selectedAward?.["Award ID"] === award["Award ID"] ? null : award)}
                                      className="text-blue-600 hover:text-blue-800 hover:underline cursor-pointer transition-colors"
                                    >
                                      {award["Award ID"]}
                                    </button>
                                  </td>
                                  <td className="p-3">{award["Awarding Agency"]}</td>
                                  <td className="p-3 max-w-xs truncate" title={award["Description"]}>{award["Description"]}</td>
                                  <td className="p-3">
                                    {award["Place of Performance City Name"]}, {award["Place of Performance State Code"]}
                                  </td>
                                  <td className="p-3 text-right font-mono text-green-600">
                                    ${award["Award Amount"]?.toLocaleString()}
                                  </td>
                                </tr>
                                {selectedAward?.["Award ID"] === award["Award ID"] && (
                                  <tr key={`${i}-details`}>
                                    <td colSpan={5} className="p-0">
                                      <div className="bg-accent/20 p-6 border-t border-b">
                                        <div className="flex justify-between items-start mb-6">
                                          <h4 className="text-xl font-bold">Complete Award Details</h4>
                                          <button 
                                            onClick={() => setSelectedAward(null)}
                                            className="text-muted-foreground hover:text-foreground text-sm px-3 py-1 border rounded"
                                          >
                                            ✕ Close
                                          </button>
                                        </div>

                                        <div className="space-y-6">
                                          {/* Header Section */}
                                          <div className="bg-card p-4 rounded border">
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                              <div>
                                                <p className="text-xs text-muted-foreground font-medium mb-1">Award ID</p>
                                                <p className="font-mono text-sm">{award["Award ID"]}</p>
                                              </div>
                                              <div>
                                                <p className="text-xs text-muted-foreground font-medium mb-1">Recipient</p>
                                                <p className="text-sm">{award["Recipient Name"]}</p>
                                              </div>
                                              <div>
                                                <p className="text-xs text-muted-foreground font-medium mb-1">Award Amount</p>
                                                <p className="text-lg font-bold text-green-600">${award["Award Amount"]?.toLocaleString()}</p>
                                              </div>
                                            </div>
                                            <div className="mt-3">
                                              <p className="text-xs text-muted-foreground font-medium mb-1">Description</p>
                                              <p className="text-sm">{award["Description"]}</p>
                                            </div>
                                          </div>

                                          {/* Financial Information */}
                                          <div>
                                            <h5 className="font-semibold mb-3 text-sm">💰 Financial Information</h5>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-card p-4 rounded border">
                                              {award["Total Obligation"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Total Obligation</p>
                                                  <p className="text-sm font-mono">${award["Total Obligation"]?.toLocaleString()}</p>
                                                </div>
                                              )}
                                              {award["Base and All Options Value"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Base and All Options Value</p>
                                                  <p className="text-sm font-mono">${award["Base and All Options Value"]?.toLocaleString()}</p>
                                                </div>
                                              )}
                                              {award["Base Exercised Options Val"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Base Exercised Options</p>
                                                  <p className="text-sm font-mono">${award["Base Exercised Options Val"]?.toLocaleString()}</p>
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Timeline Information */}
                                          <div>
                                            <h5 className="font-semibold mb-3 text-sm">📅 Timeline</h5>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-card p-4 rounded border">
                                              {award["Start Date"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Start Date</p>
                                                  <p className="text-sm">{award["Start Date"]}</p>
                                                </div>
                                              )}
                                              {award["End Date"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">End Date</p>
                                                  <p className="text-sm">{award["End Date"]}</p>
                                                </div>
                                              )}
                                              {award["Current End Date"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Current End Date</p>
                                                  <p className="text-sm">{award["Current End Date"]}</p>
                                                </div>
                                              )}
                                              {award["Period of Performance Start Date"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">PoP Start Date</p>
                                                  <p className="text-sm">{award["Period of Performance Start Date"]}</p>
                                                </div>
                                              )}
                                              {award["Period of Performance Current End Date"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">PoP Current End Date</p>
                                                  <p className="text-sm">{award["Period of Performance Current End Date"]}</p>
                                                </div>
                                              )}
                                              {award["Last Modified Date"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Last Modified</p>
                                                  <p className="text-sm">{award["Last Modified Date"]}</p>
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Contract Information */}
                                          <div>
                                            <h5 className="font-semibold mb-3 text-sm">📋 Contract Information</h5>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-card p-4 rounded border">
                                              {award["Award Type"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Award Type</p>
                                                  <p className="text-sm">{award["Award Type"]}</p>
                                                </div>
                                              )}
                                              {award["Contract Award Type"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Contract Award Type</p>
                                                  <p className="text-sm">{award["Contract Award Type"]}</p>
                                                </div>
                                              )}
                                              {award["IDV Type"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">IDV Type</p>
                                                  <p className="text-sm">{award["IDV Type"]}</p>
                                                </div>
                                              )}
                                              {award["Contract Pricing"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Contract Pricing</p>
                                                  <p className="text-sm">{award["Contract Pricing"]}</p>
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Competition & Set Aside */}
                                          <div>
                                            <h5 className="font-semibold mb-3 text-sm">🏆 Competition & Set Aside</h5>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-card p-4 rounded border">
                                              {award["Type of Set Aside"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Type of Set Aside</p>
                                                  <p className="text-sm">{award["Type of Set Aside"]}</p>
                                                </div>
                                              )}
                                              {award["Extent Competed"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Extent Competed</p>
                                                  <p className="text-sm">{award["Extent Competed"]}</p>
                                                </div>
                                              )}
                                              {award["Number of Offers Received"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Offers Received</p>
                                                  <p className="text-sm">{award["Number of Offers Received"]}</p>
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Agency Information */}
                                          <div>
                                            <h5 className="font-semibold mb-3 text-sm">🏛️ Agency Information</h5>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-card p-4 rounded border">
                                              <div>
                                                <p className="text-xs text-muted-foreground font-medium mb-1">Awarding Agency</p>
                                                <p className="text-sm">{award["Awarding Agency"]}</p>
                                                {award["Awarding Sub Agency"] && (
                                                  <p className="text-xs text-muted-foreground mt-1">{award["Awarding Sub Agency"]}</p>
                                                )}
                                              </div>
                                              {award["Funding Agency"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Funding Agency</p>
                                                  <p className="text-sm">{award["Funding Agency"]}</p>
                                                  {award["Funding Sub Agency"] && (
                                                    <p className="text-xs text-muted-foreground mt-1">{award["Funding Sub Agency"]}</p>
                                                  )}
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Classification */}
                                          <div>
                                            <h5 className="font-semibold mb-3 text-sm">🏷️ Classification</h5>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-card p-4 rounded border">
                                              {award["NAICS Code"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">NAICS Code</p>
                                                  <p className="text-sm font-mono">{award["NAICS Code"]}</p>
                                                  {award["NAICS Description"] && (
                                                    <p className="text-xs text-muted-foreground mt-1">{award["NAICS Description"]}</p>
                                                  )}
                                                </div>
                                              )}
                                              {award["Product or Service Code"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">PSC Code</p>
                                                  <p className="text-sm font-mono">{award["Product or Service Code"]}</p>
                                                  {award["Product or Service Code Description"] && (
                                                    <p className="text-xs text-muted-foreground mt-1">{award["Product or Service Code Description"]}</p>
                                                  )}
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Location Information */}
                                          <div>
                                            <h5 className="font-semibold mb-3 text-sm">📍 Location Information</h5>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-card p-4 rounded border">
                                              <div>
                                                <p className="text-xs text-muted-foreground font-medium mb-1">Place of Performance</p>
                                                <p className="text-sm">
                                                  {award["Place of Performance City Name"]}, {award["Place of Performance State Code"]} {award["Place of Performance ZIP Code"]}
                                                  {award["Place of Performance Country Code"] && ` - ${award["Place of Performance Country Code"]}`}
                                                </p>
                                              </div>
                                              {award["Recipient Address Line 1"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Recipient Address</p>
                                                  <p className="text-sm">
                                                    {award["Recipient Address Line 1"]}<br/>
                                                    {award["Recipient City Name"]}, {award["Recipient State Code"]} {award["Recipient ZIP Code"]}
                                                  </p>
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Identifiers */}
                                          <div>
                                            <h5 className="font-semibold mb-3 text-sm">🔑 Identifiers</h5>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-card p-4 rounded border">
                                              {award["Solicitation ID"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Solicitation ID</p>
                                                  <p className="text-sm font-mono">{award["Solicitation ID"]}</p>
                                                </div>
                                              )}
                                              {award["Contract Award Unique Key"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Contract Award Key</p>
                                                  <p className="text-sm font-mono text-xs">{award["Contract Award Unique Key"]}</p>
                                                </div>
                                              )}
                                              {award["Parent Award ID"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Parent Award ID</p>
                                                  <p className="text-sm font-mono">{award["Parent Award ID"]}</p>
                                                </div>
                                              )}
                                              {award["Recipient UEI"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">Recipient UEI</p>
                                                  <p className="text-sm font-mono">{award["Recipient UEI"]}</p>
                                                </div>
                                              )}
                                              {award["Recipient DUNS Number"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">DUNS Number</p>
                                                  <p className="text-sm font-mono">{award["Recipient DUNS Number"]}</p>
                                                </div>
                                              )}
                                              {award["Referenced IDV Agency Identifier"] && (
                                                <div>
                                                  <p className="text-xs text-muted-foreground font-medium mb-1">IDV Agency ID</p>
                                                  <p className="text-sm font-mono">{award["Referenced IDV Agency Identifier"]}</p>
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Solicitation Documents */}
                                          {award["Solicitation ID"] && (
                                            <div>
                                              <h5 className="font-semibold mb-3 text-sm">📄 Solicitation Documents</h5>
                                              {docsLoading ? (
                                                <div className="bg-card p-4 rounded border flex items-center justify-center">
                                                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                                                  <span className="text-sm text-muted-foreground">Loading documents...</span>
                                                </div>
                                              ) : (
                                                <div className="bg-card p-4 rounded border space-y-2">
                                                  {solicitationDocs.filter(doc => doc.solicitation_id === award["Solicitation ID"]).length > 0 ? (
                                                    solicitationDocs
                                                      .filter(doc => doc.solicitation_id === award["Solicitation ID"])
                                                      .map((doc, idx) => (
                                                        <a
                                                          key={idx}
                                                          href={doc.document_url}
                                                          target="_blank"
                                                          rel="noreferrer"
                                                          className="flex items-start justify-between p-3 bg-background border border-border rounded hover:border-primary/50 transition-colors group"
                                                        >
                                                          <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-2 mb-1">
                                                              <span className="text-sm font-medium truncate group-hover:text-primary">
                                                                {doc.document_filename}
                                                              </span>
                                                              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                                                doc.document_type === 'SOW' ? 'bg-blue-100 text-blue-800' :
                                                                doc.document_type === 'PWS' ? 'bg-purple-100 text-purple-800' :
                                                                doc.document_type === 'RFP' ? 'bg-green-100 text-green-800' :
                                                                doc.document_type === 'Amendment' ? 'bg-yellow-100 text-yellow-800' :
                                                                'bg-gray-100 text-gray-800'
                                                              }`}>
                                                                {doc.document_type}
                                                              </span>
                                                            </div>
                                                            {doc.opportunity_title && (
                                                              <p className="text-xs text-muted-foreground truncate">
                                                                {doc.opportunity_title}
                                                              </p>
                                                            )}
                                                          </div>
                                                          <span className="ml-2 text-muted-foreground group-hover:text-primary transition-transform group-hover:translate-x-1">
                                                            ↗
                                                          </span>
                                                        </a>
                                                      ))
                                                  ) : (
                                                    <p className="text-sm text-muted-foreground italic">
                                                      No solicitation documents found for this award.
                                                    </p>
                                                  )}
                                                </div>
                                              )}
                                            </div>
                                          )}

                                          {/* Additional Details */}
                                          {award["Sub-Award Count"] && (
                                            <div>
                                              <h5 className="font-semibold mb-3 text-sm">📊 Additional Details</h5>
                                              <div className="bg-card p-4 rounded border">
                                                <p className="text-xs text-muted-foreground font-medium mb-1">Sub-Award Count</p>
                                                <p className="text-sm">{award["Sub-Award Count"]}</p>
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                  </div>
                ) : (
                  <p className="text-muted-foreground">No recent awards found.</p>
                )}
              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg p-12 bg-muted/10">
              <div className="text-4xl mb-4">🏢</div>
              <p className="text-lg">Select an entity to view details</p>
              <p className="text-sm">Search for a company on the left to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
