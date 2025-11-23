import asyncio
import os
from fedops_core.settings import settings
import google.generativeai as genai

async def verify_model():
    print(f"Current configured model: {settings.LLM_MODEL}")
    
    if settings.LLM_MODEL != "gemini-3-pro-preview":
        print("ERROR: Model is not set to gemini-3-pro-preview")
        return

    if not settings.GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY is not set")
        return

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    
    try:
        print(f"Testing generation with model: {settings.LLM_MODEL}...")
        model = genai.GenerativeModel(settings.LLM_MODEL)
        response = await model.generate_content_async("Hello, are you Gemini 3?")
        print("Generation successful!")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"ERROR during generation: {e}")

if __name__ == "__main__":
    asyncio.run(verify_model())
