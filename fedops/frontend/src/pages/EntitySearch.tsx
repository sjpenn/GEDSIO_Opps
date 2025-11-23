import { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
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
  "Award ID": string;
  "Recipient Name": string;
  "Award Amount": number;
  "Description": string;
  "Awarding Agency": string;
  "Place of Performance City Name"?: string;
  "Place of Performance State Code"?: string;
  "Place of Performance ZIP Code"?: string;
  "Place of Performance Country Code"?: string;
}

export default function EntitySearchPage() {
  console.log('EntitySearchPage rendered');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [awards, setAwards] = useState<Award[]>([]);
  const [awardsLoading, setAwardsLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/entities/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error(err);
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
      const data = await res.json();
      setAwards(data);
    } catch (err) {
      console.error(err);
    } finally {
      setAwardsLoading(false);
    }
  };

  // Prepare Chart Data
  const chartData = useMemo(() => {
    const agencyMap: Record<string, number> = {};
    awards.forEach(award => {
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
                className="bg-primary text-primary-foreground px-4 py-2 rounded"
              >
                Search
              </button>
            </form>

            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {results.map((entity, i) => (
                <div key={i} className={`p-4 border rounded cursor-pointer transition-colors ${selectedEntity?.uei === entity.uei ? 'bg-accent/50 border-primary' : 'bg-background hover:bg-accent/50'}`}
                     onClick={() => {
                        setSelectedEntity(entity);
                        fetchAwards(entity.uei);
                     }}>
                  <div className="flex justify-between items-start">
                    <h3 className="font-bold text-sm mb-1">{entity.legal_business_name}</h3>
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
                  <div className="flex justify-center p-12">Loading awards data...</div>
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
                              <tr key={i} className="hover:bg-muted/20">
                                <td className="p-3 font-mono">{award["Award ID"]}</td>
                                <td className="p-3">{award["Awarding Agency"]}</td>
                                <td className="p-3 max-w-xs truncate" title={award["Description"]}>{award["Description"]}</td>
                                <td className="p-3">
                                  {award["Place of Performance City Name"]}, {award["Place of Performance State Code"]}
                                </td>
                                <td className="p-3 text-right font-mono text-green-600">
                                  ${award["Award Amount"]?.toLocaleString()}
                                </td>
                              </tr>
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
