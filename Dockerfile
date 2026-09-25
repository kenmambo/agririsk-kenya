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

# Copy dependency specifications first for caching
COPY pyproject.toml .
RUN uv venv && uv pip install -e .

# Copy application source and data
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

# Default port for Streamlit dashboard
EXPOSE 8501
EXPOSE 8000

# Default command launches the Streamlit decision-support dashboard
CMD ["uv", "run", "streamlit", "run", "app/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
