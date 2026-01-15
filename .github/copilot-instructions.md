# Copilot instructions for loan-dashboard

## Big picture
- FastAPI app entry is [app/main.py](../app/main.py); routers live under app/api/v1/routes and call into services + CRUD.
- Data access is SQLAlchemy 1.4: models in app/db/models, CRUD helpers in app/db/crud, and Pydantic schemas in app/db/schemas (v2 with `from_attributes`).
- Multi-tenant is enforced by `organization_id` with a default org created via `get_or_create_default_organization` (see app/db/crud/organization.py). Most CRUD functions call this helper first.
- Loan lifecycle logic is centralized in `LoanService` (state transitions + audit log + payment side effects) in app/services/loan_service.py.

## Key flows and integrations
- Document upload flow (loan documents): API routes build a stable object path, checksum, then store metadata via `create_document` (see app/api/v1/routes/loan.py and app/db/crud/document.py). Storage backend is Supabase Storage via app/integrations/supabase_storage.py.
- Signed URLs for documents are generated through Supabase Storage helpers and returned by API routes.
- Auth uses internal JWTs (app/core/token.py) + password hashing (app/core/security.py). `get_current_user` verifies internal JWT, not Supabase JWT (see app/api/deps.py).
- Redis is used for refresh token storage and lightweight caching (e.g., due-today loans) via app/core/redis.py.
- Direct debit integration uses Mono HTTP APIs (app/integrations/mono.py) and background processing in Celery tasks (app/tasks/debit.py). Celery is configured in app/core/celery_worker.py.

## Project conventions and patterns
- UUID primary keys on most models; avoid mixing int and UUID IDs in new code (see app/db/models/loan.py).
- Always fetch or create the default organization before creating/querying tenant-scoped records.
- When transitioning loan status, use `LoanService.transition_status()` to enforce the state machine and audit logging.
- For document uploads, keep object paths stable and sanitized; store `bucket`, `uri`, `content_type`, `size_bytes`, `checksum` in `LoanDocument`.

## Developer workflows (from repo)
- Local services: Postgres + Redis via docker-compose.yml.
- Migrations: `alembic upgrade head` (uses env from .env/.env.example).
- Run API: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (same as Dockerfile CMD).
- Celery workers: see docker-compose.yml for the `celery-worker` and `celery-beat` commands.

## Env/config reference
- Config is loaded from .env via app/core/config.py. Use .env.example as the template for required variables (database, Redis, Supabase, Mono).

## Where to look for examples
- CRUD + schemas: app/db/crud/loan.py, app/db/schemas/loan.py
- File upload + signed URLs: app/api/v1/routes/loan.py
- Redis token storage: app/core/token.py