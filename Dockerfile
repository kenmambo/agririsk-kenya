# ==============================================================================
# AgriRisk Kenya - Multi-Service Production Dockerfile
# ==============================================================================
FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Create a non-root system user for security compliance
RUN useradd -m -u 1000 -s /bin/bash agririsk && \
    mkdir -p /app/data /app/artifacts /app/logs /app/reports && \
    chown -R agririsk:agririsk /app

# Copy dependency specifications first for Docker layer caching
COPY --chown=agririsk:agririsk pyproject.toml .
RUN uv venv && uv pip install -e .

# Copy application source, configuration, and data snapshots
COPY --chown=agririsk:agririsk . .

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH" \
    APP_ENV=production \
    AGRIRISK_MODE=demo

# Expose ports for Streamlit (8501) and FastAPI (8000)
EXPOSE 8501 8000

# Built-in container health check targeting the Streamlit health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || curl -f http://localhost:8000/health || exit 1

# Default command launches the Streamlit decision-support dashboard
CMD ["uv", "run", "streamlit", "run", "app/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
