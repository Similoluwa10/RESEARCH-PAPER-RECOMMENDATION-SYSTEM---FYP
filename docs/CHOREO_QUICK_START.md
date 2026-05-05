## Choreo Deployment - Quick Start Guide

### Prerequisites Checklist
- [ ] Choreo account created at https://console.choreo.dev
- [ ] GitHub account connected to Choreo
- [ ] Code pushed to GitHub repository
- [ ] Strong JWT secret key generated
- [ ] Secure PostgreSQL password created
- [ ] GROQ API key (if using explainability features)

### Deployment Order

1. **PostgreSQL Database** - Deploy first, get connection string
2. **FastAPI Backend API** - Deploy after database
3. **Next.js Frontend** - Deploy after API is ready
4. **Run Migrations** - Initialize database schema
5. **Test Integration** - Verify all services communicate

---

## Quick Deploy Steps

### 1. Create Database Service
```
Choreo Console → Create → Service → PostgreSQL
- Name: research-db
- User: postgres_user  
- Password: [generate strong password]
- Database: research_recommender
- Save connection string from service details
```

### 2. Create API Service
```
Choreo Console → Create → Service → Build from GitHub
- Service Name: research-api
- Repository: [your-repo]
- Repository Path: apps/api
- Dockerfile: ../../infrastructure/docker/Dockerfile.api
- Build Context: /

Add Secrets:
  DATABASE_URL: postgresql://postgres_user:PASSWORD@DB_HOST:5432/research_recommender
  JWT_SECRET_KEY: [generate at https://uuidgenerator.net/]
  APP_ENV: production
  DEBUG: false
  GROQ_API_KEY: [your-groq-api-key]

Deploy → Wait for success → Copy API URL
```

### 3. Create Web Service
```
Choreo Console → Create → Service → Build from GitHub
- Service Name: research-web
- Repository: [your-repo]
- Repository Path: apps/web
- Dockerfile: ../../infrastructure/docker/Dockerfile.web
- Build Context: /

Build Arguments:
  NEXT_PUBLIC_API_URL: [API URL from step 2]/api

Secrets:
  NEXT_PUBLIC_API_URL: [API URL from step 2]/api
  NEXT_PUBLIC_GOOGLE_CLIENT_ID: [if using Google OAuth]

Deploy → Wait for success → Copy Web URL
```

### 4. Initialize Database
```bash
# SSH/Shell into API service or run locally
cd infrastructure/database
export DATABASE_URL="postgresql://postgres_user:PASSWORD@DB_HOST:5432/research_recommender"
alembic upgrade head
```

### 5. Update CORS (if needed)
Edit `apps/api/src/main.py`:
```python
allow_origins=[
    "https://[your-web-domain]",
    "http://localhost:3000",
]
```

### 6. Test Integration
```bash
# Test API health
curl https://[API-URL]/api/health

# Test frontend
Visit https://[WEB-URL]

# Check logs in Choreo console
API Service → Logs
Web Service → Logs
```

---

## Environment Configuration Template

### For API Service Secrets
```
DATABASE_URL=postgresql://postgres_user:[PASSWORD]@[HOST]:[PORT]/research_recommender
JWT_SECRET_KEY=[STRONG_SECRET_KEY]
APP_ENV=production
DEBUG=false
GROQ_API_KEY=[YOUR_GROQ_KEY]
LANGCHAIN_API_KEY=[OPTIONAL]
```

### For Web Service Environment
```
NEXT_PUBLIC_API_URL=https://[API-URL]/api
NEXT_PUBLIC_GOOGLE_CLIENT_ID=[OPTIONAL]
```

---

## Common Issues & Solutions

### Build Fails with "Module not found"
**Solution**: Check `requirements.txt` exists in `apps/api/`
```bash
cd apps/api
pip freeze > requirements.txt
```

### API cannot connect to database
**Solution**: Check DATABASE_URL format and firewall rules
```
Format: postgresql://user:password@host:port/database
Test: psql $DATABASE_URL -c "SELECT 1"
```

### Frontend shows CORS errors
**Solution**: Update CORS in API and redeploy
```python
# apps/api/src/main.py
allow_origins=["https://your-web-domain.com"]
```

### Build context path errors
**Solution**: Ensure Build Context is set to `/` (repository root)

---

## Performance Configuration

### Recommended Scaling Settings
- **API Service**:
  - Min Replicas: 2
  - Max Replicas: 5
  - Memory: 1GB
  - CPU: 0.5-1.0

- **Web Service**:
  - Min Replicas: 2
  - Max Replicas: 5
  - Memory: 512MB
  - CPU: 0.25-0.5

- **Database**:
  - Memory: 4GB+ (depending on data size)
  - Storage: 50GB+ (depending on paper corpus)

---

## Post-Deployment Checklist

- [ ] API service is healthy (check /health endpoint)
- [ ] Web service loads without errors
- [ ] Database migrations completed
- [ ] Frontend can communicate with API
- [ ] Custom domains configured (optional)
- [ ] SSL/TLS is enabled (auto by Choreo)
- [ ] Backups are configured
- [ ] Monitoring/alerts are set up
- [ ] Environment variables are secure

---

## Useful Links

- [Choreo Console](https://console.choreo.dev)
- [Choreo Docs](https://wso2.com/choreo/docs/)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

---

## Support & Debugging

### Enable Debug Logging
```
In Choreo: Service → Settings → Environment Variables
Add: DEBUG=true
Redeploy service
Check Service → Logs for detailed output
```

### Get Service Logs
```bash
# Via Choreo Console
Services → [Service Name] → Logs → View Latest Logs

# Or check metrics
Services → [Service Name] → Metrics
```

### Database Debugging
```bash
# Connect directly to database
psql $DATABASE_URL

# Check tables
\dt

# Check migrations
SELECT * FROM alembic_version;
```

---

## Next Steps

1. Monitor application performance in Choreo dashboard
2. Set up CI/CD with GitHub Actions
3. Configure backup policies
4. Enable monitoring/alerting
5. Plan for data retention/archival
