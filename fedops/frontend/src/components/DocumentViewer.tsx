import { Download, FileText, ExternalLink, FileSpreadsheet, FileType2, AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

const API_URL = import.meta.env.VITE_API_URL || '';

interface DocumentViewerProps {
  /** Whether the viewer modal is open */
  open: boolean;
  /** Callback when the modal is closed */
  onClose: () => void;
  /** The document to view */
  document: {
    filename: string;
    type?: string;
    id?: number;
    file_path?: string;
  } | null;
  /** ID of the opportunity the document belongs to */
  opportunityId?: number;
}

/**
 * Modal component for viewing document contents.
 * Supports:
 * - PDF files (via iframe)
 * - Office/Text files (via parsed content preview)
 * - Other files (via download prompt)
 */
export default function DocumentViewer({ open, onClose, document, opportunityId, highlightLocation }: DocumentViewerProps & { highlightLocation?: { start: number; end: number } }) {
  const [loading, setLoading] = useState(false);
  const [fileContent, setFileContent] = useState<string | null>(null);

  useEffect(() => {
    if (open && document?.id && opportunityId) {
      fetchFileDetails();
    } else {
      setFileContent(null);
    }
  }, [open, document, opportunityId]);

  // Scroll to highlight when content loads
  useEffect(() => {
    if (open && fileContent && highlightLocation) {
      // Small delay to ensure rendering
      setTimeout(() => {
        const element = window.document.getElementById('highlighted-quote');
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 500);
    }
  }, [open, fileContent, highlightLocation]);

  const fetchFileDetails = async () => {
    if (!document?.id) return;
    try {
      const response = await fetch(`${API_URL}/api/v1/files/${document.id}`);
      if (response.ok) {
        const data = await response.json();
        if (data.parsed_content) {
          setFileContent(data.parsed_content);
        }
      }
    } catch (error) {
      console.error('Error fetching file details:', error);
    }
  };

  if (!document) return null;

  const filename = document.filename?.toLowerCase() || '';
  const isPDF = filename.endsWith('.pdf');
  const isExcel = filename.match(/\.(xlsx|xls|csv)$/);
  const isWord = filename.match(/\.(docx|doc)$/);
  const isText = filename.match(/\.(txt|md|json)$/);
  
  const getFileIcon = () => {
    if (isExcel) return <FileSpreadsheet className="h-5 w-5 text-green-600" />;
    if (isWord) return <FileType2 className="h-5 w-5 text-blue-600" />;
    return <FileText className="h-5 w-5" />;
  };

  const handleDownload = async () => {
    if (!document.id || !opportunityId) {
      alert('Document information not available for download');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/v1/files/${opportunityId}/${document.id}/download`);
      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = document.filename;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download document');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenExternal = () => {
    if (!document.id || !opportunityId) {
      alert('Document information not available');
      return;
    }
    window.open(`${API_URL}/api/v1/files/${opportunityId}/${document.id}/view`, '_blank');
  };

  const renderContent = () => {
    if (!fileContent) return null;

    if (highlightLocation && highlightLocation.start >= 0 && highlightLocation.end > highlightLocation.start) {
      const before = fileContent.slice(0, highlightLocation.start);
      const highlight = fileContent.slice(highlightLocation.start, highlightLocation.end);
      const after = fileContent.slice(highlightLocation.end);

      return (
        <>
          {before}
          <span id="highlighted-quote" className="bg-yellow-200 dark:bg-yellow-900/50 border-b-2 border-yellow-500 animate-pulse">
            {highlight}
          </span>
          {after}
        </>
      );
    }

    return fileContent;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <DialogTitle className="flex items-center gap-2">
                {getFileIcon()}
                {document.filename}
              </DialogTitle>
              {document.type && (
                <DialogDescription>
                  Document Type: {document.type}
                </DialogDescription>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
                disabled={loading || !document.id}
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleOpenExternal}
                disabled={!document.id}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Open in New Tab
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 border rounded-lg overflow-hidden bg-muted/30">
          {isPDF && document.id && opportunityId ? (
            <iframe
              src={`${API_URL}/api/v1/files/${opportunityId}/${document.id}/view`}
              className="w-full h-full"
              title={document.filename}
            />
          ) : (isText || isWord || isExcel) && fileContent ? (
            <ScrollArea className="h-full p-6 bg-white dark:bg-slate-950">
              <div className="max-w-3xl mx-auto">
                <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800 flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 text-sm">Text Preview Mode</h4>
                    <p className="text-xs text-yellow-700 dark:text-yellow-300">
                      This is a text-only preview extracted from the {isExcel ? 'spreadsheet' : 'document'}. 
                      Formatting and images are not preserved. Please download the file for the full experience.
                    </p>
                  </div>
                </div>
                <pre className="text-sm font-mono whitespace-pre-wrap leading-relaxed text-slate-700 dark:text-slate-300">
                  {renderContent()}
                </pre>
              </div>
            </ScrollArea>
          ) : (
            <div className="flex items-center justify-center h-full bg-slate-50 dark:bg-slate-900/50">
              <div className="text-center space-y-4 max-w-md mx-auto p-6">
                <div className="h-24 w-24 mx-auto bg-white dark:bg-slate-800 rounded-full flex items-center justify-center shadow-sm">
                  {isExcel ? (
                    <FileSpreadsheet className="h-12 w-12 text-green-600" />
                  ) : isWord ? (
                    <FileType2 className="h-12 w-12 text-blue-600" />
                  ) : (
                    <FileText className="h-12 w-12 text-slate-400" />
                  )}
                </div>
                <div>
                  <p className="text-lg font-semibold">
                    {fileContent === null && (isWord || isExcel) ? 'Loading Preview...' : 'Preview Not Available'}
                  </p>
                  <p className="text-sm text-muted-foreground mt-2">
                    {fileContent === null && (isWord || isExcel) 
                      ? 'Extracting text content from document...'
                      : `This ${isExcel ? 'spreadsheet' : isWord ? 'document' : 'file'} cannot be previewed in the browser.`}
                  </p>
                  <Button
                    className="mt-6 w-full"
                    onClick={handleDownload}
                    disabled={loading}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download {document.filename}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
