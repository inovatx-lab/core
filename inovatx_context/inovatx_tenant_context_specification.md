# Tenant Context Specification — Task 1.2.1

**Roadmap task:** 1.2.1 — Define tenant context strategy for requests and workers
**Phase / activity:** Phase 1 / Activity 1.2
**Status:** Approved by project owner on 2026-10-25; RLS-compatible membership-validation ordering clarified under P1.2.3-D5 on 2026-10-25
**Traceability:** [Task 1.2.1 traceability record](inovatx_task_1_2_1_traceability.md)
**Sources:** PRD §3.2, FR-05, NFR-01, NFR-03; UML §§5–6, 8; Task 1.1.1 domain model and decision P1.1.1-D1; Phase 0 exit review.

## 1. Purpose and boundary

This specification defines how tenant context is selected, validated, propagated, and bounded for Django requests and Celery work. It is a design contract, not existing tenant-aware application behavior. The repository now has a minimal Django project and PostgreSQL-only settings from Task 1.3.1, but no tenant middleware, worker implementation, domain models, or RLS policy implementation.

The context identifies one organization for a tenant-scoped operation. It is not a substitute for authentication, membership validation, or resource/action authorization. It does not grant a user, worker, or global administrator permission to access data merely because an organization identifier is present.

## 2. Context invariants

1. Tenant context is explicit for every operation on tenant-owned data.
2. A tenant identifier is a selector, not proof of authorization.
3. A user's context is resolved through that authenticated user's `UserProfile` membership for the selected organization. Do not assume the global login has one implicit profile or default organization.
4. Missing, malformed, or unauthorized context must fail closed; never fall back to an unscoped query or another/default tenant.
5. Tenant context is transaction-local. Do not retain it in connection- or session-scoped database state.
6. Context is re-established independently for each request transaction and each worker execution attempt; no ambient request, thread-local, process-global, or previously borrowed connection state is a source of tenant identity.

## 3. Authenticated request contract

For a tenant-scoped request, the application must:

1. Authenticate the caller before resolving tenant context.
2. Require an explicit organization UUID selector and validate its syntax. Treat the value as an untrusted candidate, not proof of membership or permission.
3. Begin the transaction and set the candidate organization as transaction-local database context. This is necessary because the membership table itself is protected by RLS.
4. Perform only the membership-validation lookup, constrained by both the authenticated user ID and candidate organization ID. RLS further limits the lookup to the candidate organization. Do not query tenant business data at this stage.
5. If no matching membership exists or the lookup cannot be validated, stop and roll back using the approved failure policy; do not fall back to another organization or an unscoped query.
6. Apply the authorization rule for the requested resource and action. Membership selection alone is not permission.
7. Only after membership and applicable authorization succeed may the request access tenant business data. Keep that work within the transaction where context was established. Transaction completion clears the `SET LOCAL` value; request teardown must also leave the borrowed connection in a clean state.

The request selector's transport is defined in the [Core API contract](inovatx_core_api_contract.md) as the `X-INOVATX-Organization-Id` HTTP header. Whichever transport is selected, it must identify one organization and pass through the same authenticated membership validation; no transport value is trusted as authorization.

The PRD does not define a membership status field. This task therefore requires a matching membership record and applicable approved authorization checks, but does not invent additional membership lifecycle rules.

## 4. Background worker contract

Every tenant-scoped task must carry an explicit `organization_id`. A worker must establish its context from that task's own validated inputs, not from the request that enqueued it, a shared thread, a process-global variable, or a connection's prior state.

For user-originated work, the task context must preserve the initiating user and membership identifiers when applicable. At execution, the worker begins a fresh transaction, sets the explicit organization as candidate context, then performs only the membership lookup constrained by the supplied user, membership, and organization identifiers. It revalidates applicable authorization before tenant business operations. Payload identity is not authorization. If membership or applicable authorization cannot be validated, the task must stop and perform no tenant business operation.

For system- or event-originated work, the task must preserve explicit event/task provenance and its target organization. Before tenant business operations, the task must validate its provenance and applicable task authority under the relevant approved integration contract. This task does not define a service-principal model, broker authentication mechanism, or database role. Those mechanisms must not be inferred from the presence of an event identifier or organization UUID.

Each worker execution attempt must establish transaction-local tenant context before tenant-owned database access. Retries start with fresh context resolution and transaction state; they must not reuse a tenant setting from a previous attempt.

## 5. Global administrator and organization assistance boundary

The global `system_admin` role does not by itself grant access to tenant-owned data and does not create an implicit all-tenant context. A `system_admin` operation on tenant-owned data still requires an explicit target organization and the applicable authorization.

If assistance requires access beyond the organization's normal roles and permissions, the system administrator must request access from that organization. This task does not define the request, approval, grant, scope, duration, revocation, or audit workflow. No support or impersonation access may be inferred or implemented from this specification alone.

## 6. Database context and RLS boundary

The PRD specifies `SET LOCAL app.current_organization_id` for tenant context. The setting must be made within the transaction that performs tenant-owned database work and before the first such query. A connection-scoped or session-scoped tenant setting is not an acceptable substitute.

RLS is defense in depth alongside application authorization. Task 1.2.2 decisions approve a controlled setup-only bootstrap authority, a `NOLOGIN` schema/object owner, a controlled migration identity, and one shared least-privileged runtime identity for Django/Celery. They also approve strict RLS coverage of the four initial Core tenant tables with both row-visibility and write-check predicates. Exact identifiers and executable expressions depend on the Django model schema. The PRD's `student_data` and `inovatx_app_role` are illustrative examples, not approved identifiers.

The runtime identity can set a PostgreSQL custom GUC, so `SET LOCAL app.current_organization_id` does not independently protect against arbitrary SQL executed with a compromised runtime credential. The approved design retains this context mechanism for defense in depth on normal application paths and requires that its limitation be stated accurately.

The RLS design is approved; executable role/grant setup, policies, and tests remain pending until the Django schema and PostgreSQL test environment are available. They must be implemented and verified under the runtime identity before Task 1.2.2 is complete.

This document specifies the tenant-context contract at the application/database boundary only; it neither creates nor applies an RLS policy.

## 7. Failure and authorization dependencies

- Missing, invalid, or unauthorized tenant context blocks tenant-owned reads and writes. No default organization, global-admin bypass, or unscoped fallback is permitted.
- Task 1.2.3 defines the detailed fail-closed policy, including failure handling and observable behavior.
- The route/header/session carrier is deferred to Task 1.3.3.
- The detailed resource/action permission matrix and role policy are outside Task 1.2.1. A worker must not execute a user-originated operation if the applicable approved authorization decision cannot be made at execution time.
- The bootstrap, application-role, and RLS policy design is approved in Task 1.2.2 decisions. Executable implementation remains blocked on the Django schema and PostgreSQL test environment.
- The organization assistance workflow for any access beyond normal roles remains undefined and requires separate approval before implementation.

## 8. Implementation acceptance checks

When the middleware and worker contracts are implemented by their authorized tasks, verification must demonstrate:

- a user with multiple memberships can select only an organization for which that authenticated user has a matching membership;
- a missing or invalid organization selector cannot reach tenant-owned data;
- a worker task cannot obtain tenant context from another request, task, thread, or prior connection use;
- a user-originated queued task is denied if its membership or applicable authorization is no longer valid at execution;
- every tenant-scoped worker attempt explicitly establishes its organization context;
- `system_admin` role alone does not permit tenant-owned access or bypass the explicit target-organization requirement; and
- transaction completion prevents tenant context from leaking into later work on a reused connection.

These are required future implementation checks, not tests run or evidence claimed by this documentation task.
