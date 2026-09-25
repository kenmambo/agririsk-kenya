.PHONY: help setup dev ingest validate features train research dashboard api demo test docker-build docker-run clean

help:
	@echo "AgriRisk Kenya - Command Line Interface"
	@echo "----------------------------------------"
	@echo "setup        : Create virtual environment and install dependencies via uv"
	@echo "dev          : Launch development environment with Streamlit dashboard"
	@echo "api          : Launch FastAPI backend microservice on port 8000"
	@echo "dashboard    : Launch interactive Streamlit decision-support dashboard"
	@echo "demo         : Run interactive terminal early-warning demo"
	@echo "test         : Run unit and integration tests with pytest"
	@echo "pipeline     : Run automated end-to-end data and modeling pipeline"
	@echo "research     : Run benchmarks, domain ablations, bootstrap CIs, and reports"
	@echo "docker-build : Build production multi-service Docker container image"
	@echo "docker-run   : Run full multi-container stack via Docker Compose"
	@echo "clean        : Remove temporary caches, build artifacts, and pytest cache"

setup:
	uv sync
	uv pip install -e .

dev:
	uv run streamlit run app/Home.py --server.port 8501

dashboard:
	uv run streamlit run app/Home.py --server.port 8501

api:
	uv run uvicorn agririsk.api.app:app --host 0.0.0.0 --port 8000 --reload

demo:
	uv run python scripts/demo_mode.py

test:
	uv run pytest tests/ -v

ingest:
	uv run python -m agririsk.pipeline run --step ingest

validate:
	uv run python -m agririsk.pipeline run --step validate

features:
	uv run python -m agririsk.pipeline run --step features

train:
	uv run python -m agririsk.pipeline run --step train

research:
	uv run python scripts/run_milestone6_experiments.py

pipeline:
	uv run python -m agririsk.pipeline run

docker-build:
	docker build -t agririsk-kenya:latest .

docker-run:
	docker-compose up -d

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ src/agririsk/__pycache__
