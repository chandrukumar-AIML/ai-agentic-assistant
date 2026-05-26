# Makefile — AI Agentic Assistant V2

.PHONY: dev prod down logs test verify seed pull-models load-test \
        eval eval-set-baseline drift-check collect-training-data \
        canary-start canary-status canary-rollback clean

# ── Development ────────────────────────────────────────────────────────────────
dev:
	@echo "Starting V2 full stack..."
	docker compose up -d
	@echo ""
	@echo "  Frontend:   http://localhost:5173"
	@echo "  Backend:    http://localhost:8000/docs"
	@echo "  Neo4j:      http://localhost:7474"
	@echo "  MLflow:     http://localhost:5001"
	@echo "  Playwright: http://localhost:8010/health"

seed: dev
	@echo "Waiting for backend..."
	@until docker compose exec backend curl -sf http://localhost:8000/api/health; do sleep 3; done
	docker compose exec backend python -m backend.graph_db.schema
	docker compose exec backend python -m backend.graph_db.seeder
	curl -s -X POST http://localhost:8000/api/prompts/seed \
	  -H "Authorization: Bearer dev" | python3 -m json.tool
	@echo "✅ Seed complete"

pull-models:
	docker compose exec ollama ollama pull llama3
	docker compose exec ollama ollama pull nomic-embed-text
	@echo "✅ Models downloaded"

verify:
	docker compose exec backend python -m backend.verify_env

# ── Testing ────────────────────────────────────────────────────────────────────
test:
	docker compose exec backend pytest backend/tests/ \
	  --ignore=backend/tests/test_integration.py \
	  --ignore=backend/tests/test_load.py \
	  -v --tb=short

test-integration:
	docker compose exec backend pytest backend/tests/test_integration.py -v --tb=short

test-cov:
	docker compose exec backend pytest backend/tests/ \
	  --ignore=backend/tests/test_integration.py \
	  --ignore=backend/tests/test_load.py \
	  -v --cov=backend --cov-report=term-missing

load-test:
	pip install locust websocket-client
	locust -f backend/tests/test_load.py \
	  --host=http://localhost:8000 \
	  --users=50 --spawn-rate=5 \
	  --run-time=5m --headless \
	  --csv=data/load_test_results

# ── Evaluation ────────────────────────────────────────────────────────────────
eval:
	docker compose exec backend python -c "
	import asyncio
	from backend.evaluation.eval_runner import run_evaluation
	async def main():
	    r = await run_evaluation(limit=20)
	    print(f'TCR: {r[\"metrics\"][\"tcr\"]:.1%}')
	    print(f'Composite: {r[\"metrics\"][\"composite\"]:.1%}')
	    print(f'Gate: {\"PASS\" if r[\"gate\"][\"passed\"] else \"FAIL\"}'  )
	asyncio.run(main())
	"

eval-set-baseline:
	docker compose exec backend python -c "
	import asyncio
	from backend.evaluation.eval_runner import run_evaluation
	asyncio.run(run_evaluation(limit=50, save_as_baseline=True))
	"

# ── MLOps ─────────────────────────────────────────────────────────────────────
drift-check:
	curl -s -X POST "http://localhost:8000/api/mlops/drift-check" \
	  -H "Authorization: Bearer dev" | python3 -m json.tool

collect-training-data:
	curl -s -X POST "http://localhost:8000/api/mlops/collect-training-data?days_back=30" \
	  -H "Authorization: Bearer dev" | python3 -m json.tool

canary-start:
	curl -s -X POST "http://localhost:8000/api/mlops/canary/start" \
	  -H "Authorization: Bearer dev" \
	  -G --data "model_name=ollama/llama3" \
	     --data "traffic_pct=0.1" \
	     --data "min_queries=50" | python3 -m json.tool

canary-status:
	curl -s http://localhost:8000/api/mlops/canary/status \
	  -H "Authorization: Bearer dev" | python3 -m json.tool

canary-rollback:
	curl -s -X POST http://localhost:8000/api/mlops/canary/rollback \
	  -H "Authorization: Bearer dev"

# ── Production ─────────────────────────────────────────────────────────────────
prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml \
	  up -d --build

down:
	docker compose down

down-v:
	docker compose down -v

logs:
	docker compose logs -f backend

logs-all:
	docker compose logs -f

clean:
	docker system prune -f
	docker volume prune -f