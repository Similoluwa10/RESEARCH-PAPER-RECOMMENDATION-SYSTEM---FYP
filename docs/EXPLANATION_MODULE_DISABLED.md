# Explanation Module - Disabled

## Overview
The explanation module (LangChain-based explainability layer) has been **DISABLED** but not removed from the codebase.

## What Was Disabled

The following components have been disabled via code comments:

### 1. ExplanationService Initialization
- **File**: `apps/api/src/services/recommendation_service.py`
- **Line**: ~48 (in `__init__` method)
- **Change**: Commented out `self.explanation_service = ExplanationService()`
- **Status**: The import statement remains for easy re-enabling

### 2. Explanation Generation Calls
- **File**: `apps/api/src/services/recommendation_service.py`
- **Location 1**: `get_recommendations_for_text()` method (~134-139)
  - Changed to always return `explanation = None`
  - Original code commented out

- **Location 2**: `get_similar_papers()` method (~215-220)
  - Changed to always return `explanation = None`
  - Original code commented out

## How to Re-Enable

To re-enable the explanation module, follow these steps:

### Step 1: Uncomment Service Initialization
In `apps/api/src/services/recommendation_service.py`, find the `__init__` method and uncomment:
```python
self.explanation_service = ExplanationService()
```

### Step 2: Uncomment Explanation Generation in get_recommendations_for_text()
In the `get_recommendations_for_text()` method, uncomment the explanation generation block:
```python
explanation = (
    self.explanation_service.generate_explanation(
        query_text=text,
        paper=item["paper"],
        similarity_score=bounded_score,
    )
    if include_explanations
    else None
)
```

### Step 3: Uncomment Explanation Generation in get_similar_papers()
In the `get_similar_papers()` method, uncomment the explanation generation block:
```python
"explanation": (
    self.explanation_service.generate_explanation(
        query_text=query_text,
        paper=item["paper"],
        similarity_score=max(0.0, min(1.0, float(item["score"]))),
    )
    if include_explanations
    else None
),
```

### Step 4: Verify LangChain Configuration
Ensure your `.env` file has the correct LangChain settings:
```env
LANGCHAIN_PROVIDER=groq  # or openai, ollama, anthropic
LANGCHAIN_CHAT_MODEL=mixtral-8x7b-32768
LANGCHAIN_TEMPERATURE=0.7
LANGCHAIN_TIMEOUT_SECONDS=30
```

## Impact on API Responses

### With Explanation Disabled
Recommendation responses will have `explanation: null`:
```json
{
  "recommendations": [
    {
      "paper": { ... },
      "score": 0.87,
      "explanation": null
    }
  ]
}
```

### With Explanation Enabled (After Re-enabling)
Recommendation responses will include explanation data:
```json
{
  "recommendations": [
    {
      "paper": { ... },
      "score": 0.87,
      "explanation": {
        "summary": "..."
      }
    }
  ]
}
```

## Files Modified
- `apps/api/src/services/recommendation_service.py`
  - Lines in `__init__()` method
  - Lines in `get_recommendations_for_text()` method
  - Lines in `get_similar_papers()` method

## Notes
- The `ExplanationService` class and all related explanation modules remain untouched in the codebase
- Database schema and models related to explanations are unchanged
- The `include_explanation` parameter in API requests is still accepted but currently ignored
- No dependencies were removed, so re-enabling requires no additional setup beyond uncommenting code
