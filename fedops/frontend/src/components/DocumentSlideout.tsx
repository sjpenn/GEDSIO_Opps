import { useState, useEffect } from 'react';
import { Download, FileText, ExternalLink, FileSpreadsheet, FileType2, AlertCircle, Loader2, Copy, Eye, Layers } from 'lucide-react';
import { Slideout } from '@/components/ui/slideout';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

const API_URL = import.meta.env.VITE_API_URL || '';

interface DocumentSlideoutProps {
    /** Whether the slideout is open */
    isOpen: boolean;
    /** Callback when the slideout is closed */
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
    /** Optional highlight location for source quotes */
    highlightLocation?: { start: number; end: number };
}

/**
 * Slideout panel component for viewing document contents.
 * Opens from the right side when clicking on a filename.
 * 
 * Supports:
 * - PDF files (via iframe)
 * - Office/Text files (via parsed content preview)
 * - Summary and key findings display
 * - Download and external view options
 */
export default function DocumentSlideout({
    isOpen,
    onClose,
    document,
    opportunityId,
    highlightLocation
}: DocumentSlideoutProps) {
    const [loading, setLoading] = useState(false);
    const [fileContent, setFileContent] = useState<string | null>(null);
    const [fileSummary, setFileSummary] = useState<string | null>(null);
    const [fileMetadata, setFileMetadata] = useState<any>(null);
    const [activeView, setActiveView] = useState<'summary' | 'content'>('content');
    const [copied, setCopied] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [importing, setImporting] = useState(false);
    const [fileId, setFileId] = useState<number | null>(null);

    useEffect(() => {
        if (isOpen && document) {
            // If we have an id, use it directly
            if (document.id) {
                setFileId(document.id);
                fetchFileDetails(document.id);
            } else if (opportunityId && document.filename) {
                // No id means external file - try to import it first
                importAndFetch();
            }
        } else {
            // Reset state on close
            setFileContent(null);
            setFileSummary(null);
            setFileMetadata(null);
            setActiveView('content');
            setError(null);
            setFileId(null);
        }
    }, [isOpen, document, opportunityId]);

    // Import resources for the opportunity and then fetch the specific file
    const importAndFetch = async () => {
        if (!opportunityId || !document?.filename) return;

        setImporting(true);
        setError(null);

        const targetFilename = document.filename;
        console.log(`[DocumentSlideout] Looking for file: "${targetFilename}" in opportunity ${opportunityId}`);

        try {
            // First try to find the file by filename
            const listResponse = await fetch(`${API_URL}/api/v1/files/?opportunity_id=${opportunityId}`);
            if (listResponse.ok) {
                const files = await listResponse.json();
                console.log(`[DocumentSlideout] Found ${files.length} files in opportunity`);
                files.forEach((f: any) => console.log(`  - "${f.filename}" (id: ${f.id})`));

                // Try exact match first, then partial match
                let existingFile = files.find((f: any) => f.filename === targetFilename);
                if (!existingFile) {
                    // Try case-insensitive match
                    existingFile = files.find((f: any) =>
                        f.filename?.toLowerCase() === targetFilename?.toLowerCase()
                    );
                }
                if (!existingFile) {
                    // Try partial match (filename contains the target)
                    existingFile = files.find((f: any) =>
                        f.filename?.toLowerCase().includes(targetFilename?.toLowerCase()) ||
                        targetFilename?.toLowerCase().includes(f.filename?.toLowerCase())
                    );
                }

                if (existingFile?.id) {
                    console.log(`[DocumentSlideout] Found matching file: "${existingFile.filename}" (id: ${existingFile.id})`);
                    setFileId(existingFile.id);
                    await fetchFileDetails(existingFile.id);
                    setImporting(false);
                    return;
                }
            }

            // If not found, trigger import
            console.log(`[DocumentSlideout] File not found locally, importing resources...`);
            const importResponse = await fetch(`${API_URL}/api/v1/files/import-resources/${opportunityId}`, {
                method: 'POST'
            });

            if (!importResponse.ok) {
                const errorText = await importResponse.text();
                console.error(`[DocumentSlideout] Import failed: ${importResponse.status} - ${errorText}`);
                throw new Error(`Failed to import resources: ${importResponse.status}`);
            }

            const importResult = await importResponse.json();
            console.log(`[DocumentSlideout] Import response:`, importResult);

            // Wait a bit for processing to complete
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Now fetch the file list again
            const filesResponse = await fetch(`${API_URL}/api/v1/files/?opportunity_id=${opportunityId}`);
            if (filesResponse.ok) {
                const files = await filesResponse.json();
                console.log(`[DocumentSlideout] After import, found ${files.length} files`);

                // Try multiple matching strategies
                let targetFile = files.find((f: any) => f.filename === targetFilename);
                if (!targetFile) {
                    targetFile = files.find((f: any) =>
                        f.filename?.toLowerCase() === targetFilename?.toLowerCase()
                    );
                }
                if (!targetFile) {
                    targetFile = files.find((f: any) =>
                        f.filename?.toLowerCase().includes(targetFilename?.toLowerCase()) ||
                        targetFilename?.toLowerCase().includes(f.filename?.toLowerCase())
                    );
                }
                // If still not found, just use the first file if any
                if (!targetFile && files.length > 0) {
                    console.log(`[DocumentSlideout] Using first available file as fallback`);
                    targetFile = files[0];
                }

                if (targetFile?.id) {
                    console.log(`[DocumentSlideout] Using file: "${targetFile.filename}" (id: ${targetFile.id})`);
                    setFileId(targetFile.id);
                    await fetchFileDetails(targetFile.id);
                } else {
                    setError(`No files found for this opportunity.`);
                }
            } else {
                setError('Failed to fetch files after import');
            }
        } catch (err) {
            console.error('[DocumentSlideout] Error importing file:', err);
            setError(`Failed to import document: ${err instanceof Error ? err.message : 'Unknown error'}`);
        } finally {
            setImporting(false);
        }
    };

    // Scroll to highlight when content loads
    useEffect(() => {
        if (isOpen && fileContent && highlightLocation && activeView === 'content') {
            setTimeout(() => {
                const element = window.document.getElementById('highlighted-quote');
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 500);
        }
    }, [isOpen, fileContent, highlightLocation, activeView]);

    const fetchFileDetails = async (id: number) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_URL}/api/v1/files/${id}`);
            if (response.ok) {
                const data = await response.json();
                if (data.parsed_content) {
                    setFileContent(data.parsed_content);
                }
                if (data.content_summary) {
                    setFileSummary(data.content_summary);
                }
                setFileMetadata({
                    pages: data.page_count || null,
                    size: data.file_size,
                    type: data.file_type,
                    created: data.created_at
                });

                // If no parsed content, the file might not be processed yet
                if (!data.parsed_content && !data.content_summary) {
                    setError('Document has not been processed yet. Click "Process" to extract text content.');
                }
            } else {
                setError('Failed to load document details');
            }
        } catch (err) {
            console.error('Error fetching file details:', err);
            setError('Failed to load document');
        } finally {
            setLoading(false);
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
        if (isPDF) return <FileText className="h-5 w-5 text-red-600" />;
        return <FileText className="h-5 w-5" />;
    };

    const handleDownload = async () => {
        const downloadId = fileId || document.id;
        if (!downloadId || !opportunityId) {
            alert('Document information not available for download');
            return;
        }

        try {
            setLoading(true);
            const response = await fetch(`${API_URL}/api/v1/files/${opportunityId}/${downloadId}/download`);
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
        } catch (err) {
            console.error('Download error:', err);
            alert('Failed to download document');
        } finally {
            setLoading(false);
        }
    };

    const handleOpenExternal = () => {
        const viewId = fileId || document.id;
        if (!viewId || !opportunityId) {
            alert('Document information not available');
            return;
        }
        window.open(`${API_URL}/api/v1/files/${opportunityId}/${viewId}/view`, '_blank');
    };

    const handleCopyContent = () => {
        if (fileContent) {
            navigator.clipboard.writeText(fileContent);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Format content with headers and proper spacing
    const formatContent = (text: string) => {
        // Intelligently split the content - add line breaks before numbered sections
        // Only match when followed by an actual word (at least 3 letters), not just any capital
        let processedText = text
            // Add breaks before major numbered sections (e.g., "1. Introduction", "10. Key Project Tasks")
            // Must have at least 3 characters after the number to be a real section
            .replace(/(?<=[a-z.!?)])\s+(\d{1,2}\.\s+[A-Z][a-z]{2,})/g, '\n\n$1')
            // Add breaks before subsections (e.g., "4.1 Client Management System")
            .replace(/(?<=[a-z.!?)])\s+(\d{1,2}\.\d+\s+[A-Z][a-zA-Z]{2,})/g, '\n\n$1')
            // Add breaks before sub-subsections (e.g., "4.1.1 PRISM Details")
            .replace(/(?<=[a-z.!?)])\s+(\d{1,2}\.\d+\.\d+\s+[A-Z][a-zA-Z]{2,})/g, '\n\n$1')
            // Add breaks before lettered items (a), (b), (c) with text following
            .replace(/(?<=[.!?])\s+(\([a-z]\)\s+[A-Z][a-z])/gi, '\n$1');

        const lines = processedText.split('\n');
        const formattedElements: React.ReactNode[] = [];

        // Track consecutive table-like lines
        let tableBuffer: string[] = [];
        let inTable = false;

        // Helper to detect if a line looks like part of a table
        const isTableLine = (line: string): boolean => {
            const trimmed = line.trim();
            if (!trimmed) return false;

            // Table indicators:
            // 1. Contains multiple tabs
            // 2. Has multiple segments of 2+ spaces (column separators)
            // 3. Starts with common table patterns (ID, #, Task, Item, etc.)
            // 4. Contains pipe characters |
            const hasMultipleTabs = (line.match(/\t/g) || []).length >= 2;
            const hasMultiSpaces = (line.match(/\s{2,}/g) || []).length >= 2;
            const hasPipes = line.includes('|');
            const looksLikeTableHeader = /^(Task\s+ID|ID|#|Item|No\.?|Deliverable|Description|Due|Date|Title)\b/i.test(trimmed);
            const hasColumnData = /^\d+\s{2,}[A-Za-z]/.test(trimmed) || /^[A-Za-z]+\s{2,}[A-Za-z]+\s{2,}/.test(trimmed);

            return hasMultipleTabs || hasMultiSpaces || hasPipes || looksLikeTableHeader || hasColumnData;
        };

        // Helper to flush table buffer
        const flushTable = () => {
            if (tableBuffer.length > 0) {
                formattedElements.push(
                    <div key={`table-${formattedElements.length}`} className="my-4 overflow-x-auto">
                        <pre className="text-xs font-mono bg-muted/30 border rounded-lg p-4 whitespace-pre leading-relaxed">
                            {tableBuffer.join('\n')}
                        </pre>
                    </div>
                );
                tableBuffer = [];
            }
            inTable = false;
        };

        lines.forEach((line, index) => {
            const trimmedLine = line.trim();

            // Check if this line is part of a table
            if (isTableLine(line)) {
                inTable = true;
                tableBuffer.push(line);
                return;
            } else if (inTable && !trimmedLine) {
                // Empty line might be end of table or just spacing in table
                // If next non-empty line isn't table-like, flush
                tableBuffer.push(line);
                return;
            } else if (inTable) {
                // Non-table line after table content - flush table
                flushTable();
            }

            // Skip empty lines but add spacing
            if (!trimmedLine) {
                formattedElements.push(<div key={index} className="h-3" />);
                return;
            }

            // Detect ALL CAPS lines (headers)
            const isAllCaps = trimmedLine === trimmedLine.toUpperCase() &&
                trimmedLine.length > 3 &&
                trimmedLine.length < 100 &&
                /[A-Z]/.test(trimmedLine) &&
                !/^\d/.test(trimmedLine);

            // Detect major section headers: "1. Introduction", "10. Key Tasks"
            const isMajorSection = /^(\d{1,2})\.\s+[A-Z][a-zA-Z\s&\-()]+$/.test(trimmedLine) && trimmedLine.length < 80;

            // Detect subsection headers: "4.1 Client Management", "10.2 Phase 1"
            const isSubSection = /^(\d{1,2}\.\d+)\s+[A-Z]/.test(trimmedLine) && trimmedLine.length < 120;

            // Detect sub-subsection headers: "4.1.1 PRISM", "10.2.3 Details"
            const isSubSubSection = /^(\d{1,2}\.\d+\.\d+)\s+[A-Z]/.test(trimmedLine) && trimmedLine.length < 120;

            // Detect Task/Phase headers
            const isTaskHeader = /^(Task|Phase|Step|Part)\s+\d+/i.test(trimmedLine);

            // Detect colon-ending short lines (labels)
            const isLabel = trimmedLine.endsWith(':') && trimmedLine.length < 50 && !trimmedLine.includes(',');

            // Detect bullet/lettered items
            const isBulletItem = /^[\-•\*]\s/.test(trimmedLine) || /^\([a-z]\)\s/i.test(trimmedLine);

            // Major document headers (ALL CAPS with keywords)
            if (isAllCaps && (
                trimmedLine.includes('SECTION') ||
                trimmedLine.includes('PART') ||
                trimmedLine.includes('ARTICLE') ||
                trimmedLine.includes('VOLUME') ||
                trimmedLine.includes('PERFORMANCE WORK STATEMENT') ||
                trimmedLine.includes('ATTACHMENT') ||
                trimmedLine.includes('TABLE OF CONTENTS') ||
                trimmedLine.includes('APPENDIX')
            )) {
                formattedElements.push(
                    <div key={index} className="mt-8 mb-4 pt-4 border-t-2 border-primary/40">
                        <h2 className="text-lg font-bold text-primary uppercase tracking-wide">
                            {trimmedLine}
                        </h2>
                    </div>
                );
            }
            // Major numbered sections: "1. Introduction"
            else if (isMajorSection || isTaskHeader) {
                formattedElements.push(
                    <div key={index} className="mt-6 mb-3 pt-3 border-t border-primary/20">
                        <h3 className="text-base font-bold text-foreground">
                            {trimmedLine}
                        </h3>
                    </div>
                );
            }
            // Subsections: "4.1 Client Management"
            else if (isSubSection) {
                formattedElements.push(
                    <div key={index} className="mt-5 mb-2">
                        <h4 className="text-sm font-semibold text-foreground border-l-2 border-primary/50 pl-3">
                            {trimmedLine}
                        </h4>
                    </div>
                );
            }
            // Sub-subsections: "4.1.1 PRISM"
            else if (isSubSubSection) {
                formattedElements.push(
                    <div key={index} className="mt-4 mb-2 ml-2">
                        <h5 className="text-sm font-medium text-foreground/90 italic">
                            {trimmedLine}
                        </h5>
                    </div>
                );
            }
            // Label headers (ending with colon)
            else if (isLabel) {
                formattedElements.push(
                    <div key={index} className="mt-4 mb-1">
                        <span className="font-semibold text-foreground text-sm">{trimmedLine}</span>
                    </div>
                );
            }
            // Bullet/lettered items
            else if (isBulletItem) {
                formattedElements.push(
                    <div key={index} className="ml-4 mb-1 flex">
                        <span className="text-primary mr-2">•</span>
                        <p className="text-sm leading-relaxed text-muted-foreground">
                            {trimmedLine.replace(/^[\-•\*]\s*/, '').replace(/^\([a-z]\)\s*/i, '')}
                        </p>
                    </div>
                );
            }
            // Regular paragraph content
            else {
                formattedElements.push(
                    <p key={index} className="text-sm leading-relaxed text-muted-foreground mb-2">
                        {trimmedLine}
                    </p>
                );
            }
        });

        // Flush any remaining table content
        flushTable();

        return formattedElements;
    };

    const renderHighlightedContent = () => {
        if (!fileContent) return null;

        if (highlightLocation && highlightLocation.start >= 0 && highlightLocation.end > highlightLocation.start) {
            const before = fileContent.slice(0, highlightLocation.start);
            const highlight = fileContent.slice(highlightLocation.start, highlightLocation.end);
            const after = fileContent.slice(highlightLocation.end);

            return (
                <div className="space-y-0">
                    {formatContent(before)}
                    <span id="highlighted-quote" className="bg-yellow-200 dark:bg-yellow-900/50 border-b-2 border-yellow-500 animate-pulse px-1 rounded">
                        {highlight}
                    </span>
                    {formatContent(after)}
                </div>
            );
        }

        return <div className="space-y-0">{formatContent(fileContent)}</div>;
    };

    const formatFileSize = (bytes: number) => {
        if (!bytes) return 'Unknown';
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
        <Slideout
            isOpen={isOpen}
            onClose={onClose}
            title={document.filename}
            width="max-w-3xl"
            side="right"
        >
            <div className="space-y-6">
                {/* Header with file info and actions */}
                <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-muted rounded-lg">
                            {getFileIcon()}
                        </div>
                        <div>
                            <h3 className="font-semibold text-lg break-all">{document.filename}</h3>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                                {document.type && <Badge variant="outline">{document.type}</Badge>}
                                {fileMetadata?.size && <span>{formatFileSize(fileMetadata.size)}</span>}
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
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
                            <ExternalLink className="h-4 w-4" />
                        </Button>
                    </div>
                </div>

                <Separator />

                {/* Toggle between Summary and Full Content */}
                <div className="flex gap-2">
                    <Button
                        variant={activeView === 'summary' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setActiveView('summary')}
                    >
                        <Layers className="h-4 w-4 mr-2" />
                        Summary
                    </Button>
                    <Button
                        variant={activeView === 'content' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setActiveView('content')}
                    >
                        <Eye className="h-4 w-4 mr-2" />
                        Full Content
                    </Button>
                </div>

                {/* Loading state */}
                {(loading || importing) && (
                    <div className="flex flex-col items-center justify-center py-12 gap-3">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">
                            {importing ? 'Downloading and processing document...' : 'Loading document...'}
                        </p>
                    </div>
                )}

                {/* Error state */}
                {error && !loading && !importing && (
                    <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4 flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                        <div className="space-y-2">
                            <p className="text-sm text-destructive font-medium">{error}</p>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                    if (document?.id || fileId) {
                                        fetchFileDetails(fileId || document?.id || 0);
                                    } else if (opportunityId) {
                                        importAndFetch();
                                    }
                                }}
                            >
                                Retry
                            </Button>
                        </div>
                    </div>
                )}

                {/* Summary View */}
                {!loading && activeView === 'summary' && (
                    <div className="space-y-4">
                        {fileSummary ? (
                            <div className="bg-primary/5 p-4 rounded-lg border border-primary/20">
                                <h4 className="font-semibold mb-2 flex items-center gap-2 text-primary">
                                    <FileText className="h-4 w-4" />
                                    Document Summary
                                </h4>
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{fileSummary}</p>
                            </div>
                        ) : (
                            <div className="bg-muted/30 p-6 rounded-lg text-center">
                                <AlertCircle className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                                <p className="text-sm text-muted-foreground">
                                    No summary available. Click "Full Content" to view the document text.
                                </p>
                            </div>
                        )}

                        {/* Quick Stats */}
                        {fileMetadata && (
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-muted/30 p-3 rounded-lg text-center">
                                    <div className="text-xl font-bold">{fileMetadata.pages || '-'}</div>
                                    <div className="text-xs text-muted-foreground">Pages</div>
                                </div>
                                <div className="bg-muted/30 p-3 rounded-lg text-center">
                                    <div className="text-xl font-bold">{formatFileSize(fileMetadata.size)}</div>
                                    <div className="text-xs text-muted-foreground">Size</div>
                                </div>
                                <div className="bg-muted/30 p-3 rounded-lg text-center">
                                    <div className="text-xl font-bold">{fileMetadata.type?.split('/')[1]?.toUpperCase() || 'DOC'}</div>
                                    <div className="text-xs text-muted-foreground">Type</div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Full Content View */}
                {!loading && activeView === 'content' && (
                    <div className="space-y-4">
                        {/* Show parsed text content for all file types */}
                        {fileContent ? (
                            <>
                                {/* Content header with copy button */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Badge variant="outline" className="text-xs bg-yellow-50 text-yellow-700 border-yellow-300">
                                            <AlertCircle className="h-3 w-3 mr-1" />
                                            Text Preview
                                        </Badge>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleCopyContent}
                                    >
                                        <Copy className="h-4 w-4 mr-2" />
                                        {copied ? 'Copied!' : 'Copy'}
                                    </Button>
                                </div>

                                {/* Text content */}
                                <ScrollArea className="h-[50vh] border rounded-lg bg-muted/5">
                                    <div className="p-6">
                                        {renderHighlightedContent()}
                                    </div>
                                </ScrollArea>
                            </>
                        ) : (
                            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground border rounded-lg">
                                <FileText className="h-12 w-12 opacity-20 mb-4" />
                                <p className="text-lg font-medium">No Content Available</p>
                                <p className="text-sm mt-2">
                                    This document has not been processed yet, or the content could not be extracted.
                                </p>
                                <Button
                                    className="mt-4"
                                    onClick={handleDownload}
                                    disabled={loading}
                                >
                                    <Download className="h-4 w-4 mr-2" />
                                    Download {document.filename}
                                </Button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </Slideout>
    );
}
