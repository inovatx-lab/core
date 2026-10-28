# Core API Contract — Task 1.3.3

**Roadmap task:** 1.3.3 — Create initial API contract for Core endpoints  
**Phase / activity:** Phase 1 / Activity 1.3  
**Status:** Documented — contract only, no implementation  
**Traceability:** [Task 1.3.3 traceability record](inovatx_task_1_3_3_traceability.md)

## 1. Purpose and boundary

This document specifies the Core API contract for INOVATX Core (Django) tenant-facing endpoints. It defines endpoint schemas, request/response mappings, authentication, tenant context selection, membership validation flow, and error handling for the four approved Core domain models:

- `Organization`
- `UserProfile`
- `OrganizationMembershipRole`
- `SubscriptionLicense`

This is a **documentation contract only**. No Django routes, views, serializers, middleware, tenant context code, RLS policies, or runtime implementation is created by this task. The contract defines the interface that Phase 2 implementation tasks will build against.

## 2. Scope and out-of-scope items

### In scope

- Endpoint schemas (request/response) for all four Core models, tenant-scoped.
- Authentication flow: Django `auth_user` authentication precedes tenant context selection.
- Tenant context selection flow: explicit organization UUID selector, membership validation under RLS, fail closed on missing/invalid/unauthorized context.
- Error handling specification: 401, 400, 404, 403, and 500 responses with correlation identifiers.
- Transport selection for the organization selector (route/header/session) deferred to this contract.
- Scope boundaries preserving the approved privilege boundary (no RLS, no tenant middleware, no runtime grants, no production deployment).

### Out of scope

- Django REST framework or any executable route/view implementation.
- Tenant middleware implementation; RLS policy implementation; role-permission authorization matrix.
- Onboarding, payment, renewal, and lifecycle workflows.
- Production provisioning or deployment.
- Moodle endpoints; FastAPI AI endpoints; payment endpoints.
- Additional domain entities beyond the four Core models.
- Secrets, credentials, or connection strings in this document.

## 3. Authentication contract

### 3.1 Authentication precedes tenant selection

For every tenant-scoped Core API request:

1. The caller must be authenticated through Django `auth_user` before any tenant context is evaluated.
2. If authentication fails, the response is the authentication layer's `401 Unauthorized`. No tenant selector processing, membership lookup, or tenant-owned database query occurs.
3. The authenticated user's ID is used to scope the membership validation lookup. A user may have memberships in multiple organizations; there is no implicit default organization or singular `request.user.userprofile.organization_id`.

### 3.2 Authentication credential sources

- Credentials are supplied through Django's built-in authentication (session or token, determined by the implementation task).
- No API key, bearer token, or credential format is specified in this contract. The selector transport and authentication header details are deferred to implementation tasks.

## 4. Tenant context selection contract

### 4.1 Organization selector

Each tenant-scoped request must supply an explicit organization UUID selector identifying one organization as the candidate tenant context.

### 4.2 Transport

The organization selector is carried as an HTTP request header:

| Header name | Value format | Required | Example |
|---|---|---|---|
| `X-INOVATX-Organization-Id` | UUID (canonical form, case-insensitive) | Yes, for tenant-scoped endpoints | `550e8400-e29b-41d4-a716-446655440000` |

The header value is treated as an **untrusted candidate**, not proof of membership or authorization.

### 4.3 Context resolution order

Per P1.2.1-D1 and P1.2.3-D1:

1. **Authenticate first.** Authentication failure returns `401`; no tenant selection proceeds.
2. **Validate selector syntax.** A missing or non-UUID selector returns `400` before any tenant-owned database access.
3. **Establish candidate context.** Begin a transaction; set the syntactically valid organization UUID as transaction-local context (`SET LOCAL app.current_organization_id = '<UUID>'`).
4. **Perform only the membership-validation lookup.** Query for a `UserProfile` matching both the authenticated user ID and selected organization ID, under the candidate context and RLS. No tenant business-data query occurs before this lookup succeeds.
5. **Deny unmatched membership uniformly.** If no matching membership exists — whether the organization is absent or the user is not a member — roll back and return the same `404` outcome. Do not reveal which condition applied; do not fall back to another organization or a default organization.
6. **Authorize the requested action.** A member lacking the required resource/action permission receives `403`. Membership alone does not authorize an action.
7. **Access tenant business data only after validation.** All tenant operations occur within the transaction containing the validated candidate context. Transaction completion clears `SET LOCAL`; connection teardown leaves borrowed connections clean.

