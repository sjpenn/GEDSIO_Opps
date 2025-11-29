import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface SubmissionData {
  submission: any;
  award: any;
  lessons_learned: any[];
}

interface SubmissionTabProps {
  proposalId: number;
}

export default function SubmissionTab({ proposalId }: SubmissionTabProps) {
  const [data, setData] = useState<SubmissionData | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Submission state
  const [submissionForm, setSubmissionForm] = useState({
    date: new Date().toISOString().split('T')[0],
    method: 'PORTAL',
    tracking: '',
    submittedBy: 'Current User',
    notes: ''
  });
  
  // Award state
  const [awardForm, setAwardForm] = useState({
    status: 'PENDING',
    date: '',
    contractNumber: '',
    value: '',
    notes: ''
  });
  
  // Lesson state
  const [lessonForm, setLessonForm] = useState({
    category: 'PROCESS',
    observation: '',
    impact: 'NEUTRAL',
    recommendation: '',
    recordedBy: 'Current User'
  });

  useEffect(() => {
    loadData();
  }, [proposalId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/submission/proposals/${proposalId}`);
      if (res.ok) {
        const result = await res.json();
        setData(result);
        
        // Pre-fill forms if data exists
        if (result.submission) {
          setSubmissionForm({
            date: result.submission.submission_date?.split('T')[0] || '',
            method: result.submission.submission_method || 'PORTAL',
            tracking: result.submission.tracking_number || '',
            submittedBy: result.submission.submitted_by || 'Current User',
            notes: result.submission.submission_notes || ''
          });
        }
        
        if (result.award) {
          setAwardForm({
            status: result.award.status || 'PENDING',
            date: result.award.award_date?.split('T')[0] || '',
            contractNumber: result.award.contract_number || '',
            value: result.award.contract_value?.toString() || '',
            notes: result.award.award_notes || ''
          });
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const res = await fetch(`/api/v1/submission/proposals/${proposalId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          submission_date: new Date(submissionForm.date).toISOString(),
          method: submissionForm.method,
          tracking_number: submissionForm.tracking,
          submitted_by: submissionForm.submittedBy,
          notes: submissionForm.notes
        })
      });
      
      if (res.ok) {
        loadData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAward = async () => {
    try {
      const res = await fetch(`/api/v1/submission/proposals/${proposalId}/award`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: awardForm.status,
          award_date: awardForm.date ? new Date(awardForm.date).toISOString() : null,
          contract_number: awardForm.contractNumber,
          contract_value: awardForm.value ? parseFloat(awardForm.value) : null,
          notes: awardForm.notes
        })
      });
      
      if (res.ok) {
        loadData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLesson = async () => {
    try {
      const res = await fetch(`/api/v1/submission/proposals/${proposalId}/lessons`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: lessonForm.category,
          observation: lessonForm.observation,
          impact: lessonForm.impact,
          recommendation: lessonForm.recommendation,
          recorded_by: lessonForm.recordedBy
        })
      });
      
      if (res.ok) {
        setLessonForm({
          category: 'PROCESS',
          observation: '',
          impact: 'NEUTRAL',
          recommendation: '',
          recordedBy: 'Current User'
        });
        loadData();      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading submission data...</div>;
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Submission Section */}
      <Card>
        <CardHeader>
          <CardTitle>Proposal Submission</CardTitle>
          <CardDescription>Record when and how the proposal was submitted</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Submission Date</Label>
              <Input
                type="date"
                value={submissionForm.date}
                onChange={(e) => setSubmissionForm({...submissionForm, date: e.target.value})}
              />
            </div>
            <div>
              <Label>Method</Label>
              <Select
                value={submissionForm.method}
                onValueChange={(v) => setSubmissionForm({...submissionForm, method: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PORTAL">Online Portal</SelectItem>
                  <SelectItem value="EMAIL">Email</SelectItem>
                  <SelectItem value="PHYSICAL">Physical Delivery</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Tracking Number</Label>
              <Input
                value={submissionForm.tracking}
                onChange={(e) => setSubmissionForm({...submissionForm, tracking: e.target.value})}
                placeholder="Optional"
              />
            </div>
            <div>
              <Label>Submitted By</Label>
              <Input
                value={submissionForm.submittedBy}
                onChange={(e) => setSubmissionForm({...submissionForm, submittedBy: e.target.value})}
              />
            </div>
          </div>
          <div>
            <Label>Notes</Label>
            <Textarea
              value={submissionForm.notes}
              onChange={(e) => setSubmissionForm({...submissionForm, notes: e.target.value})}
              placeholder="Any additional submission details..."
              rows={3}
            />
          </div>
          <Button onClick={handleSubmit}>
            {data?.submission ? 'Update Submission' : 'Record Submission'}
          </Button>
        </CardContent>
      </Card>

      {/* Award Section */}
      <Card>
        <CardHeader>
          <CardTitle>Award Outcome</CardTitle>
          <CardDescription>Record the award decision and contract details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Award Status</Label>
              <Select
                value={awardForm.status}
                onValueChange={(v) => setAwardForm({...awardForm, status: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="WON">Won</SelectItem>
                  <SelectItem value="LOST">Lost</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Award Date</Label>
              <Input
                type="date"
                value={awardForm.date}
                onChange={(e) => setAwardForm({...awardForm, date: e.target.value})}
              />
            </div>
            <div>
              <Label>Contract Number</Label>
              <Input
                value={awardForm.contractNumber}
                onChange={(e) => setAwardForm({...awardForm, contractNumber: e.target.value})}
                placeholder="e.g., GS-12F-0123A"
              />
            </div>
            <div>
              <Label>Contract Value ($)</Label>
              <Input
                type="number"
                value={awardForm.value}
                onChange={(e) => setAwardForm({...awardForm, value: e.target.value})}
                placeholder="e.g., 1500000"
              />
            </div>
          </div>
          <div>
            <Label>Notes</Label>
            <Textarea
              value={awardForm.notes}
              onChange={(e) => setAwardForm({...awardForm, notes: e.target.value})}
              placeholder="Award details, debrief notes, etc..."
              rows={3}
            />
          </div>
          <Button onClick={handleAward}>
            {data?.award ? 'Update Award' : 'Record Award'}
          </Button>
          
          {data?.award && (
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <div className="font-semibold mb-2">Current Status:</div>
              <Badge variant={data.award.status === 'WON' ? 'default' : 'secondary'}>
                {data.award.status}
              </Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Lessons Learned Section */}
      <Card>
        <CardHeader>
          <CardTitle>Lessons Learned</CardTitle>
          <CardDescription>Capture insights from this proposal process</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Category</Label>
              <Select
                value={lessonForm.category}
                onValueChange={(v) => setLessonForm({...lessonForm, category: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PROCESS">Process</SelectItem>
                  <SelectItem value="TECHNICAL">Technical</SelectItem>
                  <SelectItem value="STRATEGY">Strategy</SelectItem>
                  <SelectItem value="PRICING">Pricing</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Impact</Label>
              <Select
                value={lessonForm.impact}
                onValueChange={(v) => setLessonForm({...lessonForm, impact: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="POSITIVE">Positive</SelectItem>
                  <SelectItem value="NEGATIVE">Negative</SelectItem>
                  <SelectItem value="NEUTRAL">Neutral</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label>Observation</Label>
            <Textarea
              value={lessonForm.observation}
              onChange={(e) => setLessonForm({...lessonForm, observation: e.target.value})}
              placeholder="What did you observe or learn?"
              rows={3}
            />
          </div>
          <div>
            <Label>Recommendation</Label>
            <Textarea
              value={lessonForm.recommendation}
              onChange={(e) => setLessonForm({...lessonForm, recommendation: e.target.value})}
              placeholder="What should we do differently next time?"
              rows={3}
            />
          </div>
          <Button onClick={handleLesson} disabled={!lessonForm.observation}>
            Add Lesson Learned
          </Button>

          {/* Display existing lessons */}
          {data?.lessons_learned && data.lessons_learned.length > 0 && (
            <div className="mt-6 space-y-3">
              <h4 className="font-semibold">Recorded Lessons ({data.lessons_learned.length})</h4>
              {data.lessons_learned.map((lesson: any) => (
                <Card key={lesson.id} className="border-l-4 border-l-primary">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex gap-2">
                        <Badge variant="outline">{lesson.category}</Badge>
                        <Badge variant={
                          lesson.impact === 'POSITIVE' ? 'default' :
                          lesson.impact === 'NEGATIVE' ? 'destructive' : 'secondary'
                        }>
                          {lesson.impact}
                        </Badge>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        by {lesson.recorded_by}
                      </span>
                    </div>
                    <p className="text-sm mb-2">{lesson.observation}</p>
                    {lesson.recommendation && (
                      <p className="text-sm text-muted-foreground italic">
                        Recommendation: {lesson.recommendation}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
