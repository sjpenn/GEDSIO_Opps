"""
Proposal Content Generator Service

Uses AI to generate comprehensive proposal content including:
- Requirements compliance matrix
- SOW/PWS decomposition and analysis
- Past performance volume with case studies
- Past Performance Questionnaires (PPQs)
"""

import os
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import google.generativeai as genai

from fedops_core.db.models import (
    Proposal, 
    ProposalRequirement, 
    Opportunity, 
    StoredFile,
    ProposalVolume,
    CompanyProfile,
    Entity,
    EntityAward
)

from fedops_core.settings import settings
from fedops_core.services.ai_service import AIService


class ProposalContentGenerator:
    """Service for generating AI-powered proposal content"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()
    
    async def generate_requirements_matrix(self, proposal_id: int) -> Dict:
        """
        Generate a comprehensive requirements compliance matrix.
        
        Returns:
            {
                "status": "success",
                "content": [
                    {
                        "id": "REQ-001",
                        "summary": "...",
                        "source": "...",
                        "proposal_section": "...",
                        "compliance": "...",
                        "notes": "..."
                    }
                ],
                "requirements_count": int
            }
        """
        # Get proposal and opportunity
        result = await self.db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            return {"status": "error", "message": "Proposal not found"}
        
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == proposal.opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        # Get all requirements
        result = await self.db.execute(
            select(ProposalRequirement).where(ProposalRequirement.proposal_id == proposal_id)
        )
        requirements = result.scalars().all()
        
        if not requirements:
            return {"status": "error", "message": "No requirements found. Please extract requirements first."}
        
        # Build context for AI
        context = self._build_opportunity_context(opportunity)
        requirements_list = self._format_requirements_for_prompt(requirements)
        
        # Generate matrix using AI
        prompt = f"""
You are a professional proposal writer for government contracts.

OPPORTUNITY CONTEXT:
{context}

TASK: Generate a comprehensive requirements compliance matrix

REQUIREMENTS ({len(requirements)} total):
{requirements_list}

