import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2, ArrowLeft, ArrowRight, Sparkles, TrendingUp, Shield, DollarSign, Zap } from "lucide-react"
import { cn } from "@/lib/utils"

interface UploadedFile {
  file: File
  preview: string
}

interface AnalysisResult {
  extracted_metadata: any
  analysis: {
    compliance_status: string
    scores: {
      strategic_alignment: number
      financial_viability: number
      contract_risk: number
      internal_capacity: number
      weighted_score: number
    }
    qualification: {
      decision: string
      details: any
    }
  }
  temp_opportunity_id: number
}

export default function ManualUploadPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  
  // Form data (populated from analysis)
  const [formData, setFormData] = useState({
    title: '',
    source: 'Manual',
    solicitation_number: '',
    department: '',
    sub_tier: '',
    office: '',
    type: 'Solicitation',
    naics_code: '',
    type_of_set_aside: '',
    description: '',
    response_deadline: '',
    posted_date: new Date().toISOString().split('T')[0],
    incumbent_vendor: '',
    incumbent_contract_number: '',
    incumbent_value: '',
    incumbent_expiration_date: ''
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    const newFiles = files.map(file => ({
      file,
      preview: file.name
    }))
    setUploadedFiles(prev => [...prev, ...newFiles])
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    
    const files = Array.from(e.dataTransfer.files)
    const newFiles = files.map(file => ({
      file,
      preview: file.name
    }))
    setUploadedFiles(prev => [...prev, ...newFiles])
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleAnalyze = async () => {
    if (uploadedFiles.length === 0) {
      setError('Please upload at least one file')
      return
    }

    setAnalyzing(true)
    setError(null)
    setAnalysisProgress(0)

    try {
      const formDataToSend = new FormData()
      
      uploadedFiles.forEach(({ file }) => {
        formDataToSend.append('files', file)
      })

      // Simulate progress
      const progressInterval = setInterval(() => {
        setAnalysisProgress(prev => Math.min(prev + 10, 90))
      }, 1000)

      const response = await fetch('/api/v1/opportunities/analyze-upload', {
        method: 'POST',
        body: formDataToSend
      })

      clearInterval(progressInterval)
      setAnalysisProgress(100)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to analyze opportunity')
      }

      const result = await response.json()
      setAnalysisResult(result)
      
      // Pre-populate form with extracted data
      const extracted = result.extracted_metadata
      const updates: any = {}
      
      Object.entries(extracted).forEach(([key, data]: [string, any]) => {
        if (data.value && data.confidence > 0.5) {
          updates[key] = data.value
        }
      })
      
      setFormData(prev => ({ ...prev, ...updates }))
      
      // Move to step 2 (analysis results)
      setStep(2)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis')
    } finally {
      setAnalyzing(false)
      setAnalysisProgress(0)
    }
  }

  const handleSubmit = async () => {
    if (!formData.title) {
      setError('Opportunity title is required')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const formDataToSend = new FormData()
      
      // Append all form fields
      Object.entries(formData).forEach(([key, value]) => {
        if (value) {
          formDataToSend.append(key, value)
        }
      })

      // Append files
      uploadedFiles.forEach(({ file }) => {
        formDataToSend.append('files', file)
      })

      const response = await fetch('/api/v1/opportunities/upload', {
        method: 'POST',
        body: formDataToSend
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to upload opportunity')
      }

      const result = await response.json()
      setSuccess(true)
      
      setTimeout(() => {
        navigate(`/opportunities/${result.opportunity_id}`)
      }, 2000)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setUploading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-orange-600'
  }

  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case 'GO':
        return <Badge className="bg-green-600">GO</Badge>
      case 'NO-GO':
        return <Badge variant="destructive">NO-GO</Badge>
      default:
        return <Badge variant="secondary">REVIEW</Badge>
    }
  }

  return (
    <div className="container max-w-6xl mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Upload Opportunity</h1>
          <p className="text-muted-foreground">Upload documents for AI analysis and opportunity creation</p>
        </div>
        <Button variant="outline" onClick={() => navigate('/opportunities')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Opportunities
        </Button>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center justify-center gap-4">
        {[1, 2, 3, 4].map((s) => (
          <div key={s} className="flex items-center">
            <div className={cn(
              "w-10 h-10 rounded-full flex items-center justify-center font-semibold",
              step >= s ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
            )}>
              {s}
            </div>
            {s < 4 && (
              <div className={cn(
                "w-16 h-1 mx-2",
                step > s ? "bg-primary" : "bg-muted"
              )} />
            )}
          </div>
        ))}
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Success Alert */}
      {success && (
        <Alert className="border-green-600 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-600">
            Opportunity created successfully! Redirecting...
          </AlertDescription>
        </Alert>
      )}

      {/* Step 1: Upload Documents */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Step 1: Upload Opportunity Documents</CardTitle>
            <CardDescription>
              Upload RFP, solicitation, or opportunity documents. AI will analyze them to extract information and score the opportunity.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div 
              className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary/50 transition-colors"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-sm text-muted-foreground mb-4">
                Drag and drop files here, or click to browse
              </p>
              <Input
                type="file"
                multiple
                onChange={handleFileChange}
                className="max-w-xs mx-auto"
                accept=".pdf,.docx,.doc,.txt,.zip,.xlsx,.xls"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Supports PDF, DOCX, TXT, XLSX, and ZIP files
              </p>
            </div>

            {uploadedFiles.length > 0 && (
              <div className="space-y-2">
                <Label>Uploaded Files ({uploadedFiles.length})</Label>
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-md">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      <span className="text-sm">{file.preview}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {analyzing && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Analyzing documents...</span>
                  <span>{analysisProgress}%</span>
                </div>
                <Progress value={analysisProgress} />
                <p className="text-xs text-muted-foreground text-center">
                  This may take 30-60 seconds. AI is extracting metadata and running comprehensive analysis.
                </p>
              </div>
            )}

            <Button
              onClick={handleAnalyze}
              disabled={uploadedFiles.length === 0 || analyzing}
              className="w-full gap-2"
              size="lg"
            >
              {analyzing ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5" />
                  Analyze Opportunity
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Analysis Results */}
      {step === 2 && analysisResult && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Extracted Metadata */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Extracted Information
                </CardTitle>
                <CardDescription>
                  AI-extracted metadata from your documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {(() => {
                  const extractedFields = Object.entries(analysisResult.extracted_metadata)
                  const fieldsWithValues = extractedFields.filter(([_, data]: [string, any]) => data.value)
                  
                  if (fieldsWithValues.length === 0) {
                    return (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          No metadata could be automatically extracted from the uploaded documents. 
                          You'll need to manually enter the opportunity details in the next step.
                        </AlertDescription>
                      </Alert>
                    )
                  }
                  
                  return extractedFields.map(([key, data]: [string, any]) => {
                    const confidenceColor = 
                      data.confidence >= 0.8 ? 'bg-green-500' :
                      data.confidence >= 0.6 ? 'bg-yellow-500' :
                      data.confidence >= 0.3 ? 'bg-orange-500' :
                      'bg-gray-400'
                    
                    const fieldLabel = key.split('_').map((word: string) => 
                      word.charAt(0).toUpperCase() + word.slice(1)
                    ).join(' ')
                    
                    return (
                      <div key={key} className="p-3 bg-background rounded-md border">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium">{fieldLabel}</span>
                          <Badge variant="outline" className="text-xs">
                            <div className={cn("w-2 h-2 rounded-full mr-1", confidenceColor)} />
                            {Math.round(data.confidence * 100)}%
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {data.value || <span className="italic text-gray-400">Not found</span>}
                        </p>
                      </div>
                    )
                  })
                })()}
              </CardContent>
            </Card>

            {/* AI Analysis */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Opportunity Analysis</CardTitle>
                  {getDecisionBadge(analysisResult.analysis.qualification.decision)}
                </div>
                <CardDescription>
                  Comprehensive AI evaluation and scoring
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Overall Score */}
                <div className="text-center p-4 bg-primary/5 rounded-lg border border-primary/20">
                  <div className="text-4xl font-bold text-primary mb-1">
                    {Math.round(analysisResult.analysis.scores.weighted_score)}
                  </div>
                  <div className="text-sm text-muted-foreground">Weighted Score</div>
                </div>

                {/* Score Breakdown */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-blue-600" />
                      <span className="text-sm">Strategic Alignment</span>
                    </div>
                    <span className={cn("text-sm font-semibold", getScoreColor(analysisResult.analysis.scores.strategic_alignment))}>
                      {Math.round(analysisResult.analysis.scores.strategic_alignment)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <span className="text-sm">Financial Viability</span>
                    </div>
                    <span className={cn("text-sm font-semibold", getScoreColor(analysisResult.analysis.scores.financial_viability))}>
                      {Math.round(analysisResult.analysis.scores.financial_viability)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-orange-600" />
                      <span className="text-sm">Contract Risk</span>
                    </div>
                    <span className={cn("text-sm font-semibold", getScoreColor(analysisResult.analysis.scores.contract_risk))}>
                      {Math.round(analysisResult.analysis.scores.contract_risk)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4 text-purple-600" />
                      <span className="text-sm">Internal Capacity</span>
                    </div>
                    <span className={cn("text-sm font-semibold", getScoreColor(analysisResult.analysis.scores.internal_capacity))}>
                      {Math.round(analysisResult.analysis.scores.internal_capacity)}
                    </span>
                  </div>
                </div>

                {/* Compliance Status */}
                <div className="pt-3 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Compliance Status</span>
                    <Badge variant={analysisResult.analysis.compliance_status === 'COMPLIANT' ? 'default' : 'destructive'}>
                      {analysisResult.analysis.compliance_status}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Navigation */}
          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(1)}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button onClick={() => setStep(3)}>
              Review & Edit Form
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Review & Edit Form */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Step 3: Review & Edit Information</CardTitle>
            <CardDescription>
              Review the AI-extracted data and make any necessary edits before submission
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="title">Opportunity Title *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Enter opportunity title"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="solicitation_number">Solicitation / RFP Number</Label>
                <Input
                  id="solicitation_number"
                  value={formData.solicitation_number}
                  onChange={e => setFormData(prev => ({ ...prev, solicitation_number: e.target.value }))}
                  placeholder="e.g., RFQ-2024-001"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="department">Department/Agency</Label>
                <Input
                  id="department"
                  value={formData.department}
                  onChange={e => setFormData(prev => ({ ...prev, department: e.target.value }))}
                  placeholder="e.g., Department of Defense"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="naics_code">NAICS Code</Label>
                <Input
                  id="naics_code"
                  value={formData.naics_code}
                  onChange={e => setFormData(prev => ({ ...prev, naics_code: e.target.value }))}
                  placeholder="e.g., 541511"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="type">Opportunity Type</Label>
                <Select value={formData.type} onValueChange={value => setFormData(prev => ({ ...prev, type: value }))}>
                  <SelectTrigger id="type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Solicitation">Solicitation</SelectItem>
                    <SelectItem value="Presolicitation">Presolicitation</SelectItem>
                    <SelectItem value="Sources Sought">Sources Sought</SelectItem>
                    <SelectItem value="RFI">RFI</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="response_deadline">Response Deadline</Label>
                <Input
                  id="response_deadline"
                  type="date"
                  value={formData.response_deadline}
                  onChange={e => setFormData(prev => ({ ...prev, response_deadline: e.target.value }))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Enter opportunity description..."
                rows={4}
              />
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(2)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Analysis
              </Button>
              <Button onClick={() => setStep(4)}>
                Continue to Review
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Final Review & Submit */}
      {step === 4 && (
        <Card>
          <CardHeader>
            <CardTitle>Step 4: Final Review & Submit</CardTitle>
            <CardDescription>
              Review all information before creating the opportunity
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-3">Opportunity Details</h3>
                <dl className="space-y-2 text-sm">
                  <div>
                    <dt className="text-muted-foreground">Title</dt>
                    <dd className="font-medium">{formData.title}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Solicitation Number</dt>
                    <dd className="font-medium">{formData.solicitation_number || 'N/A'}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Department</dt>
                    <dd className="font-medium">{formData.department || 'N/A'}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">NAICS Code</dt>
                    <dd className="font-medium">{formData.naics_code || 'N/A'}</dd>
                  </div>
                </dl>
              </div>

              {analysisResult && (
                <div>
                  <h3 className="font-semibold mb-3">AI Analysis Summary</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Qualification</span>
                      {getDecisionBadge(analysisResult.analysis.qualification.decision)}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Overall Score</span>
                      <span className="font-semibold">{Math.round(analysisResult.analysis.scores.weighted_score)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Compliance</span>
                      <Badge variant={analysisResult.analysis.compliance_status === 'COMPLIANT' ? 'default' : 'destructive'}>
                        {analysisResult.analysis.compliance_status}
                      </Badge>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Once submitted, this opportunity will be created with all uploaded files and analysis data.
                {analysisResult?.analysis.qualification.decision === 'GO' && ' It will be automatically added to your pipeline.'}
              </AlertDescription>
            </Alert>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(3)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Edit
              </Button>
              <Button onClick={handleSubmit} disabled={uploading} size="lg">
                {uploading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="mr-2 h-5 w-5" />
                    Create Opportunity
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
