@echo off
REM Railway Deployment Quick Start (Windows)

echo.
echo 🚀 Research Recommendation System - Railway Deployment
echo =======================================================
echo.

REM Check if Railway CLI is installed
where railway >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Railway CLI not installed
    echo Install it: npm i -g @railway/cli
    exit /b 1
)

echo ✓ Railway CLI found
echo.

REM Check if Git is initialized
if not exist ".git" (
    echo 📝 Initializing Git repository...
    git init
    git add .
    git commit -m "Initial commit: Research Recommendation System"
    echo ✓ Git initialized
    echo.
    echo ⚠️  Push to GitHub:
    echo    git remote add origin https://github.com/YOUR_USERNAME/repo.git
    echo    git push -u origin main
)

REM Check if logged into Railway
echo 🔐 Checking Railway authentication...
railway whoami >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Please log in to Railway:
    railway login
)

echo.
echo 📦 Initializing Railway project...
railway init

echo.
echo ✅ Railway project initialized!
echo.
echo Next steps:
echo 1. Go to https://railway.app/dashboard
echo 2. Create PostgreSQL database service
echo 3. Enable pgvector extension in database
echo 4. Configure environment variables for API and Web services
echo 5. Deploy! (railway up)
echo.
echo For detailed instructions, see: docs/RAILWAY_DEPLOYMENT.md
echo.
pause
