import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FileText, AlertCircle, Loader2, ArrowLeft, ArrowRight, Download } from "lucide-react"

interface SOWComparisonProps {
  opportunityId: number
}

interface SOWDocument {
  id: number
  filename: string
  parsed_content: string
  file_path: string
  created_at: string
}

export default function SOWComparison({ opportunityId }: SOWComparisonProps) {
  const [opportunity, setOpportunity] = useState<any>(null)
  const [previousSOW, setPreviousSOW] = useState<SOWDocument | null>(null)
  const [currentSOWs, setCurrentSOWs] = useState<SOWDocument[]>([])
  const [selectedCurrentSOW, setSelectedCurrentSOW] = useState<SOWDocument | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [opportunityId])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch opportunity details including incumbent info
      const oppResponse = await fetch(`/api/v1/opportunities/${opportunityId}`)
      if (oppResponse.ok) {
        const oppData = await oppResponse.json()
        setOpportunity(oppData)

        // Fetch previous SOW if ID exists
        if (oppData.previous_sow_document_id) {
          const sowResponse = await fetch(`/api/v1/files/${oppData.previous_sow_document_id}`)
          if (sowResponse.ok) {
            const sowData = await sowResponse.json()
            setPreviousSOW(sowData)
          }
        }
      }

      // Fetch current opportunity files
      const filesResponse = await fetch(`/api/v1/files/?opportunity_id=${opportunityId}`)
      if (filesResponse.ok) {
        const filesData = await filesResponse.json()
        // Filter for SOW-like documents (you may want to add tags or types)
        const sowFiles = filesData.filter((f: SOWDocument) => 
          f.filename.toLowerCase().includes('sow') || 
          f.filename.toLowerCase().includes('statement of work') ||
          f.filename.toLowerCase().includes('pwd') ||
          f.filename.toLowerCase().includes('pws')
        )
        setCurrentSOWs(sowFiles)
        if (sowFiles.length > 0 && !selectedCurrentSOW) {
          setSelectedCurrentSOW(sowFiles[0])
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load SOW comparison')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary mb-4" />
          <p className="text-muted-foreground">Loading SOW comparison...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!previousSOW && currentSOWs.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto opacity-20 mb-4" />
          <p>No SOW documents available for comparison</p>
          <p className="text-sm mt-2">Upload files to see them here</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Incumbent Information Banner */}
      {opportunity && (opportunity.incumbent_vendor || opportunity.incumbent_contract_number) && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-1">
              <p className="font-semibold">Incumbent Contract Information</p>
              {opportunity.incumbent_vendor && (
                <p className="text-sm">Vendor: {opportunity.incumbent_vendor}</p>
              )}
              {opportunity.incumbent_contract_number && (
                <p className="text-sm">Contract: {opportunity.incumbent_contract_number}</p>
              )}
              {opportunity.incumbent_value && (
                <p className="text-sm">Value: {opportunity.incumbent_value}</p>
              )}
              {opportunity.incumbent_expiration_date && (
                <p className="text-sm">
                  Expiration: {new Date(opportunity.incumbent_expiration_date).toLocaleDateString()}
                </p>
              )}
            </div>
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="side-by-side" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="side-by-side">Side by Side</TabsTrigger>
          <TabsTrigger value="previous">Previous SOW</TabsTrigger>
          <TabsTrigger value="current">Current SOW</TabsTrigger>
        </TabsList>

        <TabsContent value="side-by-side" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Previous SOW Column */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">Previous SOW</CardTitle>
                    {previousSOW && (
                      <p className="text-sm text-muted-foreground mt-1">{previousSOW.filename}</p>
                    )}
                  </div>
                  {previousSOW && (
                    <Button variant="ghost" size="icon" asChild>
                      <a href={`/static/${previousSOW.file_path}`} download>
                        <Download className="h-4 w-4" />
                      </a>
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="max-h-[600px] overflow-y-auto">
                {previousSOW ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-xs">
                      {previousSOW.parsed_content || 'Content not yet parsed'}
                    </pre>
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto opacity-20 mb-4" />
                    <p>No previous SOW uploaded</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Current SOW Column */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">Current Solicitation SOW</CardTitle>
                    {currentSOWs.length > 1 && (
                      <div className="flex gap-2 mt-2 flex-wrap">
                        {currentSOWs.map((sow, idx) => (
                          <Badge
                            key={sow.id}
                            variant={selectedCurrentSOW?.id === sow.id ? "default" : "outline"}
                            className="cursor-pointer"
                            onClick={() => setSelectedCurrentSOW(sow)}
                          >
                            SOW {idx + 1}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {selectedCurrentSOW && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {selectedCurrentSOW.filename}
                      </p>
                    )}
                  </div>
                  {selectedCurrentSOW && (
                    <Button variant="ghost" size="icon" asChild>
                      <a href={`/static/${selectedCurrentSOW.file_path}`} download>
                        <Download className="h-4 w-4" />
                      </a>
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="max-h-[600px] overflow-y-auto">
                {selectedCurrentSOW ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-xs">
                      {selectedCurrentSOW.parsed_content || 'Content not yet parsed'}
                    </pre>
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto opacity-20 mb-4" />
                    <p>No current SOW documents found</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="previous">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Previous SOW (Full View)</CardTitle>
                  {previousSOW && (
                    <p className="text-sm text-muted-foreground mt-1">{previousSOW.filename}</p>
                  )}
                </div>
                {previousSOW && (
                  <Button variant="outline" asChild>
                    <a href={`/static/${previousSOW.file_path}`} download>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </a>
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="max-h-[700px] overflow-y-auto">
              {previousSOW ? (
                <div className="prose dark:prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap text-sm">
                    {previousSOW.parsed_content || 'Content not yet parsed'}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto opacity-20 mb-4" />
                  <p>No previous SOW uploaded</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="current">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <CardTitle>Current Solicitation SOW (Full View)</CardTitle>
                  {currentSOWs.length > 1 && (
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {currentSOWs.map((sow, idx) => (
                        <Badge
                          key={sow.id}
                          variant={selectedCurrentSOW?.id === sow.id ? "default" : "outline"}
                          className="cursor-pointer"
                          onClick={() => setSelectedCurrentSOW(sow)}
                        >
                          SOW {idx + 1}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {selectedCurrentSOW && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedCurrentSOW.filename}
                    </p>
                  )}
                </div>
                {selectedCurrentSOW && (
                  <Button variant="outline" asChild>
                    <a href={`/static/${selectedCurrentSOW.file_path}`} download>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </a>
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="max-h-[700px] overflow-y-auto">
              {selectedCurrentSOW ? (
                <div className="prose dark:prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap text-sm">
                    {selectedCurrentSOW.parsed_content || 'Content not yet parsed'}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto opacity-20 mb-4" />
                  <p>No current SOW documents found</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Navigation Helper */}
      <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
        <ArrowLeft className="h-4 w-4" />
        <span>Use tabs to switch between views</span>
        <ArrowRight className="h-4 w-4" />
      </div>
    </div>
  )
}
