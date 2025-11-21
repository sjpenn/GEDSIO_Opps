import { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icon in Leaflet with React
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

interface Entity {
  uei: string;
  legal_business_name: string;
  entity_type?: string;
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

// Simple State to Lat/Lng mapping for demo purposes
const STATE_COORDINATES: Record<string, [number, number]> = {
  'AL': [32.806671, -86.791130], 'AK': [61.370716, -152.404419], 'AZ': [33.729759, -111.431221],
  'AR': [34.969704, -92.373123], 'CA': [36.116203, -119.681564], 'CO': [39.059811, -105.311104],
  'CT': [41.597782, -72.755371], 'DE': [39.318523, -75.507141], 'FL': [27.766279, -81.686783],
  'GA': [33.040619, -83.643074], 'HI': [21.094318, -157.498337], 'ID': [44.240459, -114.478828],
  'IL': [40.349457, -88.986137], 'IN': [39.849426, -86.258278], 'IA': [42.011539, -93.210526],
  'KS': [38.526600, -96.726486], 'KY': [37.668140, -84.670067], 'LA': [31.169546, -91.867805],
  'ME': [44.693947, -69.381927], 'MD': [39.063946, -76.802101], 'MA': [42.230171, -71.530106],
  'MI': [43.326618, -84.536095], 'MN': [45.694454, -93.900192], 'MS': [32.741646, -89.678696],
  'MO': [38.456085, -92.288368], 'MT': [46.921925, -110.454353], 'NE': [41.125370, -98.268082],
  'NV': [38.313515, -117.055374], 'NH': [43.452492, -71.563896], 'NJ': [40.298904, -74.521011],
  'NM': [34.840515, -106.248482], 'NY': [42.165726, -74.948051], 'NC': [35.630066, -79.806419],
  'ND': [47.528912, -99.784012], 'OH': [40.388783, -82.764915], 'OK': [35.565342, -96.928917],
  'OR': [44.572021, -122.070938], 'PA': [41.203322, -77.194525], 'RI': [41.680893, -71.511780],
  'SC': [33.856892, -80.945007], 'SD': [44.299782, -99.438828], 'TN': [35.747845, -86.692345],
  'TX': [31.054487, -97.563461], 'UT': [40.150032, -111.862434], 'VT': [44.045876, -72.710686],
  'VA': [37.769337, -78.169968], 'WA': [47.400902, -121.490494], 'WV': [38.491226, -80.954453],
  'WI': [44.268543, -89.616508], 'WY': [42.755966, -107.302490], 'DC': [38.9072, -77.0369]
};

export default function EntitySearchPage() {
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

  // Prepare Map Data
  const mapMarkers = useMemo(() => {
    return awards
      .filter(a => a["Place of Performance State Code"] && STATE_COORDINATES[a["Place of Performance State Code"]])
      .map(a => ({
        ...a,
        position: STATE_COORDINATES[a["Place of Performance State Code"]!]
      }));
  }, [awards]);

  return (
    <div className="h-full p-6">
      <h1 className="text-3xl font-bold mb-6">Entity Search & Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-200px)]">
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
                  <h3 className="font-bold text-sm mb-1">{entity.legal_business_name}</h3>
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
                    <h2 className="text-2xl font-bold">{selectedEntity.legal_business_name}</h2>
                    <p className="text-muted-foreground font-mono">UEI: {selectedEntity.uei}</p>
                  </div>
                  <button 
                    onClick={() => setSelectedEntity(null)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    Close
                  </button>
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

                      {/* Map */}
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
