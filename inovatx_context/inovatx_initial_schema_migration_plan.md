# INOVATX Initial Core Schema and Migration Plan — Task 1.1.3

**Roadmap task:** 1.1.3 — Define the initial database migration plan
**Phase / activity:** Phase 1 / Activity 1.1
**Status:** Draft for project-owner review
**Traceability:** [Task 1.1.3 traceability record](inovatx_task_1_1_3_traceability.md)
**Sources:** PRD §§2.1–2.2, 3.1–3.2, FR-05, FR-06, NFR-01; UML §§5, 8; approved Tasks 1.1.1 and 1.1.2; approved Task 1.1.3 planning decisions P1.1.3-D1–D6

## 1. Purpose and boundary

This document records the target relational schema for the initial Django Core domain and the order in which its schema changes should be applied once the Django application exists. It does not create executable migrations or claim that any database or schema currently exists.

The approved target is PostgreSQL. Its logical tenant database is `inovatx_db`; this plan does not create databases, configure credentials, establish application roles or grants, or apply Row-Level Security (RLS). The Phase 0 exit review initially left database bootstrap/application roles and RLS role/policy design unresolved. Task 1.2.2 subsequently approved that design; its executable implementation remains assigned to Task 1.2.2 and depends on the actual Django schema and a PostgreSQL test environment.

The roadmap lists “migration files and schema checks” as evidence. For this task, the project owner confirmed a documentation-only deliverable: executable Django migration files and schema checks are deferred until the authorized Django skeleton/model tasks establish a runnable application and database environment.

## 2. Approved entity baseline

`Organization` is the client/account record for the limited CRM_BASIC scope. Do not add a separate `Client` or `Account` table in this baseline. The Django authentication user is an external model dependency; this plan does not create or redefine it.

| Table / entity | Initial columns | Key and validation plan |
|---|---|---|
| `Organization` | `id`, `name`, `org_type`, `status`, `created_at` | UUID primary key. `org_type` and `status` are string-backed values with approved-value CHECK constraints. The name is required. |
| `UserProfile` (organization membership) | `id`, `user_id`, `organization_id`, `phone_number`, `created_at` | UUID primary key. Foreign keys to the configured Django authentication user and `Organization`. Unique `(user_id, organization_id)`. |
| `OrganizationMembershipRole` | `id`, `user_profile_id`, `role_code` | UUID primary key. Foreign key to `UserProfile`. Unique `(user_profile_id, role_code)`. `role_code` is string-backed with an approved-value CHECK constraint. |
| `SubscriptionLicense` | `id`, `organization_id`, `product_code`, `seat_capacity`, `moodle_cohort_id`, `status`, `ai_monthly_interaction_allowance_per_learner_seat`, `ai_daily_interaction_cap_per_learner_seat`, `valid_until` | UUID primary key. Foreign key to `Organization`. Unique `(organization_id, product_code)` in this baseline. Product/status values use string-backed fields with CHECK constraints; `seat_capacity >= 1`. |

The approved values for organization types, membership roles, product codes, and organization/license statuses are listed in the [Core enum taxonomy](inovatx_core_enum_taxonomy.md). Global `system_admin` is not an organization membership role.

### Column semantics and constraints

- All UUID primary keys and required foreign keys must be non-null.
- `Organization.name`, `org_type`, `status`, and `created_at` are required.
- `UserProfile.user_id`, `organization_id`, and `created_at` are required. `phone_number` is in the domain model, but PRD nullability, normalization, and uniqueness are unspecified; preserve this as a pre-migration decision rather than guessing.
- `OrganizationMembershipRole.user_profile_id` and `role_code` are required. A membership may have zero or many role assignments; each role assignment belongs to exactly one membership.
- `SubscriptionLicense.organization_id`, `product_code`, `seat_capacity`, and `status` are required. `moodle_cohort_id` is nullable. `valid_until` nullability is unspecified in the PRD and remains a pre-migration decision.
- `Organization.status` and `SubscriptionLicense.status` use separate constraints even though their approved code sets are the same. Payment state is not stored on either entity.
- `seat_capacity` is a positive integer. Its unit is product-specific; this baseline does not calculate consumption or pooling.
- The two AI interaction entitlement columns are nullable for non-`AI_PRO` products. For `AI_PRO`, both values must be present and positive. The approved learner-seat baseline is 1,000 monthly and 50 daily interactions. A conditional CHECK constraint should enforce that relationship. Whether the eventual model stores a configurable per-license value or applies the baseline as a default must be settled when executable model behavior is specified; this plan does not define usage accounting.
- String-backed enum fields use the approved value sets in `CHECK` constraints and Django model `choices`. Do not use PostgreSQL-native ENUM types for this baseline.
- Foreign-key deletion behavior, exact string-column lengths, timestamp timezone convention, and explicit non-unique index selection are not established by the approved domain sources. Decide these before executable migrations are authored; do not infer cascading deletion or irreversible data behavior.