OUTPUT FORMAT:
Return ONLY a JSON array of objects. Do not include markdown formatting like ```json.
Each object must have these fields:
- "id": Requirement ID (e.g., "REQ-001")
- "summary": Concise summary of the requirement (max 100 chars)
- "source": Source section reference
- "proposal_section": Mapped proposal volume/section (e.g., "Technical Volume, Section 3.2")
- "compliance": "Compliant", "Partial", or "Non-Compliant"
- "notes": Brief notes on approach or concerns

Example:
[
  {{
    "id": "REQ-001",
    "summary": "Contractor shall provide monthly reports",
    "source": "C.4.1",
    "proposal_section": "Management Volume, Section 1.2",
    "compliance": "Compliant",
    "notes": "Will use automated reporting tool"
  }}
]

GUIDELINES:
- **Identify Implied Requirements**: Look beyond "shall" statements.
- **Completeness**: Ensure all {len(requirements)} requirements are included.
- **Strict JSON**: Output must be valid JSON.

Generate the complete requirements compliance matrix now:
"""
        
        try:
            # Use AIService to get JSON response
            # We'll wrap the prompt to ensure it returns the list in an object if needed, 
            # but analyze_opportunity handles JSON extraction well.
            # The prompt asks for a JSON array. analyze_opportunity might wrap it in {"data": ...} if it finds an array.
            
            result = await self.ai_service.analyze_opportunity(prompt)
            
            matrix_data = []
            if result and isinstance(result, dict):
                if 'data' in result and isinstance(result['data'], list):
                    matrix_data = result['data']
                elif isinstance(result, list): # Should not happen as analyze_opportunity returns dict
                    matrix_data = result
                else:
                    # Maybe it returned the object directly?
                    # Check if the result itself is what we want (unlikely for a list)
                    # Or maybe it found a dict inside the array?
                    pass
            
            # Fallback if analyze_opportunity didn't give us the list directly (it returns a dict)
            # If the model returned a list, analyze_opportunity wraps it in {"data": list}
            
            if not matrix_data and result and isinstance(result, dict):
                 # Check if any value is a list
                 for k, v in result.items():
                     if isinstance(v, list):
                         matrix_data = v
                         break
            
            if not matrix_data:
                 # Try to parse raw response if available in fallback
                 if result.get('status') == 'error' and result.get('raw_response'):
                     import re
                     import json
                     text = result.get('raw_response')
                     json_match = re.search(r'\[.*\]', text, re.DOTALL)
                     if json_match:
                         try:
                             matrix_data = json.loads(json_match.group())
                         except:
                             pass
            
            return {
                "status": "success",
                "content": matrix_data,
                "requirements_count": len(requirements),
                "generated_at": "now"
            }
        except Exception as e:
            print(f"Error generating matrix: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate matrix: {str(e)}"
            }
    
    async def generate_sow_decomposition(self, proposal_id: int) -> Dict:
        """
        Generate structured SOW/PWS decomposition and analysis.
        
        Returns:
            {
                "status": "success",
                "content": "Markdown formatted analysis",
                "sections_count": int
            }
        """
        # Get proposal and opportunity
        result = await self.db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            return {"status": "error", "message": "Proposal not found"}
        
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == proposal.opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        # Get SOW/PWS documents
        result = await self.db.execute(
            select(StoredFile).where(
                StoredFile.opportunity_id == proposal.opportunity_id
            )
        )
        documents = result.scalars().all()
        
        # Combine document content
        sow_content = ""
        for doc in documents:
            content = doc.parsed_content
            if not content and doc.file_path and os.path.exists(doc.file_path):
                try:
                    with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading file {doc.filename}: {e}")
            
            if content:
                sow_content += f"\n\n=== {doc.filename} ===\n{content[:20000]}"
        
        if not sow_content:
            return {"status": "error", "message": "No SOW/PWS documents found"}
        
        context = self._build_opportunity_context(opportunity)
        
        prompt = f"""
You are a professional proposal analyst for government contracts.

OPPORTUNITY CONTEXT:
{context}

TASK: Decompose and analyze the Statement of Work (SOW/PWS)

SOW/PWS CONTENT:
{sow_content}

OUTPUT FORMAT:
Create a structured analysis with these sections:

# SOW/PWS Decomposition

## Executive Summary
Brief overview of the SOW scope and objectives

## Section-by-Section Analysis
For each major SOW section:
### [Section Number/Title]
- **Key Requirements**: List main requirements
- **Deliverables**: Specific deliverables expected
- **Performance Standards**: Metrics and acceptance criteria
- **Technical Challenges**: Potential difficulties
- **Compliance Strategy**: How we will ensure full compliance (e.g., "Use automated testing", "Assign dedicated QA")
- **Recommended Approach**: High-level technical strategy

## Consolidated Deliverables List
Complete list of all deliverables with due dates

## Performance Metrics Summary
All performance standards and KPIs

## Risk Factors
Key risks identified in the SOW

## Timeline and Milestones
Major milestones and schedule constraints

GUIDELINES:
- Be thorough and specific
- Identify all deliverables and deadlines
- Highlight technical challenges
- **Focus on Compliance**: The "Compliance Strategy" is critical.
- Use professional proposal language
- Organize clearly with markdown headers

Generate the complete SOW decomposition now:
"""
        
        try:
            decomposition = await self.ai_service.generate_content(prompt)
            decomposition = decomposition.strip()
            
            return {
                "status": "success",
                "content": decomposition,
                "generated_at": "now"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate SOW decomposition: {str(e)}"
            }
    
    async def generate_past_performance_volume(self, proposal_id: int) -> Dict:
        """
        Generate past performance volume with relevant case studies.
        
        Returns:
            {
                "status": "success",
                "content": "Markdown formatted volume",
                "case_studies_count": int
            }
        """
        # Get proposal and opportunity
        result = await self.db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            return {"status": "error", "message": "Proposal not found"}
        
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == proposal.opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        context = self._build_opportunity_context(opportunity)
        company_context = await self._get_company_context(opportunity)
        
        prompt = f"""
You are a professional proposal writer for government contracts.

OPPORTUNITY CONTEXT:
{context}

COMPANY CONTEXT:
{company_context}

TASK: Generate a Past Performance Volume with relevant case studies for {company_context.splitlines()[0] if company_context else 'our company'}

IMPORTANT INSTRUCTIONS:
- Use the ACTUAL awards data provided in the COMPANY CONTEXT section above
- For each case study, base it on one of the real awards listed
- Prioritize awards that match the current opportunity's NAICS code (marked with ⭐)
- Explain how each past performance relates to the current opportunity requirements
- Use real award values, dates, and agencies from the data provided
- If an award description is incomplete, you may elaborate based on the NAICS code and agency

OUTPUT FORMAT:
Create a complete past performance section with this structure:

# Past Performance Volume

## Introduction
Brief narrative establishing our relevant experience and qualifications

## Relevant Project Experience

### Case Study 1: [Project Name]
**Client**: [Government Agency]
**Contract Number**: [Number]
**Contract Value**: $[Amount]
**Period of Performance**: [Start Date] - [End Date]
**Contract Type**: [FFP/CPFF/T&M/etc.]

**Project Overview**:
[2-3 paragraphs describing the project scope]

**Relevance to Current Opportunity**:
[Explain how this project relates to the current solicitation]

**Performance Narrative (STAR Format)**:
*   **Situation**: What was the problem or context?
*   **Task**: What were we required to do?
*   **Action**: What specific actions did we take? (Use active voice: "We developed...", "We implemented...")
*   **Result**: What was the outcome? (Quantify! e.g., "Reduced costs by 15%", "Delivered 2 weeks early")

**Key Accomplishments**:
- [Specific achievement with metrics]
- [Another achievement]
- [Another achievement]

**Challenges and Solutions**:
[Describe a challenge faced and how it was overcome]

**Reference**:
Name: [Contact Name]
Title: [Title]
Phone: [Phone]
Email: [Email]

[Repeat for 3-5 case studies total]

## Summary of Qualifications
Brief conclusion reinforcing our capabilities

GUIDELINES:
- **Strict STAR Format**: Ensure the narrative follows Situation, Task, Action, Result.
- **Quantify Results**: Use numbers, percentages, and dollars whenever possible.
- **Relevance**: Explicitly tie past work to the *current* opportunity's requirements.
- Generate 3-5 highly relevant case studies
- Make projects realistic for government contracting
- Include complete reference information

Generate the complete past performance volume now:
"""
        
        try:
            volume_content = await self.ai_service.generate_content(prompt)
            volume_content = volume_content.strip()
            
            # Count case studies in response
            case_studies_count = volume_content.count("### Case Study")
            
            # Save to database
            # Check if volume exists
            result = await self.db.execute(
                select(ProposalVolume).where(
                    ProposalVolume.proposal_id == proposal_id,
                    ProposalVolume.title.ilike("%Past Performance%")
                )
            )
            volume = result.scalar_one_or_none()
            
            if not volume:
                volume = ProposalVolume(
                    proposal_id=proposal_id,
                    title="Volume III: Past Performance",
                    order=3,
                    blocks=[]
                )
                self.db.add(volume)
            
            # Update volume content
            import uuid
            volume.blocks = [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Past Performance Volume",
                    "content": volume_content,
                    "order": 1
                }
            ]
            await self.db.commit()
            
            return {
                "status": "success",
                "content": volume_content,
                "case_studies_count": case_studies_count,
                "generated_at": "now"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate past performance volume: {str(e)}"
            }
    
    async def generate_ppqs(self, proposal_id: int) -> Dict:
        """
        Generate Past Performance Questionnaire (PPQ) responses.
        
        Returns:
            {
                "status": "success",
                "content": "Markdown formatted PPQ responses"
            }
        """
        # Get proposal and opportunity
        result = await self.db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            return {"status": "error", "message": "Proposal not found"}
        
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == proposal.opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        context = self._build_opportunity_context(opportunity)
        company_context = await self._get_company_context(opportunity)
        
        prompt = f"""
You are a professional proposal writer for government contracts.

OPPORTUNITY CONTEXT:
{context}

COMPANY CONTEXT:
{company_context}

TASK: Complete a Past Performance Questionnaire (PPQ) for {company_context.splitlines()[0] if company_context else 'our company'}

Standard PPQ questions to answer:

1. **Contract Performance History**
   Describe your organization's history of performing similar contracts.

2. **Quality of Deliverables**
   How do you ensure quality in deliverables? Provide examples.

3. **Timeliness and Schedule Adherence**
   Describe your track record for on-time delivery. Provide metrics.

4. **Cost Control and Budget Management**
   How do you manage costs and stay within budget? Provide examples.

5. **Customer Satisfaction**
   Describe your approach to customer satisfaction. Include metrics or testimonials.

6. **Problem Resolution**
   Describe how you handle issues and resolve problems. Provide an example.

7. **Key Personnel Stability**
   Describe your retention rates and approach to maintaining qualified staff.

8. **Technical Capability**
   Describe your technical capabilities relevant to this opportunity.

9. **Subcontractor Management**
   If applicable, describe your approach to managing subcontractors.

10. **Quality Assurance/Quality Control**
    Describe your QA/QC processes and procedures.

OUTPUT FORMAT:
For each question, provide:
- Clear, specific answer (2-3 paragraphs)
- Concrete examples from past projects
- Quantifiable metrics where possible
- **Tone**: Confident, professional, but grounded in reality. Avoid hyperbole.

GUIDELINES:
- **Be Specific**: Don't just say "we have a process", describe the process steps.
- **Provide Evidence**: Cite specific past contracts where this was demonstrated.
- **Use Metrics**: "99.9% uptime", "0 cost overruns", "ISO 9001 certified".
- **Address the Question Directly**: Don't fluff.
- Maintain professional government contracting tone
- Demonstrate capability and reliability
- Keep responses concise but comprehensive

Generate complete PPQ responses now:
"""
        
        try:
            ppq_content = await self.ai_service.generate_content(prompt)
            ppq_content = ppq_content.strip()
            
            return {
                "status": "success",
                "content": ppq_content,
                "generated_at": "now"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate PPQs: {str(e)}"
            }
    
    async def generate_section_content(
        self, 
        proposal_id: int, 
        section_title: str, 
        prompt_instructions: Optional[str] = None,
        page_limit: Optional[str] = None
    ) -> Dict:
        """
        Generate content for a specific proposal section.
        
        Returns:
            {
                "status": "success",
                "content": "Markdown formatted content"
            }
        """
        # Get proposal and opportunity
        result = await self.db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            return {"status": "error", "message": "Proposal not found"}
        
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == proposal.opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        context = self._build_opportunity_context(opportunity)
        company_context = await self._get_company_context(opportunity)
        sow_content = await self._get_sow_content(proposal.opportunity_id)
        
        custom_instructions = prompt_instructions or "Provide a comprehensive response addressing the requirements for this section."
        
        # Format page limit instruction
        length_instruction = ""
        if page_limit:
            length_instruction = f"\n**Length Constraint**: Approximately {page_limit} pages. Adjust detail level accordingly."

        prompt = f"""
You are a professional proposal writer for government contracts.

OPPORTUNITY CONTEXT:
{context}

STATEMENT OF WORK (SOW) EXCERPT:
{sow_content[:15000] if sow_content else "No SOW content available."}

COMPANY CONTEXT:
{company_context}

TASK: Write the content for the proposal section titled "{section_title}".

INSTRUCTIONS:
{custom_instructions}
{length_instruction}

GUIDANCE:
1. **Address SOW Requirements**: Specifically address the requirements in the SOW related to this section.
2. **Use Company Capabilities**: substantiate your claims using the Company Context (Past Performance, Capabilities).
3. **Compliance**: Ensure all "shall" statements relevant to this section are addressed.

OUTPUT FORMAT:
Write the content in Markdown format. Do not include the section title as a header (it will be added by the system).
Focus on being compliant, compelling, and concise.
Use professional government contracting language.
Highlight our strengths and relevant experience.

Generate the section content now:
"""
        
        try:
            content = await self.ai_service.generate_content(prompt)
            content = content.strip()
            
            return {
                "status": "success",
                "content": content,
                "generated_at": "now"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate section content: {str(e)}"
            }

    def _build_opportunity_context(self, opportunity: Optional[Opportunity]) -> str:
        """Build formatted context string from opportunity details"""
        if not opportunity:
            return "No opportunity details available"
        
        context = f"""
- Title: {opportunity.title or 'N/A'}
- Agency: {opportunity.department or 'N/A'}
- Office: {opportunity.office or 'N/A'}
- NAICS Code: {opportunity.naics_code or 'N/A'}
- Set-Aside Type: {opportunity.type_of_set_aside or 'N/A'}
- Solicitation Number: {opportunity.solicitation_number or 'N/A'}
"""
        if opportunity.description:
            context += f"\n- Description: {opportunity.description[:500]}..."
        
        return context
    
    async def _get_company_context(self, opportunity: Optional[Opportunity] = None) -> str:
        """Fetch primary entity/company details and awards data"""
        # Find primary entity
        result = await self.db.execute(
            select(Entity).where(Entity.is_primary == True)
        )
        primary_entity = result.scalar_one_or_none()
        
        if not primary_entity:
            return "Company Name: [Your Company Name]\nNo past performance data available."
            
        # Try to find associated profile
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.entity_uei == primary_entity.uei)
        )
        profile = result.scalar_one_or_none()
        
        context = f"Company Name: {primary_entity.legal_business_name}\n"
        context += f"UEI: {primary_entity.uei}\n"
        
        if profile:
            if profile.target_naics:
                context += f"Target NAICS: {', '.join(profile.target_naics)}\n"
            if profile.target_keywords:
                context += f"Core Capabilities: {', '.join(profile.target_keywords)}\n"
        
        # Fetch awards for this entity
        result = await self.db.execute(
            select(EntityAward)
            .where(EntityAward.recipient_uei == primary_entity.uei)
            .order_by(EntityAward.award_date.desc())
            .limit(10)  # Get top 10 most recent awards
        )
        awards = result.scalars().all()
        
        if awards:
            context += f"\n\nPAST PERFORMANCE AWARDS ({len(awards)} recent contracts):\n"
            for i, award in enumerate(awards, 1):
                context += f"\n{i}. Award ID: {award.award_id}\n"
                if award.description:
                    context += f"   Description: {award.description[:200]}...\n"
                if award.total_obligation:
                    context += f"   Value: ${award.total_obligation:,.2f}\n"
                if award.award_date:
                    context += f"   Date: {award.award_date}\n"
                if award.awarding_agency:
                    context += f"   Agency: {award.awarding_agency}\n"
                if award.naics_code:
                    context += f"   NAICS: {award.naics_code}"
                    # Highlight if it matches opportunity NAICS
                    if opportunity and opportunity.naics_code and award.naics_code == opportunity.naics_code:
                        context += " ⭐ MATCHES CURRENT OPPORTUNITY"
                    context += "\n"
                if award.award_type:
                    context += f"   Type: {award.award_type}\n"
                    
        return context

    def _format_requirements_for_prompt(self, requirements: List[ProposalRequirement]) -> str:
        """Format requirements list for AI prompt"""
        formatted = []
        for i, req in enumerate(requirements, 1):
            formatted.append(
                f"{i}. [{req.requirement_type}] {req.requirement_text[:200]}... "
                f"(Source: {req.source_section or 'N/A'}, Priority: {req.priority})"
            )
        return "\n".join(formatted)

    async def _get_sow_content(self, opportunity_id: int) -> str:
        """Fetch and combine SOW/PWS content from stored files"""
        result = await self.db.execute(
            select(StoredFile).where(
                StoredFile.opportunity_id == opportunity_id
            )
        )
        documents = result.scalars().all()
        
        sow_content = ""
        for doc in documents:
            # Simple heuristic to prioritize SOW-like files
            if any(x in doc.filename.lower() for x in ['sow', 'pws', 'statement', 'work', 'objective', 'soo']):
                content = doc.parsed_content
                if not content and doc.file_path and os.path.exists(doc.file_path):
                    try:
                        with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"Error reading file {doc.filename}: {e}")
                
                if content:
                    sow_content += f"\n\n=== {doc.filename} ===\n{content[:20000]}"
        
        return sow_content

    async def generate_sources_sought_response(self, proposal_id: int) -> Dict:
        """
        Generate a specialized response for Sources Sought / RFI.
        
        Returns:
            {
                "status": "success",
                "content": "Markdown formatted response",
                "generated_at": "now"
            }
        """
        # Get proposal and opportunity
        result = await self.db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            return {"status": "error", "message": "Proposal not found"}
        
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == proposal.opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        # Build contexts
        from fedops_core.prompts import SOURCES_SOUGHT_RESPONSE_PROMPT
        company_context = await self._get_company_context(opportunity)
        
        prompt = SOURCES_SOUGHT_RESPONSE_PROMPT.format(
            title=opportunity.title or "N/A",
            department=opportunity.department or "N/A",
            naics_code=opportunity.naics_code or "N/A",
            description=(opportunity.description or "")[:5000],
            company_context=company_context
        )
        
        try:
            content = await self.ai_service.generate_content(prompt)
            content = content.strip()
            
            # Save to database as a new Volume
            # Check if volume exists
            result = await self.db.execute(
                select(ProposalVolume).where(
                    ProposalVolume.proposal_id == proposal_id,
                    ProposalVolume.title.ilike("%Sources Sought%")
                )
            )
            volume = result.scalar_one_or_none()
            
            if not volume:
                volume = ProposalVolume(
                    proposal_id=proposal_id,
                    title="Volume I: Sources Sought Response",
                    order=1,
                    blocks=[]
                )
                self.db.add(volume)
            
            # Update volume content
            import uuid
            volume.blocks = [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Sources Sought Response",
                    "content": content,
                    "order": 1
                }
            ]
            await self.db.commit()
            
            return {
                "status": "success",
                "content": content,
                "generated_at": "now"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate Sources Sought response: {str(e)}"
            }
