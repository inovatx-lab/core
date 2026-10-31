# Tenant-Scoped Membership Rules — Task 2.1.2

**Roadmap task:** 2.1.2 — Define tenant-scoped membership rules for `instructor`, `student`, `parent`, and `sme_staff`  
**Phase / activity:** Phase 2 / Activity 2.1  
**Status:** Documented — contract only, no implementation  
**Traceability:** [Task 2.1.2 traceability record](inovatx_task_2_1_2_traceability.md)

## 1. Purpose and boundary

This document defines the tenant-scoped membership rules for the four non-admin organization-scoped roles:

- `instructor` — Organization-scoped role for teachers, lecturers, mentors, and similar teaching roles
- `student` — Organization-scoped membership role
- `parent` — Organization-scoped membership role
- `sme_staff` — Organization-scoped membership role; its code does not enable deferred SME product modules

This is a documentation contract only. No Django permission enforcement, middleware, views, serializers, or runtime implementation is created by this task. The rules define the interface that Phase 3 implementation tasks will build against.

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| P1.1.2-D1 | Phase 0 decision log | `org_admin`, `instructor`, `student`, `parent`, `sme_staff` are organization-scoped membership role codes. Role codes identify membership classification only; they do not define permissions. Authorization remains subject to the resource/action permission model. |
| P1.1.2-D3 | Phase 0 decision log | Organization and license status codes are separate from role codes. Status does not substitute for membership role permission. |
| P1.2.1-D1 | Phase 1 tenant context | A tenant-scoped request must explicitly select an organization UUID. Membership must be validated before tenant business data is accessed. |
| P1.2.1-D4 | Phase 1 tenant context | Global `system_admin` does not by itself grant tenant-owned data access. |
| P1.2.3-D1 | Phase 1 failure policy | `401` unauthenticated; `400` missing/malformed selector; `404` absent org or no matching membership; `403` member denied resource/action; `500` internal context invariant failure. |
| FR-04 | PRD §6.1 | Distinct role-based access control boundaries in both Django and Moodle. |
| FR-05 | PRD §6.1 | Authorization enforced by role and organization membership; permissions granted by resource and action rather than broad inheritance. |
| UML §1 | Use Case | Apply role-based access. Connections between human actors and use cases describe candidate goals, not a final authorization matrix. |
| UML §6 | Class Diagram | Role assignments association between UserProfile and OrganizationMembershipRole via `role_code`. |

## 3. Membership model

### 3.1 Membership structure

Each user is represented by a `UserProfile` tied to an authenticated Django `auth_user`. A user may hold memberships in multiple organizations, with at most one `UserProfile` per `(user_id, organization_id)` pair. Each membership may carry multiple role assignments with a UUID primary key and uniqueness on `(user_profile_id, role_code)`.

### 3.2 Role classification for non-admin roles

| Role code | Classification | Teaching/learning responsibility |
|---|---|---|
| `instructor` | Teaching role | Canonical code for teachers, lecturers, mentors, and similar teaching roles |
| `student` | Learner role | Participant in learning activities, quizzes, courses |
| `parent` | Guardian role | Parent-child account mapping; viewing rights |
| `sme_staff` | Staff role | SME staff; code does not enable deferred SME modules |

### 3.3 Role assignment invariants

| Invariant | Description |
|---|---|
| Unique per membership | A role assignment is unique per `(user_profile_id, role_code)` |
| Multiple roles allowed | A membership may hold zero or many role assignments |
| No duplicates | Duplicate assignment of the same role to one membership is invalid |
| Role codes are classification only | Role codes identify membership classification; they do not define permissions |
| Organization-scoped | All non-admin roles are tied to a specific organization membership |
| `system_admin` excluded | `system_admin` is global and is not a membership role |

## 4. Permission rules by role

### 4.1 Rule principle

Permissions are resource/action based, not role-code based. Membership alone does not authorize an action. A member lacking the required resource/action permission receives `403`.

### 4.2 `instructor` — teaching role permissions

| Resource | `view` | `create` | `update` | `delete` |
|---|---|---|---|---|
| Organization | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| UserProfile | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| OrganizationMembershipRole | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| SubscriptionLicense | ✅ Tenant-scoped | ❌ | ❌ | ❌ |

**Rule:** `instructor` roles have view access to tenant-owned resources within their organization membership scope only. They cannot create, update, or delete Core tenant resources.

### 4.3 `student` — learner role permissions

| Resource | `view` | `create` | `update` | `delete` |
|---|---|---|---|---|
| Organization | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| UserProfile | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| OrganizationMembershipRole | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| SubscriptionLicense | ✅ Tenant-scoped | ❌ | ❌ | ❌ |

**Rule:** `student` roles have view access to tenant-owned resources within their organization membership scope only. They cannot create, update, or delete Core tenant resources.

### 4.4 `parent` — guardian role permissions

