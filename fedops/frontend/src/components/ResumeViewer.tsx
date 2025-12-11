import { useState } from 'react';
import { type Resume, ResumeService } from '../services/ResumeService';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Loader2, FileText, Download } from 'lucide-react';

interface ResumeViewerProps {
    resume: Resume;
    onUpdate: (updatedResume: Resume) => void;
}

export function ResumeViewer({ resume, onUpdate }: ResumeViewerProps) {
    const [loading, setLoading] = useState(false);
    const [includeSignature, setIncludeSignature] = useState(false);

    const handleFormat = async () => {
        setLoading(true);
        try {
            const updated = await ResumeService.formatResume(resume.id, includeSignature);
            onUpdate(updated);
        } catch (error) {
            console.error(error);
            alert("Failed to format resume");
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = () => {
        // Open the download link in new tab or trigger download
        if (resume.formatted_content_html) {
             const blob = new Blob([resume.formatted_content_html], { type: 'text/html' });
             const url = URL.createObjectURL(blob);
             const a = document.createElement('a');
             a.href = url;
             a.download = `resume_${resume.id}.html`;
             a.click();
             URL.revokeObjectURL(url);
        }
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[calc(100vh-200px)]">
            {/* Parsed Data View */}
            <Card className="overflow-auto h-full">
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <FileText className="h-5 w-5" />
                        Parsed Data
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <pre className="text-xs bg-muted p-4 rounded-md overflow-x-auto whitespace-pre-wrap">
                        {resume.parsed_data ? JSON.stringify(resume.parsed_data, null, 2) : "No structured data available."}
                    </pre>
                </CardContent>
            </Card>

            {/* Formatted Preview */}
            <Card className="flex flex-col h-full">
                <CardHeader className="border-b">
                    <div className="flex justify-between items-center">
                         <CardTitle className="text-lg">Formatted Preview</CardTitle>
                         <div className="flex items-center gap-4">
                             <div className="flex items-center space-x-2">
                                <Switch id="sig-mode" checked={includeSignature} onCheckedChange={setIncludeSignature} />
                                <Label htmlFor="sig-mode">Include Signature</Label>
                            </div>
                            <Button size="sm" onClick={handleFormat} disabled={loading}>
                                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : null}
                                Generate Format
                            </Button>
                            {resume.formatted_content_html && (
                                <Button size="sm" variant="outline" onClick={handleDownload}>
                                    <Download className="h-4 w-4 mr-1" />
                                    Download HTML
                                </Button>
                            )}
                         </div>
                    </div>
                </CardHeader>
                <CardContent className="flex-1 p-0 bg-gray-100 overflow-hidden relative">
                    {resume.formatted_content_html ? (
                         <iframe 
                            srcDoc={resume.formatted_content_html} 
                            className="w-full h-full border-none bg-white"
                            title="Resume Preview"
                        />
                    ) : (
                        <div className="flex items-center justify-center h-full text-muted-foreground">
                            Click "Generate Format" to preview
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
