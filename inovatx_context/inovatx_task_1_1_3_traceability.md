# Task Traceability — 1.1.3 Initial Database Migration Plan

**Task ID and title:** 1.1.3 — Define the initial database migration plan
**Phase / activity:** Phase 1 / Activity 1.1
**Owner:** Project owner; technical reviewer to be assigned
**Status:** Complete

## Outcome and sources

**Outcome / deliverable:** A documented initial Core schema baseline and ordered migration plan grounded in the approved Task 1.1.1 domain model and Task 1.1.2 taxonomy.

**PRD sources:**
- §2.1–§2.2: Django Core and PostgreSQL technology boundary.
- §3.1: organization, membership, role-assignment, and subscription-license data.
- §3.2 and NFR-01: tenant-owned data requires RLS; this task does not implement RLS.
- FR-05 and FR-06: membership-scoped authorization and distinct organization, license, and payment status.

**UML sources:**
- §5 ERD: conceptual entities, relationships, and approved cardinalities.
- §8 cloud architecture: PostgreSQL Core database boundary.

**Approved design sources:**
- Task 1.1.1 domain model and Task 1.1.2 enum taxonomy.
- Project-owner-confirmed Task 1.1.3 planning decisions below.
- Phase 0 exit review: database bootstrap, application roles, and RLS setup remain unresolved; RLS implementation must wait for approved database role/policy design.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django Core/PostgreSQL schema contract. Documentation only; no runtime database or application access is created or changed.

## Acceptance criteria

1. Document the initial table/entity baseline, dependency order, keys, relationships, and logical constraints consistent with Tasks 1.1.1 and 1.1.2.
2. Document string-backed enum storage with Django choices and PostgreSQL CHECK constraints as the approved target enforcement strategy.
3. Record role-assignment UUID key, membership/role uniqueness, one license per organization/product in the initial baseline, positive product-specific seat capacity, and AI_PRO-only nullable entitlement columns.
4. Define a safe high-level migration sequence and rollback/forward-correction considerations without providing executable migration files.
5. Explicitly identify unresolved database bootstrap/application-role and RLS design dependencies; do not select roles, grants, RLS policies, or bootstrap behavior.
6. Update the roadmap and directly affected documentation with accurate deliverable and evidence status.

## Scope

**In scope:** Documentation of target schema, object dependencies, key/constraint plan, migration order, and bounded deployment/rollback considerations.

**Out of scope:** Django project/models, executable migration files, database creation or schema checks against a live database, application database role/bootstrap design, grants, RLS policies/tests, payment or license lifecycle history, and runtime deployment.

## Approved decisions and dependencies

- `Organization` is the client/account record; no separate `Client` or `Account` table is introduced.
- `OrganizationMembershipRole` has a UUID primary key and a unique `(user_profile_id, role_code)` constraint.
- Initial baseline enforces one license row per `(organization_id, product_code)`; renewal history/versioning remains deferred to Task 2.2.1.
- AI entitlement columns are nullable for non-`AI_PRO` products and required and positive for `AI_PRO`; D17 baseline is 1,000 monthly / 50 daily interactions per learner seat.
- Store enum values as strings, using Django choices plus PostgreSQL CHECK constraints. Native PostgreSQL ENUM types are not used in the target baseline.
- Do not decide database bootstrap, application database roles/privileges, or RLS. These remain blocked on the approval specified in the Phase 0 exit review and are dependencies of Task 1.2.2.
- The deliverable is documentation-only. Executable migrations and schema checks are deferred to the authorized Django model/application tasks.

## Evidence and completion

**Evidence:**
- Check or artifact: Task 1.1.3 schema baseline, migration plan, and aligned documentation.
- Result: Project owner approved the documented schema baseline and migration plan on 2026-10-25. `git diff --check`, trailing-whitespace checks for the new Task 1.1.3 documents, and relative Markdown-link checks for the affected documents passed.
- Location: `inovatx_initial_schema_migration_plan.md`, `inovatx_task_1_1_3_traceability.md`, and directly referenced source documents.
- Validation boundary: No executable migrations, database schema checks, or runtime tests were run; these are outside this documentation-only task's approved scope.

**Completion decision:** Complete. The approved documentation-only deliverable and its acceptance criteria are satisfied; executable migration work remains deferred to the authorized Django model/application tasks.
**Reviewer / approver and date:** Project owner, approved 2026-10-25.