### 4.4 Global administrator boundary

The global `system_admin` role does not by itself grant access to tenant-owned data and does not create an implicit all-tenant context. A `system_admin` operation on tenant-owned data still requires an explicit target organization selector and successful membership validation for that organization (P1.2.1-D4).

## 5. Endpoint schemas

All endpoints are tenant-scoped and require the `X-INOVATX-Organization-Id` header plus an authenticated user with a matching membership. All resource identifiers are UUIDs in canonical form. All timestamps are UTC-aware ISO-8601 strings.

Common response envelope:

| Field | Type | Description |
|---|---|---|
| `correlation_id` | UUID | Server-generated correlation identifier included on every response. |
| `data` | object | Response payload (single object or list). |
| `errors` | array of objects | Present only on error responses; each entry contains `code`, `message`, and optional `field`. |
| `meta` | object | Optional metadata such as pagination or timestamps. |

Common error envelope:

| Field | Type | Description |
|---|---|---|
| `code` | string | Machine-readable error code (e.g., `unauthenticated`, `malformed_selector`, `not_found`, `forbidden`, `internal_error`). |
| `message` | string | Human-readable generic message; no SQL, policy, or database details. |
| `field` | string | Optional field name when the error is field-specific (e.g., selector header). |
| `correlation_id` | UUID | Correlation identifier matching the response header. |

### 5.1 Organization endpoints

#### 5.1.1 List organizations

```
GET /api/v1/organizations/
```

**Request headers:**
- `Authorization`: authenticated caller credentials (required)
- `X-INOVATX-Organization-Id`: the organization context (required)

**Query parameters:** none specified by this contract.

**Response — 200 OK:**

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Organization primary key. |
| `name` | string (max 255) | Organization display name. |
| `org_type` | enum | One of: `individual`, `school`, `sme`, `ngo`, `enterprise`. |
| `status` | enum | One of: `pending`, `active`, `suspended`, `expired`, `cancelled`. |
| `created_at` | ISO-8601 UTC | Automatically set on creation. |
| `updated_at` | ISO-8601 UTC | Automatically refreshed on save. |

**Errors:** `401`, `400`, `404`, `500` per Sections 6 and 8.

#### 5.1.2 Retrieve organization

```
GET /api/v1/organizations/{organization_id}/
```

**Path parameters:**
- `organization_id` (UUID): the organization to retrieve.

**Request headers:** `Authorization`, `X-INOVATX-Organization-Id` (must match `{organization_id}`).

**Response — 200 OK:** same fields as list.

**Errors:** `401`, `400`, `403` (member denied access to target organization), `404` (no matching membership, uniform), `500`.

#### 5.1.3 Create organization

```
POST /api/v1/organizations/
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string (max 255) | Yes | Organization display name. |
| `org_type` | enum | Yes | One of: `individual`, `school`, `sme`, `ngo`, `enterprise`. |
| `status` | enum | Yes | One of: `pending`, `active`, `suspended`, `expired`, `cancelled`. |

**Response — 201 Created:** same fields as Organization resource.

**Errors:** `401`, `400` (malformed selector or invalid body), `403`, `404`, `500`.

#### 5.1.4 Update organization

```
PATCH /api/v1/organizations/{organization_id}/
```

**Request body:** subset of Organization fields (all optional).

**Response — 200 OK:** updated Organization resource.

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.1.5 Delete organization

```
DELETE /api/v1/organizations/{organization_id}/
```

**Response — 204 No Content:** successful deletion.

**Errors:** `401`, `400`, `403`, `404`, `500`.

### 5.2 UserProfile endpoints

A `UserProfile` represents one authenticated user's membership in one organization. Fields and rules follow Task 1.1.1 domain model.

#### 5.2.1 List memberships

```
GET /api/v1/organizations/{organization_id}/memberships/
```

**Request headers:** `Authorization`, `X-INOVATX-Organization-Id`.

**Response — 200 OK:** list of UserProfile resources.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | UserProfile primary key. |
| `user_id` | integer | FK to Django `auth_user.id` (global login record). |
| `organization_id` | UUID | FK to `Organization.id` (the membership tenant). |
| `phone_number` | string (max 32) | Supplied value; no normalization or uniqueness enforcement. |
| `created_at` | ISO-8601 UTC | Automatically set on creation. |
| `updated_at` | ISO-8601 UTC | Automatically refreshed on save. |

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.2.2 Retrieve membership

```
GET /api/v1/organizations/{organization_id}/memberships/{membership_id}/
```

**Response — 200 OK:** single UserProfile resource.

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.2.3 Create membership

```
POST /api/v1/organizations/{organization_id}/memberships/
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | integer | Yes | FK to `auth_user.id`. |
| `phone_number` | string (max 32) | Yes | Supplied value; no normalization or uniqueness. |

