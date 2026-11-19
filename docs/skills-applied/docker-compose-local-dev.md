---
name: docker-compose-local-dev
description: "Set up reproducible local development with Docker Compose: services, health checks, volumes, env files, profiles, and fast rebuilds. Use when onboarding developers, running app plus database plus cache locally, or fixing flaky local environments."
---

# Docker Compose for Local Development

## Workflow
1. List the services needed locally (app, database, cache, queue, mail catcher) and pin image versions to match production.
2. Add health checks and make dependent services wait for health, not just startup.
3. Mount source code as a bind mount for live reload; keep dependencies and build artifacts inside the image or a named volume.
4. Keep configuration in an `.env` file (commit `.env.example`, never the real `.env`), and use separate files or profiles for optional services.
5. Provide one-command tasks (`make up`, `make test`, `make migrate`) and document them in the README.
6. Keep the local setup disposable: a clean `down -v` and `up` must work from scratch, including migrations and seed data.

## Rules
- Do not use production secrets or production data locally; use fake seed data.
- Do not expose databases on all interfaces; bind to `127.0.0.1` when publishing ports.
- Use named volumes for database data so rebuilds do not delete it unintentionally, and document how to reset it.
- Match the production Postgres major version to avoid surprises.
- Keep compose files simple; use `profiles` for optional services such as workers or observability.

## Example
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:-devpassword}
      POSTGRES_DB: app
    ports: ["127.0.0.1:5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d app"]
      interval: 5s
      timeout: 3s
      retries: 10
  api:
    build: .
    env_file: .env
    ports: ["127.0.0.1:8000:8000"]
    depends_on:
      db: { condition: service_healthy }
    volumes: [".:/app"]
    command: uvicorn app.main:app --host 0.0.0.0 --reload
  worker:
    build: .
    profiles: ["workers"]
    command: celery -A app.celery worker -l info
volumes:
  pgdata:
```

## Verification
On a clean checkout run `docker compose up` and confirm the app, migrations, and tests work using only the README; run `docker compose down -v` and repeat.
