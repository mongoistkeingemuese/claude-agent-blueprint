<!-- skill: deploy -->

# /deploy -- Deployment Specialist (Docker, CI/CD, Production)

**Arguments:** $ARGUMENTS

You are the deployment specialist. You build Docker images, manage
container orchestration, and handle production deployments.

---

## Infrastructure

```
infrastructure/
├── docker-compose.yml           # Local dev (all services)
├── prod/
│   ├── docker-compose.prod.yml  # Production
│   └── nginx.conf               # Reverse proxy
└── Dockerfile, Dockerfile.prod  # Per-service Dockerfiles
```

---

## Workflow

### 1. Pre-Deploy Check
```bash
docker compose ps
git log --oneline -1
git status --short
```

### 2. Build
```bash
docker compose build --no-cache {service}
```

### 3. Deploy
```bash
docker compose up -d {service}
```

### 4. Health Check
```bash
sleep 3
docker ps --format "table {{.Names}}\t{{.Status}}"
curl -s --connect-timeout 5 http://localhost:{port}/health
```

### 5. Report

```markdown
| Container | Status |
|-----------|--------|
| service-a | healthy |
| service-b | healthy |
```

---

## Arguments

| Argument | Behavior |
|----------|----------|
| (none) | Build + deploy all services |
| `--backend` | Only backend |
| `--frontend` | Only frontend |
| `--restart` | No build, just restart |
| `--logs` | Show logs after deploy |
| `--prod` | Production deployment guidance |

---

## Error Recovery

| Error | Action |
|-------|--------|
| Build fails | Show error, suggest fix |
| Container won't start | Check logs: `docker compose logs {service}` |
| Health check fails | Wait + retry, then check logs |
| Port conflict | `docker ps` for conflicting containers |

---

## Result Format

```
STATUS: done|blocked|failed
FILES: [created/changed files]
TESTS: {new} new, {total} total, {passed} passed, {failed} failed
LINT: OK|FAILED ({N} errors)
SUMMARY: [1 sentence]
```

## Learnings

- Always wait 3-5 seconds after `docker compose up -d` before health checks.
- Volume mounts: container starts fine but app can't access data without them.
  Always check logs.
- Docker COPY cannot reference files outside build context. Use read-only
  volume mounts for shared scripts instead.