**Constraints:** at most one `UserProfile` per `(user_id, organization_id)` pair (unique constraint enforced at schema level; API returns `400` on duplicate).

**Response — 201 Created:** single UserProfile resource.

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.2.4 Update membership

```
PATCH /api/v1/organizations/{organization_id}/memberships/{membership_id}/
```

**Request body:** subset of mutable fields (`phone_number`, etc.).

**Response — 200 OK:** updated UserProfile resource.

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.2.5 Delete membership

```
DELETE /api/v1/organizations/{organization_id}/memberships/{membership_id}/
```

**Response — 204 No Content:** successful deletion.

**Errors:** `401`, `400`, `403`, `404`, `500`.

### 5.3 OrganizationMembershipRole endpoints

A role assignment scopes one role code to one organization membership. `system_admin` is global and is not an organization membership role.

#### 5.3.1 List role assignments

```
GET /api/v1/organizations/{organization_id}/memberships/{membership_id}/roles/
```

**Response — 200 OK:** list of role assignment resources.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Assignment primary key. |
| `user_profile_id` | UUID | FK to `UserProfile.id`. |
| `role_code` | enum | One of: `org_admin`, `instructor`, `student`, `parent`, `sme_staff`. |
| `created_at` | ISO-8601 UTC | Automatically set on creation. |
| `updated_at` | ISO-8601 UTC | Automatically refreshed on save. |

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.3.2 Retrieve role assignment

```
GET /api/v1/organizations/{organization_id}/memberships/{membership_id}/roles/{role_id}/
```

**Response — 200 OK:** single role assignment resource.

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.3.3 Create role assignment

```
POST /api/v1/organizations/{organization_id}/memberships/{membership_id}/roles/
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `role_code` | enum | Yes | One of: `org_admin`, `instructor`, `student`, `parent`, `sme_staff`. |

**Constraints:** one assignment per `(user_profile_id, role_code)`; duplicates rejected with `400`.

**Response — 201 Created:** single role assignment resource.

**Errors:** `401`, `400` (malformed selector, duplicate role, invalid role_code), `403`, `404`, `500`.

#### 5.3.4 Delete role assignment

```
DELETE /api/v1/organizations/{organization_id}/memberships/{membership_id}/roles/{role_id}/
```

**Response — 204 No Content:** successful deletion.

**Errors:** `401`, `400`, `403`, `404`, `500`.

### 5.4 SubscriptionLicense endpoints

A `SubscriptionLicense` represents one product entitlement for one organization. AI entitlement fields apply only to `AI_PRO` product code.

#### 5.4.1 List licenses

```
GET /api/v1/organizations/{organization_id}/licenses/
```

**Response — 200 OK:** list of license resources.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | UUID | License primary key. |
| `organization_id` | UUID | FK to `Organization.id`. |
| `product_code` | enum | Yes | One of: `EDTECH_LMS`, `CRM_BASIC`, `AI_PRO`. |
| `seat_capacity` | integer | Yes | Must be ≥ 1. |
| `status` | enum | Yes | One of: `pending`, `active`, `expired`, `suspended`, `cancelled`. |
| `moodle_cohort_id` | string (max 255) | No | Nullable; opaque external Moodle cohort reference. |
| `ai_monthly_interaction_allowance_per_learner_seat` | integer | AI_PRO only | Configured monthly interaction entitlement per learner seat. |
| `ai_daily_interaction_cap_per_learner_seat` | integer | AI_PRO only | Configured daily interaction cap per learner seat. |
| `valid_until` | ISO-8601 UTC | No | Nullable entitlement validity boundary; not a lifecycle substitute. |
| `created_at` | ISO-8601 UTC | Automatically set on creation. |
| `updated_at` | ISO-8601 UTC | Automatically refreshed on save. |

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.4.2 Retrieve license

```
GET /api/v1/organizations/{organization_id}/licenses/{license_id}/
```

**Response — 200 OK:** single license resource.

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.4.3 Create license

```
POST /api/v1/organizations/{organization_id}/licenses/
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `product_code` | enum | Yes | One of: `EDTECH_LMS`, `CRM_BASIC`, `AI_PRO`. |
| `seat_capacity` | integer | Yes | Must be ≥ 1. |
| `status` | enum | Yes | One of: `pending`, `active`, `expired`, `suspended`, `cancelled`. |
| `moodle_cohort_id` | string (max 255) | No | Nullable external reference. |
| `ai_monthly_interaction_allowance_per_learner_seat` | integer | AI_PRO only | Required for `AI_PRO`. |
| `ai_daily_interaction_cap_per_learner_seat` | integer | AI_PRO only | Required for `AI_PRO`. |
| `valid_until` | ISO-8601 UTC | No | Nullable validity boundary. |

