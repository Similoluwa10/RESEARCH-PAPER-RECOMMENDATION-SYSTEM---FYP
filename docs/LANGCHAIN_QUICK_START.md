# LangChain Explainability - Quick Start (5 minutes)

## TL;DR - Get Running in 5 Steps

### Step 1: Install Dependencies
```bash
cd apps/api
pip install -r requirements.txt
```

### Step 2: Configure Provider (Choose ONE)

**For Groq (Recommended - Free & Fast):**
```bash
# Get free API key from https://console.groq.com
echo "LANGCHAIN_PROVIDER=groq" >> .env
echo "GROQ_API_KEY=gsk_paste_your_key_here" >> .env
```

**For OpenAI (Fast, Paid):**
```bash
# Create .env file with:
echo "LANGCHAIN_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=sk_test_paste_your_key_here" >> .env
```

**For Ollama (Free, Local):**
```bash
# In another terminal, first start Ollama:
ollama serve

# Then in your project's .env:
echo "LANGCHAIN_PROVIDER=ollama" >> .env
```

**For Anthropic (Claude, Paid):**
```bash
echo "LANGCHAIN_PROVIDER=anthropic" >> .env
echo "ANTHROPIC_API_KEY=sk-ant_paste_your_key_here" >> .env
```

### Step 3: Start API Server
```bash
python -m uvicorn src.main:app --reload
```

### Step 4: Test It Works
```bash
# In new terminal:
curl http://localhost:8000/api/v1/health
```

### Step 5: Make Your First Request
```bash
curl -X POST http://localhost:8000/api/v1/recommendations/text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "deep learning neural networks",
    "top_k": 3,
    "include_explanation": true
  }'
```

**Response will include explanations!** 🎉

---

## What Just Happened?

```
Your Query
    ↓
API receives request
    ↓
Finds similar papers (using embeddings)
    ↓
For each paper:
    • Extracts key matching terms
    • Asks LLM (GPT, Claude, or Mistral) "Why is this relevant?"
    ↓
LLM generates explanation
    ↓
Returns: title + explanation + reasoning steps
```

---

## Example Response

```json
{
  "recommendations": [
    {
      "title": "Attention Is All You Need",
      "similarity_score": 0.89,
      "explanation": {
        "summary": "This paper introduces the Transformer architecture, which is fundamental to modern deep learning and neural networks.",
        "reasoning_steps": "1. Main concepts: deep learning, neural networks, architecture\n2. The Transformer introduced attention mechanisms...",
        "key_terms": ["neural networks", "architecture", "attention"],
        "confidence": "high"
      }
    }
  ]
}
```

---

## Troubleshooting

### "API key not found"
- Make sure `.env` file exists in `apps/api/` folder
- Check the key name matches: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OLLAMA_*`

### "Ollama connection refused"
- Run `ollama serve` in another terminal before starting API
- Make sure `LANGCHAIN_PROVIDER=ollama` is set

### "No explanation in response"
- Check that `"include_explanation": true` is in your request
- Check API logs - may have fallen back to heuristic explanation

---

## Quick Reference

| Provider | Setup | Cost | Speed |
|----------|-------|------|-------|
| **Groq** | Just get API key | Free | ⚡ Super fast (300-500ms) |
| OpenAI | Just get API key | $0.002/explanation | Fast (1-2s) |
| Anthropic | Just get API key | $0.0015/explanation | Fast (1-2s) |
| Ollama | `ollama pull mistral` | Free | Medium (2-5s) |

**Recommendation**: Use Groq for free, unlimited, production-ready explanations!

---

## Next Steps

- Read [LANGCHAIN_EXPLAINABILITY_SETUP.md](./LANGCHAIN_EXPLAINABILITY_SETUP.md) for detailed configuration
- Monitor `/api/v1/health/cache/stats` to see caching performance
- Integrate explanations into frontend (coming next)

---

**Need help?** Check the detailed setup guide or the logs from your API server.
