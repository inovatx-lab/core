# Parent-Child Mapping — Task 2.3.3

**Roadmap task:** 2.3.3 — Implement parent-child mapping model and access policy  
**Phase / activity:** Phase 2 / Activity 2.3  
**Status:** Implemented — end-to-end local test with successful parent-child link operations  
**Traceability:** [Task 2.3.3 traceability record](inovatx_task_2_3_3_traceability.md)

## 1. Purpose and boundary

This task implements the parent-child mapping model and access policy for INOVATX Core. Per PRD FR-01, the system must allow parent-child account mapping. Per UML §1, the parent-child mapping is specified but viewing rights were previously undefined — this task defines them.

When a parent registers and links to their child:

1. A `ParentChildLink` record is created linking a parent `UserProfile` to a child `UserProfile`
2. Both profiles must belong to the same organization
3. A parent cannot link to themselves
4. A link is unique per (parent_profile, child_profile) pair
5. Parents can view their children's profiles and manage their own links

No new roles are introduced — the existing `parent` and `student` role codes are used.

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| PRD FR-01 | PRD §6.1 | The system must allow parent-child account mapping. |
| UML §1 Use Case | UML §1 | "Parent -. parent-child mapping specified; viewing rights not defined" — viewing rights defined by this task. |
| UML §9 Class Diagram | UML §9 | Included scope: parent-child mapping. |
| Task 2.1.1 RBAC matrix | `inovatx_context/inovatx_core_rbac_matrix.md` | org roles share view-only permissions; org_admin has create/update on core entities. |
| Task 2.1.2 Membership rules | `inovatx_context/inovatx_tenant_membership_rules.md` | Role codes are membership classification only; permissions are resource/action based. |
| Task 2.1.3 Django permission enforcement | `core/permissions.py` | Resource/action permission enforcement via `require_permission` decorator. |

## 3. Implementation

### 3.1 Model

**`ParentChildLink`** (`core/models.py`):
- `id` (UUID PK)
- `parent_profile` (FK to UserProfile, CASCADE)
- `child_profile` (FK to UserProfile, CASCADE)
- `created_at`, `updated_at`
- Unique constraint on (parent_profile, child_profile)
- Check constraint: parent_profile != child_profile (no self-linking)

### 3.2 Views

**`GET /api/v1/parent-children/`** — List child links for the authenticated parent (view permission)
**`POST /api/v1/parent-children/create/`** — Create a parent-child link (create permission)
**`DELETE /api/v1/parent-children/<uuid:link_id>/delete/`** — Delete a parent-child link owned by the authenticated parent (delete permission)

All views require tenant context (`X-INOVATX-Organization-Id` header) and membership validation.

### 3.3 Access policy

| Role | ParentChildLink view | create | delete |
|---|---|---|---|
| `org_admin` | ✅ | ✅ | ✅ |
| `parent` | ✅ | ✅ (own links only) | ✅ (own links only) |
| `instructor` | ✅ | ❌ | ❌ |
| `student` | ✅ | ❌ | ❌ |
| `sme_staff` | ✅ | ❌ | ❌ |

Data-level enforcement:
- Parent can only create/delete links where they are the `parent_profile`
- Child profiles must be in the same organization as the parent
- Parents cannot link to themselves

## 4. Error semantics

| Condition | Response code | Error code |
|---|---|---|
| Unauthenticated | `401` | `unauthenticated` |
| Missing org selector | `400` | `missing_organization_selector` |
| Malformed org selector | `400` | `invalid_organization_selector` |
| No matching membership | `404` | `membership_not_found` |
| Invalid JSON | `400` | `invalid_json` |
| Missing child_profile_id | `400` | `missing_field` |
| Self-link attempt | `400` | `self_link_not_allowed` |
| Child not in same org | `404` | `profile_not_found` |
| Duplicate link | `400` | `link_already_exists` |
| Link not found / not owned | `404` | `link_not_found` |
| Permission denied | `403` | `permission_denied` |

## 5. Acceptance criteria

1. ParentChildLink Django model created with constraints (unique parent-child pair, no self-link)
2. Parent-child list view implemented (`GET /api/v1/parent-children/`)
3. Parent-child create view implemented (`POST /api/v1/parent-children/create/`)
4. Parent-child delete view implemented (`DELETE /api/v1/parent-children/<uuid>/delete/`)
5. Tenant context validation required for all endpoints
6. Parent role can create/delete their own links; org_admin can manage all links in org
7. Non-parent roles (instructor, student, sme_staff) have view-only access
8. Cross-organization links blocked (child must be in same org)
9. Self-linking blocked
10. Duplicate links blocked
11. 10 parent-child tests pass
12. All 71 tests pass (41 existing + 8 payment + 5 individual + 7 institutional + 10 parent-child)

## 6. Test results

| Test | Result |
|---|---|
| Create parent-child link | Pass |
| Self-link not allowed | Pass |
| Cross-org link not found | Pass |
| Duplicate link not allowed | Pass |
| Non-parent cannot create link | Pass |
| List child links | Pass |
| List no links (empty) | Pass |
| Delete own link | Pass |
| Delete nonexistent link | Pass |
| Delete link not owned | Pass |

## 7. Out of scope

- Parent viewing child's detailed activity/grades (beyond profile view)
- Child initiating link to parent
- Multiple parents per child (supported by model but not explicitly tested)
- Bulk CSV parent-child enrollment (Phase 3)
- Moodle cohort association for parent-child pairs (Phase 3)

## 8. Completion decision

Task 2.3.3 is complete. The parent-child mapping model and access policy are implemented with:
- `ParentChildLink` Django model with constraints
- Three views (list, create, delete) with tenant context and permission enforcement
- Access policy: parent/org_admin can manage links; other roles view-only
- Data-level enforcement: parents only manage their own links; same-org requirement
- 10 parent-child tests passing
- All 71 tests passing

**Implementation completed:** 2026-10-31  
**Completion review:** pending