import { useState, useCallback, useEffect } from "react";
import { Upload, FolderOpen, FileText, Clock, Sparkles, Trash2, CheckCircle2, Loader2, AlertCircle, Eye, Download, Copy } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";
import {
    uploadFile as apiUploadFile,
    getLibraryFiles,
    processFile,
    formatFileSize,
    estimateWordCount,
    runExtraction as apiRunExtraction,
    getExtractionHistory
} from "@/services/extractionService";

interface LocalFile {
    id: string;
    apiId?: number;
    name: string;
    size: string;
    sizeBytes: number;
    words: number;
    status: "uploading" | "ready" | "processing" | "done" | "error";
    error?: string;
    file?: File;
}

interface LibraryFile {
    id: number;
    filename: string;
    file_size: number;
    selected: boolean;
}

interface ExtractionOption {
    id: string;
    label: string;
    category: "key-info" | "summaries" | "key-terms";
    isCustom?: boolean;
}

interface ExtractionResult {
    id: string;
    type: string;
    content: string;
    timestamp: string;
    files: string[];
}

const QualifyExtract = () => {
    const toastContext = useToast();
    const [activeInputTab, setActiveInputTab] = useState("upload");
    const [activeActionTab, setActiveActionTab] = useState("actions");
    const [uploadedFiles, setUploadedFiles] = useState<LocalFile[]>([]);
    const [libraryFiles, setLibraryFiles] = useState<LibraryFile[]>([]);
    const [libraryLoading, setLibraryLoading] = useState(false);
    const [selectedExtractions, setSelectedExtractions] = useState<string[]>([]);
    const [pasteText, setPasteText] = useState("");
    const [isDragging, setIsDragging] = useState(false);
    const [isExtracting, setIsExtracting] = useState(false);
    const [extractionHistory, setExtractionHistory] = useState<ExtractionResult[]>([]);

    // View States
    const [viewResult, setViewResult] = useState<ExtractionResult | null>(null);
    const [viewFile, setViewFile] = useState<LibraryFile | LocalFile | null>(null);
    const [extractedText, setExtractedText] = useState<string | null>(null);
    const [isLoadingContent, setIsLoadingContent] = useState(false);

    // Initial Load
    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            const history = await getExtractionHistory();
            // Convert to local format if needed
            const formattedHistory: ExtractionResult[] = history.map((h: any) => ({
                id: h.id,
                type: h.types ? h.types[0] : (h.type || 'Unknown'), // Backend returns 'types' array
                content: h.preview || (h.results && h.results[0]?.content) || "No content",
                timestamp: h.timestamp,
                files: h.files || [],
                full_results: h.results // Store full results for viewing
            }));
            setExtractionHistory(formattedHistory);
        } catch (error) {
            console.error("Failed to load history:", error);
        }
    };

    const keyInfoOptions: ExtractionOption[] = [
        { id: "critical-bid", label: "Critical Bid Decision Information", category: "key-info" },
        { id: "priorities", label: "Commissioner's Priorities (Requirements)", category: "key-info" },
        { id: "compliance", label: "Compliance (Non-Negotiables)", category: "key-info" },
        { id: "statistics", label: "Statistics", category: "key-info" },
        { id: "dates", label: "Dates & Timelines", category: "key-info" },
        { id: "questions", label: "Bid Questions", category: "key-info" },
        { id: "custom-extraction", label: "Custom Extraction", category: "key-info", isCustom: true },
    ];

    const summaryOptions: ExtractionOption[] = [
        { id: "two-pages", label: "Two pages", category: "summaries" },
        { id: "one-page", label: "One page", category: "summaries" },
        { id: "half-page", label: "Half-page", category: "summaries" },
        { id: "paragraph", label: "Paragraph", category: "summaries" },
        { id: "custom-summary", label: "Custom Summary", category: "summaries", isCustom: true },
    ];

    const keyTermsOptions: ExtractionOption[] = [
        { id: "default-shred", label: "Default Shred", category: "key-terms" },
        { id: "custom-shred", label: "Custom Shred", category: "key-terms", isCustom: true },
    ];

    // Load library files when tab changes
    useEffect(() => {
        if (activeInputTab === "library" && libraryFiles.length === 0) {
            loadLibraryFiles();
        }
    }, [activeInputTab]);

    const loadLibraryFiles = async () => {
        setLibraryLoading(true);
        try {
            const response = await getLibraryFiles();
            // Handle both array and paginated response { items: [], total: ... } or { files: [] }
            // Appwrite backend returns { items: [...] }
            const filesArray = Array.isArray(response)
                ? response
                : (response as any).items || (response as any).files || [];

            setLibraryFiles(filesArray.map((f: any) => ({
                id: f.id,
                filename: f.filename,
                file_size: f.file_size,
                selected: false
            })));
        } catch (error) {
            console.error("Failed to load library files:", error);
            toastContext.error("Failed to load library files");
        } finally {
            setLibraryLoading(false);
        }
    };

    const toggleLibraryFile = (fileId: number) => {
        setLibraryFiles(prev => prev.map(f =>
            f.id === fileId ? { ...f, selected: !f.selected } : f
        ));
    };

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        await uploadFiles(files);
    }, []);

    const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files ? Array.from(e.target.files) : [];
        await uploadFiles(files);
        e.target.value = ""; // Reset input
    }, []);

    const uploadFiles = async (files: File[]) => {
        // Create local file entries with uploading status
        const newFiles: LocalFile[] = files.map((file, index) => ({
            id: `file-${Date.now()}-${index}`,
            name: file.name,
            size: formatFileSize(file.size),
            sizeBytes: file.size,
            words: estimateWordCount(file.size),
            status: "uploading" as const,
            file: file,
        }));

        setUploadedFiles(prev => [...prev, ...newFiles]);

        // Upload each file
        for (const localFile of newFiles) {
            try {
                const result = await apiUploadFile(localFile.file!);

                // Update file with API data
                setUploadedFiles(prev => prev.map(f =>
                    f.id === localFile.id
                        ? {
                            ...f,
                            apiId: result.id,
                            status: "ready" as const,
                            words: result.parsed_content
                                ? estimateWordCount(result.parsed_content)
                                : estimateWordCount(result.file_size)
                        }
                        : f
                ));

                // Process file to extract content
                try {
                    await processFile(result.id);
                    setUploadedFiles(prev => prev.map(f =>
                        f.id === localFile.id ? { ...f, status: "done" as const } : f
                    ));
                } catch {
                    // Processing failed but upload succeeded
                    console.warn("Processing failed for", localFile.name);
                }
            } catch (error) {
                console.error("Upload failed:", error);
                setUploadedFiles(prev => prev.map(f =>
                    f.id === localFile.id
                        ? { ...f, status: "error" as const, error: "Upload failed" }
                        : f
                ));
                toastContext.error(`Failed to upload ${localFile.name}`);
            }
        }
    };

    const removeFile = (fileId: string) => {
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    const toggleExtraction = (optionId: string) => {
        setSelectedExtractions(prev =>
            prev.includes(optionId)
                ? prev.filter(id => id !== optionId)
                : [...prev, optionId]
        );
    };

    const runExtraction = async () => {
        setIsExtracting(true);

        try {
            // Gather file IDs from uploaded files and selected library files
            const uploadedFileIds = uploadedFiles
                .filter(f => f.apiId && (f.status === "ready" || f.status === "done"))
                .map(f => f.apiId!);
            const libraryFileIds = libraryFiles
                .filter(f => f.selected)
                .map(f => f.id);
            const allFileIds = [...uploadedFileIds, ...libraryFileIds];

            if (allFileIds.length === 0 && !pasteText) {
                toastContext.error("Please upload files, select from library, or paste text");
                setIsExtracting(false);
                return;
            }

            if (selectedExtractions.length === 0) {
                toastContext.error("Please select at least one extraction type");
                setIsExtracting(false);
                return;
            }

            // Call the real extraction API
            const response = await apiRunExtraction(
                allFileIds,
                selectedExtractions,
                pasteText || undefined
            );

            // Handle response - it now returns { success, extraction_id, results }
            const apiResponse = response as any;

            if (apiResponse.success && apiResponse.results?.length > 0) {
                // Add each result to history
                for (const result of apiResponse.results) {
                    const historyItem: ExtractionResult = {
                        id: result.id,
                        type: result.type,
                        content: result.content,
                        timestamp: result.timestamp,
                        files: result.files
                    };
                    setExtractionHistory(prev => [historyItem, ...prev]);
                }

                setActiveActionTab("history");
                toastContext.success(`Extraction complete - ${apiResponse.results.length} result(s)`);
                // Reload full history to ensure consistency
                loadHistory();
            } else if (apiResponse.error) {
                throw new Error(apiResponse.error);
            }
        } catch (error) {
            console.error("Extraction failed:", error);
            toastContext.error(error instanceof Error ? error.message : "An error occurred during extraction");
        } finally {
            setIsExtracting(false);
        }
    };

    const getFileStatusIcon = (status: LocalFile["status"]) => {
        switch (status) {
            case "uploading":
                return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
            case "processing":
                return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
            case "ready":
            case "done":
                return <CheckCircle2 className="h-4 w-4 text-green-500" />;
            case "error":
                return <AlertCircle className="h-4 w-4 text-red-500" />;
            default:
                return null;
        }
    };

    const getFileStatusText = (status: LocalFile["status"]) => {
        switch (status) {
            case "uploading":
                return "Uploading...";
            case "processing":
                return "Processing...";
            case "ready":
            case "done":
                return "File ready";
            case "error":
                return "Error";
            default:
                return "";
        }
    };

    // Helper: Determine if file type needs text extraction
    const needsTextExtraction = (fileName: string): boolean => {
        const extension = fileName.split('.').pop()?.toLowerCase() || '';
        return ['pdf', 'docx', 'doc'].includes(extension);
    };

    // Helper: Get file type from filename
    const getFileType = (fileName: string): string => {
        return fileName.split('.').pop()?.toLowerCase() || '';
    };

    // Handle viewing file with text extraction
    const handleViewFile = async (file: LibraryFile | LocalFile) => {
        setViewFile(file);
        setExtractedText(null);

        const fileName = (file as any).filename || (file as any).name || '';
        const fileId = (file as any).apiId || (file as any).id;

        if (needsTextExtraction(fileName)) {
            setIsLoadingContent(true);
            try {
                // Check if file already has parsed_content
                if ((file as any).parsed_content) {
                    setExtractedText((file as any).parsed_content);
                } else {
                    // Process file to extract text
                    const result = await processFile(fileId);
                    setExtractedText(result.parsed_content || 'No content could be extracted from this file.');
                }
            } catch (error) {
                console.error('Error extracting text:', error);
                setExtractedText('Error: Could not extract text from this file.');
                toastContext.error('Failed to extract text content');
            } finally {
                setIsLoadingContent(false);
            }
        }
    };

    const renderExtractionOption = (option: ExtractionOption) => {
        const isSelected = selectedExtractions.includes(option.id);

        return (
            <button
                key={option.id}
                onClick={() => toggleExtraction(option.id)}
                className={cn(
                    "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200",
                    "border",
                    isSelected
                        ? "bg-primary/20 border-primary text-primary"
                        : "bg-muted/50 border-border text-muted-foreground hover:border-primary/50 hover:text-foreground"
                )}
            >
                <Sparkles className={cn(
                    "h-3.5 w-3.5",
                    isSelected ? "text-primary" : "text-muted-foreground"
                )} />
                {option.label}
                {option.isCustom && <FolderOpen className="h-3.5 w-3.5 ml-1 opacity-50" />}
            </button>
        );
    };

    const hasContent = uploadedFiles.some(f => f.status === "ready" || f.status === "done") ||
        libraryFiles.some(f => f.selected) ||
        pasteText.trim().length > 0;

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-bold">Extract</h1>
                <p className="text-muted-foreground mt-2">
                    Extract key information from one or more sources in your library, uploaded files, or text you
                    already have into a single output. You can select or upload up to 20 files per extraction.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* Left Panel - File Input */}
                <div className="lg:col-span-3">
                    <Card className="h-full">
                        <CardContent className="p-6">
                            <Tabs value={activeInputTab} onValueChange={setActiveInputTab}>
                                <TabsList className="grid w-full grid-cols-3 mb-6">
                                    <TabsTrigger value="library" className="gap-2">
                                        <FolderOpen className="h-4 w-4" />
                                        Library
                                        {libraryFiles.filter(f => f.selected).length > 0 && (
                                            <Badge variant="secondary" className="ml-1">
                                                {libraryFiles.filter(f => f.selected).length}
                                            </Badge>
                                        )}
                                    </TabsTrigger>
                                    <TabsTrigger value="upload" className="gap-2">
                                        <Upload className="h-4 w-4" />
                                        File Upload
                                        {uploadedFiles.length > 0 && (
                                            <Badge variant="secondary" className="ml-1">
                                                {uploadedFiles.length}
                                            </Badge>
                                        )}
                                    </TabsTrigger>
                                    <TabsTrigger value="paste" className="gap-2">
                                        <FileText className="h-4 w-4" />
                                        Paste Text
                                    </TabsTrigger>
                                </TabsList>

                                <TabsContent value="library" className="space-y-4">
                                    {libraryLoading ? (
                                        <div className="text-center py-12">
                                            <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
                                            <p className="text-muted-foreground mt-2">Loading library...</p>
                                        </div>
                                    ) : libraryFiles.length === 0 ? (
                                        <div className="text-center py-12 text-muted-foreground">
                                            <FolderOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                            <p>No documents in your library yet</p>
                                            <Button variant="outline" className="mt-4" onClick={() => setActiveInputTab("upload")}>
                                                Upload Files
                                            </Button>
                                        </div>
                                    ) : (
                                        <div className="space-y-2 max-h-96 overflow-y-auto">
                                            {libraryFiles.map((file) => (
                                                <div
                                                    key={file.id}
                                                    onClick={() => toggleLibraryFile(file.id)}
                                                    className={cn(
                                                        "w-full flex items-center justify-between p-4 rounded-lg transition-colors text-left cursor-pointer",
                                                        file.selected
                                                            ? "border border-primary/30 bg-primary/5"
                                                            : "border border-border hover:border-primary/50"
                                                    )}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div className={cn(
                                                            "w-5 h-5 rounded border-2 flex items-center justify-center",
                                                            file.selected
                                                                ? "border-primary bg-primary"
                                                                : "border-muted-foreground"
                                                        )}>
                                                            {file.selected && <CheckCircle2 className="h-3 w-3 text-primary-foreground" />}
                                                        </div>
                                                        <FileText className="h-5 w-5 text-muted-foreground" />
                                                        <div>
                                                            <p className="font-medium">{file.filename}</p>
                                                            <p className="text-sm text-muted-foreground">
                                                                {formatFileSize(file.file_size)}
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleViewFile({ ...file, id: file.id });
                                                        }}
                                                    >
                                                        <Eye className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </TabsContent>

                                <TabsContent value="upload" className="space-y-4">
                                    {/* Drop Zone */}
                                    <div
                                        onDragOver={handleDragOver}
                                        onDragLeave={handleDragLeave}
                                        onDrop={handleDrop}
                                        className={cn(
                                            "border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200",
                                            isDragging
                                                ? "border-primary bg-primary/5"
                                                : "border-border hover:border-primary/50"
                                        )}
                                    >
                                        <Upload className={cn(
                                            "h-10 w-10 mx-auto mb-4",
                                            isDragging ? "text-primary" : "text-muted-foreground"
                                        )} />
                                        <h3 className="font-semibold mb-1">Drag and drop your files here</h3>
                                        <p className="text-sm text-muted-foreground mb-4">
                                            Limit to 2 GB or 250 pages per file, whichever is reached first.<br />
                                            We accept pdf, doc, docx, xls, xlsx, xlsm, xml, ppt, pptx, csv, txt, msg, odt, ods and odp files.
                                        </p>
                                        <label className="cursor-pointer">
                                            <Button asChild variant="outline" className="border-primary text-primary hover:bg-primary/10">
                                                <span>BROWSE FILES</span>
                                            </Button>
                                            <input
                                                type="file"
                                                multiple
                                                accept=".pdf,.doc,.docx,.xls,.xlsx,.xlsm,.xml,.ppt,.pptx,.csv,.txt,.msg,.odt,.ods,.odp"
                                                onChange={handleFileSelect}
                                                className="hidden"
                                            />
                                        </label>
                                    </div>

                                    {/* Uploaded Files List */}
                                    {uploadedFiles.length > 0 && (
                                        <div className="space-y-2 mt-4">
                                            {uploadedFiles.map((file) => (
                                                <div
                                                    key={file.id}
                                                    className={cn(
                                                        "flex items-center justify-between p-4 rounded-lg",
                                                        file.status === "error"
                                                            ? "border border-red-500/30 bg-red-500/5"
                                                            : "border border-primary/30 bg-primary/5"
                                                    )}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <FileText className="h-5 w-5 text-muted-foreground" />
                                                        <div>
                                                            <p className="font-medium">{file.name}</p>
                                                            <p className="text-sm text-muted-foreground">
                                                                {file.size} | {file.words.toLocaleString()} words
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <div className="flex items-center gap-2">
                                                            {getFileStatusIcon(file.status)}
                                                            <span className={cn(
                                                                "text-sm",
                                                                file.status === "error" ? "text-red-500" : "text-green-500"
                                                            )}>
                                                                {getFileStatusText(file.status)}
                                                            </span>
                                                        </div>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => removeFile(file.id)}
                                                            className="text-muted-foreground hover:text-destructive"
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </Button>
                                                        {(file.status === "ready" || file.status === "done") && (
                                                            <Button
                                                                variant="ghost"
                                                                size="icon"
                                                                onClick={() => handleViewFile({ ...file, id: file.apiId || file.id })}
                                                                className="text-muted-foreground hover:text-primary"
                                                            >
                                                                <Eye className="h-4 w-4" />
                                                            </Button>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </TabsContent>

                                <TabsContent value="paste" className="space-y-4">
                                    <textarea
                                        value={pasteText}
                                        onChange={(e) => setPasteText(e.target.value)}
                                        placeholder="Paste your text content here..."
                                        className="w-full h-64 p-4 rounded-lg border border-border bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                                    />
                                    {pasteText && (
                                        <p className="text-sm text-muted-foreground">
                                            {pasteText.split(/\s+/).filter(Boolean).length.toLocaleString()} words
                                        </p>
                                    )}
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                </div>

                {/* Right Panel - Extraction Options */}
                <div className="lg:col-span-2">
                    <Card className="h-full">
                        <CardHeader className="pb-4">
                            <Tabs value={activeActionTab} onValueChange={setActiveActionTab}>
                                <TabsList className="grid w-full grid-cols-2">
                                    <TabsTrigger value="actions" className="gap-2">
                                        <Sparkles className="h-4 w-4" />
                                        Actions
                                    </TabsTrigger>
                                    <TabsTrigger value="history" className="gap-2">
                                        <Clock className="h-4 w-4" />
                                        History
                                        {extractionHistory.length > 0 && (
                                            <Badge variant="secondary" className="ml-1">
                                                {extractionHistory.length}
                                            </Badge>
                                        )}
                                    </TabsTrigger>
                                </TabsList>
                            </Tabs>
                        </CardHeader>
                        <CardContent>
                            <Tabs value={activeActionTab} onValueChange={setActiveActionTab}>
                                <TabsContent value="actions" className="space-y-6 mt-0">
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <h3 className="font-semibold">Choose Extraction</h3>
                                            <Button variant="ghost" size="sm" className="text-xs text-muted-foreground">
                                                ?
                                            </Button>
                                        </div>
                                        <p className="text-sm text-muted-foreground mb-4">
                                            Select which type of extraction you would like to perform on your text.
                                        </p>
                                    </div>

                                    {/* Key Information */}
                                    <div className="space-y-3">
                                        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                                            Key Information
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {keyInfoOptions.map(renderExtractionOption)}
                                        </div>
                                    </div>

                                    {/* Summaries */}
                                    <div className="space-y-3">
                                        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                                            Summaries
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {summaryOptions.map(renderExtractionOption)}
                                        </div>
                                    </div>

                                    {/* Key Terms */}
                                    <div className="space-y-3">
                                        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                                            Key Terms
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {keyTermsOptions.map(renderExtractionOption)}
                                        </div>
                                    </div>

                                    {/* Extract Button */}
                                    <div className="pt-4">
                                        <Button
                                            className="w-full"
                                            size="lg"
                                            disabled={!hasContent || selectedExtractions.length === 0 || isExtracting}
                                            onClick={runExtraction}
                                        >
                                            {isExtracting ? (
                                                <>
                                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                    Extracting...
                                                </>
                                            ) : (
                                                <>
                                                    <Sparkles className="h-4 w-4 mr-2" />
                                                    Run Extraction
                                                    {selectedExtractions.length > 0 && (
                                                        <Badge variant="secondary" className="ml-2">
                                                            {selectedExtractions.length}
                                                        </Badge>
                                                    )}
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                </TabsContent>

                                <TabsContent value="history" className="mt-0">
                                    {extractionHistory.length === 0 ? (
                                        <div className="text-center py-12 text-muted-foreground">
                                            <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                            <p>No extraction history yet</p>
                                            <p className="text-sm mt-1">Your previous extractions will appear here</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-3 max-h-96 overflow-y-auto">
                                            {extractionHistory.map((result) => (
                                                <div
                                                    key={result.id}
                                                    className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
                                                >
                                                    <div className="flex items-center justify-between mb-2">
                                                        <Badge variant="outline">{result.type || "Extraction"}</Badge>
                                                        <span className="text-xs text-muted-foreground">
                                                            {new Date(result.timestamp).toLocaleString()}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-muted-foreground line-clamp-2">
                                                        {result.content}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground mt-2">
                                                        {result.files.length} file(s)
                                                    </p>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        className="w-full mt-3"
                                                        onClick={() => setViewResult(result)}
                                                    >
                                                        <Eye className="h-3.5 w-3.5 mr-2" />
                                                        View Full Result
                                                    </Button>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Extraction Result Modal */}
            <Dialog open={!!viewResult} onOpenChange={(open) => !open && setViewResult(null)}>
                <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-primary" />
                            {viewResult?.type} Result
                        </DialogTitle>
                        <DialogDescription>
                            Generated on {viewResult ? new Date(viewResult.timestamp).toLocaleString() : ''}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="flex-1 overflow-hidden border rounded-md bg-muted/30 p-1">
                        <ScrollArea className="h-full max-h-[60vh] p-4">
                            {viewResult && (viewResult as any).full_results ? (
                                (viewResult as any).full_results.map((res: any, idx: number) => (
                                    <div key={idx} className="mb-6 last:mb-0">
                                        <div className="flex items-center justify-between mb-2">
                                            <Badge variant="secondary">{res.type}</Badge>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="h-6"
                                                onClick={() => {
                                                    navigator.clipboard.writeText(res.content);
                                                    toastContext.success("Copied to clipboard");
                                                }}
                                            >
                                                <Copy className="h-3 w-3 mr-1" /> Copy
                                            </Button>
                                        </div>
                                        <div className="prose prose-sm dark:prose-invert max-w-none bg-background p-4 rounded-lg border">
                                            <pre className="whitespace-pre-wrap font-sans text-sm">{res.content}</pre>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="prose prose-sm dark:prose-invert max-w-none bg-background p-4 rounded-lg border">
                                    <pre className="whitespace-pre-wrap font-sans text-sm">{viewResult?.content}</pre>
                                </div>
                            )}
                        </ScrollArea>
                    </div>
                </DialogContent>
            </Dialog>

            {/* File Viewer Modal */}
            <Dialog open={!!viewFile} onOpenChange={(open) => !open && setViewFile(null)}>
                <DialogContent className="max-w-4xl h-[85vh] flex flex-col">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            {(viewFile as any)?.filename || (viewFile as any)?.name}
                        </DialogTitle>
                        <DialogDescription>
                            {(viewFile as any)?.size || formatFileSize((viewFile as any)?.file_size || 0)}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="flex-1 border rounded-lg overflow-hidden bg-muted/10 relative">
                        {viewFile && (() => {
                            const fileName = (viewFile as any)?.filename || (viewFile as any)?.name || '';
                            const needsExtraction = needsTextExtraction(fileName);

                            if (needsExtraction) {
                                // Show extracted text for PDF/DOCX
                                if (isLoadingContent) {
                                    return (
                                        <div className="flex items-center justify-center h-full">
                                            <div className="flex flex-col items-center gap-3">
                                                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                                <p className="text-sm text-muted-foreground">Extracting text content...</p>
                                            </div>
                                        </div>
                                    );
                                }

                                if (extractedText) {
                                    return (
                                        <ScrollArea className="h-full">
                                            <div className="p-6 prose prose-sm max-w-none">
                                                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                                                    {extractedText}
                                                </pre>
                                            </div>
                                        </ScrollArea>
                                    );
                                }

                                return (
                                    <div className="flex items-center justify-center h-full text-muted-foreground">
                                        <p>No content available</p>
                                    </div>
                                );
                            } else {
                                // Show iframe for other file types (txt, images, etc)
                                return (
                                    <iframe
                                        src={`/api/v1/files/${(viewFile as any).apiId || viewFile.id}/view`}
                                        className="w-full h-full"
                                        title="File Preview"
                                    />
                                );
                            }
                        })()}
                    </div>

                    <DialogFooter>
                        <Button
                            variant="default"
                            onClick={() => {
                                const link = document.createElement('a');
                                link.href = `/api/v1/files/${(viewFile as any).apiId || viewFile.id}/download`;
                                link.download = (viewFile as any)?.filename || (viewFile as any)?.name || 'download';
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                            }}
                        >
                            <Download className="h-4 w-4 mr-2" />
                            Download
                        </Button>
                        <Button variant="secondary" onClick={() => setViewFile(null)}>Close</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div >
    );
};

export default QualifyExtract;
