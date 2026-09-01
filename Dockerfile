# ============================================================================
# Multi-Stage Production Dockerfile for PO Preflight AI Gateway
# Security: Minimal Debian base, non-root user 'preflight', layer caching
# ============================================================================

# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# ----------------------------------------------------------------------------
# Stage 2: Production Runtime
# ----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL maintainer="PO Preflight Engineering Team <engineering@po-preflight.ai>"
LABEL description="AI-Native Purchase Order Intake, Preflight Rules & ERP Gateway"

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1
ENV PORT=8001

# Create secure non-root user and group
RUN groupadd -r preflight && \
    useradd -r -g preflight -d /app -s /sbin/nologin -c "PO Preflight Service Account" preflight && \
    mkdir -p /app/runtime/uploads /app/runtime/data && \
    chown -R preflight:preflight /app

# Copy application source code
COPY --chown=preflight:preflight src/ /app/src/
COPY --chown=preflight:preflight examples/ /app/examples/

# Switch to non-root user
USER preflight

# Container Healthcheck Probe
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health/live', timeout=3)" || exit 1

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "preflight.api.app:app", "--host", "0.0.0.0", "--port", "8001"]
