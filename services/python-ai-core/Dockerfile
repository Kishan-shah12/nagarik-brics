# ==============================================================================
# NagarikBRICS — Python AI Core (Multi-Stage Build)
# ==============================================================================
# Stage 1: Install dependencies in a builder image
# Stage 2: Copy installed packages to slim runtime image
#
# SECURITY: Runs as non-root 'appuser' (UID 1001)
# SIZE TARGET: Final image < 300 MB
# CONSTRAINT: No local ML models — 100% Gemini API
# ==============================================================================

# --------------------------------------------------------------------------
# STAGE 1: BUILD (install dependencies)
# --------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies (gcc may be needed for some wheels)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements into a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------------------------------
# STAGE 2: RUNTIME
# --------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Security: Create non-root user
RUN groupadd --system --gid 1001 appgroup \
    && useradd --system --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY app/ app/

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose service port (matches docker-compose.yml)
EXPOSE 8080

# Environment defaults
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run with uvicorn
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
