/**
 * useCachedOpportunities Hook
 * 
 * Provides browser-level caching for opportunity searches using sessionStorage.
 * Implements 2-hour TTL with automatic cache invalidation.
 */

import { useState, useCallback } from 'react';
import type { Opportunity } from '../types';

interface CacheEntry {
    data: {
        items: Opportunity[];
        total: number;
        page: number;
        limit: number;
        pages: number;
    };
    timestamp: number;
    params: Record<string, any>;
}

interface CachedOpportunitiesResult {
    opportunities: Opportunity[];
    total: number;
    loading: boolean;
    error: string | null;
    cacheInfo: {
        isCached: boolean;
        lastFetch: number | null;
        timeRemaining: number | null;
    };
    fetchOpportunities: (params: Record<string, any>, forceRefresh?: boolean) => Promise<void>;
    clearCache: () => void;
}

// 2 hour TTL in milliseconds
const CACHE_TTL_MS = 2 * 60 * 60 * 1000;
const CACHE_KEY_PREFIX = 'opp_cache_';

/**
 * Generate a cache key from search parameters
 */
function generateCacheKey(params: Record<string, any>): string {
    // Sort keys for consistent hashing
    const sorted = Object.keys(params)
        .sort()
        .reduce((acc, key) => {
            if (params[key] !== '' && params[key] !== null && params[key] !== undefined) {
                acc[key] = params[key];
            }
            return acc;
        }, {} as Record<string, any>);

    return CACHE_KEY_PREFIX + JSON.stringify(sorted);
}

/**
 * Get cached data if valid
 */
function getCachedData(cacheKey: string): CacheEntry | null {
    try {
        const cached = sessionStorage.getItem(cacheKey);
        if (!cached) return null;

        const entry: CacheEntry = JSON.parse(cached);
        const now = Date.now();

        // Check if cache is expired
        if (now - entry.timestamp > CACHE_TTL_MS) {
            sessionStorage.removeItem(cacheKey);
            return null;
        }

        return entry;
    } catch (error) {
        console.error('Error reading cache:', error);
        return null;
    }
}

/**
 * Save data to cache
 */
function setCachedData(cacheKey: string, data: any, params: Record<string, any>): void {
    try {
        const entry: CacheEntry = {
            data,
            timestamp: Date.now(),
            params
        };
        sessionStorage.setItem(cacheKey, JSON.stringify(entry));
    } catch (error) {
        console.error('Error writing cache:', error);
        // If sessionStorage is full, clear old entries
        if (error instanceof DOMException && error.name === 'QuotaExceededError') {
            clearOldCacheEntries();
            // Try again
            try {
                const entry: CacheEntry = {
                    data,
                    timestamp: Date.now(),
                    params
                };
                sessionStorage.setItem(cacheKey, JSON.stringify(entry));
            } catch (retryError) {
                console.error('Failed to cache after clearing:', retryError);
            }
        }
    }
}

/**
 * Clear old cache entries to free up space
 */
function clearOldCacheEntries(): void {
    const keysToRemove: string[] = [];

    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key && key.startsWith(CACHE_KEY_PREFIX)) {
            try {
                const cached = sessionStorage.getItem(key);
                if (cached) {
                    const entry: CacheEntry = JSON.parse(cached);
                    const now = Date.now();
                    if (now - entry.timestamp > CACHE_TTL_MS) {
                        keysToRemove.push(key);
                    }
                }
            } catch (error) {
                keysToRemove.push(key);
            }
        }
    }

    keysToRemove.forEach(key => sessionStorage.removeItem(key));
}

/**
 * Custom hook for cached opportunity fetching
 */
export function useCachedOpportunities(): CachedOpportunitiesResult {
    const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [cacheInfo, setCacheInfo] = useState<{
        isCached: boolean;
        lastFetch: number | null;
        timeRemaining: number | null;
    }>({
        isCached: false,
        lastFetch: null,
        timeRemaining: null
    });

    const fetchOpportunities = useCallback(async (
        params: Record<string, any>,
        forceRefresh: boolean = false
    ) => {
        const cacheKey = generateCacheKey(params);

        // Try cache first (unless force refresh)
        if (!forceRefresh) {
            const cached = getCachedData(cacheKey);
            if (cached) {
                setOpportunities(cached.data.items);
                setTotal(cached.data.total);
                setCacheInfo({
                    isCached: true,
                    lastFetch: cached.timestamp,
                    timeRemaining: CACHE_TTL_MS - (Date.now() - cached.timestamp)
                });
                return;
            }
        }

        // Fetch from API
        try {
            setLoading(true);
            setError(null);

            const queryParams = new URLSearchParams();
            Object.keys(params).forEach(key => {
                if (params[key]) {
                    queryParams.append(key, params[key].toString());
                }
            });

            const response = await fetch(`/api/v1/opportunities/?${queryParams.toString()}`);

            if (!response.ok) {
                throw new Error('Failed to fetch opportunities');
            }

            const data = await response.json();

            // Update state
            setOpportunities(data.items);
            setTotal(data.total);

            // Cache the result
            setCachedData(cacheKey, data, params);

            setCacheInfo({
                isCached: false,
                lastFetch: Date.now(),
                timeRemaining: CACHE_TTL_MS
            });

        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    }, []);

    const clearCache = useCallback(() => {
        const keysToRemove: string[] = [];
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            if (key && key.startsWith(CACHE_KEY_PREFIX)) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(key => sessionStorage.removeItem(key));

        setCacheInfo({
            isCached: false,
            lastFetch: null,
            timeRemaining: null
        });
    }, []);

    return {
        opportunities,
        total,
        loading,
        error,
        cacheInfo,
        fetchOpportunities,
        clearCache
    };
}
