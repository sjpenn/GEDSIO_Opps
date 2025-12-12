import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from fedops_core.db.models import Entity, EntityAward, Opportunity
from fedops_sources.usaspending import USASpendingClient
from fedops_core.db.engine import AsyncSessionLocal

logger = logging.getLogger(__name__)

class EntityEnrichmentService:
    def __init__(self):
        self.usaspending = USASpendingClient()

    async def enrich_entity(self, uei: str):
        """
        Background task to enrich an entity with:
        1. Prime Awards (USASpending)
        2. Sub Awards (USASpending)
        3. Linked Opportunities/Solicitations (SAM.gov via existing data or search)
        """
        logger.info(f"Starting enrichment for entity {uei}")
        
        async with AsyncSessionLocal() as db:
            # 1. Verify Entity exists
            result = await db.execute(select(Entity).where(Entity.uei == uei))
            entity = result.scalars().first()
            if not entity:
                logger.error(f"Entity {uei} not found for enrichment")
                return

            # 2. Fetch Awards
            await self._fetch_and_store_awards(db, uei)
            
            # 3. Link Opportunities (SOWs)
            # This is implicitly done if we can match solicitation IDs, 
            # but we might want to trigger a search for missing ones here.
            await self._link_opportunities(db, uei)
            
            entity.last_synced_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Completed enrichment for entity {uei}")

    async def _fetch_and_store_awards(self, db: AsyncSession, uei: str):
        """Fetch prime and sub awards and store them"""
        try:
            # Prime Awards
            prime_awards = await self.usaspending.get_awards_by_uei(uei)
            for award_data in prime_awards:
                await self._store_award(db, uei, award_data, is_prime=True)
            
            # Sub Awards
            sub_awards = await self.usaspending.get_subawards_by_uei(uei)
            for award_data in sub_awards:
                await self._store_award(db, uei, award_data, is_prime=False)
                
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error fetching awards for {uei}: {e}")
            await db.rollback()

    async def _store_award(self, db: AsyncSession, uei: str, data: dict, is_prime: bool):
        """Parse and store a single award"""
        try:
            if is_prime:
                award_id = data.get("Award ID")
                # Skip if no ID
                if not award_id: return

                # Check existence
                existing = await db.get(EntityAward, award_id)
                if existing: return # Skip update for now, just ingest new

                award = EntityAward(
                    award_id=award_id,
                    recipient_uei=uei,
                    total_obligation=float(data.get("Total Obligation") or 0),
                    description=data.get("Description"),
                    award_date=self._parse_date(data.get("Start Date")),
                    awarding_agency=data.get("Awarding Agency"),
                    naics_code=data.get("NAICS Code"),
                    solicitation_id=data.get("Solicitation ID"),
                    award_type="Prime"
                )
            else:
                award_id = data.get("Sub-Award ID")
                if not award_id: return
                
                existing = await db.get(EntityAward, award_id)
                if existing: return

                award = EntityAward(
                    award_id=award_id,
                    recipient_uei=uei,
                    # For subawards, amount is "Sub-Award Amount"
                    total_obligation=float(data.get("Sub-Award Amount") or 0),
                    description=data.get("Sub-Award Description"),
                    award_date=self._parse_date(data.get("Sub-Award Date")),
                    awarding_agency=data.get("Awarding Agency"),
                    # Sub-awards might not have simpler NAICS/Solicitation fields in the same way
                    solicitation_id=data.get("Prime Award Solicitation ID"), 
                    award_type="Sub"
                )

            db.add(award)
            # We flush per item or batch? Safe to just add and commit at end of batch in caller.
        except Exception as e:
            logger.warning(f"Failed to parse/store award {data.get('Award ID')}: {e}")

    async def _link_opportunities(self, db: AsyncSession, uei: str):
        """
        Try to find Opportunities for the newly added awards.
        If we have a solicitation ID, check if we have the Opportunity.
        If not, we could technically trigger a SAM.gov scan for it, 
        but that might be heavy. For now, let's just log or tag.
        """
        # Get awards with solicitation IDs
        stmt = select(EntityAward).where(
            EntityAward.recipient_uei == uei,
            EntityAward.solicitation_id.isnot(None)
        )
        result = await db.execute(stmt)
        awards = result.scalars().all()
        
        for award in awards:
            sol_id = award.solicitation_id
            # Clean it up? Sometimes headers have dashes
            
            # Check if we have an Opportunity with this solicitation number
            # Note: Opportunity table has `solicitation_number`, and `notice_id`.
            # Solicitation ID from USASpending usually matches `solicitation_number` in SAM.
            
            opp_stmt = select(Opportunity).where(Opportunity.solicitation_number == sol_id)
            opp_result = await db.execute(opp_stmt)
            opp = opp_result.scalars().first()
            
            if opp:
                # We found a match! 
                # We could link them formally if we had a relation, 
                # but currently EntityAward just stores the ID string.
                # Maybe we update the Award description to say "Linked to Opportunity X" ?
                # Or simply simpler: we have the data.
                pass
            else:
                # TODO: Queue a search for this solicitation ID on SAM.gov?
                pass

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str: return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return None

entity_enrichment_service = EntityEnrichmentService()
