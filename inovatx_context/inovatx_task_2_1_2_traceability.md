# Task Traceability — 2.1.2 Tenant-Scoped Membership Rules

**Task ID and title:** 2.1.2 — Define tenant-scoped membership rules for `instructor`, `student`, `parent`, and `sme_staff`  
**Phase / activity:** Phase 2 / Activity 2.1  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A documented membership rules contract specifying permission boundaries and membership invariants for the four non-admin organization-scoped roles (`instructor`, `student`, `parent`, `sme_staff`) across the four Core tenant entities. This is a contract document only — no Django permissions, middleware, or runtime implementation is created by this task.

**PRD sources:**
- §6.1: FR-04 (role-based access control), FR-05 (membership-based authorization), FR-01 (individual onboarding, parent-child mapping)
- §3.2: Tenant identification requires explicit organization selection, membership lookup under RLS, and fail-closed behavior
- §3.2 RLS coverage: Global `system_admin` does not grant implicit tenant-data access

**UML sources:**
- §1 Use Case: Apply role-based access; candidate goal associations for each actor
- §6 Class Diagram: OrganizationMembershipRole role_code enum; role assignments association between UserProfile and OrganizationMembershipRole
- §5 State Machine: Statuses are independent of role codes

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only.
- P1.1.2-D1: Canonical membership-role codes are `org_admin`, `instructor`, `student`, `parent`, `sme_staff`. Role codes identify membership classification only; they do not define permissions. Authorization remains subject to the resource/action permission model.
- P1.1.2-D3: Organization and license status code sets are separate from role codes.
- P1.2.1-D1: Explicit request organization selection; candidate context is not authorization; membership must be validated before tenant business queries.
- P1.2.1-D4: Global `system_admin` status does not by itself grant tenant-owned data access or create an implicit all-tenant context.
- P1.2.3-D1: Request error semantics — 401 (unauthenticated), 400 (malformed selector), 404 (absent org or no matching membership), 403 (member denied), 500 (internal context invariant failure).

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core authorization boundary. This task creates no public route, permission enforcement path, or runtime service. The contract defines the interface that future tasks (2.1.3, Phase 3) will implement.

## Acceptance criteria

1. Document membership rules with explicit permission boundaries for `instructor`, `student`, `parent`, and `sme_staff`
2. Define resource/action permissions for `view`, `create`, `update`, `delete` across Organization, UserProfile, OrganizationMembershipRole, and SubscriptionLicense
3. Specify that role codes are membership classification only, not authorization grants (P1.1.2-D1)
4. Specify that all four non-admin roles share the same view-only, tenant-scoped permission boundaries
5. Allow multiple role assignments per membership; most permissive applicable permission governs
6. Require explicit organization selection per request; block cross-organization access
7. Reference approved decisions (P1.1.2-D1, P1.2.1-D1/D4, P1.2.3-D1)
8. Update the roadmap and this traceability record with evidence that reflects only the documented contract

## Scope

**In scope:** Membership rules document; resource/action permissions for all Core models; role classification vs authorization distinction; multi-role-per-membership rules; cross-organization isolation; directly related project documentation.

**Out of scope:** Django permission implementation; middleware or view enforcement; actual permission check code; parent-child account mapping (deferred to Task 2.3.3); SME product modules (deferred); production provisioning/deployment; additional domain entities; Moodle or AI endpoints.

## Approved implementation decisions

- The contract documents the interface only. No executable permission checks, middleware, or views are created by this task.
- Role codes identify membership classification only; they do not define permissions (P1.1.2-D1).
- Permissions are resource/action based, not role-code based (P1.1.2-D1, FR-05).
- All four non-admin roles share the same view-only, tenant-scoped permission boundaries across all four Core entities.
- Multiple role assignments per membership are allowed; most permissive applicable permission governs.
- Cross-organization access is blocked; each request must explicitly select one target organization.
- Parent-child mapping rules are deferred to Task 2.3.3; viewing rights are not defined by this task.
- `sme_staff` code alone does not enable deferred SME product modules (P1.1.2-D2).
- No secrets, credentials, or connection strings are included in the contract document.

## Evidence and completion

**Evidence:**
- Check or artifact: Membership rules document, traceability record, roadmap update.
- Result: `inovatx_context/inovatx_tenant_membership_rules.md` documents membership rules for all four non-admin roles, resource/action permissions across all four Core models, role classification distinction, multi-role rules, cross-organization isolation, and references all approved design decisions. No routes, middleware, or runtime implementation created.
- Location: `inovatx_context/inovatx_tenant_membership_rules.md`, `inovatx_context/inovatx_task_2_1_2_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: This is a documentation-only task. No database, server, or runtime validation is required or claimed. The contract is a specification for future implementation tasks.

**Completion decision:** Complete. All Task 2.1.2 deliverables are implemented as a documented membership rules contract. No executable routes, permission middleware, Django permission configuration, or production deployment are included. Later RBAC enforcement, permission checks, and Django authorization configuration work remain outside this task.

**Reviewer / approver and date:** Contract documented 2026-10-28; completion review pending.