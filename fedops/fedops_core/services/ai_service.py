import google.generativeai as genai
from openai import AsyncOpenAI
import httpx
from fedops_core.settings import settings
from fedops_core.prompts import DocumentType, get_prompt_for_doc_type
import json
import re
import asyncio
import logging
from typing import Optional, Dict, Any, Type, TypeVar
from pydantic import BaseModel, ValidationError

# Try importing mlx_lm
try:
    from mlx_lm import load, generate
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False

T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)

class AIService:
    _instance = None
    _mlx_model = None
    _mlx_tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            # Initialize with default settings
            cls._instance.provider = settings.LLM_PROVIDER
            cls._instance.model = settings.LLM_MODEL
            cls._instance.temperature = settings.LLM_TEMPERATURE
            cls._instance.max_tokens = settings.LLM_MAX_TOKENS
            cls._instance.max_retries = settings.LLM_MAX_RETRIES
            cls._instance.retry_delay = settings.LLM_RETRY_DELAY
            cls._instance.fallback_model = settings.LLM_FALLBACK_MODEL
            
            # Configure Gemini if needed
            if settings.GOOGLE_API_KEY:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
            
            logger.info(f"AIService initialized with provider={cls._instance.provider}, model={cls._instance.model}")
        return cls._instance

    def set_provider(self, provider: str, model: Optional[str] = None):
        """Update the LLM provider at runtime."""
        self.provider = provider
        if model:
            self.model = model
        
        logger.info(f"Switched AI Provider to: {self.provider} ({self.model})")

    async def generate_content(self, prompt: str) -> str:
        """
        Generate text content using the configured LLM provider.
        """
        if self.provider == "gemini":
            return await self._call_gemini(prompt)
        elif self.provider == "openai" or self.provider == "openrouter":
            return await self._call_openai_compatible(prompt)
        elif self.provider == "local":
            return await self._call_mlx_lm(prompt)
        else:
            raise ValueError(f"Invalid LLM Provider Configuration: {self.provider}")

    async def generate_shipley_summary(self, content: str, doc_type: DocumentType = DocumentType.RFP) -> str:
        prompt = get_prompt_for_doc_type(doc_type, content)

        if self.provider == "gemini":
            return await self._call_gemini(prompt)
        elif self.provider == "openai" or self.provider == "openrouter":
            return await self._call_openai_compatible(prompt)
        elif self.provider == "local":
            return await self._call_mlx_lm(prompt)
        else:
            return "Invalid LLM Provider Configuration"

    async def _call_gemini(self, prompt: str, retry_count: int = 0) -> str:
        if not settings.GOOGLE_API_KEY:
            raise ValueError("Gemini API Key not configured.")
        
        try:
            model = genai.GenerativeModel(self.model)
            response = await model.generate_content_async(prompt)
            
            if not response or not response.text:
                raise ValueError("Gemini returned empty response")
            
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error (attempt {retry_count + 1}): {str(e)}")
            
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2 ** retry_count))
                return await self._call_gemini(prompt, retry_count + 1)
            
            raise

    async def _call_openai_compatible(self, prompt: str, model_override: Optional[str] = None, retry_count: int = 0) -> str:
        api_key = settings.OPENAI_API_KEY if self.provider == "openai" else settings.OPENROUTER_API_KEY
        base_url = "https://api.openai.com/v1" if self.provider == "openai" else "https://openrouter.ai/api/v1"
        
        if not api_key:
            raise ValueError(f"{self.provider} API Key not configured.")

        model_to_use = model_override or self.model
        
        try:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            
            # Add OpenRouter-specific headers if using OpenRouter
            extra_headers = {}
            if self.provider == "openrouter":
                extra_headers = {
                    "HTTP-Referer": "https://fedops.app",
                    "X-Title": "FedOps Analysis"
                }
            
            response = await client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": "You are an expert proposal manager using the Shipley process. Always return valid JSON when requested."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                extra_headers=extra_headers if extra_headers else None
            )
            
            if not response or not response.choices or not response.choices[0].message.content:
                raise ValueError(f"API returned empty response for model {model_to_use}")
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"API error with {model_to_use} (attempt {retry_count + 1}): {str(e)}")
            
            # Try fallback model if primary fails and we haven't tried it yet
            if retry_count == 0 and self.fallback_model and model_override != self.fallback_model:
                logger.info(f"Trying fallback model: {self.fallback_model}")
                return await self._call_openai_compatible(prompt, self.fallback_model, retry_count + 1)
            
            # Retry with exponential backoff
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2 ** retry_count))
                return await self._call_openai_compatible(prompt, model_override, retry_count + 1)
            
            raise

    async def _call_mlx_lm(self, prompt: str) -> str:
        """Call local MLX model via external server."""
        # URL for the local server running on host machine
        # From Docker container, host is accessible via host.docker.internal
        url = "http://host.docker.internal:8001/v1/chat/completions"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json={
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["content"]

        except httpx.ConnectError:
             logger.error("Failed to connect to Local LLM Server at http://host.docker.internal:8001")
             return "Error: Local LLM Server is not running. Please run 'python local_llm_server.py' on your host machine."
        except Exception as e:
            logger.error(f"Local LLM Server error: {str(e)}")
            raise

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text using multiple strategies.
        Returns None if no valid JSON found.
        """
        if not text:
            return None
        
        # Strategy 1: Try to parse entire response as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Look for JSON in markdown code blocks
        code_block_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
        ]
        
        for pattern in code_block_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        # Strategy 3: Find first complete JSON object in text
        json_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Try to find JSON array
        array_match = re.search(r'\[.*\]', text, re.DOTALL)
        if array_match:
            try:
                return {"data": json.loads(array_match.group())}
            except json.JSONDecodeError:
                pass
        
        return None

    async def analyze_opportunity(self, prompt: str) -> Dict[str, Any]:
        """
        Analyzes an opportunity using AI and returns structured JSON.
        Expects the LLM to return a JSON object.
        Returns a safe fallback structure if parsing fails.
        """
        try:
            # Get response from AI
            response_text = await self.generate_content(prompt)
            
            # Validate response
            if not response_text:
                logger.error("AI returned None or empty response")
                return self._get_fallback_response("AI returned empty response")
            
            # Extract JSON from response
            extracted_json = self._extract_json_from_text(response_text)
            
            if extracted_json:
                logger.info(f"Successfully extracted JSON with {len(extracted_json)} keys")
                return extracted_json
            
            # If no JSON found, return fallback with raw response
            logger.warning("Could not extract valid JSON from AI response")
            return self._get_fallback_response(
                "AI response did not contain valid JSON",
                raw_response=response_text[:1000]
            )
            
        except Exception as e:
            logger.error(f"Error in analyze_opportunity: {str(e)}", exc_info=True)
            return self._get_fallback_response(f"Analysis error: {str(e)}")
    
    async def analyze_with_schema(
        self,
        prompt: str,
        schema: Type[T],
        use_structured_output: bool = True
    ) -> Optional[T]:
        """
        Analyze content with Pydantic schema validation.
        
        Args:
            prompt: The analysis prompt
            schema: Pydantic model class for validation
            use_structured_output: Whether to use native structured output (OpenAI only)
            
        Returns:
            Validated Pydantic model instance or None if validation fails
        """
        try:
            # For OpenAI, we can use native structured output if enabled and provider is OpenAI
            if use_structured_output and self.provider == "openai":
                return await self._call_openai_with_schema(prompt, schema)
            
            # Otherwise, use standard approach with validation
            response_text = await self.generate_content(prompt)
            
            # Extract JSON
            extracted_json = self._extract_json_from_text(response_text)
            
            if not extracted_json:
                logger.error("Could not extract JSON from response")
                return None
            
            # Validate with schema
            return self.validate_with_schema(extracted_json, schema)
            
        except Exception as e:
            logger.error(f"Error in analyze_with_schema: {e}", exc_info=True)
            return None
    
    async def _call_openai_with_schema(
        self,
        prompt: str,
        schema: Type[T]
    ) -> Optional[T]:
        """
        Call OpenAI with structured output using response_format.
        
        Args:
            prompt: The analysis prompt
            schema: Pydantic model class
            
        Returns:
            Validated Pydantic model instance
        """
        api_key = settings.OPENAI_API_KEY
        base_url = "https://api.openai.com/v1"
        
        if not api_key:
            raise ValueError("OpenAI API Key not configured")
        
        try:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            
            # Convert Pydantic schema to JSON schema
            json_schema = schema.model_json_schema()
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert proposal manager using the Shipley process."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": json_schema,
                        "strict": True
                    }
                }
            )
            
            if not response or not response.choices:
                return None
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Validate with Pydantic
            return schema(**data)
            
        except Exception as e:
            logger.error(f"Error in OpenAI structured output: {e}", exc_info=True)
            return None
    
    def validate_with_schema(
        self,
        data: Dict[str, Any],
        schema: Type[T]
    ) -> Optional[T]:
        """
        Validate data against a Pydantic schema.
        
        Args:
            data: Dictionary to validate
            schema: Pydantic model class
            
        Returns:
            Validated model instance or None if validation fails
        """
        try:
            return schema(**data)
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e.error_count()} validation errors for {schema.__name__}")
            for error in e.errors():
                logger.error(f"  {error['loc']}")
                logger.error(f"    {error['msg']} [type={error['type']}, input_value={error.get('input', 'N/A')}, input_type={type(error.get('input', None)).__name__}]")
            logger.debug(f"Failed data keys: {list(data.keys())}")
            logger.debug(f"Full data: {json.dumps(data, indent=2, default=str)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in validation: {e}")
            return None
    
    def _get_fallback_response(self, error_message: str, raw_response: str = "") -> Dict[str, Any]:
        """
        Returns a safe fallback response structure when AI analysis fails.
        """
        return {
            "summary": error_message,
            "score": 50,
            "insights": ["Unable to parse AI response"],
            "error": error_message,
            "raw_response": raw_response,
            "status": "error"
        }
