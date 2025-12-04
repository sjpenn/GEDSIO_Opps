# OpenRouter Integration - Quick Reference

## ✅ Implementation Complete

All extraction errors have been fixed with robust error handling and OpenRouter model support.

## 🚀 Quick Start

### Current Configuration
- **Provider**: OpenRouter
- **Model**: DeepSeek R1 (default)
- **API Key**: Already configured in `.env`

### Switch Models

Edit your `.env` file and change the `LLM_MODEL` value:

```bash
# Choose one:
LLM_MODEL=deepseek/deepseek-r1              # Default - Best for structured extraction
LLM_MODEL=google/gemini-3-pro-preview       # Fast PDF analysis
LLM_MODEL=google/gemini-2.0-flash-exp       # Very fast
LLM_MODEL=qwen/qwen-2.5-32b-instruct        # High accuracy
LLM_MODEL=mistralai/mistral-large-2         # Tool calling
LLM_MODEL=anthropic/claude-3.5-sonnet       # Complex reasoning
```

### Test Models

```bash
cd /Users/sjpenn/SitesAgents/GEDSIO_Opps/fedops

# Test current model
python test_models.py --mode current

# Compare all models
python test_models.py --mode compare

# Test specific model
python test_models.py --mode single --model "google/gemini-3-pro-preview"
```

## 📚 Documentation

- **Full Guide**: [docs/OPENROUTER_MODELS.md](docs/OPENROUTER_MODELS.md)
- **Environment Template**: [.env.example](.env.example)

## 🔧 What Was Fixed

1. **Error Handling**: All agents now handle `None` responses gracefully
2. **Retry Logic**: Automatic retry with exponential backoff
3. **JSON Extraction**: Multiple strategies to extract JSON from responses
4. **Fallback Models**: Automatic fallback if primary model fails
5. **Logging**: Detailed logging for debugging

## 🎯 Key Files Changed

- `fedops_core/settings.py` - Model configuration
- `fedops_core/services/ai_service.py` - Enhanced AI service
- `fedops_agents/past_performance_agent.py` - None-checking
- `fedops_agents/personnel_agent.py` - None-checking
- `fedops_agents/compliance_agent.py` - None-checking
- `fedops_agents/financial_agent.py` - None-checking

## ✨ Features

- ✅ Support for 6+ AI models
- ✅ Automatic retry on failure
- ✅ Fallback model support
- ✅ Comprehensive JSON extraction
- ✅ Detailed error logging
- ✅ Model comparison utility
- ✅ No more `'NoneType' object has no attribute 'get'` errors!

## 📝 Next Steps

1. Run analysis on an opportunity to test
2. Compare models using `test_models.py`
3. Choose the best model for your needs
4. Monitor logs for performance

---

**Need Help?** See [docs/OPENROUTER_MODELS.md](docs/OPENROUTER_MODELS.md) for detailed documentation.
