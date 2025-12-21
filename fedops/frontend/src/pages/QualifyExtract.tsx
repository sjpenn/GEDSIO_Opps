import { useState, useCallback } from "react";
import { Upload, FolderOpen, FileText, Clock, Sparkles, Trash2, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface UploadedFile {
    id: string;
    name: string;
    size: string;
    words: number;
    status: "uploading" | "ready" | "processing" | "done";
}

interface ExtractionOption {
    id: string;
    label: string;
    category: "key-info" | "summaries" | "key-terms";
    isCustom?: boolean;
}

const QualifyExtract = () => {
    const [activeInputTab, setActiveInputTab] = useState("upload");
    const [activeActionTab, setActiveActionTab] = useState("actions");
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
    const [selectedExtractions, setSelectedExtractions] = useState<string[]>([]);
    const [pasteText, setPasteText] = useState("");
    const [isDragging, setIsDragging] = useState(false);

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

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        const newFiles: UploadedFile[] = files.map((file, index) => ({
            id: `file-${Date.now()}-${index}`,
            name: file.name,
            size: formatFileSize(file.size),
            words: Math.floor(file.size / 6), // Rough estimate
            status: "ready" as const,
        }));

        setUploadedFiles(prev => [...prev, ...newFiles]);
    }, []);

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files ? Array.from(e.target.files) : [];
        const newFiles: UploadedFile[] = files.map((file, index) => ({
            id: `file-${Date.now()}-${index}`,
            name: file.name,
            size: formatFileSize(file.size),
            words: Math.floor(file.size / 6),
            status: "ready" as const,
        }));

        setUploadedFiles(prev => [...prev, ...newFiles]);
        e.target.value = ""; // Reset input
    }, []);

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

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
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
                                    </TabsTrigger>
                                    <TabsTrigger value="upload" className="gap-2">
                                        <Upload className="h-4 w-4" />
                                        File Upload
                                    </TabsTrigger>
                                    <TabsTrigger value="paste" className="gap-2">
                                        <FileText className="h-4 w-4" />
                                        Paste Text
                                    </TabsTrigger>
                                </TabsList>

                                <TabsContent value="library" className="space-y-4">
                                    <div className="text-center py-12 text-muted-foreground">
                                        <FolderOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                        <p>Select documents from your library</p>
                                        <Button variant="outline" className="mt-4">
                                            Browse Library
                                        </Button>
                                    </div>
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
                                        <label>
                                            <Button variant="outline" className="cursor-pointer border-primary text-primary hover:bg-primary/10">
                                                BROWSE FILES
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
                                                    className="flex items-center justify-between p-4 border border-primary/30 rounded-lg bg-primary/5"
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
                                                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                                                            <span className="text-sm text-green-500">File ready</span>
                                                        </div>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => removeFile(file.id)}
                                                            className="text-muted-foreground hover:text-destructive"
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </Button>
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
                                            disabled={uploadedFiles.length === 0 && !pasteText && selectedExtractions.length === 0}
                                        >
                                            <Sparkles className="h-4 w-4 mr-2" />
                                            Run Extraction
                                            {selectedExtractions.length > 0 && (
                                                <Badge variant="secondary" className="ml-2">
                                                    {selectedExtractions.length}
                                                </Badge>
                                            )}
                                        </Button>
                                    </div>
                                </TabsContent>

                                <TabsContent value="history" className="mt-0">
                                    <div className="text-center py-12 text-muted-foreground">
                                        <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                        <p>No extraction history yet</p>
                                        <p className="text-sm mt-1">Your previous extractions will appear here</p>
                                    </div>
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default QualifyExtract;
