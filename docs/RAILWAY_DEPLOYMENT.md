# Railway Deployment Guide

## Overview

This guide walks you through deploying your Research Recommendation System on Railway.

Railway supports deploying:
1. **Backend API** (FastAPI, Python)
2. **Frontend** (Next.js, Node.js)
3. **Database** (PostgreSQL with pgvector)

## Prerequisites

1. **Railway Account**: Sign up at https://railway.app
2. **GitHub Account**: Your code repository (Railway deploys from GitHub)
3. **GitHub CLI** (optional): For pushing code

## Step 1: Push Your Code to GitHub

If not already done, push your project to GitHub:

```bash
git init
git add .
git commit -m "Initial commit: Research Recommendation System"
git remote add origin https://github.com/YOUR_USERNAME/recommendation-system.git
git branch -M main
git push -u origin main
```

## Step 2: Set Up Railway Project

### Option A: Deploy via Railway Dashboard (Easiest)

1. Go to https://railway.app/dashboard
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select your repository
4. Choose the repository and authorize Railway
5. Select the root directory (leave as `/` for monorepo)

### Option B: Deploy via Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize project in your repo root
railway init

# This will guide you through setup
```

## Step 3: Create PostgreSQL Database

In Railway Dashboard:

1. Click **"Create"** → **"Database"** → **"PostgreSQL"**
2. This automatically creates a PostgreSQL service
3. Railway will expose `DATABASE_URL` environment variable

Enable **pgvector** extension (required for embeddings):

1. Go to your PostgreSQL service in Railway
2. Click **"Connect"** → **"PostgreSQL Shell**
3. Run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

## Step 4: Configure Environment Variables

### For API Service

Go to Railway Dashboard → API Service → Variables tab → Add:

```env
# Application
APP_NAME=Research Paper Recommender API
APP_ENV=production
DEBUG=false
API_V1_PREFIX=/api/v1

# Database (Railway auto-generates, just verify it exists)
DATABASE_URL=postgresql://user:password@postgres-service:5432/railway

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (add your frontend URL)
CORS_ORIGINS=["https://your-frontend.railway.app","https://yourdomain.com"]

# Embedding
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EMBEDDING_BATCH_SIZE=64

# Caching
EMBEDDING_CACHE_TTL_SECONDS=3600
EMBEDDING_CACHE_MAX_ITEMS=10000
RECOMMENDATION_CACHE_TTL_SECONDS=1800
RECOMMENDATION_CACHE_MAX_ITEMS=5000

# Logging
LOG_LEVEL=INFO

# LangChain (Choose one provider)
LANGCHAIN_PROVIDER=groq
GROQ_API_KEY=gsk_...your_api_key...
GROQ_MODEL=llama-3.3-70b-versatile
LANGCHAIN_TEMPERATURE=0.3

# OR for Ollama
# LANGCHAIN_PROVIDER=ollama
# OLLAMA_BASE_URL=http://ollama-service:11434
# OLLAMA_MODEL=mistral

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your_google_client_id

# Hugging Face
HUGGINGFACE_API_KEY=hf_...your_api_key...
```

### For Frontend Service

Go to Railway Dashboard → Web Service → Variables tab → Add:

```env
NEXT_PUBLIC_API_URL=https://your-api.railway.app/api/v1
NODE_ENV=production
```

## Step 5: Deploy API Service

1. In Railway Dashboard, create a **new service**
2. Select **"Deploy from GitHub"** or **"Docker"**
3. If using Docker:
   - Set Dockerfile Path: `infrastructure/docker/Dockerfile.api`
   - Working Directory: `/app`
4. Configure the service:
   - **Port**: 8000
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

## Step 6: Deploy Frontend Service

1. Create another service for the frontend
2. Set Dockerfile Path: `infrastructure/docker/Dockerfile.web`
3. Configure:
   - **Port**: 3000
   - Build Args: `NEXT_PUBLIC_API_URL=https://your-api.railway.app/api/v1`

## Step 7: Initialize Database

After API is running, initialize the database schema:

```bash
# Get your Railway API URL
API_URL=https://your-api.railway.app

# Run migrations (if you have them)
# Or hit the health endpoint to trigger initialization
curl https://your-api.railway.app/api/v1/health
```

## Step 8: Verify Deployment

Test your deployed API:

