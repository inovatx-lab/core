# Task Traceability — 1.2.3 Tenant Fail-Closed Policy

**Task ID and title:** 1.2.3 — Define fail-closed behavior for missing tenant context
**Phase / activity:** Phase 1 / Activity 1.2
**Owner:** Project owner and technical/security owner
**Status:** In progress — policy approved; implementation tests blocked on application/database environment

## Outcome and sources

**Outcome / deliverable:** A tenant failure policy and focused verification matrix that prevent tenant-owned operations when request or worker context is missing, malformed, unauthorized, or internally invalid.

**PRD sources:**
- §3.2: explicit request/worker context, `SET LOCAL`, RLS plus application validation, and fail-closed behavior.
- FR-05: membership-based authorization distinct from resource/action permission.
- NFR-01: zero cross-tenant access and PostgreSQL RLS boundary tests.
- NFR-03: bounded retries for transient webhook/Moodle failures; context errors must not be treated as transient infrastructure failures.

**UML sources:**
- §5 ERD: multi-organization user memberships and tenant-owned entities.
- §6 class view: Django Core and Celery worker responsibilities.
- §8 cloud architecture: application/database trust boundary.

**Approved design sources:**
- Task 1.2.1 tenant-context specification and Task 1.2.2 RLS decisions P1.2.2-D1–D5.
- Project-owner/technical-security-owner-confirmed Task 1.2.3 failure-policy decisions P1.2.3-D1–D6, confirmed 2026-10-25.
- Phase 1 authorization covers Task 1.2.3; API transport/schema remains assigned to Task 1.3.3 and database policies to Task 1.2.2.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django request authorization, Celery execution, and PostgreSQL RLS boundary. This task defines behavior and verification expectations; it does not create a runtime implementation.

## Acceptance criteria

1. Distinguish authentication failure, missing/malformed organization selector, unmatched membership, resource/action denial, internal context invariant failure, and invalid worker context.
2. Define deny behavior with no default organization, cross-tenant fallback, implicit global-admin access, or existence disclosure.
3. Define transaction rollback, sanitized responses/logging, and non-retry behavior for permanent tenant-context/authorization failures.
4. Define a focused test matrix covering requests, workers, RLS interactions, write rejection, and transaction/connection reuse.
5. Preserve transient retries only under their approved policy and require context to be re-resolved and revalidated on each attempt.
6. Record the policy and update the roadmap/security documentation without claiming implementation or tests that have not run.

## Scope

**In scope:** Documentation of request and worker failure semantics, boundary between tenant membership and action authorization, sanitized operational/security events, retry classification, and focused implementation test cases.

**Out of scope:** Django middleware/API implementation, authentication implementation, selector transport and serialized error schema, full RBAC policy, database role/grant design, RLS policy implementation, production alert thresholds, and deployment.

## Approved decisions and dependencies

- An unauthenticated request is rejected by the authentication layer (`401`); tenant selection is not evaluated first.
- A missing or malformed UUID selector is a client request error (`400`) before tenant-owned data access.
- An absent organization and an organization for which the authenticated user has no matching membership return the same `404` outcome; do not reveal organization existence or fall back to another membership.
- A member denied a specific resource/action receives an authorization denial (`403`); the role/resource/action matrix remains with its assigned task. Exact API error serialization remains for Task 1.3.3.
- Because `UserProfile` is protected by RLS, after authentication and selector syntax validation establish the selected organization as candidate transaction-local context, then perform only the matching authenticated-user/organization membership lookup. No tenant business-data access occurs until membership is verified.
- Missing or inconsistent internal transaction-local context is an invariant failure: stop tenant access, roll back, return a generic `500` at the HTTP boundary, and emit a sanitized event with a correlation identifier.
- Missing, mismatched, or no-longer-authorized worker context is a permanent task failure with no automatic retry and no tenant-owned operation. Use the task's existing terminal/dead-letter handling where applicable. Transient infrastructure failures follow their already-approved retry policy and revalidate context on every attempt.
- Emit minimal structured security events for tenant-context denials and invariant failures. Include a correlation/request/task ID, event category, timestamp, source component, and actor/organization identifiers only when validated and needed. Do not log credentials, tokens, full request/task payloads, learner content, raw SQL, or database exception details. Follow the approved audit/security-event retention.
- The approved custom-GUC RLS boundary does not independently protect against arbitrary SQL executed with a compromised runtime credential; the response policy must not overstate that guarantee.

## Evidence and completion

**Evidence:**
- Check or artifact: Tenant failure policy, this traceability record, aligned decision/source updates, and documentation validation.
- Result: Policy documentation and test matrix approved by project owner/technical-security owner on 2026-10-25. No middleware, database, or runtime tests have been implemented or run.
- Location: `inovatx_tenant_failure_policy.md`, `inovatx_task_1_2_3_traceability.md`, and directly referenced project sources.
- Validation boundary: The repository currently has no Django project or PostgreSQL test environment. Tests described in the policy are acceptance cases, not executed evidence.

**Completion decision:** Policy approved; task completion remains pending implementation of the focused tests in an available Django/PostgreSQL environment.
**Reviewer / approver and date:** Project owner/technical-security owner approved the policy documentation on 2026-10-25; test evidence pending.
