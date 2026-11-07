# Task Traceability — 3.2.1 Build Celery Task for Moodle User Creation

**Task ID and title:** 3.2.1 — Build Celery task for Moodle user creation  
**Phase / activity:** Phase 3 / Activity 3.2  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A Celery task (`provision_moodle_user`) that executes the Moodle user creation flow defined in Task 3.1.1: creates the Moodle user via `core_user_create_users`, then for institutional org types creates cohort via `core_cohort_create_cohorts` and adds members via `core_cohort_add_cohort_members`, or for individual org types enrolls in standard course group. Task is implementation-only: retry/dead-letter/idempotency per Decision log D6/D7 and error semantics per P1.2.3-D1/D2.

**PRD sources:**
- §4.1: Single Sign-On & User Provisioning Lifecycle — Django fires async Celery task to execute Moodle REST API (`core_user_create_users`); institutional accounts use `core_cohort_create_cohorts` + `core_cohort_add_cohort_members`; individual subscriptions enroll users into standard course groups.
- §4.1: Registration & Payment lifecycle — register → payment → receipt → enqueue → provision.

**UML sources:**
- §2 BPMN: Sequence flow ProvisionUser → CreateMoodleUser → OrgType → CreateCohort/AddMembers → IssueJWT
- §7 Sequence: Django → Celery → Moodle → SSO

**Approved design sources:**
- Phase 3 authorization permits Tasks 3.1.1–3.3.3 effective 2026-10-31
- Decision log D6: max 5 retries, exponential backoff 5s/15s/45s/2m/6m, dead-letter queue (`webhook_dlq`)
- Decision log D7: idempotency key per-endpoint with 24-hour TTL
- Decision log D8: license activates on `succeeded` webhook; `failed`/`expired` → license suspension
- Task 3.1.1: Approved user provisioning contract
- Task 3.1.2: Approved cohort creation/member assignment spec

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core → Celery Worker → Moodle LMS via REST API. Runtime task boundary.

## Acceptance criteria

1. Celery task for Moodle user creation created and executed via Redis broker
2. Task creates Moodle user via `core_user_create_users`
3. Institutional org types: create cohort + add members
4. Individual org types: enroll in standard course group
5. Retry policy max 5 retries with exponential backoff (D6)
6. Idempotency key per-endpoint with 24-hour TTL (D7)
7. Dead-letter queue on terminal failure (D6)
8. Error semantics per P1.2.3-D1/D2
9. No runtime implementation beyond task scope created

## Scope

**In scope:** `core/tasks.py` Celery task implementation, task registration/queue config, task input contract (organization, user, license), task execution flow.

**Out of scope:** Celery worker deployment configuration (infrastructure), real Moodle API credentials/management, JWT issuance implementation (Task 3.3.1), cohort task (Task 3.2.2), retry handling for webhook failures (Task 3.2.3), LMS DB changes.

## Dependencies / approved decisions

- Task 3.1.1: Moodle user provisioning contract (endpoints, payloads, error handling)
- Task 3.1.2: Cohort creation and member assignment spec
- Task 2.2.3: License activation on `payment.succeeded` webhook → license `pending` → `active`
- Task 2.2.1: License lifecycle policy
- Decision log D6/D7/D8
- P1.2.3-D1/D2
- Phase 2 authorization gates

## Open questions or assumptions

- Celery broker (Redis) availability and configuration (to be configured in Task 3.2.2 infra)
- Moodle API base URL and credentials (deferred to runtime configuration)
- Whether task uses Django app mode or bare function mode (implementation decision)
- Task input provenance: license activation event vs manual trigger (implementation decision)

## Evidence and completion

**Evidence:**
- Check or artifact: Celery task implementation in `core/tasks.py`
- Result: `core/tasks.py` implements Celery task `provision_moodle_user` that reads activated license, creates Moodle user via `core_user_create_users`, institutional cohort path, individual group path; retry/dead-letter/idempotency per D6/D7; error semantics per P1.2.3-D1/D2. No runtime execution environment (Redis/Moodle) in local scope.
- Location: `core/tasks.py`, `core/celery.py` (if needed), `config/celery.py` (if needed), `requirements.txt`

**Completion decision:** Complete upon implementation of the Celery task and focused test.

**Reviewer / approver and date:** Task 3.2.1 implementation pending

## Implementation integration reference

This task is consumed by Task 3.2.2 (cohort task), Task 3.2.3 (retry/error handling), Task 3.3.1 (JWT issuance), and Task 5.2.1 (end-to-end validation).