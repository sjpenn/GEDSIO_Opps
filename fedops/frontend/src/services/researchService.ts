/**
 * Research Service
 * 
 * Handles vector store searches and research queries for the Research module.
 */

const API_BASE = '/api/v1';

export interface SearchResult {
    id: string;
    content: string;
    score: number;
    source: string;
    filename?: string;
    section?: string;
    page_number?: number;
    metadata?: Record<string, any>;
}

export interface ResearchQuery {
    query: string;
    sources: {
        library: boolean;
        web: boolean;
        sam: boolean;
    };
    opportunityId?: number;
    entityUei?: string;
    topK?: number;
}

export interface VectorStoreStats {
    total_collections: number;
    total_documents: number;
    total_chunks: number;
    collections: Array<{
        name: string;
        count: number;
    }>;
}

/**
 * Search the vector store for relevant documents
 */
export async function searchVectors(
    query: string,
    opportunityId?: number,
    topK: number = 10,
    section?: string
): Promise<SearchResult[]> {
    const params = new URLSearchParams({
        query,
        top_k: topK.toString()
    });

    if (section) {
        params.set('section', section);
    }

    const endpoint = opportunityId
        ? `${API_BASE}/vector-store/opportunity/${opportunityId}/search`
        : `${API_BASE}/vector-store/search`;

    const response = await fetch(`${endpoint}?${params}`);

    if (!response.ok) {
        throw new Error('Search failed');
    }

    const data = await response.json();

    // Transform results to our format
    return (data.results || data).map((result: any, index: number) => ({
        id: result.id || `result-${index}`,
        content: result.content || result.text || '',
        score: result.score || result.similarity || 0,
        source: result.source || 'Library',
        filename: result.filename || result.metadata?.filename,
        section: result.section || result.metadata?.section,
        page_number: result.page_number || result.metadata?.page_number,
        metadata: result.metadata
    }));
}

/**
 * Search entity-specific vectors
 */
export async function searchEntityVectors(
    entityUei: string,
    query: string,
    opportunityId?: number,
    topK: number = 10
): Promise<SearchResult[]> {
    const params = new URLSearchParams({
        query,
        top_k: topK.toString()
    });

    if (opportunityId) {
        params.set('opportunity_id', opportunityId.toString());
    }

    const response = await fetch(
        `${API_BASE}/vector-store/entity/${entityUei}/search?${params}`
    );

    if (!response.ok) {
        throw new Error('Entity search failed');
    }

    const data = await response.json();

    return (data.results || data).map((result: any, index: number) => ({
        id: result.id || `result-${index}`,
        content: result.content || result.text || '',
        score: result.score || result.similarity || 0,
        source: result.source || 'Library',
        filename: result.filename,
        section: result.section,
        page_number: result.page_number,
        metadata: result.metadata
    }));
}

/**
 * Get vector store statistics
 */
export async function getVectorStoreStats(): Promise<VectorStoreStats> {
    const response = await fetch(`${API_BASE}/vector-store/stats`);

    if (!response.ok) {
        throw new Error('Failed to fetch stats');
    }

    return response.json();
}

/**
 * Get vector statistics for a specific opportunity
 */
export async function getOpportunityVectorStats(opportunityId: number): Promise<{
    has_vectors: boolean;
    chunk_count: number;
    file_count: number;
}> {
    const response = await fetch(
        `${API_BASE}/vector-store/opportunity/${opportunityId}/stats`
    );

    if (!response.ok) {
        if (response.status === 404) {
            return { has_vectors: false, chunk_count: 0, file_count: 0 };
        }
        throw new Error('Failed to fetch opportunity stats');
    }

    return response.json();
}

/**
 * Search SAM.gov for opportunities
 */
export async function searchSamGov(query: string, limit: number = 10): Promise<any[]> {
    const params = new URLSearchParams({
        q: query,
        limit: limit.toString()
    });

    const response = await fetch(`${API_BASE}/opportunities/search?${params}`);

    if (!response.ok) {
        throw new Error('SAM.gov search failed');
    }

    const data = await response.json();
    return data.opportunities || data;
}

/**
 * Perform unified search across multiple sources
 */
export async function unifiedSearch(
    query: string,
    sources: { library: boolean; web: boolean; sam: boolean },
    opportunityId?: number,
    topK: number = 10
): Promise<{
    library: SearchResult[];
    sam: any[];
    web: any[];
}> {
    const results: {
        library: SearchResult[];
        sam: any[];
        web: any[];
    } = {
        library: [],
        sam: [],
        web: []
    };

    const promises: Promise<void>[] = [];

    // Search library (vector store)
    if (sources.library) {
        promises.push(
            searchVectors(query, opportunityId, topK)
                .then(r => { results.library = r; })
                .catch(e => { console.error('Library search failed:', e); })
        );
    }

    // Search SAM.gov
    if (sources.sam) {
        promises.push(
            searchSamGov(query, topK)
                .then(r => { results.sam = r; })
                .catch(e => { console.error('SAM.gov search failed:', e); })
        );
    }

    // Web search would go here (future implementation)
    if (sources.web) {
        // Placeholder - would integrate with Perplexity or similar
        results.web = [];
    }

    await Promise.allSettled(promises);

    return results;
}

/**
 * Format relevance score for display
 */
export function formatScore(score: number): string {
    if (score >= 0.9) return 'Excellent';
    if (score >= 0.7) return 'Good';
    if (score >= 0.5) return 'Fair';
    return 'Low';
}

/**
 * Truncate content for preview
 */
export function truncateContent(content: string, maxLength: number = 200): string {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
}
