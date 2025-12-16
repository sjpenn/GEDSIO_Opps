from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalLLM")

app = FastAPI(title="Local LLM Server")

# Global model state
_model = None
_tokenizer = None
MODEL_PATH = "mistralai/Mistral-7B-Instruct-v0.3"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = MODEL_PATH
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class ChatCompletionResponse(BaseModel):
    content: str
    model: str

@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    global _model, _tokenizer
    try:
        from mlx_lm import load
        logger.info(f"Loading model: {MODEL_PATH}...")
        _model, _tokenizer = load(MODEL_PATH)
        logger.info("Model loaded successfully.")
    except ImportError:
        logger.error("mlx_lm not installed. Please install it with: pip install mlx_lm")
        raise RuntimeError("mlx_lm not installed")

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def generate_chat(request: ChatCompletionRequest):
    global _model, _tokenizer
    
    if not _model or not _tokenizer:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        from mlx_lm import generate
        
        # Format messages using tokenizer's template
        # Convert pydantic models to dicts
        messages_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
        
        prompt = _tokenizer.apply_chat_template(
            messages_dicts, 
            tokenize=False, 
            add_generation_prompt=True
        )

        logger.info("Generating response...")
        response_text = generate(
            _model, 
            _tokenizer, 
            prompt=prompt, 
            verbose=True, 
            max_tokens=request.max_tokens,
        )
        
        return ChatCompletionResponse(
            content=response_text,
            model=MODEL_PATH
        )

    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
