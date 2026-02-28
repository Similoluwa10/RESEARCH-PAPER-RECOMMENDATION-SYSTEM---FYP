#!/bin/bash

# Deployment script

set -e

echo "🚀 Starting deployment..."

# Build and push Docker images
echo "📦 Building Docker images..."
docker-compose -f infrastructure/docker/docker-compose.prod.yml build

# Run database migrations
echo "🗃️ Running database migrations..."
docker-compose -f infrastructure/docker/docker-compose.prod.yml run --rm api alembic upgrade head

# Start services
echo "🚀 Starting services..."
docker-compose -f infrastructure/docker/docker-compose.prod.yml up -d

echo ""
echo "✅ Deployment complete!"
echo "   API: http://localhost:8000"
echo "   Web: http://localhost:3000"
