# Multi-stage build for ALMA
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY pyproject.toml /tmp/
WORKDIR /tmp

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ALMA_ENV=production

# Create app user
RUN useradd -m -u 1000 alma && \
    mkdir -p /app /app/logs && \
    chown -R alma:alma /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=alma:alma . .

# Install application
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER alma

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/monitoring/health/detailed || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "run_server.py"]
