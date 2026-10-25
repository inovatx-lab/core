# Task Traceability — 1.1.2 Enum Taxonomy and Constraints

**Task ID and title:** 1.1.2 — Define enums and constraints for organization types, roles, and product codes
**Phase / activity:** Phase 1 / Activity 1.1
**Owner:** Project owner; technical reviewer to be assigned
**Status:** Complete

## Outcome and sources

**Outcome / deliverable:** An owner-approved taxonomy and logical validation rules for organization types, organization membership roles, organization and license statuses, product codes, and product-specific seat/AI entitlement applicability.

**PRD sources:**
- §3.1: organization type/status, membership role, product code, seat capacity, and license fields.
- FR-04 and FR-05: distinct role boundaries and membership-based authorization; global `system_admin` is distinct from tenant-scoped `org_admin`.
- FR-06: organization, license, and payment statuses are distinct.
- FR-07 and §7 decisions 1–4: AI interaction allowances are distinct from provider-token usage and are enforced through a usage ledger.

**UML sources:**
- §5 ERD: conceptual organization, membership, role, and license attributes.
- §6 class diagram: Core responsibilities and role distinctions.
- §9 recommended resolutions: proposed role naming, organization/license lifecycle values, and product entitlements; recommendations are adopted only where explicitly approved below.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django Core domain/data contract; this task defines validation rules only and does not implement models, database constraints, authorization, or RLS.

## Acceptance criteria

1. Specify canonical allowed values for organization types, membership roles, product codes, organization statuses, and license statuses, with global `system_admin` excluded from membership roles.
2. Specify logical validation rules for positive product-specific seat capacity and AI allowance applicability/default values.
3. Record the owner's CRM_BASIC first-client scope and canonical `instructor` terminology without implying permissions, broader CRM features, or deferred SME/NGO modules.
4. Align directly affected PRD, UML, approved domain model, scope, roadmap, and decision-log references with the approved taxonomy.
5. Keep implementation, database enforcement/migrations, role permissions, payment lifecycle, and license/organization state transitions outside scope.

## Scope

**In scope:** Documentation of the taxonomy and logical validation rules; directly related source-of-truth and roadmap updates; owner decisions required to close Task 1.1.2.

**Out of scope:** Application code, migrations, physical database constraints, RBAC permissions, payment status, lifecycle transitions, product-specific seat-count calculations, broader CRM modules, and SME/NGO product expansion.

## Approved decisions and dependencies

- Use `instructor` as the canonical membership-role name for teachers, lecturers, mentors, and similar teaching roles.
- Organization types: `individual`, `school`, `sme`, `ngo`, `enterprise`; codes do not imply product/module availability.
- Membership roles: `org_admin`, `instructor`, `student`, `parent`, `sme_staff`; `system_admin` is global and excluded.
- Product codes: `EDTECH_LMS`, `CRM_BASIC`, `AI_PRO`. CRM_BASIC is included in the first-client baseline only for global client/account tracking, tenant account overview, and gateway into the tenant's Moodle learning platform; broader CRM remains deferred.
- Organization statuses: `pending`, `active`, `suspended`, `expired`, `cancelled`.
- License statuses: `pending`, `active`, `expired`, `suspended`, `cancelled`. `pending` means the entitlement exists but is not usable.
- `seat_capacity` is an integer of at least 1; its licensed unit is product-specific.
- AI interaction entitlement fields apply only to `AI_PRO`; the D17 learner-seat baseline is 1,000 monthly and 50 daily interactions.
- These decisions define allowed values and entitlement classification only; permissions, lifecycle transitions, payment behavior, and physical enforcement remain deferred.

## Evidence and completion

**Evidence:**
- Check or artifact: Task 1.1.2 taxonomy, aligned source documents, decision log, and roadmap status.
- Result: Project owner approved the taxonomy as documented on 2026-10-25. `git diff --check` and a trailing-whitespace check on the new documents passed; the aligned source documents were reviewed.
- Location: `inovatx_core_enum_taxonomy.md`, `inovatx_product_requirements_document_prd.md`, `inovatx_uml.md`, `inovatx_phase1_core_domain_model.md`, `inovatx_phase0_decision_log.md`, `inovatx_executive_signoff_gate.md`, `inovatx_completion_checklist.md`, and `inovatx_project_todo.md`.

**Completion decision:** Complete; the approved taxonomy and logical validation rules satisfy the task acceptance criteria.
**Reviewer / approver and date:** Project owner, 2026-10-25.
