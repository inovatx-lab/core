# RBAC Matrix — Task 2.1.1: system_admin vs org_admin permissions

**Roadmap task:** 2.1.1 — Define system_admin vs org_admin permissions  
**Phase / activity:** Phase 2 / Activity 2.1  
**Status:** Documented — contract only, no implementation  
**Traceability:** [Task 2.1.1 traceability record](inovatx_task_2_1_1_traceability.md)

## 1. Purpose and boundary

This document defines the Role-Based Access Control (RBAC) matrix for the INOVATX Core platform, explicitly distinguishing:

- **Global `system_admin` role**: System-wide authority, not an organization membership role
- **Tenant-scoped organization roles**: `org_admin`, `instructor`, `student`, `parent`, `sme_staff` — each scoped to a single organization membership

This is a documentation contract only. No Django permission enforcement, middleware, views, serializers, or runtime implementation is created by this task. The matrix defines the interface that Phase 3 implementation tasks will build against.

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| P1.1.2-D1 | Phase 0 decision log | `system_admin` is global and not a membership role. Use `org_admin`, `instructor`, `student`, `parent`, and `sme_staff` as organization-scoped membership role codes. `instructor` is the canonical role name for teachers, lecturers, mentors and similar teaching roles. Role codes identify membership classification only; they do not define permissions. |
| P1.2.1-D1 | Phase 1 tenant context spec | Global `system_admin` does not by itself grant tenant-owned data access and does not create an implicit all-tenant context. Any assistance beyond normal roles and permissions must be requested from that organization. |
| P1.2.1-D4 | Phase 1 tenant failure policy | A request must explicitly select an organization UUID. After authentication and selector syntax validation, establish the selected organization as candidate transaction-local context and perform only a `UserProfile` lookup matching both the authenticated user and selected organization under RLS. Do not access tenant business data until the membership is validated. |
| P1.2.3-D1 | Phase 1 failure policy | Reject unauthenticated requests through the authentication layer with `401`; reject missing or malformed organization UUID selectors with `400`; return the same `404` outcome for an absent organization and for an organization with no matching authenticated-user membership; and return `403` for a member denied a resource/action. |

## 3. RBAC Matrix Definition

### 3.1 Role hierarchy and scope

| Category | Role code | Scope | Membership status |
|---|---|---|---|
| Global | `system_admin` | System-wide, not organization-scoped | Not an organization membership role |
| Organization-scoped | `org_admin` | Single organization membership | Organization membership role |
| Organization-scoped | `instructor` | Single organization membership | Organization membership role (canonical for teachers, lecturers, mentors) |
| Organization-scoped | `student` | Single organization membership | Organization membership role |
| Organization-scoped | `parent` | Single organization membership | Organization membership role |
| Organization-scoped | `sme_staff` | Single organization membership | Organization membership role |

### 3.2 Permission matrix

The matrix below defines access for each role across the four Core tenant-owned entities. All permissions are **resource/action** based; role codes alone do not grant authorization.

| Role | Resource | `view` | `create` | `update` | `delete` |
|---|---|---|---|---|---|
| **`system_admin`** | `Organization` | ✅ | ✅ | ✅ | ✅ |
| | `UserProfile` | ✅ | ⚠️ | ⚠️ | ⚠️ |
| | `OrganizationMembershipRole` | ✅ | ⚠️ | ⚠️ | ⚠️ |
| | `SubscriptionLicense` | ✅ | ✅ | ✅ | ✅ |
| **`org_admin`** | `Organization` | ✅ | ✅ | ✅ | ❌ |
| | `UserProfile` | ✅ | ⚠️ | ⚠️ | ❌ |
| | `OrganizationMembershipRole` | ✅ | ⚠️ | ⚠️ | ❌ |
| | `SubscriptionLicense` | ✅ | ✅ | ✅ | ❌ |
| **`instructor`** | `Organization` | ✅ | ❌ | ❌ | ❌ |
| | `UserProfile` | ✅ | ❌ | ❌ | ❌ |
| | `OrganizationMembershipRole` | ✅ | ❌ | ❌ | ❌ |
| | `SubscriptionLicense` | ✅ | ❌ | ❌ | ❌ |
| **`student`** | `Organization` | ✅ | ❌ | ❌ | ❌ |
| | `UserProfile` | ✅ | ❌ | ❌ | ❌ |
| | `OrganizationMembershipRole` | ✅ | ❌ | ❌ | ❌ |
| | `SubscriptionLicense` | ✅ | ❌ | ❌ | ❌ |
| **`parent`** | `Organization` | ✅ | ❌ | ❌ | ❌ |
| | `UserProfile` | ✅ | ❌ | ❌ | ❌ |
| | `OrganizationMembershipRole` | ✅ | ❌ | ❌ | ❌ |
| | `SubscriptionLicense` | ✅ | ❌ | ❌ | ❌ |
| **`sme_staff`** | `Organization` | ✅ | ❌ | ❌ | ❌ |
| | `UserProfile` | ✅ | ❌ | ❌ | ❌ |
| | `OrganizationMembershipRole` | ✅ | ❌ | ❌ | ❌ |
| | `SubscriptionLicense` | ✅ | ❌ | ❌ | ❌ |

