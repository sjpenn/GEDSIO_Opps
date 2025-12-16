from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fedops_agents.base_agent import BaseAgent
from fedops_core.services.ai_service import AIService
from fedops_core.db.models import Proposal, ProposalVolume

class WriterAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("WriterAgent", db)
        self.ai_service = AIService()

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        """
        Default execution method (required by BaseAgent).
        For WriterAgent, we typically call specific methods like 'draft_section'.
        """
        return {"status": "success", "message": "WriterAgent ready. Use specific methods."}

    async def draft_section(
        self, 
        section_title: str, 
        requirements: List[str], 
        context: Optional[str] = None,
        style_guide: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a draft for a specific proposal section.
        """
        try:
            prompt = self._build_drafting_prompt(section_title, requirements, context, style_guide)
            
            content = await self.ai_service.generate_content(prompt)
            
            return {
                "status": "success",
                "content": content,
                "model_used": self.ai_service.model
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _build_drafting_prompt(
        self, 
        title: str, 
        requirements: List[str], 
        context: Optional[str], 
        style_guide: Optional[str]
    ) -> str:
        req_list = "\n- ".join(requirements) if requirements else "No specific requirements provided."
        
        prompt = f"""
        You are an expert Federal Proposal Writer acting as the 'Writer AI' in the AutoGen workflow.
        Your task is to write a high-scoring, compliant draft for the following proposal section.
        
        ## SECTION INFO
        **Title:** {title}
        
        ## REQUIREMENTS (Compliance is mandatory)
        - {req_list}
        
        ## CONTEXT & SOURCE MATERIAL
        {context or "No additional source material provided. Use general best practices."}
        
        ## STYLE GUIDELINES
        {style_guide or "Use active voice, clear and concise language. Focus on 'Benefit to the Government'."}
        
        ## OUTPUT INSTRUCTIONS
        - Write in Markdown format.
        - Use appropriate headers (###, ####).
        - Do not include meta-commentary (e.g., "Here is the draft"). just the content.
        - Ensure all requirements are addressed.
        """
        return prompt
