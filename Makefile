.PHONY: setup dev api web db-migrate db-upgrade db-seed test lint clean

# Development Setup
setup:
	@echo "Setting up development environment..."
	cd apps/api && pip install -r requirements.txt
	cd apps/web && npm install
	cd packages/nlp && pip install -r requirements.txt

# Run Development Servers
dev:
	@echo "Starting development servers..."
	docker-compose -f infrastructure/docker/docker-compose.yml up -d db
	make api & make web

api:
	cd apps/api && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

# Database
db-migrate:
	cd infrastructure/database/migrations && alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	cd infrastructure/database/migrations && alembic upgrade head

db-downgrade:
	cd infrastructure/database/migrations && alembic downgrade -1

db-seed:
	cd infrastructure/database && python seeds/sample_papers.py

db-reset:
	cd infrastructure/database/scripts && python reset_db.py

# Testing
test:
	cd apps/api && pytest tests/ -v
	cd packages/nlp && pytest tests/ -v

test-api:
	cd apps/api && pytest tests/ -v --cov=src

test-nlp:
	cd packages/nlp && pytest tests/ -v --cov=src

# Linting
lint:
	cd apps/api && ruff check src/
	cd packages/nlp && ruff check src/
	cd apps/web && npm run lint

format:
	cd apps/api && ruff format src/
	cd packages/nlp && ruff format src/
	cd apps/web && npm run format

# Experiments
evaluate:
	cd experiments/evaluation && python benchmark.py

# Docker
docker-up:
	docker-compose -f infrastructure/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f infrastructure/docker/docker-compose.yml down

docker-logs:
	docker-compose -f infrastructure/docker/docker-compose.yml logs -f

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
