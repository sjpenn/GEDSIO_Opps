# OpenRouter Model Configuration Guide

## Overview

The FedOps system now supports multiple AI models through OpenRouter, allowing you to test and compare different models for document extraction and analysis.

## Supported Models

### DeepSeek R1 (Default)
- **Model ID**: `deepseek/deepseek-r1`
- **Best for**: Strong structured JSON/tool calling for precise entity extraction
- **Use case**: Complex document parsing, structured data extraction

### Gemini Models
- **Model ID**: `google/gemini-3-pro-preview` or `google/gemini-2.0-flash-exp`
- **Best for**: Native PDF support, fast analysis, zero-shot planning
- **Use case**: Quick analysis, complex requirements shredding

### Qwen 2.5
- **Model ID**: `qwen/qwen-2.5-32b-instruct`
- **Best for**: High accuracy in zero-shot relation/entity extraction
- **Use case**: Relationship mapping, entity extraction

### Mistral Large 2
- **Model ID**: `mistralai/mistral-large-2`
- **Best for**: Tool calling and schema support for lightweight extraction
- **Use case**: Fast, efficient extraction tasks

### Claude 3.5 Sonnet
- **Model ID**: `anthropic/claude-3.5-sonnet`
- **Best for**: Excellent reasoning and complex analysis
- **Use case**: Strategic analysis, risk assessment

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Required: OpenRouter API Key
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Override default settings
LLM_PROVIDER=openrouter
LLM_MODEL=deepseek/deepseek-r1
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096
LLM_MAX_RETRIES=3
LLM_FALLBACK_MODEL=google/gemini-2.0-flash-exp
```

### Switching Models

To switch models, update the `LLM_MODEL` setting in your `.env` file or in `fedops_core/settings.py`:

```python
# In settings.py
LLM_MODEL: str = "google/gemini-3-pro-preview"  # Change to desired model
```

Or set environment variable:
```bash
export LLM_MODEL="qwen/qwen-2.5-32b-instruct"
```

## Model-Specific Settings

### Temperature
- **Range**: 0.0 - 1.0
- **Default**: 0.1 (more deterministic for extraction)
- **Higher values**: More creative/varied responses
- **Lower values**: More consistent/deterministic responses

### Max Tokens
- **Default**: 4096
- **Recommendation**: Increase for complex documents (up to 8192)

### Retry Logic
- **Max Retries**: 3 (default)
- **Retry Delay**: 1.0 seconds with exponential backoff
- **Fallback Model**: Automatically tries fallback model if primary fails

## Testing Different Models

### Quick Test Script

Create a test file to compare models:

```python
import asyncio
from fedops_core.services.ai_service import AIService
from fedops_core.settings import settings

async def test_model(model_name: str):
    # Temporarily override model
    original_model = settings.LLM_MODEL
    settings.LLM_MODEL = model_name
    
    ai_service = AIService()
    
    prompt = """
    Extract the following information from this text and return as JSON:
    - Title
    - Department
    - Value
    
    Text: "RFP for IT Services at Department of Defense, estimated value $5M"
    """
    
    result = await ai_service.analyze_opportunity(prompt)
    print(f"\n{model_name}:")
    print(result)
    
    # Restore original model
    settings.LLM_MODEL = original_model

async def main():
    models = [
        "deepseek/deepseek-r1",
        "google/gemini-2.0-flash-exp",
        "qwen/qwen-2.5-32b-instruct",
        "mistralai/mistral-large-2"
    ]
    
    for model in models:
        await test_model(model)

if __name__ == "__main__":
    asyncio.run(main())
```

## Troubleshooting

### Error: "API Key not configured"
- Ensure `OPENROUTER_API_KEY` is set in your `.env` file
- Verify the `.env` file is in the correct directory

### Error: "Model not found"
- Check the model ID is correct (case-sensitive)
- Verify the model is available on OpenRouter
- Try the fallback model

### Poor Extraction Quality
- Try different models (some excel at different tasks)
- Adjust temperature (lower for more consistent results)
- Increase max_tokens for complex documents
- Check prompt formatting in `fedops_core/prompts.py`

### Rate Limiting
- OpenRouter has rate limits per model
- The system will automatically retry with exponential backoff
- Consider using the fallback model for high-volume operations

## Best Practices

1. **Start with DeepSeek R1**: Best overall performance for structured extraction
2. **Use Gemini for speed**: When you need fast results
3. **Try Qwen for accuracy**: When precision is critical
4. **Test multiple models**: Different models excel at different document types
5. **Monitor logs**: Check application logs for model performance and errors
6. **Set appropriate fallback**: Choose a reliable fallback model

## Getting an OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Add credits to your account
6. Copy the API key to your `.env` file

## Cost Considerations

Different models have different pricing on OpenRouter:
- **DeepSeek R1**: Very cost-effective
- **Gemini models**: Moderate pricing
- **Claude 3.5 Sonnet**: Higher cost but excellent quality
- **Qwen 2.5**: Cost-effective
- **Mistral**: Moderate pricing

Check current pricing at [OpenRouter Pricing](https://openrouter.ai/docs#models)
