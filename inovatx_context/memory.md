# Memory — INOVATX Phase 3 Activity 3.1 Task 3.1.3

Last updated: 2026-11-07

## What was built

### Phase 3 Activity 3.1 Task 3.1.3 — JWT SSO Contract and Claims
- Created `inovatx_context/inovatx_task_3_1_3_traceability.md` — traceability record mapping to PRD §4.1/FR-02, UML §2 BPMN, Decision log D6/D7/D8, and P1.2.3-D1/D2
- Updated `inovatx_context/inovatx_project_todo.md` — Task 3.1.3 marked Complete
- Updated `REPOSITORY_STRUCTURE.md` — added Task 3.1.3 traceability file
- All committed and pushed to `feature/T3.1.3`

### Phase 3 Activity 3.1 Task 3.1.2 — Moodle Cohort Creation and Member Assignment Logic
- Created `inovatx_context/inovatx_task_3_1_2_traceability.md` — cohort sync specification with cohort creation parameters, member assignment logic, institutional vs individual org-type branching, cross-tenant isolation, retry/idempotency policies, and error semantics
- Updated `inovatx_context/inovatx_project_todo.md` — Task 3.1.2 marked Complete
- Updated `REPOSITORY_STRUCTURE.md` — added Task 3.1.2 traceability file
- All committed and pushed to `feature/T3.1.2`

### Phase 3 Activity 3.1 Task 3.1.1 — Moodle User Provisioning Contract
- Created `inovatx_context/inovatx_moodle_provisioning_contract.md` — Moodle user provisioning contract:
  - Moodle REST API endpoints: `core_user_create_users`, `core_cohort_create_cohorts`, `core_cohort_add_cohort_members`
  - Payload schema for user creation (username, password, firstname, lastname, email, auth, lang, timezone)
  - Institutional org type path: create cohort → add members → issue JWT
  - Individual org type path: enroll in standard course group → issue JWT
  - Idempotency key per-endpoint with 24-hour TTL (Decision log D7)
  - Retry policy: max 5 retries, exponential backoff (5s/15s/45s/2m/6m), dead-letter queue (Decision log D6)
  - Error semantics: 400/403/404/500 per P1.2.3-D1/D2
  - Cross-tenant isolation: organization_id must match user membership
  - system_admin excluded from Moodle provisioning (not a membership role)
- Created `inovatx_context/inovatx_task_3_1_1_traceability.md` — traceability record mapping to PRD §4.1/FR-02, UML §2 BPMN, Decision log D6/D7/D8
- Updated `inovatx_context/inovatx_project_todo.md` — Task 3.1.1 marked Complete
- Updated `inovatx_context/inovatx_completion_checklist.md` — Phase 3 gate updated
- Updated `REPOSITORY_STRUCTURE.md` — added both new documents
- All committed and pushed to `feature/T3.1.1` (commit `430cdc2`)

### Phase 3 authorized (Tasks 3.1.1–3.3.3)
- Phase 3 authorized effective 2026-10-31

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

## Decisions made

- Django templates + Tailwind CSS via CDN (no build step) for UI development
- Webhook endpoint CSRF-exempt; security via HMAC-SHA256 signature verification
- `system_admin` excluded from Moodle provisioning (not a membership role)
- Provisioning triggered by `payment.succeeded` webhook → license `pending` → `active`

## Problems solved

- Fixed `core/views.py` import errors (`_extract_organization_id`, `_validate_membership`, `_is_system_admin`, `ROLE_PERMISSIONS`)
- Fixed `ensure_org_header` decorator to auto-redirect to `?org=<first_org>` when no org selector
- Fixed `ui_logout` to accept GET requests and clear session
- Fixed `base.html` admin link to only show for `is_staff`/`is_superuser` users

## Current state

- Phase 2 fully complete (2.1.1 through 2.3.3)
- Phase 3 authorized (Tasks 3.1.1–3.3.3)
- Task 3.1.1 complete — Moodle user provisioning contract documented
- Task 3.1.2 complete — Moodle cohort creation and member assignment logic documented
- Task 3.1.3 complete — JWT SSO contract and claims documented
- All work committed and pushed to `feature/T3.1.3`
- Django dev server running at `http://127.0.0.1:8000`

## Next session starts with

Task 3.2.1 — Build Celery task for Moodle user creation, OR Task 3.3.1 — Build SSO token generation in Django (depending on which Activity 3.x task to tackle first).

## Open questions

- Exact cohort naming convention for institutional orgs (deferred to Task 3.2.2)
- Standard course group ID for individual enrollments (deferred to Task 3.2.2)
- JWT SSO contract and claims details (deferred to Task 3.1.3)
- Task 1.2.2 RLS implementation still blocked on Django schema and PostgreSQL test environment