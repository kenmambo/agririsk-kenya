.PHONY: help setup ingest validate features train research dashboard demo test clean

help:
	@echo "AgriRisk Kenya - Command Line Interface"
	@echo "----------------------------------------"
	@echo "setup      : Create virtual environment and install dependencies via uv"
	@echo "ingest     : Ingest all external data sources into raw versioned storage"
	@echo "validate   : Validate data quality and run drift detection"
	@echo "features   : Process raw inputs and engineer modeling feature store"
	@echo "train      : Train baseline and 1-3 month risk forecast models"
	@echo "research   : Run Milestone 6 benchmarks, ablations, bootstrap CI, and report"
	@echo "dashboard  : Launch interactive Streamlit decision-support dashboard"
	@echo "demo       : Run interactive terminal early-warning demo"
	@echo "test       : Run unit and integration tests with pytest"
	@echo "clean      : Remove temporary caches, build artifacts, and pytest cache"

setup:
	uv sync
	uv pip install -e .

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

dashboard:
	uv run streamlit run app/Home.py --server.port 8501

demo:
	uv run python scripts/demo_mode.py

test:
	uv run pytest tests/ -v

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ src/agririsk/__pycache__
