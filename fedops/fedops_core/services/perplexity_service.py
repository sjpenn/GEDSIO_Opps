"""
Perplexity Service for Competitive Analysis

Uses the Perplexity API to research entities and generate structured
competitive intelligence with cited sources.
"""
import httpx
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fedops_core.settings import settings
from fedops_core.schemas.competitive_analysis_schemas import (
    CompetitiveAnalysisResult,
    Citation,
    Strength,
    Weakness,
    CompetitiveStrategy,
    AgencyResearchResult,
    COResearchResult,
    ContractingProfessionalSearchResult,
    ContractingProfessionalMatch,
    LOBItem,
    BudgetItem,
    OrgNode
)
from fedops_core.prompts import CONTRACTING_PRO_SEARCH_PROMPT

logger = logging.getLogger(__name__)


class PerplexityService:
    """Service to perform competitive research using Perplexity API"""
    
    BASE_URL = "https://api.perplexity.ai/chat/completions"
    DEFAULT_MODEL = "sonar-pro"  # Better citations than base sonar
    
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not configured. Competitive analysis will be unavailable.")
    
    def _build_analysis_prompt(self, entity_name: str, context: Optional[str] = None) -> str:
        """Build the prompt for competitive analysis research"""
        context_str = f"\n\nAdditional context: {context}" if context else ""
        
        return f"""Perform a comprehensive competitive analysis of "{entity_name}" as a federal government contractor.{context_str}

Research and provide a structured analysis in the following JSON format. Be thorough and cite your sources.

{{
    "overview": "2-3 sentence executive summary of who they are and what they do",
    "market_position": "Description of their position in the federal contracting market",
    "strengths": [
        {{"description": "Strength 1", "evidence": "Supporting details"}},
        {{"description": "Strength 2", "evidence": "Supporting details"}}
    ],
    "weaknesses": [
        {{"description": "Weakness 1", "evidence": "Supporting details"}},
        {{"description": "Weakness 2", "evidence": "Supporting details"}}
    ],
    "key_differentiators": ["What sets them apart 1", "What sets them apart 2"],
    "how_to_beat_them": [
        {{"strategy": "Strategy to compete", "rationale": "Why this works", "priority": "HIGH/MEDIUM/LOW"}},
        {{"strategy": "Another strategy", "rationale": "Why this works", "priority": "HIGH/MEDIUM/LOW"}}
    ]
}}

Focus on:
- Federal contracting history and capabilities
- Agency relationships and past performance
- Technology and service offerings
- Known contract wins and losses
- Pricing strategies if known
- Team composition and key personnel
- Certifications (8(a), WOSB, SDVOSB, etc.)

Provide at least 3 strengths, 3 weaknesses, and 3 strategies to beat them.
Return ONLY valid JSON, no other text."""

    def _build_agency_prompt(self, agency_name: str) -> str:
        return f"""Perform a deep analysis of the "{agency_name}" for a government contractor looking to do business with them.

Provide a structured analysis in the following JSON format:
{{
    "agency_name": "{agency_name}",
    "acronym": "Agency Acronym",
    "overview": "Detailed overview of the agency's mission",
    "strategic_goals": ["Goal 1", "Goal 2", "Goal 3"],
    "budget_outlook": "Summary of current budget and future outlook",
    "org_structure": "Text description of organizational structure",
    "org_tree": {{
        "name": "Agency Head",
        "title": "Secretary/Administrator",
        "icon_type": "leadership",
        "children": [
            {{"name": "Deputy", "title": "Deputy Secretary", "icon_type": "default", "children": []}}
        ]
    }},
    "key_bureaus": ["Bureau 1", "Bureau 2"],
    "lines_of_business": [
        {{
            "name": "LOB Name",
            "description": "What this LOB does",
            "responsibilities": ["Responsibility 1", "Responsibility 2"],
            "key_programs": ["Program A", "Program B"],
            "budget_share": "15%"
        }}
    ],
    "budget_by_division": [
        {{"division": "Division Name", "amount": "$2.5B", "percentage": 25.0, "trend": "increasing"}}
    ],
    "pain_points": ["Challenge 1", "Challenge 2"],
    "procurement_priorities": ["What they buy 1", "What they buy 2"]
}}

Focus on:
- Mission and strategic direction
- Detailed organizational hierarchy (org chart)
- Lines of Business and their specific responsibilities
- Budget allocation by division/program with trends
- Budget trends and spending priorities
- Organizational structure and key decision-making units
- Major challenges they are facing (pain points)
- Recent procurement trends and priorities

Return ONLY valid JSON."""

    def _build_co_prompt(self, co_name: str, agency: Optional[str] = None) -> str:
        agency_str = f" at {agency}" if agency else ""
        return f"""Research Contracting Officer "{co_name}"{agency_str}.

Provide a structured profile in the following JSON format:
{{
    "co_name": "{co_name}",
    "agency": "{agency if agency else 'Identify Agency'}",
    "overview": "Professional background and bio",
    "career_history": ["Role 1", "Role 2"],
    "education": "Education details if available",
    "awarding_patterns": "Observations on their awarding behavior (e.g. prefers innovative solutions, risk-averse, etc.)",
    "preferred_vehicles": ["Vehicle 1", "Vehicle 2"]
}}

Focus on:
- Professional background
- Current role and agency
- Any public speaking or industry engagement
- Mentioned in solicitation documents or award notices
- Awarding tendencies if discernible

Return ONLY valid JSON."""

    async def research_contracting_professionals(self, query: str) -> ContractingProfessionalSearchResult:
        """Search for contracting professionals by name (fuzzy match)"""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not configured")
            
        prompt = CONTRACTING_PRO_SEARCH_PROMPT.replace("{query}", query)
        return await self._execute_research(prompt, query, "contracting_pro_search")


    async def research_entity(
        self, 
        entity_name: str, 
        context: Optional[str] = None,
        entity_uei: Optional[str] = None
    ) -> CompetitiveAnalysisResult:
        """Research an entity using Perplexity API"""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not configured")
        
        prompt = self._build_analysis_prompt(entity_name, context)
        return await self._execute_research(prompt, entity_name, "entity", entity_uei=entity_uei)

    async def research_agency(self, agency_name: str) -> AgencyResearchResult:
        """Research a federal agency"""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not configured")
            
        prompt = self._build_agency_prompt(agency_name)
        return await self._execute_research(prompt, agency_name, "agency")

    async def research_co(self, co_name: str, agency: Optional[str] = None) -> COResearchResult:
        """Research a contracting officer"""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not configured")
            
        prompt = self._build_co_prompt(co_name, agency)
        return await self._execute_research(prompt, co_name, "co")



    async def _execute_research(
        self, 
        prompt: str, 
        subject_name: str, 
        result_type: str,
        entity_uei: Optional[str] = None
    ):
        """Execute the API call and parse based on type"""
        payload = {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a federal government market intelligence analyst. Provide accurate, structured data in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "web_search_options": {
                "search_context_size": "high"
            },
            "return_related_questions": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Researching {result_type}: {subject_name}")
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
            return self._parse_response(data, subject_name, result_type, entity_uei)
            
        except httpx.TimeoutException:
            logger.error(f"Perplexity API timed out for {subject_name}")
            raise ValueError("Research timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error researching {subject_name}: {e}")
            raise

    def _parse_response(
        self, 
        response: Dict[str, Any], 
        subject_name: str,
        result_type: str,
        entity_uei: Optional[str] = None
    ):
        """Parse Perplexity API response into structured result"""
        
        choices = response.get("choices", [])
        if not choices:
            raise ValueError("No response content from Perplexity")
        
        content = choices[0].get("message", {}).get("content", "")
        raw_response = content
        
        citations = self._extract_citations(response.get("search_results", []))
        
        try:
            # Clean up potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Raise error or return partial? For now let's raise so UI shows error
            # Or handle gracefully depending on type.
            raise ValueError("Failed to parse analysis results from AI response")

        if result_type == "entity":
            # Map to CompetitiveAnalysisResult
            strengths = [
                Strength(
                    description=s.get("description", ""),
                    evidence=s.get("evidence"),
                    source_index=s.get("source_index")
                ) for s in data.get("strengths", [])
            ]
            weaknesses = [
                Weakness(
                    description=w.get("description", ""),
                    evidence=w.get("evidence"),
                    source_index=w.get("source_index")
                ) for w in data.get("weaknesses", [])
            ]
            strategies = [
                CompetitiveStrategy(
                    strategy=s.get("strategy", ""),
                    rationale=s.get("rationale", ""),
                    priority=s.get("priority", "MEDIUM")
                ) for s in data.get("how_to_beat_them", [])
            ]
            
            return CompetitiveAnalysisResult(
                entity_name=subject_name,
                entity_uei=entity_uei,
                overview=data.get("overview", ""),
                market_position=data.get("market_position", ""),
                strengths=strengths,
                weaknesses=weaknesses,
                key_differentiators=data.get("key_differentiators", []),
                how_to_beat_them=strategies,
                citations=citations,
                raw_response=raw_response
            )
            
        elif result_type == "agency":
            # Parse LOB items
            lobs = []
            for lob_data in data.get("lines_of_business", []):
                lobs.append(LOBItem(
                    name=lob_data.get("name", ""),
                    description=lob_data.get("description", ""),
                    responsibilities=lob_data.get("responsibilities", []),
                    key_programs=lob_data.get("key_programs", []),
                    budget_share=lob_data.get("budget_share")
                ))
            
            # Parse budget items
            budget_items = []
            for b_data in data.get("budget_by_division", []):
                budget_items.append(BudgetItem(
                    division=b_data.get("division", ""),
                    amount=b_data.get("amount"),
                    percentage=b_data.get("percentage"),
                    trend=b_data.get("trend")
                ))
            
            # Parse org tree recursively
            org_tree = None
            org_tree_data = data.get("org_tree")
            if org_tree_data:
                org_tree = self._parse_org_node(org_tree_data)
            
            return AgencyResearchResult(
                agency_name=data.get("agency_name", subject_name),
                acronym=data.get("acronym"),
                overview=data.get("overview", ""),
                strategic_goals=data.get("strategic_goals", []),
                budget_outlook=data.get("budget_outlook", ""),
                org_structure=data.get("org_structure", ""),
                org_tree=org_tree,
                key_bureaus=data.get("key_bureaus", []),
                lines_of_business=lobs,
                budget_by_division=budget_items,
                pain_points=data.get("pain_points", []),
                procurement_priorities=data.get("procurement_priorities", []),
                citations=citations,
                raw_response=raw_response
            )
            
        elif result_type == "co":
            return COResearchResult(
                co_name=data.get("co_name", subject_name),
                agency=data.get("agency"),
                overview=data.get("overview", ""),
                career_history=data.get("career_history", []),
                education=data.get("education"),
                awarding_patterns=data.get("awarding_patterns"),
                preferred_vehicles=data.get("preferred_vehicles", []),
                citations=citations,
                raw_response=raw_response
            )

        elif result_type == "contracting_pro_search":
            item_matches = []
            for m in data.get("matches", []):
                item_matches.append(ContractingProfessionalMatch(
                    name=m.get("name", "Unknown"),
                    agency=m.get("agency", "Unknown"),
                    office=m.get("office"),
                    role=m.get("role"),
                    match_reason=m.get("match_reason"),
                    location=m.get("location"),
                    contact_info=m.get("contact_info"),
                    overview=m.get("overview"),
                    recent_activity=m.get("recent_activity")
                ))
            
            return ContractingProfessionalSearchResult(
                query=subject_name,
                matches=item_matches,
                citations=citations,
                raw_response=raw_response
            )
            
        raise ValueError(f"Unknown result type: {result_type}")
    
    def _parse_org_node(self, node_data: Dict[str, Any]) -> OrgNode:
        """Recursively parse org tree node"""
        children = []
        for child_data in node_data.get("children", []):
            children.append(self._parse_org_node(child_data))
        
        return OrgNode(
            name=node_data.get("name", ""),
            title=node_data.get("title"),
            icon_type=node_data.get("icon_type", "default"),
            children=children
        )
    
    def _extract_citations(self, search_results: List[Dict[str, Any]]) -> List[Citation]:
        """Extract citations from Perplexity search_results"""
        citations = []
        for result in search_results:
            citations.append(Citation(
                title=result.get("title", "Unknown Source"),
                url=result.get("url", ""),
                snippet=result.get("snippet"),
                date=result.get("date")
            ))
        return citations


# Singleton instance
perplexity_service = PerplexityService()