### Authentication-user dependency

`UserProfile.user_id` references the primary key of Django's built-in `auth.User`, selected for the initial project configuration under decision P1.3.1-D1. The first Core migration must depend on the configured authentication model's initial migration and use a compatible key type; model code should reference it through `settings.AUTH_USER_MODEL`. This resolves the authentication-model prerequisite only; it does not settle other open physical-schema choices.

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

Executable files are deferred. When the authorized Django application/model work begins, implement and review schema changes in this dependency order:

1. **Confirm migration prerequisites:** establish Django version/app labels and `AUTH_USER_MODEL`; verify the authentication model's initial migration is available. Obtain approved database-bootstrap/application-role design before provisioning or granting access to an application database role.
2. **Create `Organization`:** UUID primary key, required name/type/status/creation fields, and organization type/status CHECK constraints.
3. **Create `UserProfile`:** UUID primary key, authentication-user and organization foreign keys, required creation field, unique user/organization constraint, and a reviewed nullability decision for `phone_number`.
4. **Create `OrganizationMembershipRole`:** UUID primary key, membership foreign key, role code, role-code CHECK, and unique membership/role constraint.
5. **Create `SubscriptionLicense`:** UUID primary key, organization foreign key, product/status codes and CHECK constraints, positive capacity, nullable external Moodle cohort, reviewed `valid_until` nullability, conditional AI entitlement constraint, and unique organization/product constraint.
6. **Review the complete migration graph and resulting schema:** check dependency ordering, constraint behavior, and forward/reverse operation on a disposable local PostgreSQL database when the application and database are available. This is evidence for the later executable migration task, not a test run claimed by this document.
7. **Handle tenant security separately:** implement no RLS policy or application database grant as part of these schema steps. Task 1.2.2 owns the approved RLS design and its implementation after the Django schema and PostgreSQL test environment are available.

The exact number of Django migration files is left to the application layout and dependency graph. Keep the schema changes reviewable and ordered by dependency; do not combine this plan with unrelated feature or lifecycle changes.

## 5. Rollback and correction considerations

- Before data exists, a migration may be reversed in reverse dependency order in a disposable development database to validate reversibility.
- Once data exists, dropping these tables or columns is destructive. Do not use an automatic reverse/drop as a production recovery procedure.
- For an applied migration, prefer a new forward corrective migration over editing migration history that has already been applied elsewhere.
- Before any later production migration, require an approved backup/restore and rollback procedure appropriate to that release. This plan does not claim that procedure has been tested.
- Any data conversion needed for future enum changes must be designed and validated explicitly; CHECK constraints must not be weakened with a silent default or an unreviewed value mapping.

## 6. Unresolved pre-migration decisions and dependencies

These do not change the approved logical domain model, but must be resolved before executable migrations are authored:

1. The Django application and `AUTH_USER_MODEL` choice, including its migration dependency and primary-key compatibility.
2. `phone_number` nullability and any normalization/uniqueness requirements.
3. `valid_until` nullability and timestamp timezone convention.
4. Exact string-field lengths and any name normalization/length requirements.
5. Foreign-key deletion behavior and any additional indexes based on the approved query patterns.
6. PostgreSQL bootstrap, application database roles, and grants; do not assume privileges or owner role.
7. RLS role/policy design, approved and recorded under Task 1.2.2 decisions; executable policy implementation awaits the Django schema and PostgreSQL test environment.
8. Whether AI_PRO allowance values are stored as explicit per-license values or supplied by a later approved plan/default mechanism; the schema invariant is that both values are present and positive only for AI_PRO.

No database bootstrap, credentials, role grants, RLS policy, license history, or payment model is selected by this document.
