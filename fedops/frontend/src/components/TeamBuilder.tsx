import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Trash2, Users, GripVertical, AlertCircle } from 'lucide-react';
import type { Entity } from '../types';
import { DndContext, DragOverlay, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';

interface TeamMember {
  entity_uei: string;
  role: 'PRIME' | 'SUB';
  notes?: string;
  entity?: Entity; // Enriched data
}

interface TeamBuilderProps {
  opportunityId: number;
  onSave: (team: { name: string, members: TeamMember[] }) => void;
  initialMembers?: TeamMember[];
  initialTeamName?: string;
}

export function TeamBuilder({ opportunityId: _opportunityId, onSave, initialMembers = [], initialTeamName = '' }: TeamBuilderProps) {
  const [teamName, setTeamName] = useState(initialTeamName);
  const [members, setMembers] = useState<TeamMember[]>(initialMembers);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Entity[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [partnerEntities, setPartnerEntities] = useState<Entity[]>([]);
  const [loadingPartners, setLoadingPartners] = useState(false);
  const [activeDragId, setActiveDragId] = useState<string | null>(null);
  const [primaryEntity, setPrimaryEntity] = useState<Entity | null>(null);

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  // Fetch partner entities and primary entity on mount
  useEffect(() => {
    fetchPartnerEntities();
    fetchPrimaryEntity();
  }, []);

  // Enrich members with entity data once partners are loaded
  useEffect(() => {
    if (partnerEntities.length > 0 && members.length > 0) {
      setMembers(prev => prev.map(m => {
        if (!m.entity) {
          const entity = partnerEntities.find(p => p.uei === m.entity_uei);
          return entity ? { ...m, entity } : m;
        }
        return m;
      }));
    }
  }, [partnerEntities.length]); // Only run when partners loaded

  const fetchPartnerEntities = async () => {
    setLoadingPartners(true);
    try {
      const response = await fetch('/api/v1/entities/partners');
      if (response.ok) {
        const data = await response.json();
        setPartnerEntities(data);
      }
    } catch (error) {
      console.error("Failed to fetch partner entities", error);
    } finally {
      setLoadingPartners(false);
    }
  };

  const fetchPrimaryEntity = async () => {
    try {
      const response = await fetch('/api/v1/entities/primary');
      if (response.ok) {
        const data = await response.json();
        setPrimaryEntity(data);
      }
    } catch (error) {
      console.error("Failed to fetch primary entity", error);
    }
  };

  // Ensure primary entity is always in members
  useEffect(() => {
    if (primaryEntity && !members.some(m => m.entity_uei === primaryEntity.uei)) {
      // Primary entity not in team, add it
      setMembers(prev => [{
        entity_uei: primaryEntity.uei,
        role: prev.length === 0 ? 'PRIME' : 'SUB', // PRIME if first, otherwise SUB
        entity: primaryEntity
      }, ...prev]);
    }
  }, [primaryEntity, members.length]); // Re-check when primaryEntity loads or members count changes

  // Mock search function (replace with API call)
  const searchEntities = async (query: string) => {
    if (query.length < 3) return;
    setIsSearching(true);
    try {
      const response = await fetch(`/api/v1/entities/search?q=${query}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data);
      }
    } catch (error) {
      console.error("Search failed", error);
    } finally {
      setIsSearching(false);
    }
  };

  const addMember = (entity: Entity) => {
    if (members.some(m => m.entity_uei === entity.uei)) return;
    
    setMembers([...members, {
      entity_uei: entity.uei,
      role: members.length === 0 ? 'PRIME' : 'SUB', // Default first to Prime
      entity: entity
    }]);
    setSearchQuery('');
    setSearchResults([]);
  };

  const removeMember = (uei: string) => {
    // Prevent removal of primary entity
    if (primaryEntity && uei === primaryEntity.uei) {
      return; // Silently ignore removal of primary entity
    }
    setMembers(members.filter(m => m.entity_uei !== uei));
  };

  const updateRole = (uei: string, role: 'PRIME' | 'SUB') => {
    setMembers(members.map(m => m.entity_uei === uei ? { ...m, role } : m));
  };

  const handleSave = () => {
    if (!teamName) return;
    onSave({ name: teamName, members });
  };

  // Drag and drop handlers
  const handleDragStart = (event: any) => {
    setActiveDragId(event.active.id);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveDragId(null);

    if (!over || over.id !== 'team-dropzone') return;

    // Find the entity being dragged
    const entityUei = active.id as string;
    const entity = partnerEntities.find(e => e.uei === entityUei);

    if (entity) {
      addMember(entity);
    }
  };

  const handleDragCancel = () => {
    setActiveDragId(null);
  };

  // Check if entity is already in team
  const isInTeam = (uei: string) => members.some(m => m.entity_uei === uei);

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="space-y-6">
        <div className="flex items-end gap-4">
          <div className="flex-1 space-y-2">
            <label className="text-sm font-medium">Team Name</label>
            <Input 
              placeholder="e.g. IBM-Acme Joint Venture" 
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
            />
          </div>
          <Button onClick={handleSave} disabled={!teamName || members.length === 0}>
            Save Team
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Partner Entities List (Draggable) */}
          <Card className="border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Users className="h-5 w-5" /> Partner Entities
              </CardTitle>
              <CardDescription>Drag partners to add to team</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {loadingPartners ? (
                <div className="text-center py-8 text-muted-foreground">
                  Loading partners...
                </div>
              ) : partnerEntities.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No partner entities found.</p>
                  <p className="text-xs mt-1">Mark entities as "PARTNER" in Entity Search.</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {partnerEntities.map((entity) => (
                    <DraggablePartnerCard
                      key={entity.uei}
                      entity={entity}
                      isInTeam={isInTeam(entity.uei)}
                      isDragging={activeDragId === entity.uei}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Team Members List (Drop Zone) */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" /> Team Composition
              </CardTitle>
              <CardDescription>Manage team members and roles</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <DroppableTeamArea
                members={members}
                updateRole={updateRole}
                removeMember={removeMember}
                isOver={activeDragId !== null}
                primaryEntity={primaryEntity}
              />
            </CardContent>
          </Card>

          {/* Partner Search */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" /> Add Partners
              </CardTitle>
              <CardDescription>Search SAM.gov entities</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input 
                  placeholder="Search by name or UEI..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && searchEntities(searchQuery)}
                />
                <Button size="icon" onClick={() => searchEntities(searchQuery)} disabled={isSearching}>
                  <Search className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {searchResults.map((entity) => (
                  <div key={entity.uei} className="p-3 border rounded-lg hover:bg-accent cursor-pointer transition-colors" onClick={() => addMember(entity)}>
                    <div className="font-medium text-sm">{entity.legal_business_name}</div>
                    <div className="flex items-center justify-between mt-1">
                      <Badge variant="outline" className="text-[10px]">{entity.uei}</Badge>
                      {members.some(m => m.entity_uei === entity.uei) && (
                        <Badge variant="secondary" className="text-[10px]">Added</Badge>
                      )}
                    </div>
                  </div>
                ))}
                {searchResults.length === 0 && searchQuery && !isSearching && (
                  <div className="text-sm text-muted-foreground text-center py-4">
                    No results found
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <DragOverlay>
        {activeDragId ? (
          <DragOverlayCard entity={partnerEntities.find(e => e.uei === activeDragId)!} />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

// Draggable Partner Card Component
function DraggablePartnerCard({ entity, isInTeam, isDragging }: { entity: Entity; isInTeam: boolean; isDragging: boolean }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: entity.uei,
    disabled: isInTeam,
  });

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    opacity: isDragging ? 0.5 : 1,
    touchAction: 'none',
  } : { 
    opacity: isDragging ? 0.5 : 1,
    touchAction: 'none',
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`p-3 border rounded-lg transition-all ${
        isInTeam 
          ? 'bg-muted/50 opacity-50 cursor-not-allowed' 
          : 'hover:bg-accent hover:shadow-md cursor-grab active:cursor-grabbing'
      }`}
      {...attributes}
      {...listeners}
    >
      <div className="flex items-center gap-2">
        <GripVertical className={`h-4 w-4 ${isInTeam ? 'text-muted-foreground' : 'text-muted-foreground/50'}`} />
        <div className="flex-1">
          <div className="font-medium text-sm">{entity.legal_business_name}</div>
          <div className="flex items-center justify-between mt-1">
            <Badge variant="outline" className="text-[10px]">{entity.uei}</Badge>
            {isInTeam && (
              <Badge variant="secondary" className="text-[10px]">In Team</Badge>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


// Droppable Team Area Component
function DroppableTeamArea({ 
  members, 
  updateRole, 
  removeMember,
  isOver,
  primaryEntity
}: { 
  members: TeamMember[]; 
  updateRole: (uei: string, role: 'PRIME' | 'SUB') => void;
  removeMember: (uei: string) => void;
  isOver: boolean;
  primaryEntity: Entity | null;
}) {
  const { setNodeRef } = useDroppable({
    id: 'team-dropzone',
  });

  const isPrimaryEntity = (uei: string) => primaryEntity?.uei === uei;

  return (
    <div
      ref={setNodeRef}
      className={`min-h-[300px] transition-all ${
        isOver 
          ? 'border-2 border-dashed border-primary bg-primary/5 rounded-lg' 
          : 'border-2 border-transparent'
      }`}
    >
      {members.length === 0 ? (
        <div className={`text-center py-12 border-2 border-dashed rounded-lg transition-colors ${
          isOver ? 'border-primary bg-primary/10' : 'border-muted-foreground/25'
        }`}>
          <Users className="h-8 w-8 mx-auto mb-2 opacity-20" />
          <p className="text-muted-foreground">
            {isOver ? 'Drop here to add to team' : 'Drag partners here or search to add'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {members.map((member) => {
            const isPrimary = isPrimaryEntity(member.entity_uei);
            return (
              <div key={member.entity_uei} className={`flex items-center justify-between p-3 border rounded-lg ${isPrimary ? 'bg-primary/5 border-primary/30' : 'bg-card'}`}>
                <div className="flex items-center gap-3">
                  <div className={`h-10 w-10 rounded flex items-center justify-center font-bold ${isPrimary ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>
                    {member.entity?.legal_business_name?.substring(0, 2) || '??'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <div className="font-medium">{member.entity?.legal_business_name || member.entity_uei}</div>
                      {isPrimary && (
                        <Badge variant="default" className="text-[10px]">Your Company</Badge>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">UEI: {member.entity_uei}</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <Select 
                    value={member.role} 
                    onValueChange={(val: 'PRIME' | 'SUB') => updateRole(member.entity_uei, val)}
                  >
                    <SelectTrigger className="w-[100px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PRIME">Prime</SelectItem>
                      <SelectItem value="SUB">Sub</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => removeMember(member.entity_uei)}
                    disabled={isPrimary}
                    title={isPrimary ? "Cannot remove your company from team" : "Remove from team"}
                  >
                    <Trash2 className={`h-4 w-4 ${isPrimary ? 'text-muted-foreground' : 'text-destructive'}`} />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Drag Overlay Card Component
function DragOverlayCard({ entity }: { entity: Entity }) {
  return (
    <div className="p-3 border-2 border-primary rounded-lg bg-card shadow-lg">
      <div className="flex items-center gap-2">
        <GripVertical className="h-4 w-4 text-primary" />
        <div>
          <div className="font-medium text-sm">{entity.legal_business_name}</div>
          <Badge variant="outline" className="text-[10px] mt-1">{entity.uei}</Badge>
        </div>
      </div>
    </div>
  );
}

// Import the hooks from dnd-kit
import { useDraggable, useDroppable } from '@dnd-kit/core';
