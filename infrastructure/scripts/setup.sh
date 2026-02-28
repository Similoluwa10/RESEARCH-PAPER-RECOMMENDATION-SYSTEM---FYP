#!/bin/bash

# Development environment setup script

set -e

echo "🚀 Setting up development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$python_version" < "3.11" ]]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi
echo "✓ Python version: $python_version"

# Check Node.js version
node_version=$(node --version 2>&1 | cut -d'v' -f2 | cut -d'.' -f1)
if [[ "$node_version" -lt 18 ]]; then
    echo "❌ Node.js 18+ is required. Current version: $(node --version)"
    exit 1
fi
echo "✓ Node.js version: $(node --version)"

# Create Python virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install API dependencies
echo "📦 Installing API dependencies..."
cd apps/api
pip install -r requirements.txt
cd ../..

# Install NLP package dependencies
echo "📦 Installing NLP package dependencies..."
cd packages/nlp
pip install -r requirements.txt
cd ../..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd apps/web
npm install
cd ../..

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start PostgreSQL with pgvector: docker-compose -f infrastructure/docker/docker-compose.yml up -d db"
echo "  2. Initialize database: python infrastructure/database/scripts/init_db.py"
echo "  3. Run migrations: cd infrastructure/database/migrations && alembic upgrade head"
echo "  4. Seed sample data: python infrastructure/database/seeds/sample_papers.py"
echo "  5. Start API: cd apps/api && uvicorn src.main:app --reload"
echo "  6. Start frontend: cd apps/web && npm run dev"
