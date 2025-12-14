"""
Past Performance Service
Handles business logic for past performance questionnaires including
CRUD operations, AI content generation, and structured output export.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime

from fedops_core.db.models import PastPerformance, Entity, EntityAward, Opportunity
from fedops_core.schemas.past_performance_schemas import (
    PastPerformanceCreate,
    PastPerformanceUpdate,
    GenerateSectionRequest,
    QuestionnaireTemplate
)
from fedops_core.services.perplexity_service import perplexity_service


class PastPerformanceService:
    """Service for managing past performance questionnaires"""
    
    @staticmethod
    async def create_past_performance(
        db: AsyncSession,
        data: PastPerformanceCreate
    ) -> PastPerformance:
        """Create a new past performance questionnaire"""
        # Verify entity exists
        result = await db.execute(select(Entity).where(Entity.uei == data.entity_uei))
        entity = result.scalars().first()
        if not entity:
            raise ValueError(f"Entity with UEI {data.entity_uei} not found")
        
        # Verify award exists if provided
        if data.award_id:
            result = await db.execute(select(EntityAward).where(EntityAward.award_id == data.award_id))
            award = result.scalars().first()
            if not award:
                raise ValueError(f"Award with ID {data.award_id} not found")
        
        # Verify opportunity exists if provided
        if data.opportunity_id:
            result = await db.execute(select(Opportunity).where(Opportunity.id == data.opportunity_id))
            opp = result.scalars().first()
            if not opp:
                raise ValueError(f"Opportunity with ID {data.opportunity_id} not found")
        
        # Create past performance with default questionnaire structure
        past_perf = PastPerformance(
            entity_uei=data.entity_uei,
            award_id=data.award_id,
            opportunity_id=data.opportunity_id,
            title=data.title,
            created_by=data.created_by,
            questionnaire_data={
                "project_overview": {"content": "", "generated": False},
                "scope_of_work": {"content": "", "generated": False},
                "technical_approach": {"content": "", "generated": False},
                "challenges_solutions": {"content": "", "generated": False},
                "results_outcomes": {"content": "", "generated": False},
                "relevance": {"content": "", "generated": False},
                "references": {"content": "", "generated": False}
            }
        )
        
        db.add(past_perf)
        await db.commit()
        await db.refresh(past_perf)
        
        return past_perf
    
    @staticmethod
    async def get_past_performance(
        db: AsyncSession,
        past_perf_id: int
    ) -> Optional[PastPerformance]:
        """Get a specific past performance by ID"""
        result = await db.execute(
            select(PastPerformance).where(PastPerformance.id == past_perf_id)
        )
        return result.scalars().first()
    
    @staticmethod
    async def list_by_entity(
        db: AsyncSession,
        entity_uei: str,
        status: Optional[str] = None
    ) -> List[PastPerformance]:
        """List all past performances for an entity"""
        query = select(PastPerformance).where(PastPerformance.entity_uei == entity_uei)
        
        if status:
            query = query.where(PastPerformance.status == status)
        
        query = query.order_by(desc(PastPerformance.created_at))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def list_all(
        db: AsyncSession,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[PastPerformance]:
        """List all past performances with optional filtering"""
        query = select(PastPerformance)
        
        if status:
            query = query.where(PastPerformance.status == status)
        
        query = query.order_by(desc(PastPerformance.created_at)).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_past_performance(
        db: AsyncSession,
        past_perf_id: int,
        data: PastPerformanceUpdate
    ) -> Optional[PastPerformance]:
        """Update an existing past performance"""
        result = await db.execute(
            select(PastPerformance).where(PastPerformance.id == past_perf_id)
        )
        past_perf = result.scalars().first()
        
        if not past_perf:
            return None
        
        # Update fields
        if data.title is not None:
            past_perf.title = data.title
        
        if data.status is not None:
            past_perf.status = data.status
        
        if data.questionnaire_data is not None:
            past_perf.questionnaire_data = data.questionnaire_data
        
        if data.approved_by is not None:
            past_perf.approved_by = data.approved_by
        
        if data.approved_at is not None:
            past_perf.approved_at = data.approved_at
        
        past_perf.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(past_perf)
        
        return past_perf
    
    @staticmethod
    async def delete_past_performance(
        db: AsyncSession,
        past_perf_id: int
    ) -> bool:
        """Delete a past performance"""
        result = await db.execute(
            select(PastPerformance).where(PastPerformance.id == past_perf_id)
        )
        past_perf = result.scalars().first()
        
        if not past_perf:
            return False
        
        await db.delete(past_perf)
        await db.commit()
        
        return True
    
    @staticmethod
    async def generate_section_content(
        db: AsyncSession,
        past_perf_id: int,
        request: GenerateSectionRequest
    ) -> Dict[str, Any]:
        """Generate AI content for a specific questionnaire section"""
        # Get past performance
        result = await db.execute(
            select(PastPerformance).where(PastPerformance.id == past_perf_id)
        )
        past_perf = result.scalars().first()
        
        if not past_perf:
            raise ValueError(f"Past performance with ID {past_perf_id} not found")
        
        # Validate section name
        valid_sections = [
            "project_overview", "scope_of_work", "technical_approach",
            "challenges_solutions", "results_outcomes", "relevance", "references"
        ]
        if request.section_name not in valid_sections:
            raise ValueError(f"Invalid section name. Must be one of: {', '.join(valid_sections)}")
        
        # Check if content already exists and force_regenerate is False
        current_section = past_perf.questionnaire_data.get(request.section_name, {})
        if current_section.get("content") and not request.force_regenerate:
            raise ValueError(f"Section '{request.section_name}' already has content. Set force_regenerate=true to override.")
        
        # Get entity and award data for context
        entity_result = await db.execute(select(Entity).where(Entity.uei == past_perf.entity_uei))
        entity = entity_result.scalars().first()
        
        award = None
        if past_perf.award_id:
            award_result = await db.execute(select(EntityAward).where(EntityAward.award_id == past_perf.award_id))
            award = award_result.scalars().first()
        
        opportunity = None
        if past_perf.opportunity_id:
            opp_result = await db.execute(select(Opportunity).where(Opportunity.id == past_perf.opportunity_id))
            opportunity = opp_result.scalars().first()
        
        # Build context for AI generation
        context = await PastPerformanceService._build_generation_context(
            entity=entity,
            award=award,
            opportunity=opportunity,
            section_name=request.section_name,
            additional_context=request.context
        )
        
        # Generator switching logic: Use Perplexity for research, AIService for static content
        # For now, keeping Perplexity as requested in original implementation, 
        # but adding TODO for future switch.
        
        # Generate content using Perplexity service
        generated_content = await perplexity_service.generate_past_performance_section(
            section_name=request.section_name,
            context=context
        )
        
        # Update questionnaire data
        questionnaire_data = past_perf.questionnaire_data.copy()
        questionnaire_data[request.section_name] = {
            "content": generated_content,
            "generated": True,
            "last_generated_at": datetime.utcnow().isoformat(),
            "model_used": perplexity_service.DEFAULT_MODEL
        }
        
        past_perf.questionnaire_data = questionnaire_data
        past_perf.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(past_perf)
        
        return {
            "section_name": request.section_name,
            "content": generated_content,
            "generated": True,
            "model_used": perplexity_service.DEFAULT_MODEL,
            "generated_at": datetime.utcnow()
        }

    @staticmethod
    async def generate_from_document(
        db: AsyncSession,
        doc_id: int,
        ai_service: Any  # Typed as Any to avoid circular import, assumed to be AIService instance
    ) -> PastPerformance:
        """
        Generate a full Past Performance record from an uploaded CompanyProfileDocument.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        from fedops_core.db.models import CompanyProfileDocument
        
        logger.info(f"generate_from_document called with doc_id={doc_id}")
        
        # Fetch the document
        result = await db.execute(select(CompanyProfileDocument).where(CompanyProfileDocument.id == doc_id))
        doc = result.scalars().first()
        
        if not doc:
            logger.error(f"Document with ID {doc_id} not found")
            raise ValueError(f"Document with ID {doc_id} not found")
        
        logger.info(f"Found document: title={doc.title}, company_uei={doc.company_uei}")
        
        if not doc.parsed_content:
            logger.error(f"Document {doc_id} has no parsed content")
            raise ValueError(f"Document {doc_id} has no parsed content. Please ensure it is processed first.")
            
        # Get Company Entity via UEI
        # IMPORTANT: This logic must match the logic in get_company_profile endpoint
        # to ensure generated PPs are queryable by the same UEI used for fetching.
        from fedops_core.db.models import CompanyProfile
        company_result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == doc.company_uei))
        company = company_result.scalars().first()
        
        logger.info(f"Company lookup: found={company is not None}, entity_uei={company.entity_uei if company else 'N/A'}")
        
        # Use the same UEI resolution as get_company_profile:
        # If company has entity_uei set, use that; otherwise use the company's own UEI
        entity_uei = company.entity_uei if (company and company.entity_uei) else doc.company_uei
        
        logger.info(f"Resolved entity_uei={entity_uei}")
        
        # Verify the entity exists in the database
        entity_check = await db.execute(select(Entity).where(Entity.uei == entity_uei))
        entity = entity_check.scalars().first()
        if not entity:
            logger.error(f"Entity with UEI {entity_uei} not found in database")
            raise ValueError(f"Entity with UEI {entity_uei} not found. Please ensure the entity is registered in the system.")


        # Prompt for extraction
        prompt = f"""
        You are an expert Government Contracting Proposal Manager.
        Analyze the following document text and extract standardized Past Performance information.
        
        Return a valid JSON object with the following keys:
        - title: A professional title for this project (e.g. "Cybersecurity Support for DHS")
        - project_overview: Brief summary of the engagement.
        - scope_of_work: Detailed bullet points of tasks performed.
        - technical_approach: Tools, methodologies, and standards used.
        - challenges_solutions: Key challenges faced and how they were overcome.
        - results_outcomes: Quantifiable results and benefits delivered to the client.
        - relevance: Why this is relevant to future federal contracting (capabilities demonstrated).
        
        Text to analyze:
        {doc.parsed_content[:50000]}
        """
        
        # Call AI Service
        logger.info(f"Calling AI service to generate PP content from document (length={len(doc.parsed_content)} chars)")
        try:
            # Using generate_content assuming it returns string, we might need json enforcement
            response_text = await ai_service.generate_content(prompt)
            logger.info(f"AI service returned response (length={len(response_text)} chars)")

            
            # Extract JSON from response
            import json
            import re
            
            # Clean markdown code blocks
            json_str = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            # Find first { and last }
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = json_str[start:end]
            
            data = json.loads(json_str)
            
        except Exception as e:
            # Fallback for parsing error
            data = {
                "title": f"Extracted from {doc.title}",
                "project_overview": "AI Extraction failed. Please review document content.",
                "scope_of_work": "",
                "technical_approach": "",
                "challenges_solutions": "",
                "results_outcomes": "",
                "relevance": ""
            }
        
        # Create PastPerformance Record
        # Check source_document_id availability (handled by recent migration)
        # Using default dictionary structure
        pp = PastPerformance(
            entity_uei=entity_uei,
            source_document_id=doc.id,
            title=data.get("title", f"Project from {doc.title}"),
            status="DRAFT",
            questionnaire_data={
                "project_overview": {"content": data.get("project_overview", ""), "generated": True},
                "scope_of_work": {"content": data.get("scope_of_work", ""), "generated": True},
                "technical_approach": {"content": data.get("technical_approach", ""), "generated": True},
                "challenges_solutions": {"content": data.get("challenges_solutions", ""), "generated": True},
                "results_outcomes": {"content": data.get("results_outcomes", ""), "generated": True},
                "relevance": {"content": data.get("relevance", ""), "generated": True},
                "references": {"content": "", "generated": False}
            }
        )
        
        db.add(pp)
        await db.commit()
        await db.refresh(pp)
        
        return pp
    
    @staticmethod
    async def _build_generation_context(
        entity: Entity,
        award: Optional[EntityAward],
        opportunity: Optional[Opportunity],
        section_name: str,
        additional_context: Optional[str]
    ) -> str:
        """Build context string for AI generation"""
        context_parts = []
        
        # Entity information
        context_parts.append(f"Entity: {entity.legal_business_name} (UEI: {entity.uei})")
        
        # Award information
        if award:
            context_parts.append(f"Award ID: {award.award_id}")
            if award.description:
                context_parts.append(f"Award Description: {award.description}")
            if award.total_obligation:
                context_parts.append(f"Award Value: ${award.total_obligation:,.2f}")
            if award.award_date:
                context_parts.append(f"Award Date: {award.award_date}")
            if award.awarding_agency:
                context_parts.append(f"Awarding Agency: {award.awarding_agency}")
            if award.naics_code:
                context_parts.append(f"NAICS Code: {award.naics_code}")
        
        # Opportunity information
        if opportunity:
            context_parts.append(f"Related Opportunity: {opportunity.title}")
            if opportunity.description:
                context_parts.append(f"Opportunity Description: {opportunity.description[:500]}...")
            if opportunity.naics_code:
                context_parts.append(f"Opportunity NAICS: {opportunity.naics_code}")
        
        # Section-specific guidance
        template = QuestionnaireTemplate()
        section_info = template.sections.get(section_name, {})
        if section_info:
            context_parts.append(f"Section: {section_info.get('title')}")
            context_parts.append(f"Guidance: {section_info.get('prompt_hint')}")
        
        # Additional context
        if additional_context:
            context_parts.append(f"Additional Context: {additional_context}")
        
        return "\n".join(context_parts)
    
    @staticmethod
    async def export_structured_output(
        db: AsyncSession,
        past_perf_id: int,
        format: str = "json",
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Export past performance as structured output"""
        result = await db.execute(
            select(PastPerformance).where(PastPerformance.id == past_perf_id)
        )
        past_perf = result.scalars().first()
        
        if not past_perf:
            raise ValueError(f"Past performance with ID {past_perf_id} not found")
        
        # Get entity for additional context
        entity_result = await db.execute(select(Entity).where(Entity.uei == past_perf.entity_uei))
        entity = entity_result.scalars().first()
        
        if format == "json":
            return PastPerformanceService._export_json(past_perf, entity, include_metadata)
        elif format == "text":
            return PastPerformanceService._export_text(past_perf, entity, include_metadata)
        elif format == "markdown":
            return PastPerformanceService._export_markdown(past_perf, entity, include_metadata)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def _export_json(
        past_perf: PastPerformance,
        entity: Entity,
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Export as JSON"""
        output = {
            "title": past_perf.title,
            "entity": entity.legal_business_name,
            "sections": {}
        }
        
        for section_name, section_data in past_perf.questionnaire_data.items():
            output["sections"][section_name] = section_data.get("content", "")
        
        if include_metadata:
            output["metadata"] = {
                "id": past_perf.id,
                "entity_uei": past_perf.entity_uei,
                "award_id": past_perf.award_id,
                "opportunity_id": past_perf.opportunity_id,
                "status": past_perf.status,
                "created_at": past_perf.created_at.isoformat(),
                "updated_at": past_perf.updated_at.isoformat()
            }
        
        return {"format": "json", "content": output, "metadata": output.get("metadata")}
    
    @staticmethod
    def _export_text(
        past_perf: PastPerformance,
        entity: Entity,
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Export as plain text"""
        lines = []
        
        lines.append(f"PAST PERFORMANCE QUESTIONNAIRE")
        lines.append("=" * 80)
        lines.append(f"Title: {past_perf.title}")
        lines.append(f"Entity: {entity.legal_business_name}")
        lines.append("=" * 80)
        lines.append("")
        
        template = QuestionnaireTemplate()
        for section_name, section_data in past_perf.questionnaire_data.items():
            section_info = template.sections.get(section_name, {})
            title = section_info.get("title", section_name.replace("_", " ").title())
            
            lines.append(f"{title}")
            lines.append("-" * 80)
            lines.append(section_data.get("content", "[No content]"))
            lines.append("")
        
        content = "\n".join(lines)
        
        metadata = None
        if include_metadata:
            metadata = {
                "id": past_perf.id,
                "status": past_perf.status,
                "created_at": past_perf.created_at.isoformat()
            }
        
        return {"format": "text", "content": content, "metadata": metadata}
    
    @staticmethod
    def _export_markdown(
        past_perf: PastPerformance,
        entity: Entity,
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Export as Markdown"""
        lines = []
        
        lines.append(f"# {past_perf.title}")
        lines.append("")
        lines.append(f"**Entity:** {entity.legal_business_name}")
        lines.append("")
        
        if include_metadata:
            lines.append(f"**Status:** {past_perf.status}")
            lines.append(f"**Created:** {past_perf.created_at.strftime('%Y-%m-%d')}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        template = QuestionnaireTemplate()
        for section_name, section_data in past_perf.questionnaire_data.items():
            section_info = template.sections.get(section_name, {})
            title = section_info.get("title", section_name.replace("_", " ").title())
            
            lines.append(f"## {title}")
            lines.append("")
            lines.append(section_data.get("content", "*No content*"))
            lines.append("")
        
        content = "\n".join(lines)
        
        metadata = None
        if include_metadata:
            metadata = {
                "id": past_perf.id,
                "status": past_perf.status,
                "created_at": past_perf.created_at.isoformat()
            }
        
        return {"format": "markdown", "content": content, "metadata": metadata}
    
    @staticmethod
    def get_template() -> QuestionnaireTemplate:
        """Get the questionnaire template"""
        return QuestionnaireTemplate()
    
    @staticmethod
    async def generate_citations_for_solicitation(
        db: AsyncSession,
        past_perf_id: int,
        section_l_text: str,
        section_m_text: str,
        sow_pws_text: str,
        agency_name: str,
        solicitation_id: Optional[str] = None,
        solicitation_title: Optional[str] = None,
        required_citations: int = 3,
        ai_service: Any = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive past performance citations for a solicitation.
        
        Args:
            db: Database session
            past_perf_id: Past performance record ID
            section_l_text: Section L instructions text
            section_m_text: Section M evaluation factors text
            sow_pws_text: SOW/PWS text
            agency_name: Agency name
            solicitation_id: Optional solicitation ID
            solicitation_title: Optional solicitation title
            required_citations: Number of citations to generate
            ai_service: AI service instance for generation
            
        Returns:
            Dictionary with solicitation_meta and citations
        """
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        # Get past performance record
        result = await db.execute(
            select(PastPerformance).where(PastPerformance.id == past_perf_id)
        )
        past_perf = result.scalars().first()
        
        if not past_perf:
            raise ValueError(f"Past performance with ID {past_perf_id} not found")
        
        # Get entity and awards for context
        entity_result = await db.execute(select(Entity).where(Entity.uei == past_perf.entity_uei))
        entity = entity_result.scalars().first()
        
        # Get all awards for this entity
        awards_result = await db.execute(
            select(EntityAward).where(EntityAward.recipient_uei == past_perf.entity_uei)
        )
        awards = awards_result.scalars().all()
        
        # Get all past performances for this entity to use as project summaries
        pp_result = await db.execute(
            select(PastPerformance).where(PastPerformance.entity_uei == past_perf.entity_uei)
        )
        all_past_perfs = pp_result.scalars().all()
        
        # Build project summaries from past performances and awards
        project_summaries = await PastPerformanceService._build_project_summaries(
            entity, awards, all_past_perfs
        )
        
        # Import AI service if not provided
        if ai_service is None:
            from fedops_core.services.ai_service import AIService
            ai_service = AIService()
        
        # Import prompt
        from fedops_core.prompts import PAST_PERFORMANCE_CITATION_PROMPT
        
        # Build prompt
        prompt = PAST_PERFORMANCE_CITATION_PROMPT.format(
            section_l_text=section_l_text[:10000],  # Limit to avoid token limits
            section_m_text=section_m_text[:10000],
            sow_pws_text=sow_pws_text[:10000],
            agency_name=agency_name,
            n=required_citations,
            internal_project_data=json.dumps(project_summaries, indent=2)
        )
        
        logger.info(f"Generating citations for past performance {past_perf_id}")
        
        # Generate citations using AI
        try:
            response_text = await ai_service.generate_content(prompt)
            logger.info(f"AI response received (length={len(response_text)} chars)")
            
            # Extract JSON from response
            import re
            json_str = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = json_str[start:end]
            
            citations_data = json.loads(json_str)
            
            # Store citations and solicitation context
            past_perf.citations_data = citations_data
            past_perf.solicitation_context = {
                "section_l": section_l_text,
                "section_m": section_m_text,
                "sow_pws": sow_pws_text,
                "agency_name": agency_name,
                "solicitation_id": solicitation_id,
                "solicitation_title": solicitation_title,
                "generated_at": datetime.utcnow().isoformat()
            }
            past_perf.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(past_perf)
            
            return citations_data
            
        except Exception as e:
            logger.error(f"Failed to generate citations: {e}", exc_info=True)
            raise ValueError(f"Failed to generate citations: {str(e)}")
    
    @staticmethod
    async def _build_project_summaries(
        entity: Entity,
        awards: List[EntityAward],
        past_performances: List[PastPerformance]
    ) -> List[Dict[str, Any]]:
        """
        Build project summaries from entity data for citation generation.
        
        Combines award data with past performance questionnaire data.
        """
        summaries = []
        
        # Build summaries from past performances
        for pp in past_performances:
            summary = {
                "project_id": str(pp.id),
                "title": pp.title,
                "questionnaire_data": pp.questionnaire_data
            }
            
            # If linked to an award, add award details
            if pp.award_id:
                award = next((a for a in awards if a.award_id == pp.award_id), None)
                if award:
                    summary["award_details"] = {
                        "award_id": award.award_id,
                        "total_obligation": award.total_obligation,
                        "award_date": award.award_date.isoformat() if award.award_date else None,
                        "awarding_agency": award.awarding_agency,
                        "naics_code": award.naics_code,
                        "description": award.description,
                        "award_type": award.award_type
                    }
            
            summaries.append(summary)
        
        # Add awards without past performances
        for award in awards:
            # Check if award already included
            if not any(s.get("award_details", {}).get("award_id") == award.award_id for s in summaries):
                summaries.append({
                    "project_id": f"award_{award.award_id}",
                    "title": award.description or f"Award {award.award_id}",
                    "award_details": {
                        "award_id": award.award_id,
                        "total_obligation": award.total_obligation,
                        "award_date": award.award_date.isoformat() if award.award_date else None,
                        "awarding_agency": award.awarding_agency,
                        "naics_code": award.naics_code,
                        "description": award.description,
                        "award_type": award.award_type
                    }
                })
        
        return summaries
    
    @staticmethod
    async def get_citations(
        db: AsyncSession,
        past_perf_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get stored citations for a past performance"""
        result = await db.execute(
            select(PastPerformance).where(PastPerformance.id == past_perf_id)
        )
        past_perf = result.scalars().first()
        
        if not past_perf:
            return None
        
        return past_perf.citations_data

