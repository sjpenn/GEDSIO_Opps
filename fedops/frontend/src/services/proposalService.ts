/**
 * Proposal Management Service
 * 
 * Handles proposal data fetching and management for the Manage module.
 */

const API_BASE = '/api/v1';

export interface Proposal {
    id: number;
    opportunity_id: number;
    title: string;
    status: 'draft' | 'in_progress' | 'review' | 'submitted' | 'awarded';
    progress: number;
    deadline?: string;
    team?: TeamMember[];
    created_at: string;
    updated_at: string;
}

export interface TeamMember {
    id: string;
    name: string;
    role: string;
    avatar?: string;
}

export interface Opportunity {
    id: number;
    title: string;
    agency: string;
    posted_date: string;
    response_deadline: string;
    naics_code?: string;
    set_aside?: string;
    type?: string;
}

export interface ProposalStats {
    total: number;
    active: number;
    submitted: number;
    won: number;
    winRate: number;
}

/**
 * Get list of proposals in pipeline
 */
export async function getProposals(): Promise<Proposal[]> {
    // Use the pipeline endpoint which returns proposals
    const response = await fetch(`${API_BASE}/pipeline/`);

    if (!response.ok) {
        throw new Error('Failed to fetch proposals');
    }

    const data = await response.json();

    // Transform pipeline entries to proposal format
    return data.map((entry: any) => ({
        id: entry.proposal_id || entry.id,
        opportunity_id: entry.opportunity_id,
        title: entry.opportunity?.title || entry.title || 'Untitled Proposal',
        status: mapPipelineStatus(entry.stage),
        progress: calculateProgress(entry),
        deadline: entry.opportunity?.response_deadline,
        team: entry.team || [],
        created_at: entry.created_at,
        updated_at: entry.updated_at
    }));
}

/**
 * Get a single proposal by ID
 */
export async function getProposal(proposalId: number): Promise<Proposal | null> {
    const response = await fetch(`${API_BASE}/proposals/${proposalId}`);

    if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch proposal');
    }

    return response.json();
}

/**
 * Get proposal for an opportunity
 */
export async function getProposalByOpportunity(opportunityId: number): Promise<any> {
    const response = await fetch(`${API_BASE}/proposals/generate/${opportunityId}`);

    if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch proposal');
    }

    return response.json();
}

/**
 * Get list of opportunities
 */
export async function getOpportunities(limit: number = 20): Promise<Opportunity[]> {
    const response = await fetch(`${API_BASE}/opportunities/?limit=${limit}`);

    if (!response.ok) {
        throw new Error('Failed to fetch opportunities');
    }

    const data = await response.json();
    return data.opportunities || data;
}

/**
 * Get proposal statistics
 */
export async function getProposalStats(): Promise<ProposalStats> {
    try {
        const proposals = await getProposals();

        const total = proposals.length;
        const active = proposals.filter(p =>
            p.status === 'draft' || p.status === 'in_progress' || p.status === 'review'
        ).length;
        const submitted = proposals.filter(p => p.status === 'submitted').length;
        const won = proposals.filter(p => p.status === 'awarded').length;

        return {
            total,
            active,
            submitted,
            won,
            winRate: submitted > 0 ? (won / submitted) * 100 : 0
        };
    } catch {
        // Return zeros if fetch fails
        return { total: 0, active: 0, submitted: 0, won: 0, winRate: 0 };
    }
}

// Helper functions

function mapPipelineStatus(stage: string): Proposal['status'] {
    const stageMap: Record<string, Proposal['status']> = {
        'qualifying': 'draft',
        'capture': 'draft',
        'in_progress': 'in_progress',
        'writing': 'in_progress',
        'review': 'review',
        'submitted': 'submitted',
        'won': 'awarded',
        'awarded': 'awarded',
        'lost': 'submitted'
    };

    return stageMap[stage?.toLowerCase()] || 'draft';
}

function calculateProgress(entry: any): number {
    if (entry.progress) return entry.progress;

    // Estimate progress based on stage
    const progressMap: Record<string, number> = {
        'qualifying': 10,
        'capture': 25,
        'in_progress': 50,
        'writing': 65,
        'review': 85,
        'submitted': 100,
        'won': 100,
        'awarded': 100,
        'lost': 100
    };

    return progressMap[entry.stage?.toLowerCase()] || 0;
}

/**
 * Format deadline for display
 */
export function formatDeadline(deadline?: string): string {
    if (!deadline) return 'No deadline';

    const date = new Date(deadline);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

    if (days < 0) return 'Overdue';
    if (days === 0) return 'Due today';
    if (days === 1) return 'Due tomorrow';
    if (days <= 7) return `${days} days left`;

    return date.toLocaleDateString();
}
