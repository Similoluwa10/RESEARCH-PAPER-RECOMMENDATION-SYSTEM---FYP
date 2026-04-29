# LangChain Explainability Setup Guide

This guide walks you through setting up and configuring the LangChain-based explainability module for generating detailed explanations of paper recommendations.

## Overview

The explainability system uses LangChain to generate multi-step reasoning explanations for why papers are recommended. It supports multiple LLM providers:

- **OpenAI** (GPT-3.5, GPT-4) - Best quality, requires API key
- **Ollama** (Local models like Mistral, Llama2) - Free, runs locally
- **Anthropic** (Claude) - High quality, requires API key

The system automatically falls back to heuristic explanations if the LLM provider is unavailable.

## Architecture

```
User Query
    ↓
Recommendation Service
    ├→ Generate recommendations (embeddings + similarity)
    └→ For each paper:
        ├→ Extract key terms (keyword matching)
        └→ Generate explanation (LLM or heuristic)
            ├→ LLM-based: Multi-step reasoning chains
            └→ Fallback: Template-based heuristic
```

## Installation

### 1. Install LangChain Dependencies

Navigate to the API directory and install Python packages:

```bash
cd apps/api
pip install -r requirements.txt
```

This installs:
- `langchain>=0.1.0` - Core framework
- `langchain-openai>=0.0.1` - OpenAI provider
- `langchain-anthropic>=0.1.0` - Claude provider
- `langchain-community>=0.0.1` - Ollama and other providers

### 2. Configure Environment Variables

Create or edit `apps/api/.env` with your chosen provider:

#### Option A: OpenAI (Recommended for quality)

```env
# Provider selection
LANGCHAIN_PROVIDER=openai
LANGCHAIN_CHAT_MODEL=gpt-3.5-turbo
LANGCHAIN_TEMPERATURE=0.3

# OpenAI API key (get from https://platform.openai.com/account/api-keys)
OPENAI_API_KEY=sk_test_...your_api_key_here...
```

**Cost**: ~$0.002 per recommendation explanation (GPT-3.5-turbo)

#### Option B: Ollama (Free, local)

First, install Ollama from https://ollama.ai

```bash
# Pull a model (one-time)
ollama pull mistral
# Or try: ollama pull llama2

# Start Ollama service (keep running in background)
ollama serve
```

Then configure `.env`:

```env
# Provider selection
LANGCHAIN_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
LANGCHAIN_TEMPERATURE=0.3
```

**Cost**: Free (runs on your machine)

#### Option C: Anthropic/Claude

```env
# Provider selection
LANGCHAIN_PROVIDER=anthropic
LANGCHAIN_TEMPERATURE=0.3

# Anthropic API key (get from https://console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-...your_api_key_here...
```

**Cost**: ~$0.0015 per recommendation explanation

### 3. Restart API Server

```bash
cd apps/api

# Kill any running uvicorn process
# Then restart:
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing the Implementation

### 1. Check System Health

```bash
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status": "ok", "database": "connected", "message": "API is healthy"}
```

### 2. View Cache Statistics

```bash
curl http://localhost:8000/api/v1/health/cache/stats

# Expected response:
{
  "embedding_cache": {
    "hits": 0,
    "misses": 0,
    "size": 0,
    "max_items": 5000
  },
  "recommendation_cache": {
    "hits": 0,
    "misses": 0,
    "size": 0,
    "max_items": 500
  }
}
```

### 3. Generate Recommendations with Explanations

Make a request to the recommendation endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "machine learning optimization algorithms",
    "top_k": 5,
    "include_explanation": true
  }'
```

Expected response structure:

```json
{
  "recommendations": [
    {
      "rank": 1,
      "paper_id": "2404.01234",
      "title": "Adam: A Method for Stochastic Optimization",
      "authors": ["Kingma, D.", "Ba, J."],
      "similarity_score": 0.87,
      "explanation": {
        "summary": "This paper is highly relevant due to its focus on optimization algorithms, which are core to implementing machine learning systems.",
        "reasoning_steps": "1. Main concepts: optimization, gradient descent, algorithms\n2. Paper discusses Adam optimizer...",
        "key_terms": ["optimization", "algorithms", "adaptive learning rate"],
        "confidence": "high"
      }
    }
  ],
  "search_time_ms": 234
}
```

### 4. Monitor Cache Performance

After running several searches, check cache stats again:

```bash
curl http://localhost:8000/api/v1/health/cache/stats
```

