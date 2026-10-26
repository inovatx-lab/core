# Memory — INOVATX Task 1.3.1 Local Django Foundation

Last updated: 2026-10-26 19:20 +03:00

## What was built

- Created a minimal Django 5.2 project with root `manage.py`, `config/`, and a `core` app.
- Added PostgreSQL-only environment-driven settings, `requirements.txt`, and PowerShell local setup guidance in `README.md`.
- Added Task 1.3.1 traceability and recorded the selected built-in `auth.User` in the decision log and schema plan.
- Updated repository structure, environment/roadmap evidence, and prior tenant-task docs to distinguish the new Django skeleton from still-missing models, middleware, workers, and PostgreSQL testing.

## Decisions made

- Use Python 3.12, Django 5.2 LTS, PostgreSQL only, Django built-in `auth.User`, `requirements.txt`, and environment-only secrets/configuration.
- Task 1.3.1 does not include domain models/admin, API routes, tenant middleware/RLS, database provisioning, or production deployment.
- Task 1.2.3 documentation commit `185fa99` is on `feature/T1.2.3` and is published to `origin`.

## Problems solved

- Verified the prior Task 1.2.3 commit includes an SSH signature; local signature display warns because `gpg.ssh.allowedSignersFile` is not configured.
- Identified that Django `runserver` checks migration history at startup, so it cannot establish a successful local server boot when PostgreSQL is unavailable.

## Current state

- Current branch: `feature/T1.3.1`.
- The scaffold passes `manage.py check`, `compileall`, and a WSGI request smoke test (expected 404 because no routes are defined). Settings runtime validation confirmed PostgreSQL and `auth.User`; missing `DJANGO_SECRET_KEY` fails explicitly.
- No PostgreSQL server is available at `127.0.0.1:5432`. `makemigrations --check --dry-run` found no model changes but could not check database migration history; `runserver` could not complete its startup check.
- Task 1.3.1 is incomplete: successful development-server boot and PostgreSQL-backed migration setup validation remain unverified. Do not proceed to Task 1.3.2 until the Task 1.3.1 deliverables are met.
- Task 1.3.1 changes are pending commit/push. This memory is staged and should be included with the task changes by the user's latest instruction.

## Next session starts with

- Check whether the Task 1.3.1 commit was created and published. If not, finish commit/push on `feature/T1.3.1`, then verify the remote ref and clean worktree.
- Resume Task 1.3.1 validation with an available PostgreSQL 16+ environment; only then consider Task 1.3.2, after the applicable traceability and quality-gate process.

## Open questions

- When and where will a PostgreSQL test service be made available for local migration validation?
