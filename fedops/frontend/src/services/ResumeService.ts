export interface Resume {
    id: number;
    user_id?: string;
    stored_file_id: number;
    parsed_data?: any;
    raw_text?: string;
    status: string;
    error_message?: string;
    formatted_content_html?: string;
    created_at: string;
}

export const ResumeService = {
    async uploadResume(file: File, userId?: string): Promise<Resume> {
        const formData = new FormData();
        formData.append('file', file);
        if (userId) formData.append('user_id', userId);

        const response = await fetch('/api/v1/resumes/upload', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Failed to upload resume');
        }

        return response.json();
    },

    async getResume(id: number): Promise<Resume> {
        const response = await fetch(`/api/v1/resumes/${id}`);
        if (!response.ok) {
            throw new Error('Failed to fetch resume');
        }
        return response.json();
    },

    async formatResume(id: number, includeSignature: boolean): Promise<Resume> {
        const response = await fetch(`/api/v1/resumes/${id}/format?include_signature=${includeSignature}`, {
            method: 'POST',
        });
        if (!response.ok) {
            throw new Error('Failed to format resume');
        }
        return response.json();
    },

    async listResumes(): Promise<Resume[]> {
        const response = await fetch('/api/v1/resumes/');
        if (!response.ok) {
            throw new Error('Failed to fetch resumes');
        }
        return response.json();
    },

    async downloadFormattedResume(id: number): Promise<void> {
        const response = await fetch(`/api/v1/resumes/${id}/download`);
        if (!response.ok) {
            throw new Error('Failed to download resume');
        }
        const data = await response.json();
        
        // Create a blob and download it
        const blob = new Blob([data.html], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `resume_${id}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
};
