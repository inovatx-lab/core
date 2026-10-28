# Task Traceability — 2.1.1 RBAC Matrix Definition

**Task ID and title:** 2.1.1 — Define `system_admin` vs `org_admin` permissions  
**Phase / activity:** Phase 2 / Activity 2.1  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A documented RBAC matrix specifying permission boundaries between global `system_admin` and tenant-scoped organization roles (`org_admin`, `instructor`, `student`, `parent`, `sme_staff`) across the four Core tenant entities. This is a contract document only — no Django permissions, middleware, or runtime implementation is created by this task.

**PRD sources:**
- §6.1: FR-04 (role-based access control), FR-05 (membership-based authorization)
- §3.2: Tenant identification requires explicit organization selection, membership lookup under RLS, and fail-closed behavior

**UML sources:**
- §1 Use Case: Apply role-based access
- §6 Class Diagram: Django Core authorization responsibilities
- §7 Sequence Diagram: Request flow through Core

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only.
- P1.1.2-D1: `system_admin` is global and not a membership role; `org_admin`, `instructor`, `student`, `parent`, `sme_staff` are organization-membership role codes. Role codes identify membership classification only; they do not define permissions. Authorization remains subject to the resource/action permission model and its assigned task.
- P1.1.2-D2: `CRM_BASIC` first-client scope — global client/account tracking, tenant users' account overview, and gateway into tenant's Moodle learning platform. Broader CRM capabilities remain deferred.
- P1.2.1-D1: Explicit request organization selection; candidate context is not authorization; membership must be validated before tenant business queries.
- P1.2.1-D4: Global `system_admin` status does not by itself grant tenant-owned data access or create an implicit all-tenant context. Any assistance requiring access beyond an organization's normal roles and permissions must be requested from that organization.
- P1.2.3-D1: Request error semantics — 401 (unauthenticated), 400 (malformed selector), 404 (absent org or no membership), 403 (member denied), 500 (internal context invariant failure).

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core authorization boundary. This task creates no public route, permission enforcement path, or runtime service. The contract defines the interface that future tasks (2.1.2, 2.1.3, Phase 3) will implement.

## Acceptance criteria

1. Document the RBAC matrix with explicit permission boundaries for `system_admin` vs all organization-scoped roles.
2. Define resource/action permissions for `view`, `create`, `update`, `delete` across Organization, UserProfile, OrganizationMembershipRole, and SubscriptionLicense.
3. Specify that `system_admin` does not grant implicit tenant-data access (P1.2.1-D4).
4. Specify that org roles are tenant-scoped and cannot bypass tenant isolation.
5. Preserve the approved privilege boundary — no RLS, no tenant middleware, no runtime grants, no production deployment.
6. Update the roadmap, repository structure, and this traceability record with evidence that reflects only the documented contract.

## Scope

**In scope:** RBAC matrix document; resource/action permissions for all Core models; explicitly distinguishing global vs tenant-scoped roles; directly related project documentation.

**Out of scope:** Django permission implementation; middleware or view enforcement; actual permission check code; onboarding, payment, renewal, and lifecycle workflows; production provisioning/deployment; additional domain entities; Moodle or AI endpoints.

## Approved implementation decisions

- The contract documents the interface only. No executable permission checks, middleware, or views are created by this task.
- `system_admin` is global; org roles are organization-scoped. `system_admin` alone does not grant tenant-owned data access (P1.2.1-D4).
- Permissions are resource/action based, not role-code based (P1.1.2-D1).
- All org roles (`org_admin`, `instructor`, `student`, `parent`, `sme_staff`) share the same permission boundaries; differences are in classification, not authorization scope.
- Org roles cannot create, update, or delete Core tenant resources; only `view` is permitted for non-admin org roles.
- `org_admin` can create/update within their organization scope but cannot delete.
- No secrets, credentials, or connection strings are included in the contract document.

## Evidence and completion

**Evidence:**
- Check or artifact: RBAC matrix document, traceability record, roadmap update.
- Result: `inovatx_context/inovatx_core_rbac_matrix.md` documents permission boundaries for all roles across all four Core models, explicit global vs tenant scope distinction, resource/action granularity, and references all approved design decisions. No routes, middleware, or runtime implementation created.
- Location: `inovatx_context/inovatx_core_rbac_matrix.md`, `inovatx_context/inovatx_task_2_1_1_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: This is a documentation-only task. No database, server, or runtime validation is required or claimed. The contract is a specification for future implementation tasks.

**Completion decision:** Complete. All Task 2.1.1 deliverables are implemented as a documented RBAC matrix. No executable routes, permission middleware, Django permission configuration, or production deployment are included. Later RBAC enforcement, permission checks, and Django authorization configuration work remain outside this task.

**Reviewer / approver and date:** Contract documented 2026-10-28; completion review pending.