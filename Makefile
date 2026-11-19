.PHONY: setup up down migrate test test-pg lint audit lock
setup:   ; cp -n backend/.env.example backend/.env || true
up:      ; docker compose up --build
down:    ; docker compose down
migrate: ; docker compose run --rm api alembic upgrade head
test:    ; cd backend && pytest                      # SQLite
test-pg: ; cd backend && TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/drama_test pytest
lint:    ; cd backend && ruff check app tests alembic && ruff format --check app tests alembic
audit:   ; cd backend && bandit -q -r app && pip-audit -r requirements.txt
lock:    ; cd backend && pip-compile --generate-hashes --strip-extras -o requirements.txt requirements.in && pip-compile --generate-hashes --strip-extras -o requirements-dev.txt requirements-dev.in
