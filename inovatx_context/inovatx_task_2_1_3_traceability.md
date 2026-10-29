# Task Traceability — 2.1.3 Django Permission Enforcement

**Task ID and title:** 2.1.3 — Implement Django permission enforcement for the first client flow  
**Phase / activity:** Phase 2 / Activity 2.1  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** Executable Django permission enforcement implementing the RBAC matrix (Task 2.1.1) and tenant-scoped membership rules (Task 2.1.2). Deliverables include CRUD views for Organization, UserProfile, OrganizationMembershipRole, and SubscriptionLicense with tenant context validation and role-based action checks, URL routes for all endpoints, and authorization tests covering every permission boundary.

**PRD sources:**
- §6.1: FR-04 (role-based access control), FR-05 (membership-based authorization)
- §3.2: Tenant identification requires explicit organization selection, membership lookup under RLS, and fail-closed behavior
- §3.2 RLS coverage: Global `system_admin` does not grant implicit tenant-data access

**UML sources:**
- §1 Use Case: Apply role-based access
- §6 Class Diagram: OrganizationMembershipRole role_code enum; role assignments association

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only.
- P1.1.2-D1: Role codes identify membership classification only; they do not define permissions. Authorization remains subject to the resource/action permission model.
- P1.2.1-D1: Explicit request organization selection; candidate context is not authorization; membership must be validated before tenant business queries.
- P1.2.1-D4: Global `system_admin` status does not by itself grant tenant-owned data access.
- P1.2.3-D1: Request error semantics — 401 (unauthenticated), 400 (malformed selector), 404 (absent org or no matching membership), 403 (member denied), 500 (internal context invariant failure).

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core authorization boundary. This task creates executable permission enforcement at the view layer, enforcing tenant isolation and role-based access control on all Core tenant endpoints.

## Acceptance criteria

1. Implement Django permission enforcement based on RBAC matrix from Task 2.1.1
2. Enforce tenant-scoped membership rules from Task 2.1.2
3. `org_admin`: view/create/update on all Core entities, no delete
4. `instructor`, `student`, `parent`, `sme_staff`: view only on all Core entities
5. `system_admin` (superuser): full CRUD within validated tenant context
6. Tenant context via `X-INOVATX-Organization-Id` header + membership validation under transaction-local context
7. Error semantics: 401/400/404/403/500 per P1.2.3-D1
8. Cross-organization access blocked (403)
9. Uniform 404 for absent org or no membership (P1.2.3-D1)
10. Authorization tests covering all permission boundaries pass

## Scope

**In scope:** Django permission classes/decorators, CRUD views with tenant context and RBAC checks, URL routes for all Core model endpoints, authorization tests, directly related project documentation.

**Out of scope:** RLS policies (blocked pending Django schema/PG test environment), tenant middleware, onboarding workflows, subscription lifecycle, production deployment, Moodle/FastAPI endpoints.

## Approved implementation decisions

- `require_tenant_context` decorator: authenticates user, extracts `X-INOVATX-Organization-Id` header, validates membership via `UserProfile` lookup under candidate transaction-local context, returns 401/400/404 per P1.2.3-D1.
- `require_permission` decorator: enforces role-based action checks against `ROLE_PERMISSIONS` matrix; `system_admin` (is_superuser) bypasses role checks but still requires validated tenant context.
- Permissions are resource/action based, not role-code based (P1.1.2-D1).
- All four non-admin roles share view-only tenant-scoped permission boundaries.
- `org_admin` cannot delete any Core tenant resources.
- Cross-organization access returns 403 (profile/role/license) or 404 (organization list filtered to own org).
- Error responses include correlation IDs from `X-Correlation-ID` header when present.
- No public FastAPI exposure; FastAPI remains private/internal per architecture guardrails.

## Evidence and completion

**Evidence:**
- Check or artifact: `core/permissions.py`, `core/views.py`, `config/urls.py`, `core/tests.py` (CoreAuthorizationTests: 27 authorization tests + 14 existing model/admin tests = 41 total).
- Result: All 41 tests pass (41/41). Permission enforcement verified for org_admin (view/create/update, no delete), view-only roles (instructor/student/parent/sme_staff blocked on mutations), system_admin (full CRUD), cross-organization isolation, and error semantics (401/400/404/403).
- Location: `core/permissions.py`, `core/views.py`, `config/urls.py`, `core/tests.py`, `inovatx_context/inovatx_task_2_1_3_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: Tests run against isolated test database `inovatx_test_db` using `config.test_settings`. Django dev server verified locally on `http://127.0.0.1:8000`.

**Completion decision:** Complete. All Task 2.1.3 deliverables implemented with passing authorization tests. RLS policies (Task 1.2.2) remain blocked pending Django schema and PostgreSQL test environment. Later tasks (2.2.1 license lifecycle, 2.3.x onboarding) remain outside this task's scope.

**Reviewer / approver and date:** Implementation verified 2026-10-29; completion review pending.