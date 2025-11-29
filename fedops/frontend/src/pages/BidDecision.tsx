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
  Target
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
  historical_wins: number;
  total_obligation: number;
  is_incumbent: boolean;
  naics_match: string;
}

export default function BidDecisionPage() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const navigate = useNavigate();
  
  const [bidScore, setBidScore] = useState<BidScore | null>(null);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [decision, setDecision] = useState<'BID' | 'NO_BID' | null>(null);
  const [justification, setJustification] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [decisionBy] = useState('Current User'); // TODO: Get from auth context

  useEffect(() => {
    loadBidScore();
    refreshCompetitiveIntel();
  }, [opportunityId]);

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
        <p className="text-gray-600">Opportunity #{opportunityId} - Phase 2: Opportunity Assessment</p>
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
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              <CardTitle>Competitive Intelligence</CardTitle>
            </div>
            <CardDescription>Historical competitor data from USAspending.gov</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {competitors.slice(0, 5).map((competitor) => (
                <div key={competitor.id} className="flex items-center justify-between p-3 border rounded-lg">
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
              ))}
            </div>
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
