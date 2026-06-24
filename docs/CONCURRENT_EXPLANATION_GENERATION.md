# Concurrent Async Explanation Generation

## Overview

The explainability layer has been upgraded to use **concurrent async/await** patterns for generating explanations. This means multiple LLM explanation requests run **in parallel** instead of sequentially, dramatically improving response times.

### Performance Improvement

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| 5 recommendations | ~10-15s | 2-3s | **5-7x faster** |
| 10 recommendations | ~20-30s | 3-5s | **6-10x faster** |
| 20 recommendations | ~40-60s | 5-8s | **8-12x faster** |

*Assumes 2-3 seconds per LLM explanation call with 5 concurrent slots*

---

## Architecture Changes

### 1. **LangChainExplainer** - Now Async

**File:** `apps/api/src/services/langchain_explainer.py`

```python
# Before: Synchronous blocking call
def generate_explanation(self, query: str, paper: Any, ...):
    reasoning_result = self.llm.invoke([reasoning_message])      # Blocks
    summary_result = self.llm.invoke([summary_message])          # Blocks
    return {...}

# After: Async non-blocking calls
async def generate_explanation(self, query: str, paper: Any, ...):
    reasoning_result = await self.llm.ainvoke([reasoning_message])  # Non-blocking
    summary_result = await self.llm.ainvoke([summary_message])      # Non-blocking
    return {...}
```

**Key Changes:**
- Method is now `async def`
- Uses `await self.llm.ainvoke()` instead of `self.llm.invoke()`
- LangChain handles the async operations internally

### 2. **ExplanationService** - Now Concurrent

**File:** `apps/api/src/services/explanation_service.py`

```python
class ExplanationService:
    def __init__(self, max_concurrent: int = 5):
        # Semaphore controls max concurrent LLM calls
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def generate_explanation(self, ...):
        # Acquire semaphore slot (max 5 concurrent)
        async with self.semaphore:
            result = await self.langchain_explainer.generate_explanation(...)
        return result
```

**Key Features:**
- **Semaphore Control**: Limits concurrent LLM calls to avoid rate limiting
- **Graceful Degradation**: Falls back to heuristics if LLM fails
- **Thread-Safe**: Semaphore handles concurrent access safely

### 3. **RecommendationService** - Now Parallelizes

**File:** `apps/api/src/services/recommendation_service.py`

```python
# Before: Sequential explanation generation
recommendations = []
for item in matches:
    explanation = self.explanation_service.generate_explanation(...)  # One at a time
    recommendations.append(...)

# After: Parallel explanation generation
explanation_tasks = [
    self.explanation_service.generate_explanation(...)
    for item in matches
]
explanations = await asyncio.gather(*explanation_tasks, return_exceptions=True)
recommendations = [... for item, exp in zip(matches, explanations)]
```

