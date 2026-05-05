# Deploying to WSO2 Choreo

This guide explains how to deploy your Research Recommendation System application to WSO2 Choreo, including the FastAPI backend, Next.js frontend, and PostgreSQL database.

## Prerequisites

1. **Choreo Account**: Create a free account at https://console.choreo.dev
2. **GitHub Repository**: Push your code to GitHub (Choreo integrates with GitHub)
3. **Environment Variables**: Prepare your configuration values
4. **Docker Knowledge**: Basic understanding of containerization
5. **Git CLI**: Installed and configured on your machine

## Architecture Overview

Your deployment will consist of:
- **Database Layer**: PostgreSQL with pgvector (managed PostgreSQL or self-hosted)
- **API Service**: FastAPI backend
- **Web Service**: Next.js frontend
- **Reverse Proxy**: Optional nginx for routing

## Step 1: Prepare Your Repository

### 1.1 Create Choreo-Specific Files

Create a `.choreo` directory in your repository root with deployment configurations:

```bash
mkdir -p .choreo
```

### 1.2 Create Dockerfile for API Service

Ensure `infrastructure/docker/Dockerfile.api` is properly configured (already done ✓)

### 1.3 Create Dockerfile for Web Service

Ensure `infrastructure/docker/Dockerfile.web` is properly configured (already done ✓)

### 1.4 Push to GitHub

```bash
git add .
git commit -m "Prepare for Choreo deployment"
git push origin main
```

## Step 2: Deploy PostgreSQL Database

### Option A: Use Managed PostgreSQL (Recommended)

