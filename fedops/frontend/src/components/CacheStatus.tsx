import { useEffect, useState } from 'react';
import { Info, Clock, RefreshCw } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface CacheStatusProps {
    cacheInfo: {
        isCached: boolean;
        lastFetch: number | null;
        timeRemaining: number | null;
    };
    onRefresh: () => void;
    loading?: boolean;
}

export function CacheStatus({ cacheInfo, onRefresh, loading = false }: CacheStatusProps) {
    const [timeDisplay, setTimeDisplay] = useState<string>('');

    useEffect(() => {
        if (!cacheInfo.timeRemaining || cacheInfo.timeRemaining <= 0) {
            setTimeDisplay('');
            return;
        }

        const updateTimer = () => {
            const remaining = cacheInfo.timeRemaining || 0;
            const hours = Math.floor(remaining / (1000 * 60 * 60));
            const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));

            if (hours > 0) {
                setTimeDisplay(`${hours}h ${minutes}m`);
            } else {
                setTimeDisplay(`${minutes}m`);
            }
        };

        updateTimer();
        const interval = setInterval(updateTimer, 60000); // Update every minute

        return () => clearInterval(interval);
    }, [cacheInfo.timeRemaining]);

    if (!cacheInfo.lastFetch) {
        return null;
    }

    const lastFetchDate = new Date(cacheInfo.lastFetch);
    const isExpired = cacheInfo.timeRemaining !== null && cacheInfo.timeRemaining <= 0;

    return (
        <Card className="border-muted">
            <CardContent className="p-3">
                <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm">
                        <Info className="h-4 w-4 text-muted-foreground" />
                        <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                            <span className="text-muted-foreground">
                                {cacheInfo.isCached ? 'Cached data' : 'Fresh data'}
                                {' '}from{' '}
                                <span className="font-medium text-foreground">
                                    {lastFetchDate.toLocaleTimeString()}
                                </span>
                            </span>
                            {timeDisplay && !isExpired && (
                                <Badge variant="secondary" className="text-xs gap-1 h-5 px-1.5">
                                    <Clock className="h-3 w-3" />
                                    {timeDisplay} until refresh
                                </Badge>
                            )}
                            {isExpired && (
                                <Badge variant="destructive" className="text-xs h-5 px-1.5">
                                    Cache expired
                                </Badge>
                            )}
                        </div>
                    </div>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onRefresh}
                        disabled={loading}
                        className="gap-2 shrink-0"
                    >
                        <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} />
                        <span className="hidden sm:inline">Refresh Now</span>
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