### 3.3 Permission semantics

#### 3.3.1 `view` (read access)
- **`system_admin`**: Global scope — can view all Core tenant entities across all organizations
- **Org roles**: Tenant-scoped — can view entities **only within their scoped organization membership**
- Cross-organization `view` blocked by tenant isolation (RLS + app-level validation)

#### 3.3.2 `create` (resource creation)
- **`system_admin`**: Global scope — can create resources in any organization
- **`org_admin`**: Tenant-scoped — can create resources **within** their organization's scope only
- **`instructor`, `student`, `parent`, `sme_staff`**: Cannot create Core tenant resources (no `create` permission)
- Creation outside authorized scope returns `403` (forbidden)

#### 3.3.3 `update` (resource modification)
- **`system_admin`**: Global scope — can update any Core tenant entity
- **`org_admin`**: Tenant-scoped — can update resources **within** their organization's scope only
- **`instructor`, `student`, `parent`, `sme_staff`**: Cannot update Core tenant resources (no `update` permission)
- Unauthorized `update` attempts return `403` (forbidden)

#### 3.3.4 `delete` (resource removal)
- **`system_admin`**: Global scope — can delete any Core tenant entity
- **`org_admin`**: Cannot delete any Core tenant resources (organization-owned data requires authorization)
- **`instructor`, `student`, `parent`, `sme_staff`**: Cannot delete Core tenant resources
- Unauthorized `delete` attempts return `403` (forbidden)

### 3.4 Key RBAC boundaries

| Boundary | Description |
|---|---|
| Global vs tenant scope | `system_admin` is global; org roles are organization-scoped. `system_admin` alone does not grant tenant-data access (P1.2.1-D4). |
| Permission granularity | Permissions are resource/action based, not role-code based (P1.1.2-D1). |
| Org role consistency | All org roles share the same permission boundaries; differences are in classification, not authorization. |
| Cross-tenant isolation | Org roles cannot access another organization's data. |
| Admin deletion restriction | `org_admin` cannot delete organization or membership records; only `system_admin` can, with explicit target organization selection. |

## 4. Acceptance criteria

1. RBAC matrix documents permission boundaries for all five role types across all four Core tenant entities
2. `system_admin` access is explicitly global; org roles are explicitly tenant-scoped
3. `system_admin` does not bypass tenant context selection or grant implicit all-tenant access (P1.2.1-D4)
4. Org roles cannot perform actions outside their organization membership scope
5. Permission matrix references approved decisions (P1.1.2-D1, P1.2.1-D1, P1.2.1-D4, P1.2.3-D1)
6. No routes, middleware, views, or serializers created by this task
7. Matrix serves as contract for Phase 3 implementation tasks (RBAC enforcement, permission checks)

## 5. Traceability mapping

| Matrix element | PRD source | UML source | Approved decision |
|---|---|---|---|
| `system_admin` global role | §6.1 FR-04 | §1 Use Case: Apply role-based access | P1.1.2-D1 |
| Org role boundary (tenant-scoped) | §6.1 FR-04/FR-05 | §1 Use Case: Apply role-based access | P1.1.2-D1 |
| Permission is resource/action, not role-code | §6.1 FR-04 | §1 Use Case: Apply role-based access | P1.1.2-D1, P1.1.2-D2 |
| Org roles cannot bypass tenant isolation | §3.2 NFR-01 | §1 Use Case | P1.2.1-D4, P1.2.3-D1 |
| Org admin create/update within scope | Defined by task 2.1.1 | N/A | Task 2.1.1 |
| Org admin cannot delete | Defined by task 2.1.1 | N/A | Task 2.1.1 |

## 6. Completion decision

Task 2.1.1 deliverable is complete as a documented RBAC matrix:

- Permission boundaries defined for `system_admin` vs all org roles (`org_admin`, `instructor`, `student`, `parent`, `sme_staff`)
- Access rules specified for `view`, `create`, `update`, `delete` across all four Core tenant entities (Organization, UserProfile, OrganizationMembershipRole, SubscriptionLicense)
- Approved design decisions preserved (P1.1.2-D1, P1.2.1-D1, P1.2.1-D4, P1.2.3-D1)
- No executable implementation created by this task
- Later RBAC enforcement, permission checks, and Django permission configuration remain outside this task's scope
- Task 2.2.1 (license lifecycle) and Task 2.3.3 (onboarding flow) reference this matrix for access control decisions

**RBAC matrix documented:** 2026-10-28  
**Completion review:** pending

## 7. Open questions

- None blocking Task 2.1.1 contract documentation.
- RBAC enforcement implementation (Django permissions, middleware, views) assigned to later tasks
- Exact `create`/`update` permission boundaries for org roles beyond the matrix scope to be clarified in Task 2.1.2 or Task 2.2.1
