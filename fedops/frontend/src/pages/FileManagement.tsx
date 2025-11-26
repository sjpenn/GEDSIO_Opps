import React, { useState, useEffect } from 'react';
import { Loader2, FileText, Upload, RefreshCw, Download, Copy, Mail, File, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

interface StoredFile {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  content_summary?: string;
  parsed_content?: string;
  created_at: string;
}

interface FileManagementPageProps {
  opportunityId?: number;
}

const FileManagementPage: React.FC<FileManagementPageProps> = ({ opportunityId }) => {
  const [files, setFiles] = useState<StoredFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<StoredFile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState<number | null>(null);

  useEffect(() => {
    fetchFiles();
  }, [opportunityId]);

  const fetchFiles = async () => {
    try {
      const url = opportunityId ? `/api/v1/files/?opportunity_id=${opportunityId}` : '/api/v1/files/';
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setFiles(data);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || event.target.files.length === 0) return;

    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    if (opportunityId) {
      formData.append('opportunity_id', opportunityId.toString());
    }

    setUploading(true);
    try {
      const response = await fetch('/api/v1/files/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        await fetchFiles();
      } else {
        console.error('Upload failed');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleProcessFile = async (fileId: number) => {
    setProcessing(fileId);
    try {
      const response = await fetch(`/api/v1/files/${fileId}/process`, {
        method: 'POST',
      });

      if (response.ok) {
        const updatedFile = await response.json();
        setFiles(files.map(f => f.id === fileId ? updatedFile : f));
        if (selectedFile?.id === fileId) {
          setSelectedFile(updatedFile);
        }
      } else {
        console.error('Processing failed');
      }
    } catch (error) {
      console.error('Error processing file:', error);
    } finally {
      setProcessing(null);
    }
  };

  const handleBatchProcess = async () => {
    try {
      const response = await fetch('/api/v1/files/batch-process', {
        method: 'POST',
      });
      if (response.ok) {
        alert('Batch processing started. Refresh to see updates.');
      }
    } catch (error) {
      console.error('Error starting batch process:', error);
    }
  };

  const handleImportResources = async () => {
    if (!opportunityId) return;
    
    setUploading(true);
    try {
      const response = await fetch(`/api/v1/files/import-resources/${opportunityId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        await fetchFiles();
      } else {
        console.error('Failed to import resources');
      }
    } catch (error) {
      console.error('Error importing resources:', error);
    } finally {
      setUploading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Could add toast here
  };

  return (
    <div className="h-full flex flex-col space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">File Management</h2>
          <p className="text-muted-foreground">Upload, manage, and analyze documents with AI.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {opportunityId && (
            <Button
              variant="secondary"
              onClick={handleImportResources}
              disabled={uploading}
              className="gap-2"
            >
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              Import Resources
            </Button>
          )}
          <Button
            variant="outline"
            onClick={handleBatchProcess}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" /> Batch Process
          </Button>
          <div className="relative">
            <Button disabled={uploading} className="gap-2 cursor-pointer relative overflow-hidden">
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              Upload File
              <input 
                type="file" 
                onChange={handleFileUpload} 
                className="absolute inset-0 opacity-0 cursor-pointer" 
                disabled={uploading}
              />
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 min-h-0">
        {/* File List */}
        <Card className="col-span-1 flex flex-col h-full max-h-[calc(100vh-200px)]">
          <CardHeader className="pb-3 border-b">
            <CardTitle className="text-lg flex items-center gap-2">
              <File className="h-5 w-5" /> Files
              <Badge variant="secondary" className="ml-auto">{files.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="divide-y">
                {files.map(file => (
                  <div 
                    key={file.id} 
                    className={cn(
                      "p-4 cursor-pointer hover:bg-muted/50 transition-all text-sm group",
                      selectedFile?.id === file.id ? "bg-muted border-l-4 border-l-primary pl-[12px]" : "border-l-4 border-l-transparent"
                    )}
                    onClick={() => setSelectedFile(file)}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium truncate pr-2 flex-1" title={file.filename}>{file.filename}</span>
                      {file.content_summary && (
                        <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />
                      )}
                    </div>
                    <div className="flex justify-between items-center text-xs text-muted-foreground mt-2">
                      <span>{(file.file_size / 1024).toFixed(1)} KB • {new Date(file.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
                {files.length === 0 && (
                  <div className="p-8 text-center text-muted-foreground flex flex-col items-center gap-2">
                    <Upload className="h-8 w-8 opacity-20" />
                    <p>No files uploaded yet.</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* File Details */}
        <Card className="col-span-2 flex flex-col h-full max-h-[calc(100vh-200px)]">
          {selectedFile ? (
            <>
              <CardHeader className="pb-4 border-b">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <CardTitle className="text-xl break-all">{selectedFile.filename}</CardTitle>
                    <CardDescription className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">{selectedFile.file_type}</Badge>
                      <span>{(selectedFile.file_size / 1024).toFixed(1)} KB</span>
                    </CardDescription>
                  </div>
                  <Button 
                    onClick={() => handleProcessFile(selectedFile.id)}
                    disabled={processing === selectedFile.id}
                    size="sm"
                    className="gap-2 shrink-0"
                  >
                    {processing === selectedFile.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    {processing === selectedFile.id ? 'Processing...' : (selectedFile.content_summary ? 'Regenerate Summary' : 'Generate Summary')}
                  </Button>
                </div>
              </CardHeader>
              
              <CardContent className="flex-1 overflow-hidden p-0">
                <ScrollArea className="h-full p-6">
                  {selectedFile.content_summary ? (
                    <div className="space-y-6">
                      <div>
                        <div className="flex justify-between items-center mb-4">
                          <h3 className="text-lg font-semibold flex items-center gap-2 text-primary">
                            <FileText className="h-5 w-5" /> Shipley Summary
                          </h3>
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => selectedFile.content_summary && copyToClipboard(selectedFile.content_summary)}
                              title="Copy to clipboard"
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              asChild
                              title="Send via email"
                            >
                              <a href={`mailto:?subject=Summary of ${selectedFile.filename}&body=${encodeURIComponent(selectedFile.content_summary || '')}`}>
                                <Mail className="h-4 w-4" />
                              </a>
                            </Button>
                          </div>
                        </div>
                        <div className="bg-muted/30 p-6 rounded-lg whitespace-pre-wrap text-sm leading-relaxed border shadow-sm font-sans">
                          {selectedFile.content_summary}
                        </div>
                      </div>
                      
                      <Separator />
                      
                      <div>
                        <details className="group">
                          <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground flex items-center gap-2 select-none">
                            <div className="bg-muted p-1 rounded group-open:rotate-90 transition-transform">
                              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                            </div>
                            View Raw Parsed Content
                          </summary>
                          <div className="mt-4 p-4 bg-black/90 text-white rounded-lg text-xs font-mono whitespace-pre-wrap max-h-[400px] overflow-y-auto shadow-inner">
                            {selectedFile.parsed_content || "No content parsed."}
                          </div>
                        </details>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-[400px] text-muted-foreground bg-muted/5 rounded-lg border-2 border-dashed m-4">
                      <div className="bg-muted/20 p-4 rounded-full mb-4">
                        <FileText className="h-12 w-12 opacity-20" />
                      </div>
                      <h3 className="text-lg font-semibold mb-2">No Summary Available</h3>
                      <p className="text-sm max-w-xs text-center mb-6">
                        Click "Generate Summary" to analyze this file using AI.
                      </p>
                      <Button 
                        onClick={() => handleProcessFile(selectedFile.id)}
                        disabled={processing === selectedFile.id}
                        variant="secondary"
                      >
                        Generate AI Summary
                      </Button>
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground bg-muted/5 m-6 rounded-lg border-2 border-dashed">
              <FileText className="h-16 w-16 opacity-10 mb-4" />
              <p className="text-lg font-medium">Select a file to view details</p>
              <p className="text-sm opacity-70">Or upload a new file to get started</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default FileManagementPage;
