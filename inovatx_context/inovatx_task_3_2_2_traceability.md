# Task Traceability — 3.2.2 Build Celery Task for Cohort Creation and Member Assignment

**Task ID and title:** 3.2.2 — Build Celery task for cohort creation and member assignment  
**Phase / activity:** Phase 3 / Activity 3.2  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A dedicated Celery task (`provision_moodle_cohort`) that handles cohort creation and member assignment independently from user creation. Task executes `core_cohort_create_cohorts` for institutional org types and `core_cohort_add_cohort_members` to assign users to cohorts. Implementation-only: retry/dead-letter/idempotency per Decision log D6/D7, error semantics per P1.2.3-D1/D2, license.cohort_id sync.

**PRD sources:**
- §4.1: Single Sign-On & User Provisioning Lifecycle — institutional accounts use `core_cohort_create_cohorts` + `core_cohort_add_cohort_members`; `moodle_cohort_id` tracked on SubscriptionLicense per ERD §5.
- §4.1: Registration & Payment lifecycle — cohort creation occurs during provisioning flow after user creation.

**UML sources:**
- §2 BPMN: Sequence flow CreateCohort → AddMembers → IssueJWT
- §5 ERD: SubscriptionLicense.moodle_cohort_id field (nullable varchar)
- §7 Sequence: Cohort provisioning (Celery) → cohort enrollment

**Approved design sources:**
- Phase 3 authorization permits Tasks 3.1.1–3.3.3 effective 2026-10-31
- Decision log D6: max 5 retries, exponential backoff 5s/15s/45s/2m/6m, dead-letter queue (`webhook_dlq`)
- Decision log D7: idempotency key per-endpoint with 24-hour TTL
- Decision log D8: license activates on `succeeded` webhook
- Task 3.1.2: Approved cohort creation and member assignment spec
- Task 3.2.1: Approved Moodle user creation Celery task pattern

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core → Celery Worker → Moodle LMS via REST API. Cohort + member assignment boundary.

## Acceptance criteria

1. Dedicated Celery task `provision_moodle_cohort` for cohort creation and member assignment
2. Task calls `core_cohort_create_cohorts` for institutional org types
3. Task calls `core_cohort_add_cohort_members` to assign users to cohort
4. Task updates `SubscriptionLicense.moodle_cohort_id` on success
5. Retry policy max 5 retries with exponential backoff (D6)
6. Idempotency key per-endpoint with 24-hour TTL (D7)
7. Dead-letter queue on terminal failure (D6)
8. Error semantics per P1.2.3-D1/D2
9. Tests pass (success/failure paths)
10. No runtime environment dependencies (Redis/Moodle) needed for test execution

## Scope

**In scope:** `core/tasks.py` dedicated cohort task (`provision_moodle_cohort`), tests, update task list with cohort task registration.

**Out of scope:** Moodle user creation (Task 3.2.1), individual group enrollment, cohort CRUD endpoints, Moodle API credential management, worker deployment config.

## Dependencies / approved decisions

- Task 3.1.2: Cohort creation and member assignment spec
- Task 3.2.1: Celery task pattern for Moodle provisioning (retry/idempotency/dead-letter)
- Task 2.2.1: License lifecycle policy (moodle_cohort_id field tracking)
- Decision log D6/D7/D8
- P1.2.3-D1/D2

## Open questions or assumptions

- Whether cohort task should check for existing cohort before creation (idempotency design)
- Task input provenance: license event vs manual trigger (implementation decision)
- Moodle API credentials sourced from settings/env (runtime configuration)

## Evidence and completion

**Evidence:**
- Check or artifact: `core/tasks.py` `provision_moodle_cohort` task + `core/tests.py` cohort tests
- Result: Dedicated Celery task `provision_moodle_cohort` handles cohort creation (`core_cohort_create_cohorts`), member assignment (`core_cohort_add_cohort_members`), license.moodle_cohort_id sync; retry/dead-letter/idempotency per D6/D7; error semantics per P1.2.3-D1/D2. Tests cover institutional cohort path, existing-user assignment, and failure conditions.
- Location: `core/tasks.py`, `core/tests.py`, `inovatx_context/inovatx_task_3_2_2_traceability.md`

**Completion decision:** Complete upon implementation and test verification of `provision_moodle_cohort`.

**Reviewer / approver and date:** Task 3.2.2 implementation complete

## Implementation integration reference

This task is consumed by Task 3.2.3 (retry/error handling), Task 3.3.1 (JWT issuance with cohort authorization), Task 5.2.1 (end-to-end validation), and institutional onboarding flow (Task 2.3.2).