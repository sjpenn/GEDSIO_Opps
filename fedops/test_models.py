"""
Model Testing Utility for FedOps

This script allows you to test different OpenRouter models with sample prompts
to compare their performance on document extraction tasks.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fedops_core.services.ai_service import AIService
from fedops_core.settings import settings


SAMPLE_PROMPTS = {
    "extraction": """
    Extract the following information from this RFP text and return ONLY a valid JSON object:
    
    Text: "Request for Proposal: IT Infrastructure Modernization for Department of Defense. 
    NAICS Code: 541512. Set-Aside: Small Business. Estimated Contract Value: $5,000,000 - $8,000,000.
    Period of Performance: 36 months. Key Personnel Required: Project Manager (Secret Clearance), 
    Technical Lead (Top Secret), 5 Software Engineers. Labor Categories: PM-III, Tech Lead-IV, 
    Software Engineer-II. Cybersecurity Requirements: NIST 800-171 compliance, FedRAMP Moderate."
    
    Return JSON with these fields:
    {
        "title": "...",
        "department": "...",
        "naics_code": "...",
        "set_aside": "...",
        "estimated_value": {"min": 0, "max": 0},
        "period_months": 0,
        "key_personnel": [],
        "labor_categories": [],
        "security_requirements": []
    }
    """,
    
    "analysis": """
    Analyze this opportunity and provide a risk assessment. Return ONLY valid JSON:
    
    Opportunity: "RFP for Cloud Migration Services at VA. Requires FedRAMP High certification,
    which we don't currently have. Incumbent is a large business with 10 years on contract.
    Our team has only 2 years of VA experience. Contract value is $50M over 5 years."
    
    Return JSON:
    {
        "risk_score": 0-100,
        "high_risks": [],
        "medium_risks": [],
        "recommendation": "BID/NO-BID",
        "summary": "..."
    }
    """
}


async def test_model(model_name: str, prompt_type: str = "extraction"):
    """Test a specific model with a sample prompt."""
    print(f"\n{'='*80}")
    print(f"Testing Model: {model_name}")
    print(f"Prompt Type: {prompt_type}")
    print(f"{'='*80}\n")
    
    # Temporarily override model
    original_model = settings.LLM_MODEL
    settings.LLM_MODEL = model_name
    
    try:
        ai_service = AIService()
        prompt = SAMPLE_PROMPTS.get(prompt_type, SAMPLE_PROMPTS["extraction"])
        
        print("Sending request...")
        result = await ai_service.analyze_opportunity(prompt)
        
        print("\n✅ Response received:")
        print("-" * 80)
        
        if isinstance(result, dict):
            import json
            print(json.dumps(result, indent=2))
            
            # Check for errors
            if result.get("error"):
                print(f"\n⚠️  Warning: Response contains error: {result.get('error')}")
            if result.get("status") == "error":
                print(f"\n❌ Error status in response")
        else:
            print(result)
            
    except Exception as e:
        print(f"\n❌ Error testing model {model_name}:")
        print(f"   {str(e)}")
    finally:
        # Restore original model
        settings.LLM_MODEL = original_model


async def compare_models(prompt_type: str = "extraction"):
    """Compare multiple models side-by-side."""
    models = [
        "deepseek/deepseek-r1",
        "google/gemini-2.0-flash-exp",
        "qwen/qwen-2.5-32b-instruct",
        "mistralai/mistral-large-2",
    ]
    
    print("\n" + "="*80)
    print("OPENROUTER MODEL COMPARISON TEST")
    print("="*80)
    print(f"\nCurrent Settings:")
    print(f"  Provider: {settings.LLM_PROVIDER}")
    print(f"  Temperature: {settings.LLM_TEMPERATURE}")
    print(f"  Max Tokens: {settings.LLM_MAX_TOKENS}")
    print(f"  Max Retries: {settings.LLM_MAX_RETRIES}")
    print(f"  Fallback Model: {settings.LLM_FALLBACK_MODEL}")
    
    for model in models:
        await test_model(model, prompt_type)
        await asyncio.sleep(1)  # Rate limiting
    
    print("\n" + "="*80)
    print("COMPARISON COMPLETE")
    print("="*80)


async def test_current_model():
    """Test the currently configured model."""
    print("\n" + "="*80)
    print("TESTING CURRENT MODEL CONFIGURATION")
    print("="*80)
    print(f"\nProvider: {settings.LLM_PROVIDER}")
    print(f"Model: {settings.LLM_MODEL}")
    
    await test_model(settings.LLM_MODEL, "extraction")
    await test_model(settings.LLM_MODEL, "analysis")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OpenRouter models for FedOps")
    parser.add_argument(
        "--mode",
        choices=["current", "compare", "single"],
        default="current",
        help="Test mode: current (test configured model), compare (test all models), single (test specific model)"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Specific model to test (for single mode)"
    )
    parser.add_argument(
        "--prompt",
        choices=["extraction", "analysis"],
        default="extraction",
        help="Type of prompt to test"
    )
    
    args = parser.parse_args()
    
    # Check API key
    if not settings.OPENROUTER_API_KEY and settings.LLM_PROVIDER == "openrouter":
        print("\n❌ Error: OPENROUTER_API_KEY not configured!")
        print("   Please set OPENROUTER_API_KEY in your .env file")
        sys.exit(1)
    
    if args.mode == "current":
        asyncio.run(test_current_model())
    elif args.mode == "compare":
        asyncio.run(compare_models(args.prompt))
    elif args.mode == "single":
        if not args.model:
            print("❌ Error: --model required for single mode")
            sys.exit(1)
        asyncio.run(test_model(args.model, args.prompt))


if __name__ == "__main__":
    main()