**Key Changes:**
- Creates list of explanation tasks (doesn't execute yet)
- Uses `asyncio.gather()` to run all tasks concurrently
- `return_exceptions=True` prevents one failure from stopping all

---

## Configuration

### Environment Variable

Add to `apps/api/.env`:

```env
# Concurrent Explanation Generation (LLM)
# Max concurrent LLM calls for generating explanations
# Higher = more parallelism but may hit rate limits
# Lower = safer but slower explanations
# Recommended: 3-10 depending on LLM provider limits
MAX_CONCURRENT_EXPLANATIONS=5
```

### Recommended Values by Provider

| Provider | Recommended | Max Safe | Notes |
|----------|------------|----------|-------|
| **Groq** | 5-10 | 20 | Very fast, high rate limits |
| **OpenAI** | 3-5 | 10 | Standard rate limits |
| **Anthropic** | 2-3 | 5 | More conservative limits |
| **Ollama** | 2-4 | 4 | Local deployment, CPU-bound |

---

## Execution Flow

### Sequential Request (Old)
```
Request received for 5 papers
│
├─ Paper 1 → LLM Explanation (2-3s) → Response
├─ Paper 2 → LLM Explanation (2-3s) → Response
├─ Paper 3 → LLM Explanation (2-3s) → Response
├─ Paper 4 → LLM Explanation (2-3s) → Response
└─ Paper 5 → LLM Explanation (2-3s) → Response
│
Total: ~10-15 seconds
```

### Concurrent Request (New)
```
Request received for 5 papers
│
├─ Paper 1 → ┐
├─ Paper 2 → ├─ LLM (max 5 concurrent, 2-3s) ─┐
├─ Paper 3 → │                                  ├─ All responses
├─ Paper 4 → │                                  │
└─ Paper 5 → ┘                                  ┘
│
Total: ~2-3 seconds (same as 1 paper!)
```

---

## Semaphore Behavior

### Example: 10 papers with max_concurrent=5

```
Time: 0s
  Papers 1-5 start explanation generation

Time: 2-3s
  Papers 1-5 complete
  Papers 6-10 start explanation generation

Time: 4-6s
  Papers 6-10 complete
  All responses ready

Total: ~4-6 seconds instead of 20-30 seconds
```

The semaphore automatically queues papers when all slots are occupied.

---

## Error Handling

### Graceful Degradation

If an individual explanation fails:
```python
# Errors don't crash entire response
explanations = await asyncio.gather(*explanation_tasks, return_exceptions=True)

for item, explanation in zip(matches, explanations):
    if isinstance(explanation, Exception):
        # Return None for this paper's explanation
        explanation = None
```

**Result:** Some papers get explanations, others don't (vs. failing entire request)

### Fallback to Heuristics

If LLM fails:
1. First failure caught
2. `_llm_failed` flag set
3. All subsequent calls use heuristic fallbacks
4. No repeated API failures

---

## Monitoring & Debugging

### Enable Debug Logging

In `apps/api/src/main.py` or `.env`:
```python
LOG_LEVEL=DEBUG
```

You'll see logs like:
```
Generating 10 explanations concurrently...
LangChain initialized with provider: groq (max 5 concurrent)
Extracted key terms: ['machine', 'learning', 'bug', 'detection']
```

### Performance Metrics

Check how many explanations are being batched:
```python
# In logs
"Generating 10 explanations concurrently..."
```

Monitor semaphore usage (via logging):
```
# When semaphore is full:
Async with semaphore: waiting for slot...
```

---

## Testing the Async Implementation

### 1. Basic Test

```python
# In test file
import asyncio
from src.services.recommendation_service import RecommendationService

async def test_concurrent_explanations():
    service = RecommendationService(db)
    result = await service.get_recommendations_for_text(
        "machine learning bug detection",
        include_explanations=True
    )
    assert len(result.recommendations) > 0
    assert all(r.explanation is not None for r in result.recommendations)

# Run test
asyncio.run(test_concurrent_explanations())
```

### 2. Performance Comparison

```python
import time

# Measure time for 10 papers
start = time.time()
result = await service.get_recommendations_for_text(query, include_explanations=True)
elapsed = time.time() - start

print(f"Generated {len(result.recommendations)} explanations in {elapsed:.2f}s")
# Expected: ~3-5s for 10 papers (vs ~20-30s before)
```

---

## Important Notes

### 1. Async Context Required
The endpoints already use `async def`, so they automatically support async operations.

### 2. Backward Compatibility
- Synchronous calls still work (they just await the async calls)
- Fallback to heuristics works the same
- API responses unchanged

### 3. Rate Limiting
- Adjust `MAX_CONCURRENT_EXPLANATIONS` if you hit rate limits
- Monitor API usage and scale accordingly
- Start conservative (3-5) then increase if safe

### 4. LLM Provider Specific
- **Groq**: Very fast, can handle higher concurrency (8-10)
- **OpenAI**: Moderate concurrency (3-5)
- **Anthropic**: Conservative (2-3)
- **Ollama**: Limited by local CPU (2-4)

---

## Performance Tips

1. **Adjust MAX_CONCURRENT_EXPLANATIONS**
   - Too low: Slower responses
   - Too high: Rate limit errors
   - Start at 5, monitor, adjust

2. **Cache Results**
   - Responses are already cached for 1 hour
   - Same query reuses cached explanations

3. **Monitor Token Usage**
   - Each explanation = 2 LLM calls
   - 10 papers = ~20 LLM calls
   - Budget accordingly for API costs

4. **Use Heuristic Fallback**
   - If LLM fails, system falls back gracefully
   - Users still get explanations (just simpler ones)
   - No failed requests

---

## Migration Checklist

- ✅ Updated `LangChainExplainer` to async
- ✅ Updated `ExplanationService` with semaphore
- ✅ Updated `RecommendationService` with `asyncio.gather()`
- ✅ Added `MAX_CONCURRENT_EXPLANATIONS` config
- ✅ Updated `.env` with default value
- ✅ Routers already async-compatible
- ✅ Error handling in place
- ⚠️ **TODO: Add comprehensive async tests**

---

## Future Improvements

1. **Metrics Collection**
   - Track concurrent explanation generation performance
   - Monitor queue depth
   - Analyze response time trends

2. **Adaptive Concurrency**
   - Auto-adjust `max_concurrent` based on response times
   - Implement backpressure mechanisms

3. **Result Streaming**
   - Stream explanations as they complete (Server-Sent Events)
   - Don't wait for all to finish before responding

4. **Explanation Caching**
   - Cache explanations separately from full recommendations
   - Reuse across queries when paper + query is similar
