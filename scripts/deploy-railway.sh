#!/bin/bash
# Railway Deployment Quick Start

echo "🚀 Research Recommendation System - Railway Deployment"
echo "======================================================="
echo ""

# Check if user is logged into Railway
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not installed"
    echo "Install it: npm i -g @railway/cli"
    exit 1
fi

echo "✓ Railway CLI found"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Research Recommendation System"
    echo "✓ Git initialized"
    echo ""
    echo "⚠️  Push to GitHub:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/repo.git"
    echo "   git push -u origin main"
fi

# Check if logged into Railway
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "Please log in to Railway:"
    railway login
fi

echo ""
echo "📦 Initializing Railway project..."
railway init

echo ""
echo "✅ Railway project initialized!"
echo ""
echo "Next steps:"
echo "1. Go to https://railway.app/dashboard"
echo "2. Create PostgreSQL database service"
echo "3. Enable pgvector extension in database"
echo "4. Configure environment variables for API and Web services"
echo "5. Deploy! (railway up)"
echo ""
echo "For detailed instructions, see: docs/RAILWAY_DEPLOYMENT.md"
