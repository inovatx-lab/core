# INOVATX Core Enum Taxonomy and Validation Rules — Task 1.1.2

**Roadmap task:** 1.1.2 — Define enums and constraints for organization types, roles, and product codes
**Phase / activity:** Phase 1 / Activity 1.1
**Status:** Approved by project owner on 2026-10-25
**Traceability:** [Task 1.1.2 traceability record](inovatx_task_1_1_2_traceability.md)
**Sources:** PRD §3.1, FR-04–FR-07, §7; UML §§4–6, recommended resolutions; approved decisions P1.1.2-D1–D4

## 1. Scope and boundary

This document specifies canonical code values and logical validation rules for the Phase 1 Core domain. It is a documentation contract, not an implementation or physical database schema. Task 1.1.3 owns physical keys, database constraints, and migrations. Role permissions and organization/license lifecycle transitions remain in their assigned roadmap tasks.

Codes are exact and case-sensitive. Implementations must reject values outside the applicable set; they must not silently map unknown codes to a default. Database-level enforcement is not claimed by this specification.

## 2. Organization types

| Canonical code | Meaning / scope note |
|---|---|
| `individual` | Individual client classification. |
| `school` | Educational institution classification. |
| `sme` | Small or medium enterprise classification. The code alone does not enable deferred SME product modules. |
| `ngo` | Non-governmental organization classification. The code alone does not enable deferred NGO product modules. |
| `enterprise` | Enterprise organization classification. |

**Validation:** `Organization.org_type` must contain exactly one listed code and must not be null. Organization type is classification data; it does not independently grant a product, feature, or role.

## 3. Organization membership roles

| Canonical code | Scope |
|---|---|
| `org_admin` | Organization-scoped membership role. |
| `instructor` | Organization-scoped role for teachers, lecturers, mentors, and similar teaching roles. |
| `student` | Organization-scoped membership role. |
| `parent` | Organization-scoped membership role. |
| `sme_staff` | Organization-scoped membership role; its code does not enable deferred SME modules. |

`system_admin` is a global system role and is not a `UserProfile` membership role. `teacher`, `lecturer`, and `mentor` are not separate canonical role codes; use `instructor`.

**Validation:** each `OrganizationMembershipRole.role_code` must contain exactly one listed membership-role code and must not be null. A membership may have zero or many role assignments; duplicate assignments of the same role to one membership are invalid. Role codes identify membership classification only; they do not define permissions. Authorization remains subject to the resource/action permission model and its assigned task.

## 4. Organization and license statuses

These are independent status enums. Payment status is separate and is not defined by this task.

| Entity | Allowed status codes |
|---|---|
| `Organization.status` | `pending`, `active`, `suspended`, `expired`, `cancelled` |
| `SubscriptionLicense.status` | `pending`, `active`, `expired`, `suspended`, `cancelled` |

For a subscription license, `pending` means the entitlement exists but is not usable. These values do not specify state transitions, triggers, payment coupling, or renewal/history behavior; those remain deferred to the assigned lifecycle tasks.

**Validation:** each status field must contain exactly one code from its entity's set and must not be null. An organization status must not be used as a substitute for license or payment status.

## 5. Product codes and product-specific entitlements

| Canonical code | First-client scope / entitlement note |
|---|---|
| `EDTECH_LMS` | Learning-platform product entitlement. |
| `CRM_BASIC` | First-client baseline, limited to global client/account tracking, tenant users' account overview, and a gateway into the tenant's Moodle learning platform. Broader CRM capabilities remain deferred. This scope does not grant blanket cross-tenant access; authorization remains separately defined. |
| `AI_PRO` | AI product entitlement; AI interaction allowance fields apply to this product only. |

**Validation:** `SubscriptionLicense.product_code` must contain exactly one listed code and must not be null. The code identifies a product entitlement; it does not itself grant permissions, activate the entitlement, or define payment behavior.

`seat_capacity` must be an integer greater than or equal to 1. It counts licensed units for the selected product; the unit is product-specific. The code taxonomy does not define a universal user-count formula, pooling rule, or seat-usage calculation.

The AI interaction entitlement fields apply only to `AI_PRO`. The approved D17 learner-seat baseline is 1,000 interactions per month and 50 per day. Other product codes do not carry these AI entitlement values under this taxonomy. Usage, reservation, reconciliation, pooling, and provider-token accounting remain separate from the license and are governed by the approved usage-ledger decisions.

**Applicability representation:** This is a logical product rule. Whether non-applicable AI fields are absent, null, or represented by a separate entitlement record is a physical schema decision for Task 1.1.3.

## 6. Related logical invariants

- A membership role is unique per `(user_profile_id, role_code)`.
- A membership is unique per `(user_id, organization_id)`.
- At most one current license exists per `(organization_id, product_code)`.
- `seat_capacity` is positive for every license; product-specific unit definitions must not be conflated.
- Enum membership, positive seat capacity, and the product-to-AI-entitlement relationship are validation requirements. Their physical database enforcement belongs to the schema/migration task.

## 7. Deferred behavior

This taxonomy does not define role permissions, lifecycle transitions, payment statuses, renewal/history semantics, product-specific seat calculations, or AI allowance resets and pooling. Those decisions remain with the relevant roadmap tasks; no behavior should be inferred from an enum value alone.
