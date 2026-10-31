# Task Traceability — 2.3.3 Parent-Child Mapping

**Task ID and title:** 2.3.3 — Implement parent-child mapping model and access policy  
**Phase / activity:** Phase 2 / Activity 2.3  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** Executable parent-child mapping model and access policy:
- `ParentChildLink` Django model linking parent and child `UserProfile` within same organization
- `GET /api/v1/parent-children/` — list child links for authenticated parent
- `POST /api/v1/parent-children/create/` — create parent-child link
- `DELETE /api/v1/parent-children/<uuid>/delete/` — delete owned parent-child link
- Access policy: parent/org_admin manage links; other roles view-only
- Data-level enforcement: parents manage only their own links; same-org requirement
- 10 parent-child tests

**PRD sources:**
- §6.1: FR-01 (Multi-Tenant Onboarding — parent-child account mapping)

**UML sources:**
- §1 Use Case: "Parent -. parent-child mapping specified; viewing rights not defined" — viewing rights defined by this task
- §9 Class Diagram: Included scope — parent-child mapping

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only.
- Task 2.1.1: RBAC matrix — org roles share permission boundaries; resource/action based.
- Task 2.1.2: Membership rules — role codes are classification only; permissions are resource/action.
- Task 2.1.3: Django permission enforcement via `require_permission` decorator.

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core onboarding boundary. Parent-child links are tenant-scoped (within an organization). All views require tenant context validation.

## Acceptance criteria

1. ParentChildLink Django model created with constraints
2. Parent-child list, create, delete views implemented
3. Tenant context validation (X-INOVATX-Organization-Id + membership)
4. Parent role can create/delete their own links
5. org_admin can manage all links in their organization
6. Non-parent roles (instructor, student, sme_staff) view-only
7. Cross-organization links blocked
8. Self-linking blocked
9. Duplicate links blocked
10. Error semantics match P1.2.3-D1/D2

## Scope

**In scope:** ParentChildLink model, views, URL routes, access policy, tests, directly related documentation.

**Out of scope:** Parent viewing child's detailed activity/grades, child initiating links, multiple parents per child (model supports but not tested), bulk CSV enrollment (Phase 3), Moodle cohort association (Phase 3).

## Approved implementation decisions

- `ParentChildLink` uses UUID PK, CASCADE on both FKs
- Unique constraint on (parent_profile, child_profile)
- Check constraint prevents self-linking (parent_profile != child_profile)
- Parent role has create/delete for ParentChildLink (own links enforced by view logic)
- org_admin has create/delete for ParentChildLink (all links in org)
- Other roles (instructor, student, sme_staff) have view-only
- No secrets committed to source code

## Evidence and completion

**Evidence:**
- Check or artifact: `core/models.py` (ParentChildLink model), `core/views.py` (parent_child_list/create/delete), `config/urls.py` (routes), `core/permissions.py` (PARENT_CHILD_ACTIONS, PARENT_RESOURCES), `core/tests.py` (CoreParentChildTests: 10 tests)
- Result: All 71 tests pass (71/71). Parent-child operations verified for create, list, delete, self-link prevention, cross-org blocking, duplicate prevention, non-parent denial.
- Location: `core/models.py`, `core/views.py`, `config/urls.py`, `core/permissions.py`, `core/migrations/0003_parentchildlink.py`, `core/tests.py`, `inovatx_context/inovatx_parent_child_mapping.md`, `inovatx_context/inovatx_task_2_3_3_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: Tests run against isolated test database `inovatx_test_db` using `config.test_settings`.

**Completion decision:** Complete. All Task 2.3.3 deliverables implemented with passing parent-child tests. The parent-child mapping model and access policy are operational at the Django view layer.

**Reviewer / approver and date:** Implementation verified 2026-10-31; completion review pending.