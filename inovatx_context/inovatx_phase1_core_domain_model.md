# INOVATX Core Domain Model — Task 1.1.1

**Roadmap task:** 1.1.1 — Finalize `Organization`, `UserProfile`, and `SubscriptionLicense` structure
**Phase / activity:** Phase 1 / Activity 1.1
**Status:** Approved by project owner on 2026-10-25; physical model details amended for Task 1.3.2 on 2026-10-27
**Traceability:** [Task 1.1.1 traceability record](inovatx_task_1_1_1_traceability.md)
**Sources:** PRD §3.1, FR-01, FR-05, FR-06, §7; UML §§5–6; approved Phase 0 decisions D3 and D17

## 1. Purpose and boundary

This document defines the first Core domain structure for organizations, organization memberships, and product licenses. It resolves the owner-approved user/membership and license cardinalities required to describe those entities.

This is a domain specification, not Django code, a migration, an RLS policy, or an authorization implementation. Enum values and logical validation rules are specified in [Task 1.1.2's taxonomy](inovatx_core_enum_taxonomy.md); physical constraints and the schema/migration baseline are completed in Task 1.1.3. License state transitions remain for Task 2.2.1.

## 2. Approved model decisions

1. One global Django authentication user may have memberships in more than one organization. A membership is organization-scoped and unique for a given `(auth_user, organization)` pair.
2. One membership may have multiple organization-scoped role assignments. Roles are attached to the membership, not stored as a single role on the global login.
3. No role-specific one-organization restriction is imposed; in particular, the model does not restrict a student to one organization.
4. One current `SubscriptionLicense` entitlement exists for each `(organization, product_code)` pair. Different products may coexist. This task does not model license renewal/payment history.
5. The license stores configured AI interaction entitlements per learner seat. Actual interactions, reservations, reconciliation, and provider-token usage are not license counters; they belong to the separately specified usage ledger.
6. The PRD's singular `request.user.userprofile.organization_id` tenant-context example is insufficient for a multi-membership login. Task 1.2.1 must define explicit active-membership selection and validation. Missing, invalid, or unauthorized tenant context must fail closed under the approved tenant-isolation requirements.

These decisions are recorded in the Task 1.1.1 section of the project decision log. Task 1.1.2 separately records the approved enum values and logical validation rules. Neither approval settles role permissions, lifecycle transitions, or runtime behavior.

## 3. Entity fields

`Required` below means the source defines a value and does not specify it as nullable. Where the source does not state nullability, that gap is explicit rather than silently decided.

### Organization

| Field | Type / meaning | Nullability | Notes |
|---|---|---|---|
| `id` | UUID primary key | Required | Matches PRD §3.1. |
| `name` | Variable-length string, max 255 characters | Required | Organization display/name value. No normalization rule is defined. |
| `org_type` | Organization-type enum | Required | Allowed values and logical validation are specified in the Task 1.1.2 taxonomy. |
| `status` | Organization lifecycle enum | Required | Allowed values are specified in the Task 1.1.2 taxonomy; transitions remain out of scope. |
| `created_at` | UTC-aware timestamp | Required | Automatically set when created. |
| `updated_at` | UTC-aware timestamp | Required | Owner-approved Task 1.3.2 addition; automatically refreshed when saved. |

### UserProfile (organization membership)

`UserProfile` is the PRD/UML name for a person's membership in one organization; it is not the global login record.

| Field | Type / meaning | Nullability | Notes |
|---|---|---|---|
| `id` | UUID primary key | Required | Matches PRD §3.1. |
| `user_id` | Foreign key to Django `auth_user.id` | Required | The PRD/UML depicts an integer authentication-user key. Login credentials and global identity fields remain on the auth user. |
| `organization_id` | Foreign key to `Organization.id` | Required | Establishes the membership's tenant. |
| `phone_number` | Variable-length string, max 32 characters | Required | Owner-approved Task 1.3.2 decision. Store the supplied value without normalization or uniqueness enforcement. |
| `created_at` | UTC-aware timestamp | Required | Automatically set when created. |
| `updated_at` | UTC-aware timestamp | Required | Owner-approved Task 1.3.2 addition; automatically refreshed when saved. |

#### OrganizationMembershipRole association

An explicit association is needed because one membership may have multiple roles.

| Field | Type / meaning | Nullability | Notes |
|---|---|---|---|
| `id` | UUID primary key | Required | Task 1.1.3 uses a surrogate UUID key. |
| `user_profile_id` | Foreign key to `UserProfile.id` | Required | Scopes each role assignment to one organization membership. |
| `role_code` | Role enum/code | Required | Allowed values are specified in the Task 1.1.2 taxonomy; permission semantics belong to the later RBAC task. `system_admin` is global and is not an organization-membership role. |
| `created_at` | UTC-aware timestamp | Required | Owner-approved Task 1.3.2 addition; automatically set when created. |
| `updated_at` | UTC-aware timestamp | Required | Owner-approved Task 1.3.2 addition; automatically refreshed when saved. |

Logical uniqueness: one assignment per `(user_profile_id, role_code)`, enforced by a unique constraint in the schema.

### SubscriptionLicense

`SubscriptionLicense` represents product entitlement. Payment is a separate lifecycle/entity; this task does not introduce a `Payment` entity.

| Field | Type / meaning | Nullability | Notes |
|---|---|---|---|
| `id` | UUID primary key | Required | Matches PRD §3.1. |
| `organization_id` | Foreign key to `Organization.id` | Required | The license belongs to an organization/tenant. |
| `product_code` | Product enum/code | Required | Allowed values and first-client scope are specified in the Task 1.1.2 taxonomy. |
| `seat_capacity` | Integer seat entitlement | Required | Must be at least 1; its licensed unit is product-specific. |
| `status` | License lifecycle enum | Required | Allowed values are specified in the Task 1.1.2 taxonomy; transitions remain for Task 2.2.1. |
| `moodle_cohort_id` | External Moodle cohort identifier, max 255 characters | Nullable | It is an opaque external reference, not a Core tenant key. Whether one license maps to multiple cohorts remains outside this task. |
| `ai_monthly_interaction_allowance_per_learner_seat` | Integer configured monthly interaction entitlement | Required for `AI_PRO` | Learner-seat baseline D17 sets 1,000 interactions per month. |
| `ai_daily_interaction_cap_per_learner_seat` | Integer configured daily interaction cap | Required for `AI_PRO` | D17 sets 50 interactions per learner seat per day. |
| `valid_until` | Nullable UTC-aware timestamp for entitlement validity boundary | Nullable | Owner-approved Task 1.3.2 decision. Must not be used as a substitute for the license lifecycle/status (FR-06). Renewal and expiry behavior belong to Task 2.2.1. |
| `created_at` | UTC-aware timestamp | Required | Owner-approved Task 1.3.2 addition; automatically set when created. |
| `updated_at` | UTC-aware timestamp | Required | Owner-approved Task 1.3.2 addition; automatically refreshed when saved. |

Do not carry the PRD ERD's `ai_tokens_used_current_month` field into the license. D3 requires reserving and reconciling provider tokens, while D17 defines customer-facing interaction allowances. Usage and token accounting must be represented in the later usage-ledger model, not as a mutable counter on this entitlement record.

## 4. Relationships and cardinality

| Relationship | Cardinality / invariant |
|---|---|
| `auth_user` to `UserProfile` | One auth user may have zero or many organization memberships. |
| `Organization` to `UserProfile` | One organization may have zero or many memberships. |
| `UserProfile` identity | At most one membership for a given `(user_id, organization_id)` pair. |
| `UserProfile` to `OrganizationMembershipRole` | One membership may have zero or many role assignments; a role assignment belongs to exactly one membership. Onboarding and authorization must ensure a role is assigned before granting protected access; exact workflow is outside this task. |
| `Organization` to `SubscriptionLicense` | One organization may have zero or many product licenses. |
| Current license uniqueness | At most one current license per `(organization_id, product_code)` pair. Historical renewals and whether they replace or version this record are out of scope and must be settled in Task 2.2.1 before implementing lifecycle/history behavior. |

## 5. Cross-task dependencies and unresolved details

- **Task 1.1.2:** see the approved [enum taxonomy and logical validation rules](inovatx_core_enum_taxonomy.md).
- **Task 1.1.3:** decide physical keys/unique constraints, migration representation, and database schema baseline.
- **Task 1.2.1:** define how a request chooses and validates one of a user's memberships as active tenant context; do not use an implicit singular `request.user.userprofile`.
- **Task 1.2.2:** implement the approved RLS design after the Django schema and PostgreSQL test environment are available. This model specification does not implement those policies.
- **Task 2.1:** define role permissions and enforcement. The role association does not itself grant authorization.
- **Task 2.2.1:** define license states, renewal/history semantics, and lifecycle transitions.
- **Later parent/guardian scope:** parent-child links and the authorization path between a parent membership and a learner remain separate from merely holding a `parent` role.

## 6. Review status

**Status:** Logical model approved by the project owner on 2026-10-25; physical details above were clarified for Task 1.3.2 on 2026-10-27.
**Acceptance evidence:** Field definitions, membership/license cardinalities, task boundaries, and cross-task dependencies were reviewed and approved. The UML and decision log reflect the approved membership/license cardinalities. Task 1.3.2 physical decisions are recorded in the decision log and corresponding schema plan.
**Completion decision:** Task 1.1.1 logical-model deliverable remains complete; Task 1.3.2 implements the approved physical model.
