# INOVATX Initial Core Schema and Migration Plan — Task 1.1.3

**Roadmap task:** 1.1.3 — Define the initial database migration plan
**Phase / activity:** Phase 1 / Activity 1.1
**Status:** Approved Task 1.1.3 baseline; physical-schema decisions approved for Task 1.3.2 on 2026-10-27
**Traceability:** [Task 1.1.3 traceability record](inovatx_task_1_1_3_traceability.md)
**Sources:** PRD §§2.1–2.2, 3.1–3.2, FR-05, FR-06, NFR-01; UML §§5, 8; approved Tasks 1.1.1 and 1.1.2; approved Task 1.1.3 planning decisions P1.1.3-D1–D6

## 1. Purpose and boundary

This document records the target relational schema for the initial Django Core domain and the order in which its schema changes should be applied once the Django application exists. It does not create executable migrations or claim that any database or schema currently exists.

The approved target is PostgreSQL. Its logical tenant database is `inovatx_db`; this plan does not create databases, configure credentials, establish application roles or grants, or apply Row-Level Security (RLS). Task 1.3.1 records the local owner/migrator/runtime role baseline and its narrow Django startup metadata grant; those local setup steps do not implement this plan's tenant-table grants or RLS. Task 1.2.2 approved the RLS role/policy design; executable implementation remains assigned to Task 1.2.2 and depends on the actual Django schema and a PostgreSQL test environment.

The roadmap lists “migration files and schema checks” as evidence. For this task, the project owner confirmed a documentation-only deliverable: executable Django migration files and schema checks are deferred until the authorized Django skeleton/model tasks establish a runnable application and database environment.

## 2. Approved entity baseline

`Organization` is the client/account record for the limited CRM_BASIC scope. Do not add a separate `Client` or `Account` table in this baseline. The Django authentication user is an external model dependency; this plan does not create or redefine it.

| Table / entity | Initial columns | Key and validation plan |
|---|---|---|
| `Organization` | `id`, `name`, `org_type`, `status`, `created_at`, `updated_at` | UUID primary key. Required name max 255. `org_type` and `status` are string-backed values with approved-value CHECK constraints. |
| `UserProfile` (organization membership) | `id`, `user_id`, `organization_id`, `phone_number`, `created_at`, `updated_at` | UUID primary key. Protected foreign keys to the configured Django authentication user and `Organization`. Required phone number max 32, without normalization or uniqueness. Unique `(user_id, organization_id)`. |
| `OrganizationMembershipRole` | `id`, `user_profile_id`, `role_code`, `created_at`, `updated_at` | UUID primary key. Foreign key to `UserProfile` with role-row cascade on explicit membership deletion. Unique `(user_profile_id, role_code)`. `role_code` is string-backed with an approved-value CHECK constraint. |
| `SubscriptionLicense` | `id`, `organization_id`, `product_code`, `seat_capacity`, `moodle_cohort_id`, `status`, `ai_monthly_interaction_allowance_per_learner_seat`, `ai_daily_interaction_cap_per_learner_seat`, `valid_until`, `created_at`, `updated_at` | UUID primary key. Protected foreign key to `Organization`. Unique `(organization_id, product_code)`. Product/status values use string-backed fields with CHECK constraints; `seat_capacity >= 1`. |

The approved values for organization types, membership roles, product codes, and organization/license statuses are listed in the [Core enum taxonomy](inovatx_core_enum_taxonomy.md). Global `system_admin` is not an organization membership role.

### Column semantics and constraints

- All UUID primary keys and required foreign keys must be non-null.
- `Organization.name` (max 255), `org_type`, `status`, `created_at`, and `updated_at` are required.
- `UserProfile.user_id`, `organization_id`, `phone_number` (max 32), `created_at`, and `updated_at` are required. The phone number is stored as supplied; there is no normalization or uniqueness rule.
- `OrganizationMembershipRole.user_profile_id`, `role_code`, `created_at`, and `updated_at` are required. A membership may have zero or many role assignments; each role assignment belongs to exactly one membership.
- `SubscriptionLicense.organization_id`, `product_code`, `seat_capacity`, `status`, `created_at`, and `updated_at` are required. `moodle_cohort_id` is nullable with max length 255. `valid_until` is nullable.
- String lengths are `Organization.name` 255, `UserProfile.phone_number` 32, and `SubscriptionLicense.moodle_cohort_id` 255; each enum/code field is sized to its longest approved value.
- `Organization.status` and `SubscriptionLicense.status` use separate constraints even though their approved code sets are the same. Payment state is not stored on either entity.
- `seat_capacity` is a positive integer. Its unit is product-specific; this baseline does not calculate consumption or pooling.
- The two AI interaction entitlement columns are nullable for non-`AI_PRO` products. For `AI_PRO`, both values must be explicitly supplied per license and be positive. The approved learner-seat baseline is 1,000 monthly and 50 daily interactions, but no implicit model default is applied. A conditional CHECK constraint enforces applicability; this plan does not define usage accounting.
- String-backed enum fields use the approved value sets in `CHECK` constraints and Django model `choices`. Do not use PostgreSQL-native ENUM types for this baseline.
- `created_at` and `updated_at` use UTC-aware Django timestamps. Both are present on the four Core models only; Django built-in tables are unchanged. `created_at` is set on insertion and `updated_at` refreshed on save.
- Protect Django auth users and organizations while referenced. A membership-role row cascades only when its `UserProfile` is explicitly deleted. No additional non-unique indexes are selected; use the standard foreign-key indexes and uniqueness indexes.

