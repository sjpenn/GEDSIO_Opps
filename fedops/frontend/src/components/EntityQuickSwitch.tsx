import { useState, useEffect } from 'react';
import {
    Building2,
    CheckCircle,
    ChevronDown,
    FileText,
    Loader2,
    RefreshCw
} from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { EntityProfileSummary } from '../types';

interface EntityQuickSwitchProps {
    currentEntityUei?: string;
    onEntitySwitch: (entity: EntityProfileSummary) => void;
}

export default function EntityQuickSwitch({ currentEntityUei: _currentEntityUei, onEntitySwitch }: EntityQuickSwitchProps) {
    const [entities, setEntities] = useState<EntityProfileSummary[]>([]);
    const [loading, setLoading] = useState(false);
    const [switching, setSwitching] = useState(false);

    useEffect(() => {
        fetchEntityProfiles();
    }, []);

    const fetchEntityProfiles = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/v1/entities/profiles');
            if (res.ok) {
                const data = await res.json();
                setEntities(data);
            }
        } catch (err) {
            console.error('Failed to fetch entity profiles', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSwitch = async (entity: EntityProfileSummary) => {
        if (entity.is_primary) return;

        setSwitching(true);
        try {
            const res = await fetch(`/api/v1/entities/${entity.uei}/activate`, {
                method: 'POST'
            });

            if (res.ok) {
                // Refresh the entity list
                await fetchEntityProfiles();
                onEntitySwitch(entity);
            }
        } catch (err) {
            console.error('Failed to switch entity', err);
        } finally {
            setSwitching(false);
        }
    };

    const currentEntity = entities.find(e => e.is_primary);
    const otherEntities = entities.filter(e => !e.is_primary);

    if (loading) {
        return (
            <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Loading entities...</span>
            </div>
        );
    }

    if (entities.length === 0) {
        return null;
    }

    // If only one entity, just show it without dropdown
    if (entities.length === 1 && currentEntity) {
        return (
            <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg border">
                {currentEntity.logo_url ? (
                    <img
                        src={currentEntity.logo_url}
                        alt="Logo"
                        className="h-8 w-8 object-contain bg-white rounded border"
                    />
                ) : (
                    <div className="h-8 w-8 bg-primary/10 rounded flex items-center justify-center">
                        <Building2 className="h-4 w-4 text-primary" />
                    </div>
                )}
                <div>
                    <p className="font-medium text-sm">{currentEntity.legal_business_name}</p>
                    <p className="text-xs text-muted-foreground">
                        {currentEntity.document_count} documents
                    </p>
                </div>
                <Badge variant="outline" className="ml-auto text-green-600 border-green-500/30 bg-green-500/10">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Active
                </Badge>
            </div>
        );
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" className="w-full justify-between gap-2" disabled={switching}>
                    <div className="flex items-center gap-2">
                        {currentEntity?.logo_url ? (
                            <img
                                src={currentEntity.logo_url}
                                alt="Logo"
                                className="h-6 w-6 object-contain bg-white rounded"
                            />
                        ) : (
                            <Building2 className="h-4 w-4" />
                        )}
                        <span className="truncate max-w-[200px]">
                            {currentEntity?.legal_business_name || 'Select Entity'}
                        </span>
                        {currentEntity && (
                            <Badge variant="secondary" className="text-xs">
                                {currentEntity.document_count} docs
                            </Badge>
                        )}
                    </div>
                    {switching ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <ChevronDown className="h-4 w-4" />
                    )}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-80">
                <DropdownMenuLabel className="flex items-center justify-between">
                    <span>Switch Entity</span>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2"
                        onClick={(e) => {
                            e.preventDefault();
                            fetchEntityProfiles();
                        }}
                    >
                        <RefreshCw className="h-3 w-3" />
                    </Button>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />

                {/* Current Primary Entity */}
                {currentEntity && (
                    <>
                        <DropdownMenuItem
                            className="flex items-center gap-3 p-3 cursor-default"
                            disabled
                        >
                            <div className="flex items-center gap-3 flex-1">
                                {currentEntity.logo_url ? (
                                    <img
                                        src={currentEntity.logo_url}
                                        alt="Logo"
                                        className="h-8 w-8 object-contain bg-white rounded border"
                                    />
                                ) : (
                                    <div className="h-8 w-8 bg-green-100 rounded flex items-center justify-center">
                                        <Building2 className="h-4 w-4 text-green-600" />
                                    </div>
                                )}
                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-sm truncate">{currentEntity.legal_business_name}</p>
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                        <FileText className="h-3 w-3" />
                                        <span>{currentEntity.document_count} documents</span>
                                        {Object.keys(currentEntity.document_types).length > 0 && (
                                            <span className="text-muted-foreground/70">
                                                ({Object.entries(currentEntity.document_types).map(([k, v]) => `${v} ${k}`).join(', ')})
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <Badge className="bg-green-500 text-white shrink-0">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Active
                            </Badge>
                        </DropdownMenuItem>

                        {otherEntities.length > 0 && <DropdownMenuSeparator />}
                    </>
                )}

                {/* Other Entities */}
                {otherEntities.map((entity) => (
                    <DropdownMenuItem
                        key={entity.uei}
                        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-accent"
                        onClick={() => handleSwitch(entity)}
                    >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                            {entity.logo_url ? (
                                <img
                                    src={entity.logo_url}
                                    alt="Logo"
                                    className="h-8 w-8 object-contain bg-white rounded border"
                                />
                            ) : (
                                <div className="h-8 w-8 bg-muted rounded flex items-center justify-center">
                                    <Building2 className="h-4 w-4 text-muted-foreground" />
                                </div>
                            )}
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm truncate">{entity.legal_business_name}</p>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                    <FileText className="h-3 w-3" />
                                    <span>{entity.document_count} documents</span>
                                </div>
                            </div>
                        </div>
                        <Badge variant="outline" className="shrink-0">
                            Switch
                        </Badge>
                    </DropdownMenuItem>
                ))}

                {otherEntities.length === 0 && !currentEntity && (
                    <div className="p-4 text-center text-muted-foreground text-sm">
                        No entities configured. Search for your company on SAM.gov to get started.
                    </div>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
