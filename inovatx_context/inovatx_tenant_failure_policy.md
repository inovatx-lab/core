# Tenant Failure Policy — Task 1.2.3

**Roadmap task:** 1.2.3 — Define fail-closed behavior for missing tenant context
**Phase / activity:** Phase 1 / Activity 1.2
**Status:** Approved by project owner/technical-security owner on 2026-10-25; implementation tests remain pending
**Traceability:** [Task 1.2.3 traceability record](inovatx_task_1_2_3_traceability.md)
**Sources:** PRD §3.2, FR-05, NFR-01, NFR-03; UML §§5–6, 8; approved Task 1.2.1 context contract; approved Task 1.2.2 RLS design.

## 1. Purpose and boundary

This policy defines how requests and workers fail when tenant context is absent, malformed, unauthorized, or inconsistent. It prohibits default-tenant behavior, unscoped fallback, and disclosure of another organization's existence.

This is a behavior specification and future test matrix, not middleware, worker, API, or RLS implementation. The exact selector transport and response schema are defined in the [Core API contract](inovatx_core_api_contract.md). The Task 1.3.1 Django project and local PostgreSQL environment are now reported operational, but tenant middleware, workers, and domain models remain unimplemented; the cases below are acceptance criteria, not tests claimed to have run.

## 2. Request decision policy

Process tenant-scoped requests in this order:

1. **Authenticate first.** If authentication fails, return the authentication layer's `401` response without evaluating tenant selection.
2. **Validate the selector syntax.** A missing or malformed organization UUID returns `400` before tenant-owned database access.
3. **Establish candidate context.** Begin a transaction and set the syntactically valid organization UUID as transaction-local candidate context. The selector is untrusted and is not authorization.
4. **Perform only the membership-validation lookup.** Query for a `UserProfile` matching both the authenticated user's ID and selected organization ID, under the candidate context and RLS. No tenant business-data query is allowed until this lookup succeeds.
5. **Deny unmatched membership uniformly.** If no matching membership exists—whether the organization is absent or the user is not a member—roll back and return the same `404` outcome. Do not reveal which condition applied and do not select another membership or default organization.
6. **Authorize the requested action.** A member who lacks the required resource/action permission receives `403`. Membership alone does not authorize an action; the role/resource/action matrix remains outside this task.
7. **Access tenant business data only after validation.** Keep all tenant operations in the transaction with the validated candidate context. Transaction end clears `SET LOCAL`.

The initial application may use a minimal membership lookup before tenant business access because the `UserProfile` table itself is RLS-protected. The lookup must constrain both user and organization. This does not authorize any other tenant query; it is not an unscoped exception.

## 3. Internal context and database failures

- If application code reaches tenant business data without an established transaction-local context, or the effective context differs from the validated organization, stop processing and roll back the unit of work. Return a generic `500` response with a correlation ID; do not expose SQL, policy, or database details.
- Missing context at the RLS layer must match no rows and reject writes. A malformed database context must error and fail closed; it must never be replaced with a default or unscoped query.
- A read of a resource not visible under the selected tenant returns the same not-found outcome as an absent resource. A write rejected by an RLS policy is rolled back and mapped to a generic access-denied response without exposing policy details. Unexpected database failures remain server errors and must not be silently converted into success or authorization.
- No broad database-error catch or retry may mask a missing-context invariant failure. Error classification and exact API serialization are implemented with their assigned application/API tasks.

## 4. Worker decision policy

- Every tenant-scoped task must contain explicit organization context and required event/task provenance. User-originated work must preserve the actor and membership identifiers when applicable.
- At execution, start a fresh transaction and establish candidate context from the explicit organization identifier. Perform only the required membership/provenance validation before tenant business operations.
- Missing or malformed organization context, missing required provenance, mismatched actor/membership/organization, or no-longer-valid membership/authorization is a permanent context/authorization failure. Do not perform tenant business operations and do not automatically retry it. Use the task's already-defined terminal failure/dead-letter mechanism where applicable; do not invent new lifecycle states in this task.
- Transient infrastructure failures may use their approved retry/backoff policy. Every attempt must start with clean transaction state and rebuild/revalidate its context before tenant business operations.
- System/event tasks must pass their applicable approved provenance/authority validation. An event ID or organization UUID alone is not proof of authorization.

