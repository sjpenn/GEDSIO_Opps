"""
Contracting Officer extraction and management service.
Extracts CO data from SAM.gov opportunities and stores in local database.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.dialects.postgresql import insert
from fedops_core.db.models import ContractingOfficer, Opportunity
from datetime import datetime


def parse_name(full_name: str) -> tuple[Optional[str], Optional[str]]:
    """Parse a full name into first and last name."""
    if not full_name:
        return None, None
    
    parts = full_name.strip().split()
    if len(parts) == 0:
        return None, None
    elif len(parts) == 1:
        return None, parts[0]  # Assume it's a last name
    else:
        return parts[0], parts[-1]  # First and last


def extract_agency_from_opportunity(opp: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract agency info from opportunity data."""
    full_response = opp.get("full_response", {}) or {}
    
    # Try to get from fullParentPathName (e.g., "DEPT OF DEFENSE.DEPT OF THE NAVY.NAVSUP...")
    parent_path = full_response.get("fullParentPathName", "")
    if parent_path:
        parts = parent_path.split(".")
        agency = parts[0] if len(parts) > 0 else None
        sub_agency = parts[1] if len(parts) > 1 else None
        office = parts[-1] if len(parts) > 2 else None
        return agency, sub_agency, office
    
    return None, None, None


async def extract_cos_from_opportunity(
    db: AsyncSession,
    opp_id: int,
    point_of_contact: List[Dict[str, Any]],
    full_response: Optional[Dict[str, Any]] = None
) -> List[ContractingOfficer]:
    """
    Extract contracting officers from opportunity's point_of_contact field.
    Upserts into contracting_officers table.
    """
    if not point_of_contact:
        return []
    
    extracted_cos = []
    
    # Get agency info from opportunity
    agency, sub_agency, office = extract_agency_from_opportunity({"full_response": full_response})
    
    for poc in point_of_contact:
        full_name = poc.get("fullName")
        name = full_name.strip() if full_name else ""
        if not name or len(name) < 2:
            continue
        
        email_raw = poc.get("email")
        email = email_raw.strip() if email_raw else None
        phone_raw = poc.get("phone")
        phone = phone_raw.strip() if phone_raw else None
        title_raw = poc.get("title")
        title = title_raw.strip() if title_raw else None
        
        first_name, last_name = parse_name(name)
        
        # Try to find existing CO by email (most reliable) or by name+agency
        stmt = select(ContractingOfficer)
        if email:
            stmt = stmt.where(ContractingOfficer.email == email)
        else:
            stmt = stmt.where(
                ContractingOfficer.name == name,
                ContractingOfficer.agency == agency
            )
        
        result = await db.execute(stmt)
        existing_co = result.scalar_one_or_none()
        
        if existing_co:
            # Update existing CO
            existing_co.last_seen_at = datetime.utcnow()
            existing_co.opportunity_count = (existing_co.opportunity_count or 0) + 1
            if opp_id not in (existing_co.opportunity_ids or []):
                existing_co.opportunity_ids = (existing_co.opportunity_ids or []) + [opp_id]
            if phone and not existing_co.phone:
                existing_co.phone = phone
            if title and not existing_co.title:
                existing_co.title = title
            extracted_cos.append(existing_co)
        else:
            # Create new CO
            new_co = ContractingOfficer(
                name=name,
                email=email,
                phone=phone,
                title=title,
                agency=agency,
                sub_agency=sub_agency,
                office=office,
                first_name=first_name,
                last_name=last_name,
                opportunity_count=1,
                opportunity_ids=[opp_id],
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow()
            )
            db.add(new_co)
            extracted_cos.append(new_co)
    
    await db.commit()
    return extracted_cos


async def search_cos_local(
    db: AsyncSession,
    query: str,
    limit: int = 20
) -> List[ContractingOfficer]:
    """
    Search contracting officers in local database.
    Supports fuzzy matching on name, email, and agency.
    """
    query = query.strip().lower()
    
    stmt = select(ContractingOfficer).where(
        or_(
            func.lower(ContractingOfficer.name).contains(query),
            func.lower(ContractingOfficer.last_name).contains(query),
            func.lower(ContractingOfficer.first_name).contains(query),
            func.lower(ContractingOfficer.email).contains(query),
            func.lower(ContractingOfficer.agency).contains(query),
            func.lower(ContractingOfficer.office).contains(query)
        )
    ).order_by(
        ContractingOfficer.opportunity_count.desc()
    ).limit(limit)
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def backfill_cos_from_opportunities(db: AsyncSession) -> int:
    """
    Backfill contracting_officers table from existing opportunities.
    Returns count of COs extracted.
    """
    stmt = select(Opportunity).where(
        Opportunity.point_of_contact.isnot(None)
    )
    result = await db.execute(stmt)
    opportunities = result.scalars().all()
    
    total_extracted = 0
    for opp in opportunities:
        if opp.point_of_contact:
            cos = await extract_cos_from_opportunity(
                db,
                opp.id,
                opp.point_of_contact,
                opp.full_response
            )
            total_extracted += len(cos)
    
    return total_extracted