You should see:
- `hits` incrementing (repeated searches are cached)
- `misses` incrementing (new queries/papers)
- Hit rate improving over time

## Configuration Reference

| Setting | Default | Values | Purpose |
|---------|---------|--------|---------|
| `LANGCHAIN_PROVIDER` | `openai` | `openai`, `ollama`, `anthropic` | Which LLM to use |
| `LANGCHAIN_CHAT_MODEL` | `gpt-3.5-turbo` | Model name | OpenAI model selection |
| `LANGCHAIN_TEMPERATURE` | `0.3` | 0.0 - 1.0 | Reasoning consistency (lower = more deterministic) |
| `OPENAI_API_KEY` | `""` | Your API key | OpenAI authentication |
| `ANTHROPIC_API_KEY` | `""` | Your API key | Anthropic authentication |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL | Ollama service endpoint |
| `OLLAMA_MODEL` | `mistral` | Model name | Which Ollama model to use |

## Key Features

### 1. Multi-Step Reasoning
Each explanation includes:
- **Summary**: 1-2 sentence high-level explanation
- **Reasoning Steps**: Step-by-step analysis of why the paper matches
- **Key Terms**: Extracted matching concepts between query and paper
- **Confidence**: High/Medium/Low based on similarity score

### 2. Intelligent Caching
- Embedding cache (5000 items, 1 hour TTL): Avoids re-encoding repeated queries
- Recommendation cache (500 items, 1 hour TTL): Caches full recommendation results
- Cache stats endpoint: Monitor hit rates and performance

### 3. Graceful Degradation
If the LLM provider is unavailable:
- Heuristic explanations generated automatically
- Key term extraction from semantic similarity
- System remains fully functional

### 4. Thread-Safe
- All cache operations protected with locks
- Safe for concurrent API requests
- Production-ready

## Performance Considerations

### Latency
- **Cold start**: First explanation ~1-3 seconds (LLM generation)
- **Cached results**: <100ms (from recommendation cache)
- **Typical**: 2nd+ request same query ~100-200ms

### Cost (Per Recommendation)
- OpenAI GPT-3.5: ~$0.0015
- Anthropic Claude: ~$0.0015  
- Ollama (local): Free

### Optimization Tips
1. Use OpenAI's gpt-3.5-turbo (cheaper than gpt-4, nearly as good)
2. Keep LANGCHAIN_TEMPERATURE at 0.3 (faster inference, consistent results)
3. Monitor cache hit rates - high hit rates = lower cost
4. Use Ollama for development (free) and OpenAI for production (predictable cost)

## Troubleshooting

### Issue: "OPENAI_API_KEY not set in environment"

**Solution**: Make sure your `.env` file contains:
```env
OPENAI_API_KEY=sk_test_...
```

Verify the file exists at: `apps/api/.env`

### Issue: "Failed to initialize LangChain"

**Check the API server logs:**
```bash
# Look for error messages in stdout/stderr
```

**Try switching to Ollama** (if API keys are the problem):
```env
LANGCHAIN_PROVIDER=ollama
# Make sure Ollama is running:
# ollama serve
```

### Issue: Timeouts with explanations

**Reduce model complexity:**
```env
# For OpenAI - use faster model
LANGCHAIN_CHAT_MODEL=gpt-3.5-turbo

# For Ollama - use faster model
OLLAMA_MODEL=neural-chat  # Faster than mistral
```

### Issue: Cache stats showing no improvement

**Allow time for caching:**
- Cache is populated on first use
- Run several searches with identical queries to see cache benefits
- Check that `include_explanation=true` is passed to API

## Next Steps

1. ✅ **Install dependencies** - `pip install -r requirements.txt`
2. ✅ **Configure .env** - Add API keys for chosen provider
3. ✅ **Test explanation generation** - Use curl examples above
4. ✅ **Monitor performance** - Check cache stats endpoint
5. 📋 **Frontend integration** - Display explanations in UI (next phase)
6. 📋 **Advanced analysis** - Feature importance scoring (future)

## Code Structure

```
apps/api/src/services/
├── langchain_explainer.py      # LLM chains & provider initialization
├── explanation_service.py       # High-level explainability orchestration
├── embedding_service.py         # Embedding generation with caching
└── recommendation_service.py    # Recommendations with explanations

apps/api/src/routers/
└── health.py                    # Cache stats & health endpoints

apps/api/src/
└── config.py                    # Settings & environment variables
```

## References

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction.html)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Anthropic API Documentation](https://docs.anthropic.com)

