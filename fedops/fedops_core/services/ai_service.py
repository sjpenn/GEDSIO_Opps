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
