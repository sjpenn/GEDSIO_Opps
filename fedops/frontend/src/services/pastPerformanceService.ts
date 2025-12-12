/**
 * Past Performance Service
 * Frontend service for communicating with past performance API endpoints
 */

export interface PastPerformance {
  id: number;
  entity_uei: string;
  award_id?: string;
  opportunity_id?: number;
  title: string;
  status: string;
  questionnaire_data: Record<string, QuestionnaireSection>;
  created_by?: string;
  approved_by?: string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface QuestionnaireSection {
  content: string;
  generated: boolean;
  last_generated_at?: string;
  model_used?: string;
}

export interface CreatePastPerformanceRequest {
  entity_uei: string;
  award_id?: string;
  opportunity_id?: number;
  title: string;
  created_by?: string;
}

export interface UpdatePastPerformanceRequest {
  title?: string;
  status?: string;
  questionnaire_data?: Record<string, QuestionnaireSection>;
  approved_by?: string;
  approved_at?: string;
}

export interface GenerateSectionRequest {
  section_name: string;
  context?: string;
  force_regenerate?: boolean;
}

export interface GenerateSectionResponse {
  section_name: string;
  content: string;
  generated: boolean;
  model_used: string;
  generated_at: string;
}

export interface ExportRequest {
  format: 'json' | 'text' | 'markdown';
  include_metadata?: boolean;
}

export interface ExportResponse {
  format: string;
  content: any;
  metadata?: Record<string, any>;
}

export interface QuestionnaireTemplate {
  sections: Record<string, {
    title: string;
    description: string;
    prompt_hint: string;
  }>;
}

class PastPerformanceService {
  private baseUrl = '/api/v1/past-performance';

  /**
   * Create a new past performance questionnaire
   */
  async create(data: CreatePastPerformanceRequest): Promise<PastPerformance> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create past performance');
    }

    return response.json();
  }

  /**
   * Get a specific past performance by ID
   */
  async getById(id: number): Promise<PastPerformance> {
    const response = await fetch(`${this.baseUrl}/${id}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch past performance');
    }

    return response.json();
  }

  /**
   * List all past performances for an entity
   */
  async listByEntity(entityUei: string, status?: string): Promise<PastPerformance[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);

    const response = await fetch(`${this.baseUrl}/entity/${entityUei}?${params.toString()}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch past performances');
    }

    return response.json();
  }

  /**
   * List all past performances with optional filtering
   */
  async listAll(status?: string, limit: number = 50): Promise<PastPerformance[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());

    const response = await fetch(`${this.baseUrl}?${params.toString()}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch past performances');
    }

    return response.json();
  }

  /**
   * Update an existing past performance
   */
  async update(id: number, data: UpdatePastPerformanceRequest): Promise<PastPerformance> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update past performance');
    }

    return response.json();
  }

  /**
   * Delete a past performance
   */
  async delete(id: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete past performance');
    }
  }

  /**
   * Generate AI content for a specific section
   */
  async generateSection(
    id: number,
    request: GenerateSectionRequest
  ): Promise<GenerateSectionResponse> {
    const response = await fetch(`${this.baseUrl}/${id}/generate-section`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate section content');
    }

    return response.json();
  }

  /**
   * Export past performance as structured output
   */
  async export(id: number, request: ExportRequest): Promise<ExportResponse> {
    const response = await fetch(`${this.baseUrl}/${id}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to export past performance');
    }

    return response.json();
  }

  /**
   * Get the questionnaire template
   */
  async getTemplate(): Promise<QuestionnaireTemplate> {
    const response = await fetch(`${this.baseUrl}/templates/questionnaire`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch template');
    }

    return response.json();
  }
}

export const pastPerformanceService = new PastPerformanceService();
