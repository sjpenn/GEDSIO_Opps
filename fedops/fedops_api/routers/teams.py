from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from fedops_core.db.engine import get_db
from fedops_core.db.team_models import OpportunityTeam, TeamMember
from fedops_core.db.models import Entity
from fedops_core.services.partner_service import PartnerService

router = APIRouter()

# Schemas
class TeamMemberCreate(BaseModel):
    entity_uei: str
    role: str = "SUB"  # PRIME or SUB
    notes: Optional[str] = None

class TeamMemberResponse(TeamMemberCreate):
    id: int
    team_id: int
    capabilities_contribution: Optional[Dict[str, Any]] = None
    entity_name: Optional[str] = None # Enriched field

    class Config:
        from_attributes = True

class TeamCreate(BaseModel):
    opportunity_id: int
    name: str
    description: Optional[str] = None
    members: List[TeamMemberCreate] = []

class TeamResponse(BaseModel):
    id: int
    opportunity_id: int
    name: str
    description: Optional[str] = None
    members: List[TeamMemberResponse] = []
    
    class Config:
        from_attributes = True

class GapAnalysisResponse(BaseModel):
    total_requirements: int
    covered_count: int
    uncovered_count: int
    coverage_percentage: float
    coverage_details: List[Dict[str, Any]]
    gaps: List[str]


@router.post("/", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new team for an opportunity"""
    # Check for duplicate team name for this opportunity
    existing_team_result = await db.execute(
        select(OpportunityTeam).where(
            OpportunityTeam.opportunity_id == team_data.opportunity_id,
            OpportunityTeam.name == team_data.name
        )
    )
    existing_team = existing_team_result.scalar_one_or_none()
    
    if existing_team:
        raise HTTPException(
            status_code=400, 
            detail=f"A team named '{team_data.name}' already exists for this opportunity. Please use a different name or update the existing team."
        )
    
    # Create team
    team = OpportunityTeam(
        opportunity_id=team_data.opportunity_id,
        name=team_data.name,
        description=team_data.description
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)
    
    # Add members
    for member_data in team_data.members:
        member = TeamMember(
            team_id=team.id,
            entity_uei=member_data.entity_uei,
            role=member_data.role,
            notes=member_data.notes
        )
        db.add(member)
    
    await db.commit()
    await db.refresh(team)
    
    # Re-fetch with members to ensure relationships are loaded
    # (Or rely on lazy loading if configured, but explicit is better with async)
    result = await db.execute(
        select(OpportunityTeam).where(OpportunityTeam.id == team.id)
    )
    team = result.scalars().first()
    
    # Manually populate members if relationship not eager loaded?
    # SQLAlchemy async relationship loading can be tricky.
    # Let's fetch members explicitly to construct response if needed, 
    # but Pydantic from_attributes should handle it if relationship is loaded.
    # We might need select(OpportunityTeam).options(selectinload(OpportunityTeam.members))
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(OpportunityTeam)
        .options(selectinload(OpportunityTeam.members))
        .where(OpportunityTeam.id == team.id)
    )
    team = result.scalars().first()
    
    team = result.scalars().first()
    
    return team

class TeamUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    members: List[TeamMemberCreate] = []

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing team"""
    # Get existing team
    result = await db.execute(select(OpportunityTeam).where(OpportunityTeam.id == team_id))
    team = result.scalars().first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    # Update fields
    team.name = team_data.name
    team.description = team_data.description
    
    # Update members (Full sync: delete existing, add new)
    # First, delete existing members
    await db.execute(delete(TeamMember).where(TeamMember.team_id == team_id))
    
    # Add new members
    for member_data in team_data.members:
        member = TeamMember(
            team_id=team.id,
            entity_uei=member_data.entity_uei,
            role=member_data.role,
            notes=member_data.notes
        )
        db.add(member)
        
    await db.commit()
    await db.refresh(team)
    
    # Re-fetch with members
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(OpportunityTeam)
        .options(selectinload(OpportunityTeam.members))
        .where(OpportunityTeam.id == team.id)
    )
    team = result.scalars().first()
    
    # Enrich members
    for member in team.members:
        entity_res = await db.execute(select(Entity).where(Entity.uei == member.entity_uei))
        entity = entity_res.scalars().first()
        if entity:
            member.entity_name = entity.legal_business_name
            
    return team

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get team details"""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(OpportunityTeam)
        .options(selectinload(OpportunityTeam.members))
        .where(OpportunityTeam.id == team_id)
    )
    team = result.scalars().first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    # Enrich members with entity names
    # This might be better done in a service or with a join
    for member in team.members:
        entity_res = await db.execute(select(Entity).where(Entity.uei == member.entity_uei))
        entity = entity_res.scalars().first()
        if entity:
            # We can't modify the ORM object directly if it's not a mapped column easily
            # But we can attach it for Pydantic if we use a dict or modify the schema to accept it
            member.entity_name = entity.legal_business_name
            
    return team

@router.post("/{team_id}/members", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: int,
    member_data: TeamMemberCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a member to the team"""
    member = TeamMember(
        team_id=team_id,
        entity_uei=member_data.entity_uei,
        role=member_data.role,
        notes=member_data.notes
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    
    # Fetch entity name
    entity_res = await db.execute(select(Entity).where(Entity.uei == member.entity_uei))
    entity = entity_res.scalars().first()
    if entity:
        member.entity_name = entity.legal_business_name
        
    return member

@router.delete("/{team_id}")
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an entire team"""
    print(f"[DELETE_TEAM] Attempting to delete team ID: {team_id}")
    
    result = await db.execute(select(OpportunityTeam).where(OpportunityTeam.id == team_id))
    team = result.scalars().first()
    
    if not team:
        print(f"[DELETE_TEAM] Team ID {team_id} not found")
        raise HTTPException(status_code=404, detail="Team not found")
    
    team_name = team.name
    print(f"[DELETE_TEAM] Found team: {team_name} (ID: {team_id})")
    
    await db.delete(team)
    await db.commit()
    
    print(f"[DELETE_TEAM] Successfully deleted team: {team_name}")
    return {"status": "success", "message": f"Team '{team_name}' deleted successfully"}

@router.delete("/{team_id}/members/{member_id}")
async def remove_team_member(
    team_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove a member from the team"""
    result = await db.execute(select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team_id))
    member = result.scalars().first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    await db.delete(member)
    await db.commit()
    return {"status": "success"}

@router.get("/{team_id}/analysis", response_model=GapAnalysisResponse)
async def get_team_analysis(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get capability gap analysis for the team"""
    result = await db.execute(select(OpportunityTeam).where(OpportunityTeam.id == team_id))
    team = result.scalars().first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    service = PartnerService(db)
    analysis = await service.analyze_capability_gaps(team_id, team.opportunity_id)
    
    return analysis

@router.get("/opportunity/{opp_id}", response_model=List[TeamResponse])
async def get_opportunity_teams(
    opp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all teams for an opportunity"""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(OpportunityTeam)
        .options(selectinload(OpportunityTeam.members))
        .where(OpportunityTeam.opportunity_id == opp_id)
    )
    teams = result.scalars().all()
    
    # Enrich members
    for team in teams:
        for member in team.members:
            entity_res = await db.execute(select(Entity).where(Entity.uei == member.entity_uei))
            entity = entity_res.scalars().first()
            if entity:
                member.entity_name = entity.legal_business_name
                
    return teams
