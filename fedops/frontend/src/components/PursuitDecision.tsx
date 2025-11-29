import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

interface PursuitDecisionProps {
  opportunityId: number;
  opportunityTitle: string;
  onDecisionMade?: (decision: 'GO' | 'NO_GO', proposalId?: number) => void;
}

export default function PursuitDecision({ 
  opportunityId, 
  opportunityTitle,
  onDecisionMade 
}: PursuitDecisionProps) {
  const [decision, setDecision] = useState<'GO' | 'NO_GO' | null>(null);
  const [justification, setJustification] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [decisionBy] = useState('Current User'); // TODO: Get from auth context

  const handleSubmit = async () => {
    if (!decision) return;
    
    if (!justification.trim()) {
      setError('Justification is required for pursuit decisions');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/gates/opportunities/${opportunityId}/pursuit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          decision_by: decisionBy,
          justification
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit pursuit decision');
      }

      const result = await response.json();
      
      // Notify parent component
      if (onDecisionMade) {
        onDecisionMade(decision, result.proposal_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit pursuit decision');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pursuit Decision Gate</CardTitle>
        <CardDescription>
          Phase 1 → Phase 2: Decide whether to pursue this opportunity
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div>
          <h4 className="font-semibold mb-2">Opportunity</h4>
          <p className="text-sm text-gray-600">{opportunityTitle}</p>
        </div>

        <div className="border-t pt-4">
          <h4 className="font-semibold mb-3">Decision Criteria</h4>
          <div className="space-y-2 text-sm">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Strategic alignment with company capabilities</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Sufficient time to prepare competitive proposal</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Resources available for capture activities</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5" />
              <span>Preliminary assessment shows reasonable win probability</span>
            </div>
          </div>
        </div>

        <div className="border-t pt-4">
          <h4 className="font-semibold mb-3">Make Decision</h4>
          
          <div className="flex gap-4 mb-4">
            <Button
              variant={decision === 'GO' ? 'default' : 'outline'}
              className={decision === 'GO' ? 'bg-green-600 hover:bg-green-700' : ''}
              onClick={() => setDecision('GO')}
              size="lg"
            >
              <CheckCircle2 className="mr-2 h-5 w-5" />
              Pursue (GO)
            </Button>
            <Button
              variant={decision === 'NO_GO' ? 'default' : 'outline'}
              className={decision === 'NO_GO' ? 'bg-red-600 hover:bg-red-700' : ''}
              onClick={() => setDecision('NO_GO')}
              size="lg"
            >
              <XCircle className="mr-2 h-5 w-5" />
              Do Not Pursue (NO GO)
            </Button>
          </div>

          {decision && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Justification (Required)
                </label>
                <Textarea
                  value={justification}
                  onChange={(e) => setJustification(e.target.value)}
                  placeholder={
                    decision === 'GO' 
                      ? "Explain why this opportunity is worth pursuing (e.g., strategic fit, capability match, relationship with agency)..."
                      : "Explain why this opportunity should not be pursued (e.g., insufficient resources, poor strategic fit, low win probability)..."
                  }
                  rows={4}
                  className={!justification.trim() ? 'border-yellow-500' : ''}
                />
              </div>

              {decision === 'GO' && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Next Steps:</strong> Proceeding to Phase 2 (Opportunity Assessment) will create a proposal record and enable detailed Bid/No-Bid analysis.
                  </AlertDescription>
                </Alert>
              )}

              {decision === 'NO_GO' && (
                <Alert variant="destructive">
                  <AlertDescription>
                    <strong>Note:</strong> This opportunity will remain in the pipeline but will not progress to Phase 2. You can revisit this decision later if circumstances change.
                  </AlertDescription>
                </Alert>
              )}

              <Button
                onClick={handleSubmit}
                disabled={submitting || !justification.trim()}
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
  );
}
