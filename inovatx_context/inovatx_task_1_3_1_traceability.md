# Task Traceability — 1.3.1 Django Local Foundation

**Task ID and title:** 1.3.1 — Set up Django app skeleton and settings for local environment
**Phase / activity:** Phase 1 / Activity 1.3
**Owner:** Project owner
**Status:** Complete — local project, migration setup, and runtime startup validated

## Outcome and sources

**Outcome / deliverable:** A minimal local Django Core project that boots and is configured for PostgreSQL-backed migration work without implementing domain models, APIs, tenant middleware, or production deployment.

**PRD sources:**
- §2.2: Django 5.x and Python 3.12+ are the Core technology baseline; PostgreSQL 16+ is the target database.
- §3.1–§3.2: the Core uses PostgreSQL and transaction-local tenant context; executable domain schema and RLS remain with their assigned tasks.

**UML sources:**
- §8: Django Core and PostgreSQL service boundaries.

**Approved design sources:**
- Phase 1 authorization permits Tasks 1.1.1–1.3.3 only.
- Task 1.1.3 schema/migration plan, including the authentication-model dependency.
- Project-owner choices confirmed on 2026-10-26 and recorded under P1.3.1-D1: Python 3.12, Django 5.2 LTS, `requirements.txt`, repository-root `manage.py`, `config/` project package, `core/` Django app, Django's built-in `User`, PostgreSQL-only settings, and environment-variable-only local configuration.
- Task 1.2.2 and Task 1.2.3 records: RLS and tenant failure behavior are approved designs, but their executable implementation and tests remain separate and pending.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django Core local process and PostgreSQL configuration boundary. This task creates no public route, tenant authorization path, or production service.

## Acceptance criteria

1. Create a minimal Django project and `core` app using the approved repository layout and supported Python/Django baseline.
2. Configure Django to use PostgreSQL only, taking required local values from environment variables without committing credentials or providing an SQLite fallback.
3. Configure the built-in Django `User`; do not introduce a custom authentication model or Core domain models in this task.
4. Provide the minimum settings and documented commands needed to install dependencies, run Django checks, and prepare for migrations.
5. Demonstrate the Django WSGI application loads and responds, and pass available non-database checks. Report PostgreSQL-dependent `runserver` startup and migration-history validation as blocked if the database is unavailable.
6. Update the roadmap, repository structure, and directly related schema documentation with evidence that reflects only what was implemented and validated.

## Scope

**In scope:** Django project/app skeleton, Python dependency manifest, local settings, environment configuration, PostgreSQL driver configuration, and task-local setup/validation instructions.

**Out of scope:** Domain models/admin (Task 1.3.2), API contracts/routes (Task 1.3.3), tenant middleware/RLS implementation (Tasks 1.2.1–1.2.3/1.2.2 executable work), database service provisioning, Docker deployment, production settings, and features from later phases.

## Approved decisions and dependencies

- Use Python 3.12 and Django 5.2 LTS with a `requirements.txt` dependency workflow.
- Place `manage.py` at the repository root, with the `config` project package and `core` Django app.
- Use Django's built-in `User`; `UserProfile` remains a separate organization-membership model to be implemented under Task 1.3.2.
- Configure PostgreSQL as the sole database backend. Do not use SQLite as a fallback or as evidence of RLS behavior.
- Read required database and Django secret settings from environment variables. Do not commit secrets or add a dotenv dependency.
- Use separate migration and runtime database identities per P1.3.1-D2. Runtime access to `django_migrations` is limited to `SELECT` for Django's startup history check.
- Keep this task to a local project foundation; it does not authorize a full-stack or production deployment.

## Evidence and completion

**Evidence:**
- Check or artifact: Django skeleton, dependency/settings files, local setup instructions, and focused startup/configuration checks.
- Result: Python 3.12 with Django 5.2.18 installed from the declared requirements. `manage.py check` passed under both default and migration settings; all three focused database-settings unit tests passed; Python compilation and `git diff --check` passed. WSGI smoke checks passed: with `DEBUG=false`, `/` returns 404; with `DEBUG=true`, Django displays its development install page because the URL map is intentionally empty. The project owner reports PostgreSQL 18.6 listening on localhost, the approved owner/migrator/runtime roles and database privileges configured, migrations completed using the migration settings, and the development server started with runtime credentials. The supplied browser screenshot shows the expected Django development install page at `127.0.0.1:8000`. The migration console output and database privilege state were not independently captured by this review; no passwords or credential values were recorded.
- Location: `README.md`, `requirements.txt`, `manage.py`, `config/`, `core/`, and the validation output for this task.
- Validation boundary: PostgreSQL role/database setup, successful migration execution, and runtime-credential server startup are owner-reported; the screenshot corroborates the local server response but does not independently establish database grants. This task does not implement domain models/admin, tenant tables, RLS, or production deployment.

**Completion decision:** Complete. All Task 1.3.1 deliverables are implemented and the PostgreSQL migration/server validation has been reported successful by the project owner. Later domain, tenant-isolation, and deployment work remains outside this task.
**Reviewer / approver and date:** Project owner supplied the migration and runtime-server validation on 2026-10-26; implementation scope and evidence reviewed on 2026-10-26.