**Constraints:** at most one current license per `(organization_id, product_code)` pair; duplicates rejected with `400`.

**Response — 201 Created:** single license resource.

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.4.4 Update license

```
PATCH /api/v1/organizations/{organization_id}/licenses/{license_id}/
```

**Request body:** subset of mutable license fields.

**Response — 200 OK:** updated license resource.

**Errors:** `401`, `400`, `403`, `404`, `500`.

#### 5.4.5 Delete license

```
DELETE /api/v1/organizations/{organization_id}/licenses/{license_id}/
```

**Response — 204 No Content:** successful deletion.

**Errors:** `401`, `400`, `403`, `404`, `500`.

## 6. Request flow summary

For each tenant-scoped request:

1. Client sends authenticated request with `X-INOVATX-Organization-Id` header.
2. Django authentication layer validates caller; failure → `401`.
3. Selector syntax validated; missing or non-UUID → `400`.
4. Transaction begins; candidate organization set as transaction-local context.
5. Membership lookup constrained by `(auth_user.id, organization_id)` under RLS.
6. No matching membership → rollback, uniform `404` (no disclosure of organization absence vs. non-membership).
7. Resource/action authorization checked; denied → `403`.
8. Tenant business operation executed within validated context.
9. Transaction commits or rolls back; `SET LOCAL` cleared; connection returned clean.

## 7. Worker context contract (deferred implementation)

Tenant-scoped background workers (Celery) must carry explicit organization context and, for user-originated work, actor/membership identifiers. Each worker execution attempt begins a fresh transaction, establishes its own candidate context, performs membership/provenance validation, revalidates applicable authorization, then performs tenant business operations. Missing or invalid worker context is a permanent failure with no automatic retry.

This contract defers the worker route/payload schema and exact event provenance fields to the Phase 2 worker implementation tasks.

## 8. Error handling specification

Error semantics follow P1.2.3-D1 and P1.2.3-D2:

| Status | Code | Condition | Response content |
|---|---|---|---|
| `401 Unauthorized` | `unauthenticated` | Authentication failed before tenant selection. | Generic message; `correlation_id`; no tenant processing. |
| `400 Bad Request` | `malformed_selector` | Organization selector missing or not a valid UUID. | Generic message; `correlation_id`; no tenant query. |
| `400 Bad Request` | `invalid_body` / `duplicate_resource` | Request body invalid or unique constraint violated (e.g., duplicate membership, duplicate role, duplicate license). | Generic message; `correlation_id`; optional `field`. |
| `404 Not Found` | `not_found` | Organization absent OR user has no membership for selected organization (uniform response). | Generic message; `correlation_id`; does not disclose which condition applied. |
| `403 Forbidden` | `forbidden` | Valid membership but caller lacks required resource/action permission. | Generic message; `correlation_id`; operation does not mutate tenant data. |
| `500 Internal Server Error` | `internal_error` | Internal context invariant failure (tenant business data accessed without validated transaction-local context, or context mismatch). | Generic message; `correlation_id`; sanitized security event recorded; no SQL/database details exposed. |

