# Task Traceability — 2.3.2 Institutional Registration Path

**Task ID and title:** 2.3.2 — Implement institutional onboarding path  
**Phase / activity:** Phase 2 / Activity 2.3  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** Executable institutional registration endpoint and flow:
- `POST /api/v1/register/institutional/` endpoint creating User, Organization (institutional, pending), UserProfile, OrganizationMembershipRole (org_admin), SubscriptionLicense (pending)
- Institutional org type validation (rejects `individual`)
- Input validation, duplicate detection, error handling
- 8 registration tests

**PRD sources:**
- §6.1: FR-01 (Multi-Tenant Onboarding — institutional registration)
- §4.1: Registration & Payment lifecycle (register at app.inovatx.com, complete payment via gateway)

**UML sources:**
- §2 BPMN: Register → CompletePayment → ... flow; registration separate from payment; OrgType gate for institutional vs individual
- §9 Class Diagram: Included scope — registration, organization and user administration

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only.
- Task 2.2.1: License `pending` means entitlement exists but is not usable.
- Task 2.2.2: Payment status separate from license status.

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core onboarding boundary. The registration endpoint is open (CSRF-exempt, no authentication) since the user has no organization yet. Security via input validation and unique constraints.

## Acceptance criteria

1. Individual registration endpoint implemented at `POST /api/v1/register/institutional/`
2. Creates User, Organization (institutional, pending), UserProfile, OrganizationMembershipRole (org_admin), SubscriptionLicense (pending)
3. No tenant context required — open endpoint for unregistered users
4. Institutional org types accepted: `school`, `sme`, `ngo`, `enterprise`
5. Individual org type (`individual`) rejected with 400
6. Duplicate username/email rejected with 409
7. Missing required fields rejected with 400
8. Invalid JSON rejected with 400
9. License created in `pending` status (activation via Task 2.2.3 payment webhook)
10. Institutional seat capacity configurable (default 50)

## Scope

**In scope:** Institutional registration endpoint, view, URL route, tests, directly related documentation.

**Out of scope:** Individual registration (Task 2.3.1), parent-child mapping (Task 2.3.3), payment processing (Task 2.2.3), Moodle provisioning (Phase 3), SSO (Phase 3), cohort creation and member assignment (Phase 3).

## Approved implementation decisions

- Registration endpoint is CSRF-exempt and open (no auth required) — user has no org/session yet
- Organization created with `org_type` from request (school/sme/ngo/enterprise), `status=pending`
- Role assigned is `org_admin` (registrant owns their organization)
- License created with `status=pending`, configurable `seat_capacity` (default 50), `product_code=EDTECH_LMS`
- Payment activation happens separately via Task 2.2.3 webhook
- No secrets committed to source code

## Evidence and completion

**Evidence:**
- Check or artifact: `core/views.py` (institutional_register), `config/urls.py` (route), `core/tests.py` (CoreInstitutionalRegistrationTests: 8 tests)
- Result: All 61 tests pass (61/61). Institutional registration verified for successful flow, all org types, individual org type rejection, duplicate username/email, missing fields, invalid JSON.
- Location: `core/views.py`, `config/urls.py`, `core/tests.py`, `core/migrations/0002_payment_paymentevent_and_more.py`, `inovatx_context/inovatx_institutional_registration_flow.md`, `inovatx_context/inovatx_task_2_3_2_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: Tests run against isolated test database `inovatx_test_db` using `config.test_settings`.

**Completion decision:** Complete. All Task 2.3.2 deliverables implemented with passing institutional registration tests. The institutional registration endpoint is operational at the Django view layer.

**Reviewer / approver and date:** Implementation verified 2026-10-31; completion review pending.