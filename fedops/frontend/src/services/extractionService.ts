/**
 * Extraction Service
 * 
 * Handles file uploads and AI-powered extraction for the Qualify & Extract module.
 */

const API_BASE = '/api/v1';

export interface UploadedFile {
    id: number;
    filename: string;
    file_path: string;
    file_type: string;
    file_size: number;
    opportunity_id?: number;
    parsed_content?: string;
    content_summary?: string;
    created_at: string;
    updated_at: string;
}

export interface ExtractionResult {
    id: string;
    type: string;
    content: string;
    confidence: number;
    source_file: string;
    created_at: string;
}

export interface ExtractionRequest {
    file_ids: number[];
    extraction_types: string[];
    paste_text?: string;
}

/**
 * Upload a file for extraction
 */
export async function uploadFile(file: File): Promise<UploadedFile> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/files/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(error || 'Failed to upload file');
    }

    return response.json();
}

/**
 * Upload multiple files for extraction
 */
export async function uploadFiles(files: File[]): Promise<UploadedFile[]> {
    const results: UploadedFile[] = [];

    for (const file of files) {
        try {
            const result = await uploadFile(file);
            results.push(result);
        } catch (error) {
            console.error(`Failed to upload ${file.name}:`, error);
            throw error;
        }
    }

    return results;
}

/**
 * Get list of uploaded files (library)
 */
export async function getLibraryFiles(): Promise<UploadedFile[]> {
    const response = await fetch(`${API_BASE}/files/`);

    if (!response.ok) {
        throw new Error('Failed to fetch library files');
    }

    return response.json();
}

/**
 * Process a file for extraction
 */
export async function processFile(fileId: number): Promise<UploadedFile> {
    const response = await fetch(`${API_BASE}/files/${fileId}/process`, {
        method: 'POST',
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(error || 'Failed to process file');
    }

    return response.json();
}

/**
 * Get file chunks (for detailed content extraction)
 */
export async function getFileChunks(fileId: number): Promise<{
    file_id: number;
    filename: string;
    total_chunks: number;
    chunks: Array<{
        index: number;
        content: string;
        page_number?: number;
        section?: string;
        chunk_type?: string;
        heading_context?: string[];
    }>;
}> {
    const response = await fetch(`${API_BASE}/files/${fileId}/chunks`);

    if (!response.ok) {
        throw new Error('Failed to fetch file chunks');
    }

    return response.json();
}

/**
 * Get full file content
 */
export async function getFileContent(fileId: number): Promise<{
    file_id: number;
    filename: string;
    content: string;
    source: string;
}> {
    const response = await fetch(`${API_BASE}/files/${fileId}/content`);

    if (!response.ok) {
        throw new Error('Failed to fetch file content');
    }

    return response.json();
}

/**
 * Run AI extraction on content
 * This calls the AI service to extract specific information types
 */
export async function runExtraction(
    fileIds: number[],
    extractionTypes: string[],
    pasteText?: string
): Promise<ExtractionResult[]> {
    // For now, we'll use the existing analysis endpoints
    // This could be expanded to a dedicated extraction API

    const response = await fetch(`${API_BASE}/extraction/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            file_ids: fileIds,
            extraction_types: extractionTypes,
            paste_text: pasteText,
        }),
    });

    if (!response.ok) {
        const error = await response.text();
        throw new Error(error || 'Failed to run extraction');
    }

    return response.json();
}

/**
 * Get extraction history
 */
export async function getExtractionHistory(): Promise<ExtractionResult[]> {
    const response = await fetch(`${API_BASE}/extraction/history`);

    if (!response.ok) {
        return []; // Return empty if not found
    }

    return response.json();
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Get word count estimate from file size or content
 */
export function estimateWordCount(content: string | number): number {
    if (typeof content === 'number') {
        // Rough estimate: ~6 bytes per word
        return Math.floor(content / 6);
    }
    return content.split(/\s+/).filter(Boolean).length;
}
