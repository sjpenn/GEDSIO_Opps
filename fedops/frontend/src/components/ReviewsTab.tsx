import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Clock, 
  User, 
  ShieldCheck,
  Play,
  Check
} from 'lucide-react';

interface ReviewGate {
  id: number;
  review_type: string; // PINK, RED, GOLD
  outcome: string; // PENDING, PASS, FAIL, CONDITIONAL
  decision_by: string;
  details: any;
  created_at: string;
}

interface ReviewComment {
  id: number;
  comment_text: string;
  comment_type: string;
  severity: string;
  status: string;
  reviewer_name: string;
  section_reference: string | null;
  created_at: string;
}

interface ReviewsTabProps {
  proposalId: number;
}

export default function ReviewsTab({ proposalId }: ReviewsTabProps) {
  const [activeReviewType, setActiveReviewType] = useState<string>('PINK');
  const [gate, setGate] = useState<ReviewGate | null>(null);
  const [comments, setComments] = useState<ReviewComment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // New comment state
  const [newComment, setNewComment] = useState({
    text: '',
    type: 'COMPLIANCE',
    severity: 'MEDIUM',
    section: ''
  });
  const [submittingComment, setSubmittingComment] = useState(false);

  useEffect(() => {
    loadReviewData();
  }, [proposalId, activeReviewType]);

  const loadReviewData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/reviews/proposals/${proposalId}/${activeReviewType}`);
      if (res.ok) {
        const data = await res.json();
        setGate(data.gate);
        setComments(data.comments || []);
      } else {
        // If 404 or other error, it might mean review hasn't started
        setGate(null);
        setComments([]);
      }
    } catch (err) {
      console.error(err);
      setError("Failed to load review data");
    } finally {
      setLoading(false);
    }
  };

  const startReview = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/reviews/proposals/${proposalId}/${activeReviewType}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'Current User' }) // TODO: Auth
      });
      if (res.ok) {
        loadReviewData();
      } else {
        throw new Error("Failed to start review");
      }
    } catch (err) {
      setError("Failed to start review");
      setLoading(false);
    }
  };

  const submitComment = async () => {
    if (!gate) return;
    setSubmittingComment(true);
    try {
      const res = await fetch(`/api/v1/reviews/gates/${gate.id}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: newComment.text,
          comment_type: newComment.type,
          severity: newComment.severity,
          reviewer_name: 'Current User', // TODO: Auth
          section_reference: newComment.section
        })
      });
      
      if (res.ok) {
        setNewComment({ text: '', type: 'COMPLIANCE', severity: 'MEDIUM', section: '' });
        loadReviewData(); // Refresh comments
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingComment(false);
    }
  };

  const resolveComment = async (commentId: number) => {
    try {
      await fetch(`/api/v1/reviews/comments/${commentId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'RESOLVED' })
      });
      loadReviewData();
    } catch (err) {
      console.error(err);
    }
  };

  const completeReview = async (outcome: string) => {
    if (!gate) return;
    try {
      await fetch(`/api/v1/reviews/gates/${gate.id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          outcome,
          decision_by: 'Current User'
        })
      });
      loadReviewData();
    } catch (err) {
      console.error(err);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-600 bg-red-100 border-red-200';
      case 'HIGH': return 'text-orange-600 bg-orange-100 border-orange-200';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100 border-yellow-200';
      case 'LOW': return 'text-blue-600 bg-blue-100 border-blue-200';
      default: return 'text-gray-600 bg-gray-100 border-gray-200';
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Review Type Selector */}
      <div className="flex gap-4">
        {['PINK', 'RED', 'GOLD'].map((type) => (
          <Button
            key={type}
            variant={activeReviewType === type ? 'default' : 'outline'}
            onClick={() => setActiveReviewType(type)}
            className="w-32"
          >
            {type} Team
          </Button>
        ))}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!gate ? (
        <Card>
          <CardContent className="p-12 text-center">
            <ShieldCheck className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">{activeReviewType} Team Review Not Started</h3>
            <p className="text-muted-foreground mb-6">Start this review cycle to begin adding comments and tracking status.</p>
            <Button onClick={startReview} disabled={loading}>
              <Play className="mr-2 h-4 w-4" /> Start Review
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Review Status Card */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>{activeReviewType} Team Review</CardTitle>
                  <CardDescription>Status: {gate.outcome}</CardDescription>
                </div>
                <div className="flex gap-2">
                  {gate.outcome === 'PENDING' && (
                    <>
                      <Button variant="outline" onClick={() => completeReview('FAIL')}>
                        Fail Review
                      </Button>
                      <Button onClick={() => completeReview('PASS')}>
                        Pass Review
                      </Button>
                    </>
                  )}
                  {gate.outcome !== 'PENDING' && (
                    <Badge variant={gate.outcome === 'PASS' ? 'default' : 'destructive'}>
                      {gate.outcome}
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Add Comment Section */}
            <div className="md:col-span-1 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Add Comment</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Type</Label>
                    <Select 
                      value={newComment.type} 
                      onValueChange={(v) => setNewComment({...newComment, type: v})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="COMPLIANCE">Compliance</SelectItem>
                        <SelectItem value="TECHNICAL">Technical</SelectItem>
                        <SelectItem value="STRATEGY">Strategy</SelectItem>
                        <SelectItem value="CLARITY">Clarity</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Severity</Label>
                    <Select 
                      value={newComment.severity} 
                      onValueChange={(v) => setNewComment({...newComment, severity: v})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="CRITICAL">Critical</SelectItem>
                        <SelectItem value="HIGH">High</SelectItem>
                        <SelectItem value="MEDIUM">Medium</SelectItem>
                        <SelectItem value="LOW">Low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Section Reference</Label>
                    <Input 
                      placeholder="e.g. 1.2.3" 
                      value={newComment.section}
                      onChange={(e) => setNewComment({...newComment, section: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Comment</Label>
                    <Textarea 
                      placeholder="Enter feedback..." 
                      value={newComment.text}
                      onChange={(e) => setNewComment({...newComment, text: e.target.value})}
                      rows={4}
                    />
                  </div>
                  <Button 
                    className="w-full" 
                    onClick={submitComment}
                    disabled={submittingComment || !newComment.text}
                  >
                    Add Comment
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Comments List */}
            <div className="md:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Review Comments ({comments.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {comments.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">No comments yet.</p>
                    ) : (
                      comments.map((comment) => (
                        <div key={comment.id} className="border rounded-lg p-4 space-y-2">
                          <div className="flex justify-between items-start">
                            <div className="flex gap-2 items-center">
                              <Badge variant="outline">{comment.comment_type}</Badge>
                              <span className={`text-xs px-2 py-0.5 rounded-full border ${getSeverityColor(comment.severity)}`}>
                                {comment.severity}
                              </span>
                              {comment.section_reference && (
                                <span className="text-xs text-muted-foreground">
                                  Ref: {comment.section_reference}
                                </span>
                              )}
                            </div>
                            {comment.status === 'OPEN' ? (
                              <Button 
                                size="sm" 
                                variant="ghost" 
                                onClick={() => resolveComment(comment.id)}
                              >
                                Mark Resolved
                              </Button>
                            ) : (
                              <Badge variant="secondary" className="bg-green-100 text-green-800">
                                <Check className="w-3 h-3 mr-1" /> Resolved
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm">{comment.comment_text}</p>
                          <div className="text-xs text-muted-foreground flex items-center gap-2">
                            <User className="h-3 w-3" /> {comment.reviewer_name}
                            <Clock className="h-3 w-3 ml-2" /> {new Date(comment.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
