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
    CompetitiveStrategy
)

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

    async def research_entity(
        self, 
        entity_name: str, 
        context: Optional[str] = None,
        entity_uei: Optional[str] = None
    ) -> CompetitiveAnalysisResult:
        """
        Research an entity using Perplexity API and return structured analysis.
        
        Args:
            entity_name: Name of the entity to research
            context: Optional context for more targeted research
            entity_uei: Optional UEI to include in result
            
        Returns:
            CompetitiveAnalysisResult with structured analysis and citations
        """
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not configured")
        
        prompt = self._build_analysis_prompt(entity_name, context)
        
        payload = {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a federal contracting competitive intelligence analyst. Provide accurate, well-researched analysis with specific details. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low for factual accuracy
            "web_search_options": {
                "search_context_size": "high"  # Maximize citation coverage
            },
            "return_related_questions": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Researching entity: {entity_name}")
            # Extended timeout for deep research
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
            return self._parse_response(data, entity_name, entity_uei)
            
        except httpx.TimeoutException:
            logger.error(f"Perplexity API timed out researching {entity_name}")
            raise ValueError("Research timed out. The competitor analysis is taking longer than expected. Please try again.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API error: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Perplexity API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error researching entity {entity_name}: {e}")
            raise
    
    def _parse_response(
        self, 
        response: Dict[str, Any], 
        entity_name: str,
        entity_uei: Optional[str] = None
    ) -> CompetitiveAnalysisResult:
        """Parse Perplexity API response into structured result"""
        
        # Extract the content from the response
        choices = response.get("choices", [])
        if not choices:
            raise ValueError("No response content from Perplexity")
        
        content = choices[0].get("message", {}).get("content", "")
        raw_response = content
        
        # Extract citations from search_results
        citations = self._extract_citations(response.get("search_results", []))
        
        # Parse the JSON content
        try:
            # Clean up potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            analysis_data = json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Return a minimal result with the raw content
            return CompetitiveAnalysisResult(
                entity_name=entity_name,
                entity_uei=entity_uei,
                overview=content[:500] if content else "Analysis failed to parse",
                market_position="Unable to determine",
                citations=citations,
                raw_response=raw_response
            )
        
        # Build structured result
        strengths = [
            Strength(
                description=s.get("description", ""),
                evidence=s.get("evidence"),
                source_index=s.get("source_index")
            )
            for s in analysis_data.get("strengths", [])
        ]
        
        weaknesses = [
            Weakness(
                description=w.get("description", ""),
                evidence=w.get("evidence"),
                source_index=w.get("source_index")
            )
            for w in analysis_data.get("weaknesses", [])
        ]
        
        strategies = [
            CompetitiveStrategy(
                strategy=strat.get("strategy", ""),
                rationale=strat.get("rationale", ""),
                priority=strat.get("priority", "MEDIUM")
            )
            for strat in analysis_data.get("how_to_beat_them", [])
        ]
        
        return CompetitiveAnalysisResult(
            entity_name=entity_name,
            entity_uei=entity_uei,
            overview=analysis_data.get("overview", ""),
            market_position=analysis_data.get("market_position", ""),
            strengths=strengths,
            weaknesses=weaknesses,
            key_differentiators=analysis_data.get("key_differentiators", []),
            how_to_beat_them=strategies,
            citations=citations,
            analyzed_at=datetime.utcnow(),
            raw_response=raw_response
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
