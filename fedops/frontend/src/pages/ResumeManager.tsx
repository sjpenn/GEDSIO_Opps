import React, { useState, useEffect } from 'react';
import { type Resume, ResumeService } from '../services/ResumeService';
import { ResumeViewer } from '../components/ResumeViewer';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Upload, FileText, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/components/ui/toast";

export default function ResumeManager() {
    const toast = useToast();
    const [resumes, setResumes] = useState<Resume[]>([]);
    const [currentResume, setCurrentResume] = useState<Resume | null>(null);
    const [uploading, setUploading] = useState(false);
    const [loading, setLoading] = useState(true);

    // Load all resumes on mount
    useEffect(() => {
        loadResumes();
    }, []);

    const loadResumes = async () => {
        try {
            const data = await ResumeService.listResumes();
            setResumes(data);
            // Auto-select first resume if none selected
            if (!currentResume && data.length > 0) {
                setCurrentResume(data[0]);
            }
        } catch (error) {
            console.error('Failed to load resumes:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setUploading(true);
            try {
                const file = e.target.files[0];
                const resume = await ResumeService.uploadResume(file);
                setCurrentResume(resume);
                // Reload the list
                await loadResumes();
            } catch (error) {
                console.error(error);
                toast.error("Upload failed");
            } finally {
                setUploading(false);
            }
        }
    };

    const handleSelectResume = async (resumeId: number) => {
        try {
            const resume = await ResumeService.getResume(resumeId);
            setCurrentResume(resume);
        } catch (error) {
            console.error('Failed to load resume:', error);
        }
    };

    // Poll for updates if current resume is processing
    useEffect(() => {
        let interval: ReturnType<typeof setInterval>;

        if (currentResume && (currentResume.status === 'PROCESSING' || currentResume.status === 'UPLOADED')) {
            interval = setInterval(async () => {
                try {
                    const updated = await ResumeService.getResume(currentResume.id);
                    setCurrentResume(updated);

                    // Update in the list too
                    setResumes(prev => prev.map(r => r.id === updated.id ? updated : r));

                    if (updated.status === 'PARSED' || updated.status === 'FAILED') {
                        clearInterval(interval);
                    }
                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 2000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [currentResume]);

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'PARSED':
                return <Badge variant="default" className="bg-green-500"><CheckCircle2 className="h-3 w-3 mr-1" />Parsed</Badge>;
            case 'FAILED':
                return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
            case 'PROCESSING':
            case 'UPLOADED':
                return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1 animate-pulse" />Processing</Badge>;
            default:
                return <Badge variant="outline">{status}</Badge>;
        }
    };

    return (
        <div className="flex h-[calc(100vh-4rem)] gap-4 p-6">
            {/* Left Sidebar - Resume List */}
            <div className="w-80 flex flex-col gap-4">
                <div className="flex justify-between items-center">
                    <h2 className="text-lg font-semibold">Resumes</h2>
                    <div>
                        <Input
                            type="file"
                            accept=".pdf,.docx,.doc,.txt"
                            onChange={handleFileChange}
                            className="hidden"
                            id="resume-upload"
                            disabled={uploading}
                        />
                        <Button
                            size="sm"
                            onClick={() => document.getElementById('resume-upload')?.click()}
                            disabled={uploading}
                        >
                            {uploading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Upload className="h-4 w-4 mr-1" />}
                            Upload
                        </Button>
                    </div>
                </div>

                <ScrollArea className="flex-1 border rounded-lg">
                    {loading ? (
                        <div className="flex items-center justify-center h-32">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                    ) : resumes.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-32 text-center p-4">
                            <FileText className="h-8 w-8 text-muted-foreground mb-2" />
                            <p className="text-sm text-muted-foreground">No resumes yet</p>
                            <p className="text-xs text-muted-foreground">Upload one to get started</p>
                        </div>
                    ) : (
                        <div className="p-2 space-y-2">
                            {resumes.map((resume) => (
                                <Card
                                    key={resume.id}
                                    className={`cursor-pointer transition-colors hover:bg-accent ${currentResume?.id === resume.id ? 'border-primary bg-accent' : ''
                                        }`}
                                    onClick={() => handleSelectResume(resume.id)}
                                >
                                    <CardContent className="p-3">
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">
                                                    {resume.parsed_data?.contact_info?.name || `Resume ${resume.id}`}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {new Date(resume.created_at).toLocaleDateString()}
                                                </p>
                                            </div>
                                            {getStatusBadge(resume.status)}
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </ScrollArea>
            </div>

            {/* Right Content - Resume Viewer */}
            <div className="flex-1 flex flex-col">
                <h1 className="text-3xl font-bold tracking-tight mb-4">Resume Manager</h1>

                {currentResume ? (
                    currentResume.status === 'PROCESSING' || currentResume.status === 'UPLOADED' ? (
                        <Card className="h-full flex items-center justify-center">
                            <CardContent className="text-center">
                                <Loader2 className="h-16 w-16 mx-auto mb-4 animate-spin text-primary" />
                                <h3 className="text-lg font-medium">Processing Resume...</h3>
                                <p className="text-muted-foreground">Extracting data and analyzing content with AI.</p>
                            </CardContent>
                        </Card>
                    ) : (
                        <ResumeViewer resume={currentResume} onUpdate={setCurrentResume} />
                    )
                ) : (
                    <Card className="border-dashed h-full flex items-center justify-center bg-muted/20">
                        <CardContent className="text-center">
                            <Upload className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                            <h3 className="text-lg font-medium">No Resume Selected</h3>
                            <p className="text-muted-foreground">Select a resume from the list or upload a new one.</p>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
