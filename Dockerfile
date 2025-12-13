# Multi-stage build for ALMA Backend
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
# Reliance on binary wheels and minimal tools
RUN apt-get update && apt-get install -y --fix-missing \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package metadata first for caching
COPY pyproject.toml /app/
COPY alma/__init__.py /app/alma/
WORKDIR /app

# Install Python dependencies (including dev/build deps)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim

# Install runtime dependencies (including SSH for Proxmox)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    openssh-client \
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
    mkdir -p /app /app/logs /app/data && \
    chown -R alma:alma /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=alma:alma . .

# Re-install package in editable mode or just install? 
# For production, standard install is better, but our code structure assumes package structure?
# We installed deps in builder. We just need to ensure 'alma' package is importable.
# Adding . to PYTHONPATH is simpler than re-pip installing.
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Add data volume support
VOLUME /app/data

# Switch to non-root user
USER alma

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/monitoring/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "alma.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
