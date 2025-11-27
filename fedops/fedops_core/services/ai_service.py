import google.generativeai as genai
from openai import AsyncOpenAI
from fedops_core.settings import settings
from fedops_core.prompts import DocumentType, get_prompt_for_doc_type

class AIService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        
        # Configure Gemini
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def generate_shipley_summary(self, content: str, doc_type: DocumentType = DocumentType.RFP) -> str:
        prompt = get_prompt_for_doc_type(doc_type, content)

        if self.provider == "gemini":
            return await self._call_gemini(prompt)
        elif self.provider == "openai" or self.provider == "openrouter":
            return await self._call_openai_compatible(prompt)
        else:
            return "Invalid LLM Provider Configuration"

    async def _call_gemini(self, prompt: str) -> str:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Gemini API Key not configured.")
        
        model = genai.GenerativeModel(self.model)
        response = await model.generate_content_async(prompt)
        return response.text

    async def _call_openai_compatible(self, prompt: str) -> str:
        api_key = settings.OPENAI_API_KEY if self.provider == "openai" else settings.OPENROUTER_API_KEY
        base_url = "https://api.openai.com/v1" if self.provider == "openai" else "https://openrouter.ai/api/v1"
        
        if not api_key:
            raise ValueError(f"{self.provider} API Key not configured.")

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert proposal manager using the Shipley process."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    async def analyze_opportunity(self, prompt: str) -> dict:
        """
        Analyzes an opportunity using AI and returns structured JSON.
        Expects the LLM to return a JSON object.
        """
        import json
        import re
        
        if self.provider == "gemini":
            response_text = await self._call_gemini(prompt)
        elif self.provider == "openai" or self.provider == "openrouter":
            response_text = await self._call_openai_compatible(prompt)
        else:
            raise ValueError("Invalid LLM Provider Configuration")
        
        # Try to extract JSON from the response
        try:
            # First, try to parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, return a default structure
            return {
                "summary": "AI analysis failed to return valid JSON",
                "score": 50,
                "insights": ["Unable to parse AI response"],
                "error": "JSON parsing failed",
                "raw_response": response_text[:500]
            }
