# Choreo Deployment - Complete Guide Summary

## 📋 Overview

This guide walks you through deploying your **Research Recommendation System** (FastAPI backend + Next.js frontend + PostgreSQL database) to **WSO2 Choreo**.

### What You'll Deploy
- **API Service**: FastAPI backend (Python 3.11)
- **Web Service**: Next.js frontend (Node.js 18+)
- **Database Service**: PostgreSQL with pgvector extension
- **Networking**: Automatic HTTPS/TLS, Load balancing

### Key Benefits of Choreo
✅ No infrastructure management  
✅ Auto-scaling built-in  
✅ GitHub integration for CI/CD  
✅ Free tier available for testing  
✅ 99.5% uptime SLA (paid plans)  

---

## 🚀 Pre-Deployment Checklist

Before starting, ensure you have:

- [ ] **Choreo Account**: Created at https://console.choreo.dev
- [ ] **GitHub Account**: With repository access
- [ ] **Git Installed**: Verify with `git --version`
- [ ] **Docker Installed** (optional): For local testing with `docker-compose`
- [ ] **Code Repository**: Code pushed to GitHub
- [ ] **SSH Keys**: GitHub SSH keys configured (optional but recommended)

**Estimated Time**: 30-45 minutes for complete deployment

---

## 📚 Documentation Structure

This deployment includes the following documentation:

### Quick References
1. **CHOREO_QUICK_START.md** ⭐ **START HERE**
   - Step-by-step checklist for rapid deployment
   - Common issues and quick fixes
   - Expected results at each step

2. **CHOREO_DEPLOYMENT.md** (Comprehensive)
   - Detailed explanation of each step
   - Architecture overview
   - Troubleshooting guide
   - Performance optimization

3. **deployment-config.yaml** (Configuration Reference)
   - Service configuration specifications
   - Scaling recommendations
   - Cost estimation
   - Monitoring setup

4. **env-template.txt** (Environment Variables)
   - All required environment variables
   - Security best practices
   - How to generate secure values

5. **.github/workflows/deploy-choreo.yml** (Automated Deployment)
   - GitHub Actions workflow
   - Automated testing and building
   - Optional auto-deployment to Choreo

---

## ⚡ Quick Start (5 Steps)

### Step 1: Create Database
```
Choreo Console → Create → Service → PostgreSQL
- Database: research_recommender
- Save connection string
⏱️ Time: 5 minutes
```

### Step 2: Deploy API
```
Choreo Console → Create → Service → Build from GitHub
- Repository: [your-repo]
- Path: apps/api
- Secrets: DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY
- Deploy
⏱️ Time: 10 minutes
```

### Step 3: Deploy Web
```
Choreo Console → Create → Service → Build from GitHub
- Repository: [your-repo]
- Path: apps/web
- Build Args: NEXT_PUBLIC_API_URL=[API_URL]/api
- Deploy
⏱️ Time: 10 minutes
```

### Step 4: Initialize Database
```bash
cd infrastructure/database
alembic upgrade head
⏱️ Time: 2 minutes
```

### Step 5: Test
```bash
# Test API
curl https://[API-URL]/api/health

# Test Web
Visit https://[WEB-URL]

⏱️ Time: 5 minutes
```

---

## 🔧 Detailed Step-by-Step Guide

### Phase 1: Preparation (10 minutes)

#### 1.1 Prepare Environment
```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Save this output, you'll need it for API service

# Generate database password
openssl rand -base64 32
# Save this output for PostgreSQL setup
```

#### 1.2 Prepare GitHub Repository
```bash
# Ensure all code is committed
git status

# Push latest code
git push origin main
```

### Phase 2: Database Setup (10 minutes)

#### 2.1 Create PostgreSQL Service
1. Go to https://console.choreo.dev
2. Click **Create** → **Service** → **PostgreSQL**
3. Fill in:
   - **Service Name**: `research-db`
   - **Admin User**: `postgres_user`
   - **Admin Password**: [Use generated password]
   - **Database Name**: `research_recommender`
4. Click **Create**
5. Wait for service to be ready (🟢 status)
6. **Important**: Copy and save the connection details
   - Connection string: `postgresql://postgres_user:PASSWORD@HOST:5432/research_recommender`

