# Production Deployment Guide - ALMA

Complete guide for deploying ALMA in production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Logging](#monitoring--logging)
8. [High Availability](#high-availability)
9. [Backup & Recovery](#backup--recovery)
10. [Performance Tuning](#performance-tuning)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum (Small Deployment)**:
- 4 CPU cores
- 8 GB RAM
- 50 GB SSD storage
- Ubuntu 22.04 LTS / RHEL 9

**Recommended (Production)**:
- 8+ CPU cores
- 16+ GB RAM
- 200 GB SSD storage
- Ubuntu 22.04 LTS / RHEL 9

**High Availability Setup**:
- 3+ application servers (load balanced)
- PostgreSQL cluster (primary + 2 replicas)
- Redis cluster (3+ nodes)
- Prometheus + Grafana for monitoring

### Software Dependencies

- Python 3.10+
- PostgreSQL 15+
- Redis 7+ (optional, for caching)
- Nginx (reverse proxy)
- Docker (optional, for containerized deployment)

---

## Infrastructure Requirements

### Network Architecture

```
                     ┌─────────────────┐
                     │   Load Balancer │
                     │   (Nginx/HAProxy)│
                     └────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼────┐      ┌───────▼────┐
            │  ALMA    │      │  ALMA    │
            │  Server 1  │      │  Server 2  │
            └───────┬────┘      └───────┬────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  PostgreSQL       │
                    │  Primary + Replicas│
                    └───────────────────┘
```

### Firewall Rules

| Port | Service | Source | Purpose |
|------|---------|--------|---------|
| 443 | HTTPS | Public | API access |
| 80 | HTTP | Public | Redirect to HTTPS |
| 5432 | PostgreSQL | ALMA servers | Database access |
| 6379 | Redis | ALMA servers | Cache access |
| 9090 | Prometheus | Internal | Metrics collection |
| 3000 | Grafana | Internal | Monitoring dashboards |

---

## Installation

### Option 1: Docker (Recommended)

#### Step 1: Create Docker Compose Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  aicdn-app:
    build: .
    image: aicdn:latest
    container_name: aicdn-app
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://aicdn:${DB_PASSWORD}@postgres:5432/aicdn
      - REDIS_URL=redis://redis:6379/0
      - API_CORS_ORIGINS=["https://your-domain.com"]
      - LOG_LEVEL=INFO
      - RATE_LIMIT_RPM=60
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - aicdn-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    container_name: aicdn-postgres
    restart: always
    environment:
      - POSTGRES_USER=aicdn
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=aicdn
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - aicdn-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aicdn"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: aicdn-redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - aicdn-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    container_name: aicdn-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - aicdn-app
    networks:
      - aicdn-network

  prometheus:
    image: prom/prometheus:latest
    container_name: aicdn-prometheus
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - aicdn-network

  grafana:
    image: grafana/grafana:latest
    container_name: aicdn-grafana
    restart: always
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=https://grafana.your-domain.com
    volumes:
      - grafana-data:/var/lib/grafana
      - ./config/grafana:/etc/grafana/provisioning
    depends_on:
      - prometheus
    networks:
      - aicdn-network

volumes:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  aicdn-network:
    driver: bridge
```

#### Step 2: Create Environment File

```bash
# .env.production
DB_PASSWORD=your-secure-db-password-here
REDIS_PASSWORD=your-secure-redis-password-here
GRAFANA_PASSWORD=your-secure-grafana-password-here
```

#### Step 3: Deploy

```bash
# Set production environment
export ENVIRONMENT=production

# Deploy stack
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f aicdn-app
```

### Option 2: Native Installation

#### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3-pip python3-venv \
    postgresql-15 postgresql-contrib \
    redis-server nginx certbot python3-certbot-nginx \
    build-essential libpq-dev

# Create application user
sudo useradd -m -s /bin/bash aicdn
sudo usermod -aG sudo aicdn
```

#### Step 2: Application Installation

```bash
# Switch to aicdn user
sudo su - aicdn

# Clone repository
git clone https://github.com/fabriziosalmi/alma.git
cd alma

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
pip install gunicorn uvloop httptools

# Create logs directory
mkdir -p logs
```

#### Step 3: Systemd Service

```ini
# /etc/systemd/system/aicdn.service
[Unit]
Description=ALMA API Server
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=aicdn
Group=aicdn
WorkingDirectory=/home/alma/alma
Environment="PATH=/home/alma/alma/venv/bin"
Environment="DATABASE_URL=postgresql://aicdn:password@localhost/aicdn"
ExecStart=/home/alma/alma/venv/bin/gunicorn alma.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /home/alma/alma/logs/access.log \
    --error-logfile /home/alma/alma/logs/error.log \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable aicdn
sudo systemctl start aicdn
sudo systemctl status aicdn
```

---

## Configuration

### Environment Variables

Create `.env.production`:

```bash
# Database
DATABASE_URL=postgresql://aicdn:password@localhost:5432/aicdn
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis Cache (optional)
REDIS_URL=redis://:password@localhost:6379/0
CACHE_TTL=3600

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_CORS_ORIGINS=["https://your-domain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_RPM=60
RATE_LIMIT_BURST=10

# LLM Configuration
LLM_MODEL_PATH=/models/qwen2.5-0.5b-instruct
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/aicdn/app.log

# Security
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand
API_KEY_ENABLED=true
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Deployment Engines
PROXMOX_HOST=proxmox.internal.com
PROXMOX_USER=aicdn@pve
PROXMOX_PASSWORD=secure-password
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/aicdn
upstream aicdn_backend {
    server 127.0.0.1:8000;
    # For multiple servers:
    # server 10.0.1.10:8000;
    # server 10.0.1.11:8000;
    keepalive 32;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
limit_req_status 429;

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/aicdn-access.log combined;
    error_log /var/log/nginx/aicdn-error.log warn;

    # Proxy settings
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://aicdn_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;  # Longer for streaming
        
        # Buffering
        proxy_buffering off;  # Important for SSE streaming
        proxy_cache_bypass $http_upgrade;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://aicdn_backend/health;
        access_log off;
    }

    # Metrics endpoint (restrict access)
    location /metrics {
        allow 10.0.0.0/8;  # Internal network only
        deny all;
        proxy_pass http://aicdn_backend/metrics;
    }
}
```

```bash
# Enable site and reload Nginx
sudo ln -s /etc/nginx/sites-available/aicdn /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d api.your-domain.com
```

---

## Database Setup

### PostgreSQL Configuration

```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
createuser aicdn
createdb -O aicdn aicdn
psql -c "ALTER USER aicdn WITH PASSWORD 'secure-password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE aicdn TO aicdn;"
```

### PostgreSQL Tuning

Edit `/etc/postgresql/15/main/postgresql.conf`:

```ini
# Memory
shared_buffers = 4GB              # 25% of RAM
effective_cache_size = 12GB       # 75% of RAM
maintenance_work_mem = 1GB
work_mem = 64MB

# Checkpoints
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Query Planner
random_page_cost = 1.1            # For SSD
effective_io_concurrency = 200    # For SSD

# Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 1GB
log_min_duration_statement = 1000  # Log slow queries (>1s)

# Connections
max_connections = 200
```

```bash
# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Run Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run Alembic migrations
alembic upgrade head

# Verify
psql -U aicdn -d aicdn -c "\dt"
```

---

## Security Hardening

### 1. API Key Authentication

```python
# alma/core/security.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key not in VALID_API_KEYS:  # Store in database
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

### 2. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable

# Allow internal network for database
sudo ufw allow from 10.0.0.0/8 to any port 5432
sudo ufw allow from 10.0.0.0/8 to any port 6379
```

### 3. Secrets Management

Use environment variables or secret manager:

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value \
    --secret-id aicdn/production/db-password \
    --query SecretString --output text

# HashiCorp Vault
vault kv get secret/aicdn/production/database
```

### 4. SSL/TLS Certificates

```bash
# Let's Encrypt with auto-renewal
sudo certbot --nginx -d api.your-domain.com
sudo systemctl enable certbot.timer
```

### 5. Database Encryption

```sql
-- Enable SSL in PostgreSQL
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/server.key';
SELECT pg_reload_conf();
```

---

## Monitoring & Logging

### Prometheus Configuration

```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    environment: 'prod'

scrape_configs:
  - job_name: 'aicdn-api'
    static_configs:
      - targets: ['aicdn-app:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts/*.yml'
```

### Alert Rules

```yaml
# config/alerts/aicdn.yml
groups:
  - name: aicdn_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "P95 latency is {{ $value }}s"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"

      - alert: HighRateLimiting
        expr: rate(rate_limit_hits_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate limiting activity"
```

### Centralized Logging

```yaml
# docker-compose.logging.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./config/loki.yml:/etc/loki/local-config.yaml
      - loki-data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./logs:/var/log/aicdn
      - ./config/promtail.yml:/etc/promtail/config.yml
    depends_on:
      - loki
```

---

## High Availability

### Load Balancer Configuration

```nginx
# HAProxy configuration
frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/aicdn.pem
    mode http
    default_backend aicdn_backend

backend aicdn_backend
    mode http
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    
    server aicdn1 10.0.1.10:8000 check inter 5s fall 3 rise 2
    server aicdn2 10.0.1.11:8000 check inter 5s fall 3 rise 2
    server aicdn3 10.0.1.12:8000 check inter 5s fall 3 rise 2
```

### PostgreSQL Replication

```bash
# Primary server
# postgresql.conf
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB

# pg_hba.conf
host replication replicator 10.0.1.0/24 md5

# Replica server
# Create replication slot
SELECT * FROM pg_create_physical_replication_slot('replica_1');

# Start replica
pg_basebackup -h primary -D /var/lib/postgresql/15/main -U replicator -v -P
```

### Redis Cluster

```bash
# Redis Sentinel for automatic failover
redis-sentinel /etc/redis/sentinel.conf

# sentinel.conf
sentinel monitor mymaster 10.0.1.20 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 10000
```

---

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# /home/aicdn/backups/backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -U aicdn aicdn | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /home/alma/alma

# Upload to S3
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://aicdn-backups/
aws s3 cp $BACKUP_DIR/app_$DATE.tar.gz s3://aicdn-backups/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

```bash
# Crontab entry
0 2 * * * /home/aicdn/backups/backup.sh
```

### Disaster Recovery

```bash
# Restore database
gunzip < db_backup.sql.gz | psql -U aicdn aicdn

# Restore application
tar -xzf app_backup.tar.gz -C /home/aicdn/

# Restart services
sudo systemctl restart aicdn
```

---

## Performance Tuning

### Application Optimization

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

### Caching Layer

```python
# Redis caching
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache(ttl=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### CDN for Static Assets

```nginx
# CloudFlare or AWS CloudFront
location /static {
    add_header Cache-Control "public, max-age=31536000, immutable";
    expires 1y;
}
```

---

## Troubleshooting

### Check Service Status

```bash
# Application
sudo systemctl status aicdn
sudo journalctl -u aicdn -f

# Database
sudo systemctl status postgresql
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Nginx
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Common Issues

**Database connection errors:**
```bash
# Check connections
psql -U aicdn -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '1 hour';
```

**High memory usage:**
```bash
# Check processes
ps aux --sort=-%mem | head

# Restart workers
sudo systemctl restart aicdn
```

**Slow queries:**
```sql
-- Enable query logging
ALTER DATABASE aicdn SET log_min_duration_statement = 1000;

-- Find slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

---

## Production Checklist

- [ ] SSL/TLS certificates configured
- [ ] Firewall rules applied
- [ ] Database backups automated
- [ ] Monitoring and alerting configured
- [ ] Log aggregation set up
- [ ] Rate limiting enabled
- [ ] API key authentication enabled
- [ ] Security headers configured
- [ ] Database replication configured
- [ ] Load balancer health checks working
- [ ] Auto-scaling configured (if using cloud)
- [ ] Disaster recovery plan documented
- [ ] Performance testing completed
- [ ] Security audit performed
- [ ] Documentation updated

---

## Support

For production support:
- Enterprise support: enterprise@ALMA.dev
- Security issues: security@ALMA.dev
- GitHub: https://github.com/fabriziosalmi/alma/issues