```bash
# Health check
curl https://your-api.railway.app/api/v1/health

# Test recommendations (with auth if required)
curl -X POST https://your-api.railway.app/api/v1/recommendations/text \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "machine learning",
    "include_explanation": true
  }'
```

## Architecture on Railway

```
┌─────────────────────────────────────┐
│        Railway Dashboard            │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────┐   ┌─────────┐   │
│  │  Frontend    │   │  API    │   │
│  │  (Next.js)   │→→→│(FastAPI)│   │
│  │  Port: 3000  │   │Port: 8000   │
│  └──────────────┘   └────┬────┘   │
│                          │        │
│                     ┌────v─────┐  │
│                     │ Database │  │
│                     │PostgreSQL│  │
│                     │ pgvector │  │
│                     └──────────┘  │
│                                   │
└─────────────────────────────────────┘

External Services:
- Groq API (explanations)
- Hugging Face (embeddings if cached)
```

## Monitoring & Logs

View your service logs in Railway Dashboard:

1. Go to your service
2. Click **"Deployments"** tab
3. Select the latest deployment
4. View **"Logs"** in real-time

Common things to check:
```
✓ "✓ Using LangChain for explanations" = Groq initialized
✓ "Uvicorn running on 0.0.0.0:8000" = API started
✓ "Database connected" = PostgreSQL connected
```

## Troubleshooting

### Issue 1: Database Connection Failed
- Check `DATABASE_URL` is set correctly in Environment Variables
- Ensure PostgreSQL service is running
- Verify pgvector extension is installed

### Issue 2: API Won't Start
- Check logs for missing environment variables
- Verify Docker build path is correct
- Check Python version compatibility (3.11+)

### Issue 3: Frontend Can't Connect to API
- Set `NEXT_PUBLIC_API_URL` correctly (full HTTPS URL)
- Check CORS settings in API
- Verify API is publicly accessible

### Issue 4: LangChain Failures
- Verify Groq API key is correct and has quota
- Check `LANGCHAIN_PROVIDER` is set
- Review API logs for connection errors

## Advanced: Custom Domain

1. In Railway Dashboard → Your Project → Settings
2. Add a **Custom Domain**
3. Update DNS records (CNAME to Railway)
4. Update `CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` if needed

## Cost Estimates

Railway pricing (as of May 2026):
- **Compute**: $0.000631/hour per vCPU (very cheap)
- **Memory**: $0.000100/hour per GB
- **PostgreSQL Database**: Included (free tier) or $5/month (pro)
- **Storage**: $0.50/month per GB

**Estimated monthly cost**:
- API (1 vCPU, 512MB RAM): ~$4.50
- Frontend (512MB RAM): ~$3.50
- Database (PostgreSQL): Free (if within limits) or $5
- **Total**: ~$13/month (very affordable!)

## Continuous Deployment

Railway automatically deploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update recommendation logic"
git push origin main

# Railway automatically deploys within seconds!
# Check deployment status in Dashboard
```

## Security Best Practices

1. **Don't commit .env files** - Use Railway environment variables only
2. **Use strong JWT secret** - Generated by you, never shared
3. **Restrict CORS** - Only allow your frontend domain
4. **API Keys** - Rotate Groq/HuggingFace keys regularly
5. **Database** - Railway provides SSL/TLS encryption by default

## Environment-Specific Configuration

Create different projects for different environments:

```
Production (production branch):
- Full database snapshots
- Monitoring enabled
- High availability replicas

Staging (develop branch):
- Separate database
- Same configuration
- For testing before production

Development (main branch):
- For testing new features
```

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create Railway project
3. ✅ Configure environment variables
4. ✅ Deploy services
5. ✅ Initialize database
6. ✅ Test endpoints
7. ✅ Monitor logs and performance
8. ✅ Set up custom domain
9. ✅ Enable CI/CD monitoring

## Useful Links

- Railway Docs: https://docs.railway.app
- Railway CLI: https://docs.railway.app/reference/cli-api
- PostgreSQL Docs: https://www.postgresql.org/docs/
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Next.js Production: https://nextjs.org/docs/advanced-features/output-file-tracing

## Support

For Railway-specific issues:
- Check Railway status: https://status.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app

For your application issues:
- Check API logs in Railway Dashboard
- Run health check endpoint: `/api/v1/health`
- Test locally before pushing: `uvicorn src.main:app --reload`

---

**Deployment Status**: Ready for Railway 🚀

Questions? Let me know!
