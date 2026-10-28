# Task Traceability — 1.3.3 Core API Contract

**Task ID and title:** 1.3.3 — Create initial API contract for Core endpoints
**Phase / activity:** Phase 1 / Activity 1.3
**Owner:** Project owner
**Status:** Complete

## Outcome and sources

**Outcome / deliverable:** A documented Core API contract specifying endpoint schemas, request/response mappings, authentication, tenant context selection, and error handling for the four approved Core models. This is a contract document only — no routes, middleware, or runtime implementation is created by this task.

**PRD sources:**
- §2.1: Django Core as the central hub for CRM, auth, billing, and client portal.
- §3.2: Tenant identification requires explicit organization selection, membership lookup under RLS, and fail-closed behavior.
- §6.1: FR-01 (multi-tenant onboarding), FR-02 (automated provisioning), FR-04 (RBAC), FR-05 (membership-based authorization), FR-06 (subscription/payment lifecycle).
- §7: Target-state decisions on role model, status values, tenant coverage, and webhook contracts.

**UML sources:**
- §1 Use Case: Register, Manage organization and users, Apply role-based access, Manage subscription license.
- §7 Sequence Diagram: request flow through Core, Moodle, and AI boundaries.

**Approved design sources:**
- Phase 1 authorization permits Tasks 1.1.1–1.3.3 only.
- P1.2.1-D1: Explicit request organization selection; candidate context is not authorization; membership must be validated before tenant business queries.
- P1.2.3-D1: Request error semantics — 401 (unauthenticated), 400 (malformed selector), 404 (absent org or no membership), 403 (member denied), 500 (internal context invariant failure).
- P1.2.3-D2: Internal context invariant failure returns generic 500 with correlation ID and sanitized security event.
- P1.3.1-D1: Django 5.2, Python 3.12, PostgreSQL-only, built-in auth.User.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django Core API contract boundary. This task creates no public route, tenant authorization path, or runtime service. The contract defines the interface that future tasks (2.x, 3.x) will implement.

## Acceptance criteria

1. Document the Core API contract with explicit authentication, tenant context selection, and membership validation flow per P1.2.1-D1 and P1.2.3-D5.
2. Define endpoint schemas (request/response) for Organization, UserProfile, OrganizationMembershipRole, and SubscriptionLicense with tenant-scoped access.
3. Specify error handling per P1.2.3-D1: 401, 400, 404, 403, and 500 with correlation identifiers.
4. Preserve the approved runtime privilege boundary — no RLS, no tenant middleware, no runtime grants, no production deployment.
5. Update the roadmap, repository structure, and this traceability record with evidence that reflects only the documented contract.

## Scope

**In scope:** Core API contract document; endpoint schemas; authentication and tenant context flow; error handling specification; directly related project documentation.

**Out of scope:** Django REST framework or actual route implementation; tenant middleware/RLS; role-permission authorization; onboarding, payment, renewal, and lifecycle workflows; production provisioning/deployment; additional domain entities; Moodle or AI endpoints.

## Approved implementation decisions

- The contract documents the interface only. No executable routes, views, or serializers are created by this task.
- Tenant context selection follows P1.2.1-D1: explicit organization UUID selector, membership lookup constrained by authenticated user and selected organization under RLS, fail closed if missing or invalid.
- Error semantics follow P1.2.3-D1: 401 for unauthenticated, 400 for malformed selector, 404 for absent organization or no matching membership (same response to prevent organization-existence disclosure), 403 for member denied a resource/action, 500 for internal context invariant failure with correlation ID.
- All endpoints are tenant-scoped. The global `system_admin` role does not by itself grant tenant-owned data access (P1.2.1-D4).
- No secrets, credentials, or connection strings are included in the contract document.

## Evidence and completion

**Evidence:**
- Check or artifact: Core API contract document, traceability record, roadmap update, repository structure update.
- Result: `inovatx_context/inovatx_core_api_contract.md` documents authentication flow, tenant context selection, endpoint schemas for all four Core models, error handling per P1.2.3-D1, and scope boundaries. Contract reviewed against PRD §2.1, §3.2, §6.1, §7 and UML §1, §7. No routes, middleware, or runtime implementation was created.
- Location: `inovatx_context/inovatx_core_api_contract.md`, `inovatx_context/inovatx_task_1_3_3_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: This is a documentation-only task. No database, server, or runtime validation is required or claimed. The contract is a specification for future implementation tasks.

**Completion decision:** Complete. All Task 1.3.3 deliverables are implemented as a documented contract. No executable routes, tenant middleware, RLS, or production deployment are included. Later API implementation, tenant isolation, and deployment work remain outside this task.

**Reviewer / approver and date:** Contract documented 2026-10-28; completion review approved 2026-10-28 by project owner.