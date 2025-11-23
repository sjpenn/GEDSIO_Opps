import React, { useState, useEffect } from 'react';

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

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-6 p-1">
        <h1 className="text-2xl font-bold">File Management</h1>
        <div className="flex gap-2">
          {opportunityId && (
            <button
              onClick={handleImportResources}
              disabled={uploading}
              className="bg-secondary text-secondary-foreground px-4 py-2 rounded hover:bg-secondary/90 disabled:opacity-50 flex items-center gap-2"
            >
              {uploading ? 'Importing...' : 'Import Resources'}
            </button>
          )}
          <label className="bg-primary text-primary-foreground px-4 py-2 rounded cursor-pointer hover:bg-primary/90 transition-colors flex items-center gap-2">
            {uploading ? 'Uploading...' : 'Upload File'}
            <input 
              type="file" 
              onChange={handleFileUpload} 
              className="hidden" 
              disabled={uploading}
            />
          </label>
          <button 
            onClick={handleBatchProcess}
            className="bg-accent text-accent-foreground px-4 py-2 rounded hover:bg-accent/90"
          >
            Batch Process All
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 min-h-0">
        {/* File List */}
        <div className="col-span-1 bg-card rounded-lg shadow border flex flex-col overflow-hidden">
          <div className="p-4 border-b bg-muted/50">
            <h2 className="font-semibold">Files ({files.length})</h2>
          </div>
          <div className="divide-y max-h-[600px] overflow-y-auto">
            {files.map(file => (
              <div 
                key={file.id} 
                className={`p-4 cursor-pointer hover:bg-muted/50 transition-colors ${selectedFile?.id === file.id ? 'bg-muted' : ''}`}
                onClick={() => setSelectedFile(file)}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium truncate pr-2" title={file.filename}>{file.filename}</span>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {(file.file_size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">{new Date(file.created_at).toLocaleDateString()}</span>
                  <div className="flex items-center gap-2">
                    {file.content_summary && (
                      <span className="text-green-600 text-xs font-medium px-2 py-0.5 bg-green-100 rounded-full">Processed</span>
                    )}
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleProcessFile(file.id); }}
                      disabled={processing === file.id}
                      className="text-primary hover:underline text-xs"
                    >
                      {processing === file.id ? 'Processing...' : (file.content_summary ? 'Redo' : 'Process AI')}
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {files.length === 0 && (
              <div className="p-8 text-center text-muted-foreground">
                No files uploaded yet.
              </div>
            )}
          </div>
        </div>

        {/* File Details */}
        <div className="col-span-2 bg-card rounded-lg shadow border min-h-[400px] overflow-y-auto h-full">
          {selectedFile ? (
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-xl font-bold mb-1">{selectedFile.filename}</h2>
                  <p className="text-sm text-muted-foreground">
                    Type: {selectedFile.file_type} | Size: {(selectedFile.file_size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button 
                  onClick={() => handleProcessFile(selectedFile.id)}
                  disabled={processing === selectedFile.id}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded text-sm"
                >
                  {processing === selectedFile.id ? 'Processing...' : (selectedFile.content_summary ? 'Regenerate AI Summary' : 'Generate AI Summary')}
                </button>
              </div>

              {selectedFile.content_summary ? (
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <h3 className="text-lg font-semibold text-primary">Shipley Summary</h3>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            if (selectedFile.content_summary) {
                              navigator.clipboard.writeText(selectedFile.content_summary);
                              // Optional: You could add a toast notification here
                              const btn = document.activeElement as HTMLButtonElement;
                              const originalText = btn.innerHTML;
                              btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                              setTimeout(() => {
                                btn.innerHTML = originalText;
                              }, 2000);
                            }
                          }}
                          className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors"
                          title="Copy to clipboard"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                          </svg>
                        </button>
                        <a
                          href={`mailto:?subject=Summary of ${selectedFile.filename}&body=${encodeURIComponent(selectedFile.content_summary || '')}`}
                          className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors"
                          title="Send via email"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect width="20" height="16" x="2" y="4" rx="2"></rect>
                            <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                          </svg>
                        </a>
                      </div>
                    </div>
                    <div className="bg-muted/30 p-4 rounded-lg whitespace-pre-wrap text-sm leading-relaxed border">
                      {selectedFile.content_summary}
                    </div>
                  </div>
                  
                  <div className="border-t pt-4">
                    <details>
                      <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">
                        View Raw Parsed Content
                      </summary>
                      <div className="mt-2 p-4 bg-muted rounded text-xs font-mono whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                        {selectedFile.parsed_content || "No content parsed."}
                      </div>
                    </details>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground bg-muted/10 rounded-lg border-2 border-dashed">
                  <p className="mb-2">No summary generated yet.</p>
                  <p className="text-sm">Click "Generate AI Summary" to analyze this file.</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <p>Select a file to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileManagementPage;
