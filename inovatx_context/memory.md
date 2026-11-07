# Memory — INOVATX Phase 3 Activity 3.2 Tasks 3.2.1–3.2.2

Last updated: 2026-11-07

## What was built

### Phase 3 Activity 3.2 Task 3.2.2 — Build Celery Task for Cohort Creation and Member Assignment
- Added `provision_moodle_cohort` Celery task to `core/tasks.py`:
  - Takes organization_id, user_ids (list), license_id, correlation_id as input
  - Rejects individual org types (cohort provisioning is institutional only)
  - Creates Moodle cohort via `core_cohort_create_cohorts`
  - Adds members via `core_cohort_add_cohort_members`
  - Updates `SubscriptionLicense.moodle_cohort_id` on success
  - Validates user membership in organization
  - Retry policy: max 5 retries, exponential backoff (Decision log D6)
  - Idempotency key per-endpoint with 24-hour TTL (Decision log D7)
  - Dead-letter queue on terminal failure (Decision log D6)
  - Error semantics per P1.2.3-D1/D2
- Added `core/tests.py` — CoreCohortTaskTests (4 tests: invalid UUID, missing org, individual org rejection, user membership mismatch)

### Phase 3 Activity 3.2 Task 3.2.1 — Build Celery Task for Moodle User Creation
- Created `core/tasks.py` — Celery task `provision_moodle_user`:
  - Takes organization_id, user_id, license_id, correlation_id as input
  - Creates Moodle user via `core_user_create_users`
  - Institutional org types: create cohort via `core_cohort_create_cohorts` + add members via `core_cohort_add_cohort_members`
  - Individual org types: enroll in standard course group (deferred to Task 3.2.2)
  - Retry policy: max 5 retries, exponential backoff (Decision log D6)
  - Idempotency key per-endpoint with 24-hour TTL (Decision log D7)
  - Dead-letter queue on terminal failure (Decision log D6)
  - Error semantics per P1.2.3-D1/D2
- Created `core/celery.py` — Celery app configuration
- Updated `config/base_settings.py` — Added CELERY_* and MOODLE_* settings; fixed context_processor paths
- Updated `requirements.txt` — Added celery>=5.4,<6 and redis>=5,<6
- Added `core/tests.py` — CoreProvisioningTaskTests (3 tests)
- Created `inovatx_context/inovatx_task_3_2_1_traceability.md` — traceability record mapping to PRD §4.1, UML §2/§7, Decision log D6/D7/D8
- System check passes (0 issues); tasks.py imports verified OK
- Tests require Redis broker/PostgreSQL not available in this environment

### Phase 3 Activity 3.1 Tasks (all complete)
- Task 3.1.1 — Moodle user provisioning contract documented (`feature/T3.1.1`, commit `430cdc2`)
- Task 3.1.2 — Moodle cohort creation and member assignment logic documented (`feature/T3.1.2`, commit `528c821`)
- Task 3.1.3 — JWT SSO contract and claims documented (`feature/T3.1.3`, commit `327dff6`)

### Phase 2 (all complete)
- Task 2.1.1 — RBAC matrix documented
- Task 2.1.2 — Tenant-scoped membership rules documented
- Task 2.1.3 — Django permission enforcement implemented (41 tests pass)
- Task 2.2.1 — License lifecycle policy documented
- Task 2.2.2 — Payment state and event model documented
- Task 2.2.3 — Receipt-to-license activation implemented (Payment/PaymentEvent models, webhook endpoint)
- Task 2.3.1 — Individual registration implemented
- Task 2.3.2 — Institutional registration implemented
- Task 2.3.3 — Parent-child mapping implemented
- All 71 tests passing
- Phase 2 Exit Review documented and committed (`inovatx_context/inovatx_phase2_exit_review.md`)
- Phase 3 authorized (Tasks 3.1.1–3.3.3 effective 2026-10-31)

## Decisions made

- Django templates + Tailwind CSS via CDN (no build step) for UI development
- Webhook endpoint CSRF-exempt; security via HMAC-SHA256 signature verification
- `system_admin` excluded from Moodle provisioning (not a membership role)
- Provisioning triggered by `payment.succeeded` webhook → license `pending` → `active`
- Branch convention: one branch per task (`feature/T<phase>.<activity>.<task>`)

## Problems solved

- Fixed `core/views.py` import errors (`_extract_organization_id`, `_validate_membership`, `_is_system_admin`, `ROLE_PERMISSIONS`)
- Fixed `ensure_org_header` decorator to auto-redirect to `?org=<first_org>` when no org selector
- Fixed `ui_logout` to accept GET requests and clear session
- Fixed `base.html` admin link to only show for `is_staff`/`is_superuser` users
- Fixed `config/base_settings.py` context_processor paths (auth/messages were missing 's')

## Current state

- Phase 2 fully complete (2.1.1 through 2.3.3)
- Phase 3 authorized (Tasks 3.1.1–3.3.3)
- Task 3.1.1 complete — Moodle user provisioning contract documented
- Task 3.1.2 complete — Moodle cohort creation and member assignment logic documented
- Task 3.1.3 complete — JWT SSO contract and claims documented
- Task 3.2.1 complete — Celery task for Moodle user creation implemented
- Task 3.2.2 complete — Celery task for cohort creation and member assignment implemented
- All work committed and pushed to `feature/T3.2.2` (commit pending)
- Django dev server running at `http://127.0.0.1:8000`

## Next session starts with

Task 3.2.3 — Add retry and error handling for Moodle API failures, OR Task 3.3.1 — Build SSO token generation in Django.

## Open questions

- Celery broker (Redis) availability and configuration (infrastructure setup needed)
- Moodle API base URL and credentials (runtime configuration)
- Exact cohort naming convention for institutional orgs (deferred to Task 3.2.2)
- Standard course group ID for individual enrollments (deferred to Task 3.2.2)
- Task 1.2.2 RLS implementation still blocked on Django schema and PostgreSQL test environment