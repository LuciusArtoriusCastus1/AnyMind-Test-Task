# Dockerfile for AnyMind POS Payment System
#
# Multi-stage build for optimized image size:
# 1. Builder stage: Install dependencies
# 2. Production stage: Run the application
#
# Features:
# - Uses slim Python image for smaller size
# - Non-root user for security
# - Health check for container orchestration

FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY app/ ./app/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1


# --workers: Number of worker processes (adjust based on CPU cores)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