### Authentication-user dependency

`UserProfile.user_id` references the primary key of Django's built-in `auth.User`, selected for the initial project configuration under decision P1.3.1-D1. The Core migration depends on the configured authentication model's initial migration and uses `settings.AUTH_USER_MODEL`. Its user foreign key protects a referenced auth user from deletion.

## 3. Constraint inventory

| Invariant | Target constraint |
|---|---|
| Valid organization type | CHECK `org_type` is one of `individual`, `school`, `sme`, `ngo`, `enterprise`. |
| Valid organization status | CHECK `status` is one of `pending`, `active`, `suspended`, `expired`, `cancelled`. |
| One membership per person and organization | UNIQUE `(user_id, organization_id)`. |
| Valid membership role | CHECK `role_code` is one of `org_admin`, `instructor`, `student`, `parent`, `sme_staff`; UNIQUE `(user_profile_id, role_code)`. |
| Valid product code | CHECK `product_code` is one of `EDTECH_LMS`, `CRM_BASIC`, `AI_PRO`. |
| Valid license status | CHECK `status` is one of `pending`, `active`, `expired`, `suspended`, `cancelled`. |
| Positive product capacity | CHECK `seat_capacity >= 1`. |
| One license in the initial current-license baseline | UNIQUE `(organization_id, product_code)`. Renewal/history rows are not part of this schema. |
| AI entitlement applicability | For `AI_PRO`, both AI allowance fields are NOT NULL and greater than zero; for other products, both are NULL. |

Constraint names and exact model/API error messages are implementation details for the Django model task. Database enforcement must not be described as operational until migrations have been applied and schema checks have been executed.

## 4. Ordered migration plan

Implement and review schema changes in this dependency order:

1. **Confirm migration prerequisites:** use the Django 5.2 project and configured `AUTH_USER_MODEL`; verify its initial migration is available and use the approved local migrator/owner role.
2. **Create `Organization`:** UUID primary key, required name/type/status and timestamps, organization type/status CHECK constraints.
3. **Create `UserProfile`:** UUID primary key, protected authentication-user and organization foreign keys, required phone number and timestamps, unique user/organization constraint.
4. **Create `OrganizationMembershipRole`:** UUID primary key, cascading membership foreign key, role code and timestamps, role-code CHECK, unique membership/role constraint.
5. **Create `SubscriptionLicense`:** UUID primary key, protected organization foreign key, product/status codes and timestamps, positive capacity, nullable external Moodle cohort and validity timestamp, conditional AI entitlement constraint, and unique organization/product constraint.
6. **Review the complete migration graph and resulting schema:** check dependency ordering, constraint behavior, and forward/reverse operation on a separate disposable local PostgreSQL test database.
7. **Handle tenant security separately:** implement no RLS policy or application database grant as part of these schema steps. Task 1.2.2 owns the approved RLS design and its implementation after the Django schema and PostgreSQL test environment are available.

The exact number of Django migration files is left to the application layout and dependency graph. Keep the schema changes reviewable and ordered by dependency; do not combine this plan with unrelated feature or lifecycle changes.

## 5. Rollback and correction considerations

- Before data exists, a migration may be reversed in reverse dependency order in a disposable development database to validate reversibility.
- Once data exists, dropping these tables or columns is destructive. Do not use an automatic reverse/drop as a production recovery procedure.
- For an applied migration, prefer a new forward corrective migration over editing migration history that has already been applied elsewhere.
- Before any later production migration, require an approved backup/restore and rollback procedure appropriate to that release. This plan does not claim that procedure has been tested.
- Any data conversion needed for future enum changes must be designed and validated explicitly; CHECK constraints must not be weakened with a silent default or an unreviewed value mapping.

## 6. Remaining dependencies and scope boundaries

The physical-schema choices previously open for executable migrations are approved for Task 1.3.2 and recorded in the Phase 0 decision log.

- Production PostgreSQL provisioning, credentials, and deployment remain out of scope; local development role setup is documented under Task 1.3.1.
- Task 1.2.2 owns executable RLS policies and least-privilege tenant-table grants. No RLS policy or runtime grant is created by this model/migration task.
- License lifecycle transitions/history and payment entities remain deferred to their assigned tasks.