#### 2.2 Note Database URL
Store this securely (password manager or Choreo secrets):
```
DATABASE_URL=postgresql://postgres_user:[PASSWORD]@[CHOREO_HOST]:5432/research_recommender
```

### Phase 3: API Deployment (15 minutes)

#### 3.1 Create API Service
1. Click **Create** → **Service** → **Build from GitHub**
2. Authorize Choreo with GitHub
3. Select your repository
4. Configure:
   - **Service Name**: `research-api`
   - **Repository Path**: `apps/api`
   - **Buildpack**: Python
5. Click **Next**

#### 3.2 Configure Build Settings
1. Set **Dockerfile**: `infrastructure/docker/Dockerfile.api`
2. Set **Build Context**: `/` (root of repository)
3. Click **Next**

#### 3.3 Add Secrets
Click **+ Add Secret** for each:

| Secret | Value |
|--------|-------|
| `DATABASE_URL` | `postgresql://postgres_user:PASSWORD@HOST:5432/research_recommender` |
| `JWT_SECRET_KEY` | [Generated in step 1.1] |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `GROQ_API_KEY` | [Get from https://console.groq.com] |

4. Click **Create**

#### 3.4 Deploy & Monitor
1. Click **Deploy** button
2. Monitor **Build Logs** (should take 3-5 minutes)
3. Wait for deployment to complete (status = **Running**)
4. **Copy the service URL** from service details
   - Example: `https://research-api-abc123.e1-us-cdp-1.choreoapis.com`

#### 3.5 Test API Service
```bash
# Test health endpoint
curl https://[API-URL]/api/health

# Expected response:
# {"status": "ok"}
```

### Phase 4: Web Frontend Deployment (15 minutes)

#### 4.1 Create Web Service
1. Click **Create** → **Service** → **Build from GitHub**
2. Configure:
   - **Service Name**: `research-web`
   - **Repository Path**: `apps/web`
   - **Buildpack**: Node.js
3. Click **Next**

#### 4.2 Configure Build Settings
1. Set **Dockerfile**: `infrastructure/docker/Dockerfile.web`
2. Set **Build Context**: `/`
3. Click **Next**

#### 4.3 Add Build Arguments
Click **+ Add Build Argument**:

| Argument | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://[API-URL]/api` |

Replace `[API-URL]` with the URL from Phase 3.

#### 4.4 Add Environment Variables
Click **+ Add Environment Variable**:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://[API-URL]/api` |

#### 4.5 Deploy & Monitor
1. Click **Deploy**
2. Monitor build logs
3. Wait for deployment to complete
4. **Copy the web service URL**
   - Example: `https://research-web-xyz789.e1-us-cdp-1.choreoapis.com`

#### 4.6 Test Web Service
```bash
# Test health
curl https://[WEB-URL]

# Or open in browser
# https://[WEB-URL]
```

### Phase 5: Database Initialization (5 minutes)

#### 5.1 Option A: Via API Service Shell (Recommended)
1. Go to **research-api** service in Choreo Console
2. Click **Open Console** (or **Shell**)
3. Run:
   ```bash
   cd infrastructure/database
   alembic upgrade head
   ```
4. Wait for migrations to complete
5. Verify:
   ```bash
   psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
   ```

#### 5.2 Option B: Local Execution
```bash
# Set database URL
export DATABASE_URL="postgresql://postgres_user:PASSWORD@HOST:5432/research_recommender"

# Run migrations
cd infrastructure/database
alembic upgrade head

# Verify
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```

### Phase 6: Integration & Testing (10 minutes)

#### 6.1 Update CORS Configuration
Edit `apps/api/src/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://[YOUR-WEB-SERVICE-URL]",  # ← Add this
        "http://localhost:3000",           # Keep for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 6.2 Commit and Redeploy API
```bash
git add apps/api/src/main.py
git commit -m "Update CORS for Choreo deployment"
git push origin main

# Choreo will auto-redeploy (if webhook is configured)
# Or manually trigger deployment in Choreo Console
```

#### 6.3 Test Integration
```bash
# 1. Test API health
curl https://[API-URL]/api/health

# 2. Test database connectivity (from API logs)
# Check: Services → research-api → Logs

# 3. Visit web frontend
# Open: https://[WEB-URL]

# 4. Verify frontend → API communication
# Open browser dev tools → Network tab
# Make a request and verify API calls succeed
```

#### 6.4 Verify Database
```bash
# Check tables exist
psql $DATABASE_URL -c "\dt"

# Check migrations applied
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```

---

## 📊 Monitoring & Logs

### Access Service Logs
**In Choreo Console**:
1. Select service (research-api, research-web, or research-db)
2. Click **Logs**
3. View real-time logs or search by time range

### Common Log Patterns

**Successful API startup**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Database connection successful**:
```
Database connection established
```

**Migration completion**:
```
[sqlalchemy.engine.Engine] COMMIT
```

### Monitor Metrics
**In Choreo Console**:
1. Select service
2. Click **Metrics**
3. View:
   - CPU usage
   - Memory usage
   - Request count
   - Error rate
   - Response time

---

## 🔐 Security Checklist

- [ ] All secrets stored in Choreo (not in code)
- [ ] JWT_SECRET_KEY is strong and random
- [ ] Database password is strong (16+ characters)
- [ ] CORS origins are restricted to your domain
- [ ] HTTPS/TLS is enabled (automatic in Choreo)
- [ ] Database backups are configured
- [ ] Unused API keys are revoked
- [ ] Access logs are reviewed regularly

---

## 🚨 Troubleshooting

### Issue: API Build Fails
**Solution**:
1. Check build logs in Choreo Console
2. Verify `apps/api/requirements.txt` exists
3. Update dependencies: `pip freeze > apps/api/requirements.txt`
4. Check Python version (3.11+)

### Issue: Cannot Connect to Database
**Solution**:
1. Verify DATABASE_URL format
2. Check Choreo firewall allows API service
3. Test connection: `psql $DATABASE_URL -c "SELECT 1"`

### Issue: CORS Errors in Frontend
**Solution**:
1. Update allow_origins in API
2. Check web service URL is correct
3. Redeploy API service
4. Clear browser cache

### Issue: Migrations Fail
**Solution**:
1. Check database is healthy
2. Review migration files for errors
3. Check logs: `alembic current`
4. Rollback if needed: `alembic downgrade -1`

See **CHOREO_DEPLOYMENT.md** for comprehensive troubleshooting.

---

## 💰 Cost Estimation

| Service | Est. Monthly Cost |
|---------|------------------|
| PostgreSQL DB | $30-50 |
| API Service | $10-20 |
| Web Service | $5-10 |
| **Total** | **~$45-80** |

*Costs vary by region and usage. Free tier available for testing.*

---

## 📞 Support & Next Steps

### Documentation
- [Choreo Docs](https://wso2.com/choreo/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

### Set Up CI/CD
Enable automatic deployment on GitHub push:
1. In Choreo: Service → GitHub Actions Integration
2. Trigger workflow on push to main branch

### Additional Configuration
1. **Custom Domain**: Services → Ingress → Add Custom Domain
2. **Backups**: Services → Database → Backup Settings
3. **Scaling**: Services → Scaling → Set Min/Max Replicas
4. **Monitoring**: Services → Alerts → Add Monitoring

### Performance Optimization
1. Enable caching in frontend
2. Optimize database queries
3. Set up CDN for static assets
4. Monitor and scale as needed

---

## ✅ Deployment Success Criteria

Your deployment is successful when:

- [ ] API service is **Running** in Choreo
- [ ] Web service is **Running** in Choreo
- [ ] Database is **Healthy** in Choreo
- [ ] API `/health` endpoint returns 200
- [ ] Web frontend loads without errors
- [ ] Frontend can communicate with API
- [ ] Database migrations are applied
- [ ] Logs show no errors

---

## 📝 Final Checklist Before Going Live

- [ ] Update frontend with production API URL
- [ ] Configure custom domain (optional)
- [ ] Set up monitoring and alerts
- [ ] Configure automated backups
- [ ] Review security settings
- [ ] Load test the application
- [ ] Document deployment process
- [ ] Create runbooks for common issues
- [ ] Set up on-call support
- [ ] Plan for scaling strategy

---

## 🎉 Congratulations!

Your application is now running on Choreo! 

**Next Actions**:
1. Monitor application performance
2. Gather user feedback
3. Plan additional features
4. Schedule regular backups
5. Review logs periodically

For more help, refer to the detailed documentation files in `.choreo/` and `docs/`.

---

**Last Updated**: May 2026  
**Version**: 1.0  
**Repository**: Research Recommendation System - FYP
