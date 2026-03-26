---
title: Deployment
layout: default
nav_order: 13
---

# Deployment
{: .no_toc }

Production deployment guide, infrastructure requirements, and operational considerations.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Prerequisites

| Requirement | Minimum Version | Purpose |
|:------------|:---------------|:--------|
| Docker | 24+ | Container runtime |
| Docker Compose | 2.x+ | Service orchestration |
| PostgreSQL | 16+ | Primary database |
| Redis | 7+ | Celery message broker |

## Build

```bash
# Build the Docker image
docker build -t cross-border-engine .

# Verify the image
docker images cross-border-engine
```

## Run

### Docker Compose (Recommended)

```bash
# Start all services in detached mode
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Verify health
curl http://localhost:8000/health
```

### Standalone

```bash
# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start the Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info
```

## Infrastructure Requirements

### PostgreSQL

| Setting | Recommended | Description |
|:--------|:-----------|:------------|
| Version | 16+ | Latest stable |
| Storage | 10 GB+ | Scales with transfer volume |
| Connections | 20+ | Pool size for async sessions |
| Backup | Daily | Point-in-time recovery |

The engine uses async PostgreSQL via `asyncpg`. Connection pooling is handled by SQLAlchemy's async engine.

### Redis

| Setting | Recommended | Description |
|:--------|:-----------|:------------|
| Version | 7+ | Latest stable |
| Memory | 256 MB+ | For task queue and results |
| Persistence | AOF | Durability for task queue |
| Maxmemory Policy | `allkeys-lru` | Eviction when full |

Redis serves as the Celery message broker and result backend.

## Production Checklist

### Security

- [ ] Set strong database credentials (not the dev defaults)
- [ ] Disable Swagger UI in production (`docs_url=None`)
- [ ] Add authentication to admin endpoints
- [ ] Use HTTPS termination (via reverse proxy)
- [ ] Restrict admin endpoints to internal network
- [ ] Add rate limiting to quote and transfer endpoints
- [ ] Ensure `.env` files are not in version control

### Reliability

- [ ] Configure database connection pooling
- [ ] Set up health check monitoring on `/health`
- [ ] Configure Celery retry policies for workers
- [ ] Enable database WAL mode (PostgreSQL)
- [ ] Set up log aggregation
- [ ] Configure backup schedule for PostgreSQL

### Blockchain (Future)

- [ ] Secure private key management (HSM or Vault)
- [ ] Configure gas price limits
- [ ] Set up transaction monitoring alerts
- [ ] Implement nonce management with Redis locks
- [ ] Configure chain health monitoring

## Horizontal Scaling

| Component | Scaling Strategy | Notes |
|:----------|:----------------|:------|
| **API** | Add replicas behind load balancer | Stateless — scales linearly |
| **Workers** | Add Celery worker processes | Scale based on task queue depth |
| **Database** | Read replicas for queries | Write primary + read replicas |
| **Redis** | Redis Cluster or Sentinel | For HA message brokering |

### Bottlenecks

1. **Database writes** — Sequential ledger entries and state updates; mitigate with connection pooling
2. **Blockchain confirmations** — Bounded by block time (~2s on Base); cannot be accelerated
3. **Off-ramp settlement** — Depends on partner SLAs; typically 3–5 minutes

## Monitoring

### Key Metrics

| Metric | Threshold | Alert |
|:-------|:----------|:------|
| API response time (p99) | > 500ms | Warning |
| Transfer completion rate | < 95% | Critical |
| Settlement time (p95) | > 20 min | Warning |
| Database connection pool usage | > 80% | Warning |
| Celery task queue depth | > 100 | Warning |
| Failed transfers (rate) | > 5% | Critical |
| Health check failures | Any | Critical |

### Recommended Tools

| Tool | Purpose |
|:-----|:--------|
| **Prometheus + Grafana** | Metrics collection and dashboards |
| **Sentry** | Error tracking and alerting |
| **ELK Stack** | Log aggregation and search |
| **PgHero** | PostgreSQL query performance |
| **Flower** | Celery task monitoring |

## Reverse Proxy

For production, run behind a reverse proxy (nginx or Caddy) for:
- HTTPS termination
- Rate limiting
- Request logging
- Static file serving (if needed)

**Nginx example**:

```nginx
upstream api {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl;
    server_name payments.example.com;

    ssl_certificate /etc/ssl/certs/payments.pem;
    ssl_certificate_key /etc/ssl/private/payments.key;

    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        # Restrict admin to internal network
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://api;
    }
}
```

## Environment Profiles

| Profile | Database | Redis | Workers | Use Case |
|:--------|:---------|:------|:--------|:---------|
| **Development** | SQLite | Optional | Optional | Local development |
| **Staging** | PostgreSQL | Redis | 1 worker | Integration testing |
| **Production** | PostgreSQL (HA) | Redis Sentinel | 4+ workers | Live traffic |
