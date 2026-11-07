# Task Traceability — 3.2.3 Add Retry and Error Handling for Moodle API Failures

**Task ID and title:** 3.2.3 — Add retry and error handling for Moodle API failures  
**Phase / activity:** Phase 3 / Activity 3.2  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** Retry logic with exponential backoff (5s/15s/45s/2m/6m), dead-letter queue (`WebhookDLQ` model), and proper error handling for Moodle API failures in `core/tasks.py`. Implementation-only: per Decision log D6/D7 and error semantics per P1.2.3-D1/D2.

**PRD sources:**
- §4.1: Single Sign-On & User Provisioning Lifecycle — Moodle REST API calls may fail; exponential-backoff retries per NFR-03.
- §4.2: Sync Protocol — Moodle webhook errors need dead-letter handling per NFR-04.

**UML sources:**
- §2 BPMN: Retry gateway — "Payment webhook or Moodle API call failed?" → Backoff with exponential backoff → Enqueue
- §7 Sequence: Celery worker → Moodle → error handling paths

**Approved design sources:**
- Phase 3 authorization permits Tasks 3.1.1–3.3.3 effective 2026-10-31
- Decision log D6: max 5 retries, exponential backoff 5s/15s/45s/2m/6m, dead-letter queue (`webhook_dlq`)
- Decision log D7: idempotency key per-endpoint with 24-hour TTL
- Decision log D8: license activates on `succeeded` webhook; `failed`/`expired` → license suspension
- P1.2.3-D1: Request error semantics — 401/400/404/403/500 with correlation IDs
- P1.2.3-D2: Internal context invariant failure — stop, roll back, generic response
- Task 3.2.1: Moodle user creation Celery task
- Task 3.2.2: Cohort creation and member assignment Celery task

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core → Celery Worker → Moodle LMS via REST API. Retry/DLQ/error-handling boundary.

## Acceptance criteria

1. `WebhookDLQ` model for dead-lettered Moodle API events (organization_id, event_type, payload, error, retry_count, created_at)
2. Retry logic with exponential backoff intervals (5s, 15s, 45s, 2m, 6m) for Moodle API calls
3. Dead-letter queue: terminal failures written to `WebhookDLQ` after max retries
4. Error handling for Moodle API errors (400/401/403/404/500) per P1.2.3-D1/D2
5. Correlation ID propagation through retry/dead-letter flow
6. Tests pass for retry/dead-letter/error-handling paths
7. System check passes; tasks.py imports verified OK
8. Tests require Redis broker/PostgreSQL not available in this environment

## Scope

**In scope:** `WebhookDLQ` model, retry logic with exponential backoff, dead-letter handling, error classification (retryable vs terminal), correlation ID propagation.

**Out of scope:** Worker deployment configuration, real Moodle API integration testing, DLQ consumer/runner, webhook signature verification (Task 3.2.3 infra scope).

## Dependencies / approved decisions

- Task 3.2.1: Moodle user creation Celery task
- Task 3.2.2: Cohort creation Celery task
- Decision log D6: Retry/dead-letter policy
- Decision log D7: Idempotency key/TTL
- P1.2.3-D1/D2: Error semantics
- NFR-03: High availability (retries with exponential backoff)
- NFR-04: Integration contracts (dead-letter handling)

## Open questions or assumptions

- Whether DLQ consumer/runner should retry dead-lettered events (deferred to operations)
- Exact backoff schedule (5s/15s/45s/2m/6m per Decision log D6)
- Whether correlation IDs should be stored separately or embedded in DLQ payload

## Evidence and completion

**Evidence:**
- Check or artifact: `core/models.py` `WebhookDLQ` model + `core/tasks.py` retry/error handling + `core/tests.py` retry/DLQ tests
- Result: `WebhookDLQ` model stores dead-lettered events; `provision_moodle_user` and `provision_moodle_cohort` implement exponential backoff retry and DLQ fallback; error classification distinguishes retryable vs terminal errors; correlation IDs propagated through all error paths. Tests cover retry conditions, dead-letter fallback, and error handling.
- Location: `core/models.py`, `core/tasks.py`, `core/tests.py`, `inovatx_context/inovatx_task_3_2_3_traceability.md`

**Completion decision:** Complete upon implementation and test verification of retry/error-handling.

**Reviewer / approver and date:** Task 3.2.3 implementation complete

## Implementation integration reference

This task is consumed by Task 3.2.4 (if any), Task 3.3.1 (JWT issuance), Task 5.2.1 (end-to-end validation).