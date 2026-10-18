# Memory — INOVATX Phase 0 Baseline

Last updated: 2026-10-18 12:40 +03:00

## What was built

- Added root `AGENTS.md` with project context links and guardrails.
- Updated `REPOSITORY_STRUCTURE.md` to represent the actual docs-first workspace.
- Completed Activity 0.2 locally:
  - Task 0.2.1: branch policy and current workspace structure documented; local `main` and `develop` exist.
  - Task 0.2.2: added `inovatx_context/inovatx_environment_baseline.md` and a planning-only root `docker-compose.yml`.
  - Task 0.2.3: added `inovatx_context/inovatx_architecture_baseline.md` with Mermaid diagram, PRD/UML traceability, trust boundaries, and unresolved items.
- Updated `inovatx_context/inovatx_project_todo.md` with completion status and evidence for Tasks 0.2.1–0.2.3.

## Decisions made

- The Compose file is a planning skeleton, not a runnable stack or deployment authorization.
- PostgreSQL planning topology is one service with separate logical `inovatx_db` and `moodle_db` databases.
- Nginx is the only planned published ingress; FastAPI remains private on the application network.
- Browser/learner delivery of AI SSE through Moodle remains unresolved; do not invent a public FastAPI route.
- Activity 0.3 is approved as the next Phase 0 planning/guardrail work. This is not authorization for product implementation.

## Problems solved

- Git signing worked interactively after this environment failed to unlock the encrypted key via agent. For future signed commits, provide the user an interactive PowerShell command rather than repeatedly trying to sign in the tool session.
- Docker is unavailable in the environment; prior static Compose YAML and structural checks passed, but runtime validation was not possible.

## Current state

- Current branch: `feature/T0.2.3`; working tree clean.
- Latest commit: `103a123` (`docs(phase0): define minimum viable architecture`), signed.
- Task 0.2.2 is committed on `feature/T0.2.2` as `9a57e2c`.
- The GitHub remote has no advertised branches and local work has not been pushed. GitHub branch protections/publication remain pending.
- No Activity 0.3 deliverables have been created yet.

## Next session starts with

Begin Activity 0.3, starting with Task 0.3.1: define AI coding guardrails and phase-lock policy. Inspect the full roadmap/task evidence and existing project instructions first, then create the developer checklist and code-generation protocol. Continue one task per feature branch and respect the Phase 0 approval boundary.

## Open questions

- Confirm the preferred Task 0.3.1 document location/name if the existing `AGENTS.md` and project roadmap do not settle it.
- GitHub remote repository state, branch publication, and branch protection are still unverified/configuration-pending.
- The private FastAPI-to-learner SSE forwarding mechanism and LLM hosting/network boundary remain unresolved architecture items.
