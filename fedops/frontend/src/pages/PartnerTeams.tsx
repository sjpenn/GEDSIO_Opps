import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Loader2, Users, PieChart, Table as TableIcon, Plus, Edit, Trash2 } from 'lucide-react';
import { TeamBuilder } from "@/components/TeamBuilder";
import { VennDiagramView } from "@/components/VennDiagramView";
import { CapabilityMatrix } from "@/components/CapabilityMatrix";

interface Team {
  id: number;
  name: string;
  opportunity_id: number;
  members: {
    id: number;
    entity_uei: string;
    role: string;
    entity_name?: string;
    capabilities_contribution?: any;
  }[];
}

import { useSearchParams } from 'react-router-dom';

export default function PartnerTeamsPage() {
  const [searchParams] = useSearchParams();
  const opportunityIdParam = searchParams.get('opportunityId');
  const opportunityId = opportunityIdParam ? parseInt(opportunityIdParam) : 0;

  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [showBuilder, setShowBuilder] = useState(false);
  const [editingTeam, setEditingTeam] = useState<Team | null>(null);
  const [teamToDelete, setTeamToDelete] = useState<{ id: number; name: string } | null>(null);

  useEffect(() => {
    if (opportunityId) {
      fetchTeams();
    }
  }, [opportunityId]);

  useEffect(() => {
    if (selectedTeam) {
      fetchAnalysis(selectedTeam.id);
    }
  }, [selectedTeam]);

  const fetchTeams = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/teams/opportunity/${opportunityId}`);
      if (res.ok) {
        const data = await res.json();
        setTeams(data);
        if (data.length > 0 && !selectedTeam) {
          setSelectedTeam(data[0]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch teams", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalysis = async (teamId: number) => {
    setAnalysisLoading(true);
    try {
      const res = await fetch(`/api/v1/teams/${teamId}/analysis`);
      if (res.ok) {
        const data = await res.json();
        setAnalysis(data);
      }
    } catch (err) {
      console.error("Failed to fetch analysis", err);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleSaveTeam = async (teamData: { name: string, members: any[] }) => {
    try {
      const url = editingTeam ? `/api/v1/teams/${editingTeam.id}` : '/api/v1/teams/';
      const method = editingTeam ? 'PUT' : 'POST';
      
      const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          opportunity_id: opportunityId,
          ...teamData
        })
      });
      
      if (res.ok) {
        setShowBuilder(false);
        setEditingTeam(null);
        fetchTeams();
      } else {
        // Handle error response
        const errorData = await res.json().catch(() => ({ detail: 'Failed to save team' }));
        const errorMessage = errorData.detail || 'Failed to save team';
        alert(`Error: ${errorMessage}`);
      }
    } catch (err) {
      console.error("Failed to save team", err);
      alert("An unexpected error occurred while saving the team. Please try again.");
    }
  };

  const startEditing = (team: Team) => {
    setEditingTeam(team);
    setShowBuilder(true);
  };

  const handleDeleteTeam = async (teamId: number, teamName: string) => {
    console.log('Delete team clicked:', { teamId, teamName });
    setTeamToDelete({ id: teamId, name: teamName });
  };

  const confirmDelete = async () => {
    if (!teamToDelete) return;
    
    const { id: teamId, name: teamName } = teamToDelete;
    console.log('Confirming delete for:', { teamId, teamName });

    try {
      const res = await fetch(`/api/v1/teams/${teamId}`, {
        method: 'DELETE'
      });
      
      console.log('DELETE response status:', res.status, res.statusText);
      
      if (res.ok) {
        const data = await res.json();
        console.log('Delete successful:', data);
        
        // If deleted team was selected, clear selection
        if (selectedTeam?.id === teamId) {
          setSelectedTeam(null);
        }
        setTeamToDelete(null);
        fetchTeams();
      } else {
        const errorData = await res.json().catch(() => ({ detail: 'Failed to delete team' }));
        console.error('Delete failed:', errorData);
        alert(`Error: ${errorData.detail || 'Failed to delete team'}`);
        setTeamToDelete(null);
      }
    } catch (err) {
      console.error("Failed to delete team", err);
      alert("An unexpected error occurred while deleting the team. Please try again.");
      setTeamToDelete(null);
    }
  };

  return (
    <div className="space-y-6 p-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Partner Teams</h2>
          <p className="text-muted-foreground">Manage teaming arrangements and analyze capability coverage.</p>
        </div>
        {opportunityId > 0 && (
          <Button onClick={() => {
            setEditingTeam(null);
            setShowBuilder(!showBuilder);
          }}>
            {showBuilder ? "Cancel" : <><Plus className="h-4 w-4 mr-2" /> New Team</>}
          </Button>
        )}
      </div>

      {!opportunityId ? (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center text-muted-foreground">
            <Users className="h-12 w-12 mx-auto mb-4 opacity-20" />
            <h3 className="text-lg font-semibold mb-2">No Opportunity Selected</h3>
            <p>Please select an opportunity from the Opportunities page to build a team.</p>
            <Button variant="link" onClick={() => window.location.href = '/opportunities'}>
              Go to Opportunities
            </Button>
          </CardContent>
        </Card>
      ) : showBuilder ? (
        <Card>
          <CardHeader>
            <CardTitle>{editingTeam ? 'Edit Team' : 'Build New Team'}</CardTitle>
            <CardDescription>Select partners and assign roles for this opportunity.</CardDescription>
          </CardHeader>
          <CardContent>
            <TeamBuilder 
              opportunityId={opportunityId} 
              onSave={handleSaveTeam}
              initialTeamName={editingTeam?.name}
              initialMembers={editingTeam?.members.map(m => ({
                entity_uei: m.entity_uei,
                role: m.role as 'PRIME' | 'SUB',
                notes: '', // Add notes if available in TeamMember
                entity: undefined // Will be populated by TeamBuilder
              }))}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Team Selector */}
          <div className="lg:col-span-1 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Select Team</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {loading ? (
                  <div className="flex justify-center py-4"><Loader2 className="animate-spin" /></div>
                ) : teams.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">No teams created yet.</p>
                ) : (
                  teams.map(team => (
                    <div 
                      key={team.id}
                      className={`p-3 rounded-lg border transition-colors ${selectedTeam?.id === team.id ? 'bg-primary/10 border-primary' : 'hover:bg-accent'}`}
                    >
                      <div 
                        className="cursor-pointer"
                        onClick={() => setSelectedTeam(team)}
                      >
                        <div className="font-medium">{team.name}</div>
                        <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                          <Users className="h-3 w-3" /> {team.members.length} Members
                        </div>
                      </div>
                      <div className="flex items-center gap-1 mt-2 pt-2 border-t">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-7 text-xs flex-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditing(team);
                          }}
                        >
                          <Edit className="h-3 w-3 mr-1" />
                          Edit
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-7 text-xs text-destructive hover:text-destructive hover:bg-destructive/10"
                          onClick={(e) => {
                            e.stopPropagation();
                            e.preventDefault();
                            handleDeleteTeam(team.id, team.name);
                          }}
                        >
                          <Trash2 className="h-3 w-3 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Analysis View */}
          <div className="lg:col-span-3 space-y-6">
            {selectedTeam ? (
              <Tabs defaultValue="matrix">
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-semibold">{selectedTeam.name} Analysis</h3>
                    <Button variant="ghost" size="icon" onClick={() => startEditing(selectedTeam)}>
                      <Edit className="h-4 w-4" />
                    </Button>
                  </div>
                  <TabsList>
                    <TabsTrigger value="matrix"><TableIcon className="h-4 w-4 mr-2" /> Matrix</TabsTrigger>
                    <TabsTrigger value="venn"><PieChart className="h-4 w-4 mr-2" /> Venn</TabsTrigger>
                  </TabsList>
                </div>

                <TabsContent value="matrix" className="space-y-4">
                  {analysisLoading ? (
                    <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
                  ) : analysis ? (
                    <CapabilityMatrix 
                      requirements={analysis.gaps.concat(analysis.coverage_details.map((c: any) => c.requirement))}
                      teamMembers={selectedTeam.members.map(m => ({
                        name: m.entity_name || m.entity_uei,
                        role: m.role,
                        capabilities: [] // Populated in real app
                      }))}
                      coverage={analysis.coverage_details}
                    />
                  ) : (
                    <p className="text-muted-foreground">No analysis data available.</p>
                  )}
                </TabsContent>

                <TabsContent value="venn">
                  <VennDiagramView 
                    teamMembers={selectedTeam.members.map(m => ({
                      name: m.entity_name || m.entity_uei,
                      capabilities: [] 
                    }))}
                  />
                </TabsContent>
              </Tabs>
            ) : (
              <div className="flex flex-col items-center justify-center h-[400px] border-2 border-dashed rounded-lg text-muted-foreground">
                <Users className="h-12 w-12 mb-4 opacity-20" />
                <p>Select a team to view analysis</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {teamToDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setTeamToDelete(null)}>
          <Card className="w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <Trash2 className="h-5 w-5" />
                Confirm Delete
              </CardTitle>
              <CardDescription>
                This action cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                Are you sure you want to delete the team <strong>"{teamToDelete.name}"</strong>?
              </p>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setTeamToDelete(null)}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={confirmDelete}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Team
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
