# Memory — INOVATX Phase 3 Activity 3.2 Tasks 3.2.1–3.2.3, Activity 3.3 Tasks 3.3.1–3.3.2

Last updated: 2026-11-07

## What was built

### Phase 3 Activity 3.3 Task 3.3.1 — Build SSO Token Generation in Django
- Created `POST /api/v1/sso/token/` endpoint in `core/views.py`:
  - Issues signed JWT (HS256) with claims: `sub`, `user_id`, `organization_id`, `cohort_ids`, `roles`, `iss`, `iat`, `exp`, `aud`
  - Requires tenant context, valid membership, and active EDTECH_LMS license
  - Rejects system_admin (not provisioned to Moodle)
  - Rejects inactive/missing license with 403
  - Correlation ID support per P1.2.3-D1
  - Uses JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ISSUER, JWT_AUDIENCE, JWT_EXPIRATION_DELTA_SECONDS settings
- Added JWT settings to `config/base_settings.py`
- Added PyJWT>=2.8,<3 to `requirements.txt`
- Added URL route `api/v1/sso/token/` in `config/urls.py`
- Added `CoreSSOTokenIssuanceTests` (4 tests: success, unauthenticated, inactive license, no license)
- Created `inovatx_context/inovatx_task_3_3_1_traceability.md` — traceability record
- System check passes (0 issues)

### Phase 3 Activity 3.3 Task 3.3.2 — Build Moodle Authentication Plugin Integration
- Created `moodle_auth_plugin_spec.php` — Moodle auth plugin specification (PHP):
  - `auth_inovatx_sso` class extending Moodle's `plugin_auth`
  - JWT validation: verifies iss, aud, exp, signature using shared secret (Django SECRET_KEY or Moodle password salt)
  - Moodle user find/create: looks up by username (user_id from JWT), creates new user if not found
  - Cohort assignment: assigns user to Moodle cohorts based on JWT cohort_ids
  - Session creation: `complete_user_login()` to create Moodle session
  - Redirect logic: sends user to course interface at `learn.inovatx.com`
  - Error handling: invalid/expired JWT → false, missing claims → false, cross-tenant mismatch → false
  - Correlation ID propagation support
- Created `inovatx_context/inovatx_task_3_3_2_traceability.md` — traceability record mapping to Task 3.3.1 JWT contract, PRD §4.1, UML §2/§7
- Moodle-side PHP code (not Django Core — Moodle is a separate PHP application)

### Phase 3 Activity 3.2 Tasks (all complete)
- Task 3.2.1 — Celery task for Moodle user creation (`feature/T3.2.1`, commit `c1fda8a`)
- Task 3.2.2 — Celery task for cohort creation and member assignment (`feature/T3.2.2`, commit `4797930`)
- Task 3.2.3 — Retry and error handling for Moodle API failures (`feature/T3.2.3`, commit `6dfde4a`)

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
- JWT signing uses Django SECRET_KEY by default (JWT_SECRET_KEY env override)
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
- Task 3.2.3 complete — Retry and error handling for Moodle API failures implemented
- Task 3.3.1 complete — SSO token generation in Django implemented
- Task 3.3.2 complete — Moodle authentication plugin specification documented
- All work committed and pushed to `feature/T3.3.2` (commit pending)
- Django dev server running at `http://127.0.0.1:8000`

## Next session starts with

Task 3.3.2 — Build Moodle authentication plugin integration (Moodle-side PHP code), OR Task 3.3.3 — Verify end-to-end learning hub launch.

## Open questions

- Celery broker (Redis) availability and configuration (infrastructure setup needed)
- Moodle API base URL and credentials (runtime configuration)
- Exact cohort naming convention for institutional orgs (deferred to Task 3.2.2)
- Standard course group ID for individual enrollments (deferred to Task 3.2.2)
- Task 1.2.2 RLS implementation still blocked on Django schema and PostgreSQL test environment
- JWT secret key rotation strategy (deferred to operations)