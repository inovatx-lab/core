# INOVATX Environment Baseline — Phase 0 Planning

**Status:** Planning baseline with Task 1.3.1 local Django implementation update; not a deployment authorization
**Roadmap task:** 0.2.2 — Establish environment baseline
**Sources:** [PRD](inovatx_product_requirements_document_prd.md), [system models](inovatx_uml.md), [Phase 0 decision log](inovatx_phase0_decision_log.md)

## Target technology inventory

| Component | Documented target | Planned role | Status / qualification |
|---|---|---|---|
| Django Core | Django 5.x, Python 3.12+ | Core application, identity, billing, tenant-aware APIs | Task 1.3.1 local Django 5.2 project, environment-driven PostgreSQL settings, separate migration/runtime identities, migration setup, and development-server startup are validated. Domain models/admin, container image, and production settings remain pending. |
| PostgreSQL | PostgreSQL 16+ | Core data with RLS and Moodle data | One PostgreSQL service with separate `inovatx_db` and `moodle_db` databases is the approved planning topology. Local PostgreSQL 18.6 and the Task 1.3.1 owner/migrator/runtime baseline are reported configured and used for migration/server validation; production provisioning, tenant-table grants, and RLS remain unimplemented. |
| Redis | Redis 7.x | Celery broker/cache and application caching as approved | Persistence, authentication, memory policy, and production configuration remain undefined. |
| Moodle LMS | Moodle 4.x, PHP 8.2+ / Apache | Learning hub, quizzes, cohorts, and gradebook | Exact Moodle release, image/source, plugins, configuration, and database initialization are not selected. |
| FastAPI AI | FastAPI, Python 3.12+, Pydantic v2 | Internal AI orchestration and SSE service | Application code, image, provider integration, runtime settings, and service authentication are not present. |
| Celery worker | Celery; shares the Django project/runtime target | Asynchronous Moodle provisioning and other approved background work | Worker module, command, queue topology, concurrency, and retry configuration must be defined with the application. |
| Nginx | Nginx; exact version not specified | Only planned public ingress; TLS termination, routing, and rate limiting | Nginx configuration, domains, certificate flow, and route policies are not present. |

These are targets stated by the source documents, not claims that compatible images or working services have been built. Exact patch releases and image provenance must be pinned before a runnable deployment.

## Container and network plan

The root [Compose planning skeleton](../docker-compose.yml) records the intended service boundaries. Every service is under the `planning` profile so the file does not start services under a default `docker compose up`. Even when explicitly selected, it is not runnable: application images are not built and essential setup is unresolved.

| Planned service | Networks | Planned dependencies |
|---|---|---|
| Nginx | `edge`, `app` | Django Core and Moodle |
| Django Core | `app`, `data` | PostgreSQL, Redis |
| Celery worker | `app`, `data` | PostgreSQL, Redis, Moodle |
| Moodle | `app`, `data` | PostgreSQL |
| FastAPI AI | `app` | External model-provider egress path; Redis use remains to be decided |
| PostgreSQL | `data` | None |
| Redis | `data` | None |

- `edge` is joined only by Nginx, which is the only service with planned host-published ports.
- `app` is a private, unpublished service network. It is not configured as Docker's `internal` network because services such as FastAPI may need approved outbound calls to external providers.
- `data` is an internal network for database/cache traffic; only services that need those dependencies join it.
- One PostgreSQL service will host both named databases. The skeleton's stock PostgreSQL bootstrap currently creates `inovatx_db`; a safe, repeatable `moodle_db` creation/bootstrap process is still required.
- Named volumes are placeholders for PostgreSQL and Redis persistence. Backup, restore, retention, and operational settings require separate design and validation.

## Open items before a runnable stack

1. Build and pin reviewed Django, Celery, Moodle, and FastAPI images; define their entrypoints and health checks.
2. Select exact supported release tags and image sources for every service.
3. Define secret delivery and non-default database roles/passwords; do not commit credentials or secret files.
4. Specify idempotent provisioning of `moodle_db`, database grants, and the RLS-enabled Core database role and policies.
5. Select Moodle's database settings, plugins, persistent data paths, and supported image/configuration approach.
6. Define Nginx configuration, domains, TLS certificate handling, request limits, and upstream health behavior.
7. Define Celery's application module, queues, worker command, retry policies, and scaling/resource limits.
8. Define internal service authentication and the Moodle/browser-to-private-FastAPI streaming path. The latter is unresolved in the system models and must not be addressed by exposing FastAPI publicly without approval and security review.
9. Decide whether FastAPI uses Redis and, if so, its access pattern and network boundary.
10. Decide health/readiness checks, resource limits, Redis persistence/eviction, database connection limits, and deployment/upgrade behavior.
11. Add and exercise backup/restore procedures and validate the target workload. The single-VPS topology does not establish high availability or prove the PRD's concurrency target.

## Validation boundary

The container/network plan remains planning-only. The project owner reports PostgreSQL 18.6 listening on localhost, the local Task 1.3.1 roles/schema privileges configured, migrations applied, and the runtime-credential development server started. These local checks do not validate tenant RLS, containers, images, service integration, performance targets, or production readiness.
