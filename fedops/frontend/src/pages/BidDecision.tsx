import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  Users,
  Award,
  DollarSign,
  Target,
  Building2,
  Calendar,
  Briefcase
} from 'lucide-react';

interface BidScore {
  opportunity_id: number;
  weighted_score: number;
  recommendation: 'BID' | 'NO_BID' | 'REVIEW';
  position_to_win: {
    win_probability: number;
    competitive_landscape: number;
    incumbent_advantage: number;
    composite: number;
  };
  capability_capacity: {
    technical_capability: number;
    past_performance: number;
    resource_availability: number;
    compliance: number;
    composite: number;
  };
  attractiveness: {
    contract_value: number;
    strategic_alignment: number;
    agency_relationship: number;
    composite: number;
  };
  weights: {
    position: number;
    capability: number;
    attractiveness: number;
  };
}

interface Competitor {
  id: number;
  competitor_name: string;
  competitor_uei: string;
  historical_wins: number;
  total_obligation: number;
  is_incumbent: boolean;
  naics_match: string;
}

interface EntityData {
  uei: string;
  legal_business_name: string;
  dba_name: string;
  naics_codes: Array<{
    code: string;
    description: string;
    is_primary: boolean;
  }>;
  psc_codes: Array<{
    code: string;
    description: string;
  }>;
  business_types: Array<{
    code: string;
    description: string;
  }>;
  company_division: string;
  division_number: string;
  registration_status: string;
  registration_date: string;
  expiration_date: string;
}


interface Opportunity {
  id: number;
  title: string;
  notice_id: string;
  department: string;
}

