# Task Traceability — 1.2.1 Tenant Context Strategy

**Task ID and title:** 1.2.1 — Define tenant context strategy for requests and workers
**Phase / activity:** Phase 1 / Activity 1.2
**Owner:** Project owner; technical reviewer to be assigned
**Status:** Complete

## Outcome and sources

**Outcome / deliverable:** A documented tenant-context specification and middleware/security contract for authenticated requests and background tasks, grounded in the approved multi-organization membership model and tenant-isolation requirements.

**PRD sources:**
- §3.2: request membership resolution, PostgreSQL `SET LOCAL` tenant context, connection-leakage protection, explicit worker context, tenant coverage, and fail-closed behavior.
- FR-05: membership-based authorization; global `system_admin` is distinct from tenant-scoped roles.
- NFR-01: zero cross-tenant access and RLS integration-test requirement.
- NFR-03: background-worker retry behavior; retries must not rely on inherited tenant state.

**UML sources:**
- §5 ERD: one user may have memberships in multiple organizations; explicit membership selection and validation; RLS design subsequently approved in Task 1.2.2, with implementation pending.
- §6 class view: Django Core and Celery responsibilities.
- §8 cloud architecture: Django, PostgreSQL, Redis, and Celery trust boundaries.

**Approved design sources:**
- Task 1.1.1 domain model and decision P1.1.1-D1: `UserProfile` represents an organization membership; one user may have multiple memberships; the PRD's singular profile example must not be implemented literally.
- Phase 0 exit review and subsequent Task 1.2.2 decision: role and policy design approved 2026-10-25; executable implementation remains blocked on the Django schema and PostgreSQL test environment.
- Project-owner-confirmed Task 1.2.1 design choices recorded in this traceability record; detailed choices are to be recorded in the Phase 0 decision log with the deliverable.
- Phase 1 authorization: Tasks 1.1.1–1.3.3 only; unresolved design dependencies must pause.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django Core request middleware and Celery workers at the application-to-PostgreSQL tenant boundary. Documentation only; no runtime behavior is implemented or changed.

## Acceptance criteria

1. Define request tenant selection as an explicit organization UUID resolved only through a matching, validated `UserProfile` for the authenticated user; defer the route/header/session carrier to Task 1.3.3.
2. Define tenant-scoped worker context as explicit and independent of ambient request, thread, or connection state; require `organization_id`, include actor/membership identifiers when applicable, preserve explicit provenance for system-originated work, and revalidate membership and applicable authorization when queued work executes.
3. Specify transaction-local tenant database context using the PRD's `SET LOCAL` approach; do not retain tenant identity in connection/session state.
4. State that global `system_admin` authority does not itself grant tenant-data access or create an implicit all-tenant context. Any access beyond an organization's normal permissions must be requested from that organization; the request, approval, grant, and audit workflow is not designed by this task.
5. Preserve fail-closed tenant isolation while leaving detailed missing/invalid-context behavior to Task 1.2.3 and database roles, grants, bootstrap, and RLS implementation to Task 1.2.2.
6. Update the roadmap and directly affected documentation with accurate scope, decisions, dependencies, and evidence.

## Scope

**In scope:** Documentation of request membership selection and validation, worker tenant propagation and provenance, transaction-local context lifetime, system-administrator tenant boundary, middleware contract, and unresolved dependencies.

**Out of scope:** Django middleware or worker implementation, API route/header/session contract, detailed fail-closed response policy, RBAC permission matrix, support-access workflow implementation, database bootstrap/roles/grants, RLS policy design or tests, and production/runtime behavior.

## Approved decisions and dependencies

- A request must explicitly select an organization UUID. Treat it as untrusted input and resolve the authenticated user's matching `UserProfile` membership before tenant data access. The transport carrier is deferred to Task 1.3.3.
- Every tenant-scoped worker task must carry explicit organization identity. Include user/membership identity for user-originated work when applicable and preserve explicit event/task provenance for system-originated work; do not inherit ambient request or thread context.
- For user-originated queued work, revalidate the supplied membership and applicable authorization when the worker executes, rather than treating enqueue-time authorization or payload identity as sufficient.
- Tenant database context is transaction-local, following the PRD's `SET LOCAL` requirement; do not depend on a connection/session-scoped tenant value.
- A global `system_admin` role does not imply tenant-data access. Access beyond organization-granted roles requires a request to the organization; the workflow and implementation remain undefined and out of scope.
- Missing, invalid, or unauthorized tenant context must fail closed. Task 1.2.3 owns detailed failure semantics.
- Database bootstrap, application roles/privileges, and RLS policy design were approved in Task 1.2.2 decisions; their implementation remains blocked until the Django schema and PostgreSQL test environment are available.

## Evidence and completion

**Evidence:**
- Check or artifact: Tenant-context specification, this traceability record, decision-log and source-document updates, and focused documentation validation.
- Result: Project owner approved the tenant-context specification on 2026-10-25. `git diff --check` passed; relative Markdown links resolved in all seven affected documents; the new Task 1.2.1 documents have no trailing whitespace.
- Location: `inovatx_tenant_context_specification.md`, `inovatx_task_1_2_1_traceability.md`, and directly referenced source documents.
- Validation boundary: No middleware, worker, database, RLS, or runtime tests were run; these are outside this documentation-only task's approved scope.

**Completion decision:** Complete. The approved documentation-only deliverable and its acceptance criteria are satisfied; implementation, detailed fail-closed behavior, and database/RLS design remain assigned to their authorized tasks.
**Reviewer / approver and date:** Project owner, approved 2026-10-25.