### 8.1 Correlation identifiers

- Every response includes a `correlation_id` UUID in the body envelope and a response header.
- Correlation IDs are generated server-side and propagated through the request lifecycle.
- The same `correlation_id` appears in the structured security event log for the associated failure.

### 8.2 Observability and security event rules

- Minimal structured security events are emitted for: tenant-selector rejection, membership denial, internal context invariant failure, and invalid worker context.
- Each event records: timestamp, event category, source component, and request/task correlation ID.
- Actor or organization identifiers are included only when validated and needed for investigation.
- Credentials, tokens, full request/task payloads, learner content, raw SQL, and database exception details are never logged.
- Approved audit/security-event retention: 365 days.

### 8.3 Non-disclosure rules

- Responses must not reveal whether an organization exists when the caller lacks a matching membership.
- Cross-tenant reads return the same not-found outcome as an absent resource; cross-tenant writes are rejected by RLS and mapped to generic denial.
- Raw SQL errors, database messages, policy names, task payloads, and secrets are never returned to the client.

## 9. Approved privilege boundary

- No executable tenant middleware is created by this contract.
- No RLS policies are applied by this contract.
- No runtime database grants are made by this contract.
- No production deployment is performed by this contract.
- All endpoints documented here are tenant-scoped; no unscoped or all-tenant endpoints exist in this contract.
- The `system_admin` global role does not bypass tenant context selection or grant tenant-owned data access.

## 10. Traceability mapping

| Contract element | PRD source | UML source | Approved decision |
|---|---|---|---|
| Authentication before tenant selection | §3.2 | §5, §8 | P1.2.1-D1, P1.2.3-D1 |
| Explicit organization UUID selector | §3.2 | §5, §8 | P1.2.1-D1, deferred transport to 1.3.3 |
| `X-INOVATX-Organization-Id` header | §3.2 | §5 | 1.3.3 transport decision |
| Membership validation under RLS | §3.2 | §5 | P1.2.1-D1, P1.2.3-D1 |
| Uniform 404 for absent org / no membership | §3.2 | §5 | P1.2.3-D1 |
| `system_admin` not a tenant role | §6.1 FR-04/FR-05 | §1, §6 | P1.2.1-D4 |
| Error semantics 401/400/404/403/500 | §3.2, FR-05 | §5 | P1.2.3-D1, P1.2.3-D2 |
| Correlation IDs on errors | NFR-01, §7 | §7 | P1.2.3-D2 |
| Organization endpoint schemas | PRD §3.1 ERD | UML §5 ERD | Task 1.1.1 |
| UserProfile endpoint schemas | PRD §3.1 ERD | UML §5 ERD | Task 1.1.1 |
| OrganizationMembershipRole endpoint schemas | PRD §3.1 ERD | UML §5 ERD | Task 1.1.1 |
| SubscriptionLicense endpoint schemas | PRD §3.1 ERD | UML §5 ERD | Task 1.1.1 |
| Enum values (org_type, role_code, product_code, status) | §3.1 | UML §5 | Task 1.1.2 taxonomy |
| AI entitlement fields apply only to AI_PRO | §3.1 | UML §5 | Task 1.1.2 D17 |

## 11. Completion decision

Task 1.3.3 deliverable is complete as a documented contract:

- Endpoint schemas defined for Organization, UserProfile, OrganizationMembershipRole, and SubscriptionLicense.
- Authentication flow and tenant context selection documented per P1.2.1-D1 and P1.2.3-D1.
- Error handling specified per P1.2.3-D1: 401, 400, 404, 403, 500 with correlation identifiers.
- Approved privilege boundary preserved: no RLS, no tenant middleware, no runtime grants, no production deployment.
- No routes, middleware, views, serializers, or executable implementation created by this task.
- Later API implementation, tenant isolation, RBAC, and deployment work remain outside this task.

**Contract documented:** 2026-10-28  
**Completion review:** pending
