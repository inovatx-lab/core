# Task Traceability — 1.3.2 Django Models and Admin

**Task ID and title:** 1.3.2 — Build minimal Django admin and ORM models
**Phase / activity:** Phase 1 / Activity 1.3
**Owner:** Project owner
**Status:** Complete

## Outcome and sources

**Outcome / deliverable:** Implement the approved Core domain models and PostgreSQL constraints, register them in a minimal Django admin, and validate model/admin behavior with focused tests against an isolated PostgreSQL test database.

**PRD sources:**
- §2.2: Django 5.x, Python 3.12+, and PostgreSQL 16+ are the Core technology baseline.
- §3.1: Organization, UserProfile, OrganizationMembershipRole, and SubscriptionLicense fields and relationships.
- FR-01: organization/user relationship baseline.
- FR-04–FR-05: role classification and membership boundaries; this task models role assignments but does not implement permissions.
- FR-06: organization status, license status, and payment status are distinct.
- NFR-01: PostgreSQL RLS and tenant-isolation integration tests are required; RLS implementation belongs to its assigned task.

**UML sources:**
- §5 ERD: approved entity fields, relationships, and cardinalities.
- §6 class diagram: Django Core model responsibilities.

**Approved design sources:**
- Phase 1 authorization permits Tasks 1.1.1–1.3.3 only.
- Tasks 1.1.1–1.1.3: approved domain model, enum taxonomy, and migration/constraint plan.
- Task 1.3.1: Python 3.12, Django 5.2, PostgreSQL-only settings, Django built-in `auth.User`, and separate local migration/runtime identities.
- Project-owner-approved Task 1.3.2 model decisions: required phone number; nullable `valid_until`; field lengths; FK deletion behavior; UTC-aware `created_at`/`updated_at` on the four Core models; explicit AI_PRO allowances; no additional non-unique indexes or implicit business-field defaults.
- Project-owner-approved test boundary: isolated disposable PostgreSQL test database using migration/owner settings; do not broaden runtime grants or claim runtime-admin authorization.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django Core ORM/admin and PostgreSQL schema. Tests use an isolated local database and the migration/owner identity; no runtime tenant-access path or privilege is added.

## Acceptance criteria

1. Implement `Organization`, `UserProfile`, `OrganizationMembershipRole`, and `SubscriptionLicense` with the approved keys, fields, cardinalities, choices, timestamps, and FK deletion behavior.
2. Enforce the approved uniqueness and data-integrity rules in both Django validation where applicable and PostgreSQL constraints, including enum values, positive seat capacity, and AI_PRO allowance applicability.
3. Use Django's configured `AUTH_USER_MODEL` for membership identity; keep `system_admin` out of organization membership roles.
4. Register all four models in basic Django admin pages with useful list columns, searches, and filters; add no custom authorization matrix or business workflow.
5. Generate and review executable migrations; validate their application and the model/admin smoke tests against an isolated PostgreSQL test database.
6. Preserve the approved runtime privilege boundary; do not implement RLS, grant runtime access to tenant/auth tables, or represent elevated test execution as runtime authorization evidence.
7. Update the schema/domain documentation, roadmap, repository structure, decision log, and this traceability record with evidence that reflects actual implementation and validation.

## Scope

**In scope:** The four approved ORM models; model choices and database constraints; generated migrations; basic Django admin registration; focused model and admin tests; isolated local PostgreSQL test setup; directly related project documentation.

**Out of scope:** RLS policies and runtime grants; tenant middleware or tenant request/worker behavior; role-permission authorization; onboarding, payment, renewal, and lifecycle workflows; custom authentication; API routes; production provisioning/deployment; additional domain entities.

## Approved implementation decisions

- Use UUID primary keys for all four Core models and reference `settings.AUTH_USER_MODEL` from `UserProfile`.
- `UserProfile.phone_number` is required with max length 32; do not add normalization or uniqueness behavior.
- `SubscriptionLicense.valid_until` is nullable.
- Use `Organization.name` max length 255 and nullable `moodle_cohort_id` max length 255. Size each enum/code field to the longest approved code in its set.
- Protect auth users and organizations from deletion while referenced; cascade role-assignment rows when a `UserProfile` is explicitly deleted.
- Add UTC-aware `created_at` and `updated_at` fields to each of the four Core models only. Do not modify Django built-in models.
- Store explicit positive monthly/daily AI allowance values for AI_PRO licenses; keep both columns null for other products. Add no implicit business-field defaults.
- Add no explicit non-unique indexes beyond Django foreign-key indexes and indexes inherent in approved uniqueness constraints.
- Register basic admin CRUD pages with model-specific list/search/filter configuration. No custom bulk actions, role matrix, or onboarding flow.
- Run database-backed model/admin smoke tests only against an isolated disposable PostgreSQL test database under migration/owner settings. Runtime table grants and RLS remain separately assigned.

## Evidence and completion

**Evidence:**
- Check or artifact: implementation diff, generated migration files, focused model/admin tests, PostgreSQL migration/test commands, and documentation review.
- Result: Generated `core/migrations/0001_initial.py` with all four models, CHECK constraints, unique constraints, and FK dependencies on `auth.User`. Applied migrations successfully against PostgreSQL 18 using `config.migration_settings` (migrator role with owner activation). All 13 focused tests passed against isolated PostgreSQL test database (`inovatx_test_db`) using `config.test_settings`: 11 model tests (phone required, unique profile, unique role + cascade, invalid org type rejected, invalid role rejected, license capacity positive, AI Pro requires allowances, non-AI license null allowances, unique license per org+product, protected deletion, updated_at changes) and 2 admin tests (all models registered, superuser can open changelists). `manage.py check --settings=config.migration_settings` passed with no issues. All acceptance criteria met.
- Location: `core/`, `config/`, `README.md`, and this traceability record.
- Validation boundary: PostgreSQL 18.6 running locally; roles `inovatx_owner` (NOLOGIN), `inovatx_migrator` (LOGIN, owner activation), `inovatx_runtime` (LOGIN, SELECT only) configured per README. Test database `inovatx_test_db` used migration/owner identity. Runtime grants remain unchanged — no RLS, no tenant-table grants, no elevated test authorization claimed.

**Completion decision:** Complete. All Task 1.3.2 deliverables are implemented and PostgreSQL-backed migrations and tests have been validated successfully. Domain models, admin registration, and focused tests are complete. Later tenant-isolation, RLS, and deployment work remains outside this task.
**Reviewer / approver and date:** Implementation completed 2026-10-27; PostgreSQL validation executed on 2026-10-27.
