# LangChain Explainer Migration Summary

The `langchain_explainer.py` file has been successfully moved from the API service layer to the NLP package.

## Changes Made

### 1. Created New File
- **Location**: `packages/nlp/src/explainability/langchain_explainer.py`
- **Changes**: 
  - Now accepts optional `settings` parameter in `__init__`
  - Falls back to importing settings from `apps/api/src/config` if not provided
  - Fully maintained LLM provider support (OpenAI, Anthropic, Groq, Ollama)

### 2. Updated Package Exports
- **File**: `packages/nlp/src/explainability/__init__.py`
- Added `LangChainExplainer` to package exports

### 3. Updated API Service
- **File**: `apps/api/src/services/explanation_service.py`
- Now imports from: `nlp.src.explainability` (primary)
- Fallback to local import if nlp package not available
- Passes `settings` to `LangChainExplainer` constructor

## Cleanup Required

⚠️ **Manual step**: Delete the old file that's no longer used:
```bash
# Delete the old langchain_explainer from services
rm apps/api/src/services/langchain_explainer.py
```

## Why This Refactoring?

✅ **Better architecture**: Explainability logic now lives in the NLP package where it logically belongs  
✅ **Reusability**: NLP package can use LangChainExplainer independently  
✅ **Separation of concerns**: API service layer no longer contains NLP models  

## Testing

After cleanup, test that explanations still work:

```bash
# Start API
cd apps/api
uvicorn src.main:app --reload

# Make a recommendation request with explanations
curl -X POST http://localhost:8000/api/v1/recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "machine learning",
    "include_explanation": true
  }'
```

Explanations should still be generated using your configured provider (Groq, OpenAI, etc.).