export default function BidDecisionPage() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const navigate = useNavigate();
  
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [bidScore, setBidScore] = useState<BidScore | null>(null);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [showAllCompetitors, setShowAllCompetitors] = useState(false);
  const [expandedCompetitor, setExpandedCompetitor] = useState<string | null>(null);
  const [entityData, setEntityData] = useState<Record<string, EntityData>>({});
  const [loadingEntity, setLoadingEntity] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [decision, setDecision] = useState<'BID' | 'NO_BID' | null>(null);
  const [justification, setJustification] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [decisionBy] = useState('Current User'); // TODO: Get from auth context

  useEffect(() => {
    loadOpportunity();
    loadBidScore();
    refreshCompetitiveIntel();
  }, [opportunityId]);

  const loadOpportunity = async () => {
    try {
      const response = await fetch(`/api/v1/opportunities/${opportunityId}`);
      if (!response.ok) throw new Error('Failed to load opportunity');
      const data = await response.json();
      setOpportunity(data);
    } catch (err) {
      console.error('Failed to load opportunity:', err);
    }
  };

  const loadBidScore = async () => {
    try {
      const response = await fetch(`/api/v1/gates/opportunities/${opportunityId}/bid_score`);
      if (!response.ok) throw new Error('Failed to load bid score');
      const data = await response.json();
      setBidScore(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bid score');
    } finally {
      setLoading(false);
    }
  };

  const refreshCompetitiveIntel = async () => {
    try {
      // Refresh competitive intelligence from USAspending
      await fetch(`/api/v1/competitive_intel/opportunities/${opportunityId}/refresh`, {
        method: 'POST'
      });
      
      // Then load the competitors
      await loadCompetitors();
    } catch (err) {
      console.error('Failed to refresh competitive intelligence:', err);
      // Still try to load existing competitors
      await loadCompetitors();
    }
  };

  const toggleCompetitor = async (competitor: Competitor) => {
    if (expandedCompetitor === competitor.competitor_uei) {
      setExpandedCompetitor(null);
      return;
    }

    setExpandedCompetitor(competitor.competitor_uei);

    // Fetch entity data if not already loaded
    if (!entityData[competitor.competitor_uei]) {
      setLoadingEntity(competitor.competitor_uei);
      try {
        const response = await fetch(`/api/v1/competitive_intel/competitors/${competitor.competitor_uei}/entity_details`);
        if (response.ok) {
          const data = await response.json();
          setEntityData(prev => ({
            ...prev,
            [competitor.competitor_uei]: data
          }));
        }
      } catch (err) {
        console.error('Failed to load entity data:', err);
      } finally {
        setLoadingEntity(null);
      }
    }
  };

  const loadCompetitors = async () => {
    try {
      const response = await fetch(`/api/v1/competitive_intel/opportunities/${opportunityId}/competitors`);
      if (response.ok) {
        const data = await response.json();
        setCompetitors(data);
      }
    } catch (err) {
      console.error('Failed to load competitors:', err);
    }
  };

  const handleDecision = async () => {
    if (!decision) return;
    
    // Check if override justification is required
    const requiresJustification = bidScore?.recommendation === 'NO_BID' && decision === 'BID';
    if (requiresJustification && !justification.trim()) {
      setError('Justification required when overriding NO_BID recommendation');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/gates/opportunities/${opportunityId}/bid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          decision_by: decisionBy,
          override_justification: requiresJustification ? justification : null
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit decision');
      }

      await response.json();
      
      // Navigate to proposal workspace if BID, or back to pipeline if NO_BID
      if (decision === 'BID') {
        navigate(`/proposal-workspace/${opportunityId}`);
      } else {
        navigate('/pipeline');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit decision');
    } finally {
      setSubmitting(false);
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'BID': return 'bg-green-500';
      case 'NO_BID': return 'bg-red-500';
      case 'REVIEW': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation) {
      case 'BID': return <CheckCircle2 className="h-6 w-6" />;
      case 'NO_BID': return <XCircle className="h-6 w-6" />;
      case 'REVIEW': return <AlertTriangle className="h-6 w-6" />;
      default: return null;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Calculating Bid/No-Bid Score...</p>
        </div>
      </div>
    );
  }

  if (!bidScore) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>Failed to load bid score data</AlertDescription>
        </Alert>
      </div>
    );
  }

  const requiresOverrideJustification = bidScore.recommendation === 'NO_BID' && decision === 'BID';

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Bid/No-Bid Decision</h1>
        <p className="text-lg font-semibold text-gray-900 mb-1">
          {opportunity?.title || `Opportunity #${opportunityId}`}
        </p>
        <p className="text-sm text-muted-foreground">
          {opportunity?.notice_id} • Phase 2: Opportunity Assessment
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Scorecard */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Weighted Bid Score</CardTitle>
              <CardDescription>Automated recommendation based on multi-factor analysis</CardDescription>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${getRecommendationColor(bidScore.recommendation)} text-white`}>
              {getRecommendationIcon(bidScore.recommendation)}
              <span className="font-bold text-lg">{bidScore.recommendation}</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Overall Score</span>
              <span className={`text-3xl font-bold ${getScoreColor(bidScore.weighted_score)}`}>
                {bidScore.weighted_score.toFixed(1)}
              </span>
            </div>
            <Progress value={bidScore.weighted_score} className="h-3" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Position to Win */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-lg">Position to Win</CardTitle>
                </div>
                <CardDescription>Weight: {(bidScore.weights.position * 100).toFixed(0)}%</CardDescription>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold mb-3 ${getScoreColor(bidScore.position_to_win.composite)}`}>
                  {bidScore.position_to_win.composite.toFixed(1)}
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Win Probability</span>
                    <span className="font-medium">{bidScore.position_to_win.win_probability.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Competitive Landscape</span>
                    <span className="font-medium">{bidScore.position_to_win.competitive_landscape.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Incumbent Advantage</span>
                    <span className="font-medium">{bidScore.position_to_win.incumbent_advantage.toFixed(0)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Capability/Capacity */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-purple-600" />
                  <CardTitle className="text-lg">Capability/Capacity</CardTitle>
                </div>
                <CardDescription>Weight: {(bidScore.weights.capability * 100).toFixed(0)}%</CardDescription>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold mb-3 ${getScoreColor(bidScore.capability_capacity.composite)}`}>
                  {bidScore.capability_capacity.composite.toFixed(1)}
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Technical Capability</span>
                    <span className="font-medium">{bidScore.capability_capacity.technical_capability.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Past Performance</span>
                    <span className="font-medium">{bidScore.capability_capacity.past_performance.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Resource Availability</span>
                    <span className="font-medium">{bidScore.capability_capacity.resource_availability.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Compliance</span>
                    <span className="font-medium">{bidScore.capability_capacity.compliance.toFixed(0)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Attractiveness */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-green-600" />
                  <CardTitle className="text-lg">Attractiveness</CardTitle>
                </div>
                <CardDescription>Weight: {(bidScore.weights.attractiveness * 100).toFixed(0)}%</CardDescription>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold mb-3 ${getScoreColor(bidScore.attractiveness.composite)}`}>
                  {bidScore.attractiveness.composite.toFixed(1)}
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Contract Value</span>
                    <span className="font-medium">{bidScore.attractiveness.contract_value.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Strategic Alignment</span>
                    <span className="font-medium">{bidScore.attractiveness.strategic_alignment.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Agency Relationship</span>
                    <span className="font-medium">{bidScore.attractiveness.agency_relationship.toFixed(0)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* Competitive Intelligence */}
      {competitors.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                <CardTitle>Competitive Intelligence</CardTitle>
              </div>
              <Badge variant="outline">{competitors.length} Competitors</Badge>
            </div>
            <CardDescription>Historical competitor data from USAspending.gov</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(showAllCompetitors ? competitors : competitors.slice(0, 5)).map((competitor) => (
                <div key={competitor.id} className="border rounded-lg overflow-hidden">
                  <div 
                    className="flex items-center justify-between p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => toggleCompetitor(competitor)}
                  >
                    <div className="flex items-center gap-3">
                      <div>
                        <div className="font-medium flex items-center gap-2">
                          {competitor.competitor_name}
                          {competitor.is_incumbent && (
                            <Badge variant="destructive">Incumbent</Badge>
                          )}
                        </div>
                        <div className="text-sm text-gray-600">
                          NAICS: {competitor.naics_match}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{competitor.historical_wins} wins</div>
                      <div className="text-sm text-gray-600">
                        ${(competitor.total_obligation / 1_000_000).toFixed(1)}M total
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expandedCompetitor === competitor.competitor_uei && (
                    <div className="bg-slate-50/80 p-6 border-t animate-in slide-in-from-top-2 duration-200">
                      {loadingEntity === competitor.competitor_uei ? (
                        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
                          <p className="text-sm">Fetching entity details from SAM.gov...</p>
                        </div>
                      ) : entityData[competitor.competitor_uei] ? (
                        <div className="space-y-6">
                          {/* Header Info */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                              <div className="flex items-start gap-3">
                                <Building2 className="h-5 w-5 text-blue-600 mt-0.5" />
                                <div>
                                  <h4 className="font-semibold text-gray-900">Entity Information</h4>
                                  <div className="mt-2 space-y-2 text-sm">
                                    <div className="flex justify-between gap-4">
                                      <span className="text-muted-foreground">Legal Business Name:</span>
                                      <span className="font-medium text-right">{entityData[competitor.competitor_uei].legal_business_name}</span>
                                    </div>
                                    <div className="flex justify-between gap-4">
                                      <span className="text-muted-foreground">UEI:</span>
                                      <span className="font-mono bg-slate-100 px-2 py-0.5 rounded text-xs">{entityData[competitor.competitor_uei].uei}</span>
                                    </div>
                                    {entityData[competitor.competitor_uei].dba_name && (
                                      <div className="flex justify-between gap-4">
                                        <span className="text-muted-foreground">DBA Name:</span>
                                        <span className="font-medium text-right">{entityData[competitor.competitor_uei].dba_name}</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>

                            <div className="space-y-4">
                              <div className="flex items-start gap-3">
                                <Calendar className="h-5 w-5 text-green-600 mt-0.5" />
                                <div>
                                  <h4 className="font-semibold text-gray-900">Registration Status</h4>
                                  <div className="mt-2 space-y-2 text-sm">
                                    <div className="flex justify-between gap-4">
                                      <span className="text-muted-foreground">Status:</span>
                                      <Badge variant={entityData[competitor.competitor_uei].registration_status === 'Active' ? 'default' : 'secondary'} 
                                             className={entityData[competitor.competitor_uei].registration_status === 'Active' ? 'bg-green-600 hover:bg-green-700' : ''}>
                                        {entityData[competitor.competitor_uei].registration_status}
                                      </Badge>
                                    </div>
                                    <div className="flex justify-between gap-4">
                                      <span className="text-muted-foreground">Expiration Date:</span>
                                      <span className="font-medium">{entityData[competitor.competitor_uei].expiration_date}</span>
                                    </div>
                                    <div className="flex justify-between gap-4">
                                      <span className="text-muted-foreground">Registration Date:</span>
                                      <span className="font-medium">{entityData[competitor.competitor_uei].registration_date}</span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Business Types & Certifications */}
                          {entityData[competitor.competitor_uei].business_types.length > 0 && (
                            <div className="pt-4 border-t">
                              <div className="flex items-center gap-2 mb-3">
                                <Award className="h-5 w-5 text-purple-600" />
                                <h4 className="font-semibold text-gray-900">Business Types & Certifications</h4>
                              </div>
                              <div className="flex flex-wrap gap-2">
                                {entityData[competitor.competitor_uei].business_types.map((type, idx) => (
                                  <Badge key={idx} variant="outline" className="bg-white hover:bg-slate-50 transition-colors py-1 px-2.5 border-slate-200 shadow-sm">
                                    <span className="font-medium text-slate-700">{type.description}</span>
                                    {type.code !== type.description && (
                                      <span className="ml-1.5 text-xs text-slate-400 border-l pl-1.5">{type.code}</span>
                                    )}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* NAICS & PSC Codes */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t">
                            {/* NAICS Codes */}
                            {entityData[competitor.competitor_uei].naics_codes.length > 0 && (
                              <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                  <Briefcase className="h-5 w-5 text-orange-600" />
                                  <h4 className="font-semibold text-gray-900">NAICS Codes</h4>
                                </div>
                                <div className="bg-white rounded-lg border shadow-sm max-h-48 overflow-y-auto">
                                  <table className="w-full text-sm text-left">
                                    <thead className="bg-slate-50 text-slate-500 font-medium sticky top-0">
                                      <tr>
                                        <th className="px-3 py-2 w-16">Code</th>
                                        <th className="px-3 py-2">Description</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                      {entityData[competitor.competitor_uei].naics_codes.map((naics, idx) => (
                                        <tr key={idx} className="hover:bg-slate-50/50">
                                          <td className="px-3 py-2 font-mono text-slate-600 text-xs">{naics.code}</td>
                                          <td className="px-3 py-2 text-slate-700 text-xs">
                                            {naics.description}
                                            {naics.is_primary && (
                                              <Badge variant="secondary" className="ml-2 text-[10px] h-4 bg-blue-50 text-blue-700 border-blue-200">
                                                Primary
                                              </Badge>
                                            )}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}

                            {/* PSC Codes */}
                            {entityData[competitor.competitor_uei].psc_codes && entityData[competitor.competitor_uei].psc_codes.length > 0 && (
                              <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                  <Target className="h-5 w-5 text-teal-600" />
                                  <h4 className="font-semibold text-gray-900">PSC Codes</h4>
                                </div>
                                <div className="bg-white rounded-lg border shadow-sm max-h-48 overflow-y-auto">
                                  <table className="w-full text-sm text-left">
                                    <thead className="bg-slate-50 text-slate-500 font-medium sticky top-0">
                                      <tr>
                                        <th className="px-3 py-2 w-16">Code</th>
                                        <th className="px-3 py-2">Description</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                      {entityData[competitor.competitor_uei].psc_codes.map((psc, idx) => (
                                        <tr key={idx} className="hover:bg-slate-50/50">
                                          <td className="px-3 py-2 font-mono text-slate-600 text-xs">{psc.code}</td>
                                          <td className="px-3 py-2 text-slate-700 text-xs">{psc.description}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <AlertTriangle className="h-10 w-10 text-yellow-500 mx-auto mb-3" />
                          <p className="text-gray-900 font-medium">No detailed entity data available</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            Could not retrieve detailed profile from SAM.gov for this entity.
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {competitors.length > 5 && (
              <Button
                variant="ghost"
                className="w-full mt-4 text-muted-foreground"
                onClick={() => setShowAllCompetitors(!showAllCompetitors)}
              >
                {showAllCompetitors ? 'Show Less' : `Show All (${competitors.length})`}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Decision Interface */}
      <Card>
        <CardHeader>
          <CardTitle>Make Decision</CardTitle>
          <CardDescription>
            {requiresOverrideJustification && (
              <Alert variant="destructive" className="mt-2">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Override Required:</strong> The automated recommendation is NO_BID. 
                  If you choose to BID, you must provide justification for audit purposes.
                </AlertDescription>
              </Alert>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-4">
              <Button
                variant={decision === 'BID' ? 'default' : 'outline'}
                className={decision === 'BID' ? 'bg-green-600 hover:bg-green-700' : ''}
                onClick={() => setDecision('BID')}
                size="lg"
              >
                <CheckCircle2 className="mr-2 h-5 w-5" />
                Approve Bid
              </Button>
              <Button
                variant={decision === 'NO_BID' ? 'default' : 'outline'}
                className={decision === 'NO_BID' ? 'bg-red-600 hover:bg-red-700' : ''}
                onClick={() => setDecision('NO_BID')}
                size="lg"
              >
                <XCircle className="mr-2 h-5 w-5" />
                Decline Bid
              </Button>
            </div>

            {decision && (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    {requiresOverrideJustification ? 'Override Justification (Required)' : 'Justification (Optional)'}
                  </label>
                  <Textarea
                    value={justification}
                    onChange={(e) => setJustification(e.target.value)}
                    placeholder={requiresOverrideJustification 
                      ? "Explain why you are overriding the NO_BID recommendation..."
                      : "Provide rationale for your decision..."}
                    rows={4}
                    className={requiresOverrideJustification && !justification.trim() ? 'border-red-500' : ''}
                  />
                </div>

                <Button
                  onClick={handleDecision}
                  disabled={submitting || (requiresOverrideJustification && !justification.trim())}
                  size="lg"
                  className="w-full"
                >
                  {submitting ? 'Submitting...' : `Submit ${decision} Decision`}
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