| Resource | `view` | `create` | `update` | `delete` |
|---|---|---|---|---|
| Organization | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| UserProfile | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| OrganizationMembershipRole | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| SubscriptionLicense | ✅ Tenant-scoped | ❌ | ❌ | ❌ |

**Rule:** `parent` roles have view access to tenant-owned resources within their organization membership scope only. They cannot create, update, or delete Core tenant resources. Parent-child account mapping rules are deferred to Task 2.3.3.

### 4.5 `sme_staff` — SME staff role permissions

| Resource | `view` | `create` | `update` | `delete` |
|---|---|---|---|---|
| Organization | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| UserProfile | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| OrganizationMembershipRole | ✅ Tenant-scoped | ❌ | ❌ | ❌ |
| SubscriptionLicense | ✅ Tenant-scoped | ❌ | ❌ | ❌ |

**Rule:** `sme_staff` roles have view access to tenant-owned resources within their organization membership scope only. They cannot create, update, or delete Core tenant resources. The `sme_staff` code alone does not enable deferred SME product modules.

## 5. Role sharing and combined memberships

### 5.1 Multiple roles per membership

A membership may carry multiple role assignments simultaneously (e.g., `parent` + `student` for a parent who is also enrolled). Permissions for each active role apply independently. The most permissive applicable permission governs for a given resource/action.

### 5.2 Cross-organization access

A user with memberships in multiple organizations must select one target organization per request. Access to resources in one organization does not imply access to resources in another. Cross-organization access is blocked by tenant isolation.

### 5.3 Role membership without organization context

A role assignment exists only within a membership to a specific organization. A user cannot hold an `instructor`, `student`, `parent`, or `sme_staff` role outside of an organization membership. There is no global or default organization assignment for any role.

## 6. Error semantics

| Condition | Response code | Behavior |
|---|---|---|
| Unauthenticated request | `401` | Authentication layer rejects before any tenant processing |
| Missing or malformed organization UUID selector | `400` | Rejected before tenant-owned database access |
| Absent organization or no matching membership | `404` | Same outcome for both; membership not revealed |
| Member denied resource/action | `403` | Authorization denial; membership validated but action not permitted |
| Internal context invariant failure | `500` | Stop, roll back, generic response with correlation ID |

## 7. Acceptance criteria

1. Membership rules documented for all four non-admin org-scoped roles (`instructor`, `student`, `parent`, `sme_staff`)
2. Resource/action permission matrix defined for Organization, UserProfile, OrganizationMembershipRole, SubscriptionLicense
3. All four roles share the same permission boundaries (view only, tenant-scoped)
4. Role codes classified as membership classification, not authorization grants
5. Multi-role-per-membership allowed; most permissive applicable permission governs
6. Cross-organization access blocked; each request selects one target organization
7. Approved design decisions referenced (P1.1.2-D1, P1.2.1-D1/D4, P1.2.3-D1)
8. No runtime implementation created — contract documentation only
9. Parent-child mapping explicitly deferred to Task 2.3.3
10. `sme_staff` does not enable deferred SME modules

## 8. Traceability mapping

| Rule element | PRD source | UML source | Approved decision |
|---|---|---|---|
| Role codes as classification only | FR-05 | §1 Use Case | P1.1.2-D1 |
| Distinct permission boundaries | FR-04 | §1 Use Case | FR-04, P1.1.2-D1 |
| Resource/action authorization | FR-05 | §1 Use Case | P1.1.2-D1, P1.1.2-D2 |
| Explicit organization selection | §3.2 Tenant identification | §1 Use Case | P1.2.1-D1 |
| `system_admin` boundary | §3.2 RLS coverage | §1 Use Case | P1.2.1-D4 |
| Error semantics | §3.2 Failure handling | N/A | P1.2.3-D1 |
| Instructor = teachers/lecturers/mentors | FR-04 | §1 Use Case | P1.1.2-D1 |
| Parent-child mapping deferred | FR-01 | §1 Use Case | Task 2.3.3 |
| SME staff does not enable deferred modules | P1.1.2-D2 | N/A | P1.1.2-D2 |

## 9. Completion decision

Task 2.1.2 deliverable is complete as a documented membership rules contract:

- Membership rules defined for `instructor`, `student`, `parent`, and `sme_staff`
- Resource/action permissions specified for all four Core tenant entities
- All four roles share view-only, tenant-scoped permission boundaries
- Multi-role-per-membership allowed with most-permissive-applicable semantics
- Cross-organization isolation maintained; explicit organization selection required
- Approved design decisions preserved (P1.1.2-D1, P1.2.1-D1/D4, P1.2.3-D1)
- No executable implementation created by this task
- Parent-child mapping explicitly deferred to Task 2.3.3
- Task 2.1.3 (Django permission enforcement) remains outside this task's scope

**Membership rules documented:** 2026-10-28  
**Completion review:** pending