1. Go to [Choreo Console](https://console.choreo.dev)
2. Create a new project or select existing
3. Click **Create** → **Service**
4. Choose **MySQL/PostgreSQL** or use an external database service
5. Configure:
   - **Database Name**: `research_recommender`
   - **Username**: `postgres_user`
   - **Password**: Generate strong password
   - **Port**: 5432

6. Note the **Connection String** (you'll need this for API service)

### Option B: Use External PostgreSQL

If you prefer using a cloud PostgreSQL provider:
- **AWS RDS**: https://aws.amazon.com/rds/
- **Azure Database**: https://azure.microsoft.com/services/postgresql/
- **Railway.app**: https://railway.app (free tier available)
- **Render**: https://render.com

Store the connection string securely in Choreo's secret management.

### Step 2.1: Initialize Database

After the database is running:

```bash
# Locally run migrations to verify they work
cd infrastructure/database
alembic upgrade head
```

## Step 3: Deploy FastAPI Backend

### 3.1 Create Service in Choreo

1. Go to **Choreo Console** → Your Project
2. Click **Create** → **Service**
3. Select **Build from GitHub Repository**
4. Connect your GitHub account and select your repository
5. Configure:
   - **Service Name**: `research-api`
   - **Repository Path**: `apps/api`
   - **Port**: 8000
   - **Buildpack**: Python

### 3.2 Configure Build Settings

1. In the build configuration, set:
   - **Dockerfile Path**: `../../infrastructure/docker/Dockerfile.api`
   - Or use **buildpack** with Python buildpack

2. Set **Build Context**: `/` (repository root, since Dockerfile has relative paths)

### 3.3 Configure Environment Variables

In Choreo Service Settings, add these secrets:

```
DATABASE_URL=postgresql://user:password@host:5432/research_recommender
JWT_SECRET_KEY=your-secret-key-here
APP_ENV=production
DEBUG=false
GROQ_API_KEY=your-groq-api-key
```

### 3.4 Configure Port Exposure

- **Container Port**: 8000
- **Service Port**: 8000
- **Protocol**: HTTP

### 3.5 Set Startup Command (if not using Dockerfile)

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 3.6 Deploy

Click **Deploy** and monitor the build logs.

## Step 4: Deploy Next.js Frontend

### 4.1 Create Service in Choreo

1. Click **Create** → **Service**
2. Select **Build from GitHub Repository**
3. Configure:
   - **Service Name**: `research-web`
   - **Repository Path**: `apps/web`
   - **Port**: 3000
   - **Buildpack**: Node.js

### 4.2 Configure Build Settings

1. Set **Dockerfile Path**: `../../infrastructure/docker/Dockerfile.web`
2. Set **Build Context**: `/`

### 4.3 Configure Build Arguments

In the build configuration, add:

```
NEXT_PUBLIC_API_URL=https://your-api-domain.com/api
```

Replace `your-api-domain.com` with your actual API domain from Step 3.

### 4.4 Configure Environment Variables

```
NEXT_PUBLIC_API_URL=https://your-api-domain.com/api
```

### 4.5 Set Startup Command (if not using Dockerfile)

```bash
node server.js
```

### 4.6 Deploy

Click **Deploy** and monitor the build logs.

## Step 5: Connect Frontend to API

### 5.1 Update API Endpoint

After getting the API service URL from Choreo, update your frontend:

**apps/web/lib/api.ts**:
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
```

### 5.2 Update CORS Configuration

Update your FastAPI CORS configuration in `apps/api/src/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-web-domain.com",
        "http://localhost:3000",  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 6: Configure Custom Domain (Optional)

1. In Choreo Console, go to **Services** → **Ingress**
2. Click **Add Custom Domain**
3. Configure your domain (e.g., `api.yourproject.com`)
4. Follow DNS verification steps
5. Update your frontend API URL

## Step 7: Run Database Migrations

After deployment, run Alembic migrations:

### Option A: Via Choreo Shell

1. Go to API Service → **Shell/Console**
2. Run:
   ```bash
   cd infrastructure/database
   alembic upgrade head
   ```

### Option B: Via Local Environment

1. Set the deployed database URL:
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:5432/research_recommender"
   ```

2. Run migrations:
   ```bash
   cd infrastructure/database
   alembic upgrade head
   ```

## Step 8: Monitor and Test

### 8.1 Check Service Health

1. View **Logs** in Choreo console
2. Check **Metrics** for resource usage
3. Monitor **Endpoints** for response times

### 8.2 Test API

```bash
curl https://your-api-domain.com/api/health
```

### 8.3 Test Frontend

Visit `https://your-web-domain.com` in browser

### 8.4 Test Database Connection

Check API logs for database connection errors

## Troubleshooting

### Database Connection Errors

1. Verify `DATABASE_URL` format:
   ```
   postgresql://username:password@host:port/database_name
   ```

2. Check network security:
   - Choreo IP must be whitelisted in PostgreSQL security groups
   - Or use VPN if required

3. Check logs:
   ```bash
   # In Choreo Console
   Services → API → Logs
   ```

### API Build Fails

1. Check **Build Logs** for dependency errors
2. Verify Python version (3.11 recommended)
3. Ensure `requirements.txt` is complete:
   ```bash
   pip freeze > apps/api/requirements.txt
   ```

4. Check Dockerfile paths are correct

### Frontend Build Fails

1. Verify Node.js version (18+ recommended)
2. Check `pnpm-lock.yaml` is committed
3. Verify `NEXT_PUBLIC_API_URL` is set correctly
4. Check for TypeScript errors:
   ```bash
   cd apps/web
   npm run build
   ```

### CORS Errors

1. Update `apps/api/src/main.py` with frontend domain
2. Ensure credentials and headers are properly configured
3. Test with:
   ```bash
   curl -H "Origin: https://your-web-domain.com" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        https://your-api-domain.com/api/health
   ```

## Environment Variables Reference

### API Service (.env)
```
DATABASE_URL=postgresql://user:password@host:5432/research_recommender
JWT_SECRET_KEY=your-strong-secret-key
APP_ENV=production
DEBUG=false
GROQ_API_KEY=your-api-key
LANGCHAIN_API_KEY=optional
```

### Web Service (.env.local)
```
NEXT_PUBLIC_API_URL=https://your-api-domain.com/api
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

## Scaling and Performance

### Auto-scaling

In Choreo Console:
1. Go to **Services** → **Scaling**
2. Set:
   - **Min Replicas**: 1
   - **Max Replicas**: 5
   - **CPU Target**: 70%
   - **Memory Target**: 80%

### Resource Limits

Set appropriate limits based on traffic:
- **API**: 512MB-2GB memory, 0.5-1 CPU
- **Web**: 256MB-512MB memory, 0.25-0.5 CPU
- **DB**: 2GB-8GB memory, 1-2 CPU (depending on data size)

## Continuous Deployment

### Enable Auto-Deploy

1. In Choreo Console → **Services** → **Deployments**
2. Enable **GitHub Actions** integration
3. Configure branch (e.g., `main`)
4. Services will auto-deploy on push

### Manual Deployment

Trigger deployment from Choreo Console or GitHub via webhook.

## Backup and Recovery

### Database Backups

If using managed PostgreSQL in Choreo:
1. Go to **Database Service** → **Backups**
2. Configure daily automated backups
3. Retain for at least 7 days

### Code Backup

Your GitHub repository serves as your code backup.

## Next Steps

1. **Monitor Performance**: Set up alerting in Choreo
2. **Enable Logging**: Configure log aggregation
3. **Setup CI/CD**: Use GitHub Actions for automated testing
4. **Security**: Enable SSL/TLS (auto-configured by Choreo)
5. **Analytics**: Integrate monitoring tools (Datadog, New Relic, etc.)

## Additional Resources

- [Choreo Documentation](https://wso2.com/choreo/docs/)
- [Choreo Python Buildpack](https://wso2.com/choreo/docs/references/buildpacks/python/)
- [Choreo Node.js Buildpack](https://wso2.com/choreo/docs/references/buildpacks/nodejs/)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/16/runtime-config.html)