## 5. Response and observability rules

Responses must not reveal whether an organization exists when the caller lacks a matching membership. Client-facing errors must be generic and include a correlation ID where available; do not return raw SQL errors, database messages, policy names, task payloads, or secrets.

Emit minimal structured security events for tenant-selector rejection, membership denial, internal context invariant failure, and invalid worker context. Record the timestamp, event category, source component, and request/task correlation ID. Include actor or organization identifiers only when validated and needed for investigation. Do not log credentials, tokens, full request/task payloads, learner content, raw SQL, or database exception details. Apply the approved 365-day audit/security-event retention; this policy does not define new alert thresholds.

## 6. Verification matrix

These cases must be implemented in focused request, worker, and PostgreSQL integration tests when the authorized Django application and database environment exist. “Expected” describes the required outcome; no test execution is claimed here.

| Case | Setup | Required outcome |
|---|---|---|
| Unauthenticated request | No authenticated user; tenant selector present or absent | Authentication returns `401`; no tenant selection or tenant query occurs. |
| Missing selector | Authenticated request with no organization selector | `400`; no tenant-owned query occurs. |
| Malformed selector | Authenticated request with non-UUID selector | `400`; no tenant-owned query occurs. |
| Organization absent or membership absent | Valid UUID with no matching user/organization membership | Only the candidate-scoped membership lookup occurs; transaction rolls back; same `404` response in both cases; no tenant business query occurs. |
| Valid membership | User has a matching membership | Context remains limited to selected organization; resource/action authorization is still required before the operation. |
| Resource/action denied | Valid membership but permission is absent | `403`; denied operation does not mutate tenant data. |
| Missing internal context | Tenant business operation is attempted without validated transaction context | Operation is blocked, transaction rolls back, generic `500` with correlation ID; sanitized internal event is recorded; no unscoped fallback. |
| Cross-tenant read | Request selects tenant A and attempts to address tenant B's row | RLS returns no visible row; response does not reveal whether the row exists. |
| Cross-tenant write | Insert/update attempts a row whose organization differs from context | RLS rejects the write; transaction rolls back; generic denial; no partial mutation or database detail is returned. |
| Reused connection | A tenant-A transaction completes, then a tenant-B or context-free operation uses a pooled connection | No tenant-A context is inherited; tenant-B sees only its own rows, and context-free access remains denied. |
| Invalid worker identifiers/provenance | Organization or required actor/event provenance is absent or mismatched | No tenant business operation; permanent failure; no automatic retry; sanitized event recorded. |
| Revoked worker membership | User-originated task membership/authorization is no longer valid at execution | Validation fails before tenant business operations; permanent failure; no automatic retry. |
| Transient worker failure | A retryable infrastructure failure occurs | Approved retry policy may run; each attempt starts clean and revalidates context before tenant business work. |
| Global administrator | `system_admin` has no organization membership or organization-approved access | No implicit cross-tenant row access; access is denied without an all-tenant fallback. |

RLS policy behavior and runtime-role privilege checks are also covered by Task 1.2.2's required actual-schema suite. Passing fixture-only checks is not sufficient to close either task.

## 7. Dependencies and remaining boundaries

- Task 1.2.2 owns the approved PostgreSQL RLS and role baseline; it remains blocked until the Django schema and PostgreSQL test environment exist.
- The route/header/session selector carrier and exact API error envelope are defined in the [Core API contract](inovatx_core_api_contract.md).
- The resource/action permission matrix remains outside this task. This policy does not grant permissions to any role.
- The approved `SET LOCAL` custom-GUC mechanism is not an independent defense against arbitrary SQL under a compromised runtime credential; do not state otherwise.
- Global CRM directory access remains a separate organization-authorized access decision; this policy creates no system-admin exception.
- Executable middleware, worker tests, RLS tests, and runtime verification remain pending until the relevant application and database environment are available.
