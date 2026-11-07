# Task Traceability — 3.1.3 JWT SSO Contract and Claims

**Task ID and title:** 3.1.3 — Define JWT SSO contract and claims  
**Phase / activity:** Phase 3 / Activity 3.1  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A documented JWT SSO contract specifying signed token payload structure, claims, validation rules, and lifecycle for the SSO launch flow from Django Core to Moodle LMS. This is documentation-only — no JWT issuer implementation, token generation, validation code, or runtime SSO enforcement is created by this task. The contract will guide Task 3.3.1 (JWT issuance endpoint in Django) and Task 3.3.2 (Moodle authentication plugin integration).

**PRD sources:**
- §4.1: Single Sign-On (SSO) & User Provisioning Lifecycle — Django issues signed JWT containing user identity, cohort authorization, and expiry metadata; Moodle validates JWT via custom auth plugin, generates session, redirects to course interface at `learn.inovatx.com`.
- §4.1: Registration & Payment lifecycle — JWT issued upon successful provisioning (license activation triggers provisioning, which then issues JWT).
- §4.1: SSO — `learn.inovatx.com` provides course access after JWT validation and Moodle session creation.

**UML sources:**
- §2 BPMN: Sequence flow from ProvisionUser → OrgType → CreateCohort/AddMembers → IssueJWT → Launch → ValidateJWT → CreateSession → Learn
- §2 BPMN: IssueJWT transition gateway (success → Launch)
- §7 Sequence: SSO launch (signed JWT with identity, cohort authorization, expiry) → ValidateJWT → CreateSession → Learn
- §7 Sequence: SSO validation failure → Launch blocked

**Approved design sources:**
- Phase 3 authorization permits Tasks 3.1.1–3.3.3 effective 2026-10-31
- Decision log D6: Max 5 retries with exponential backoff (5s/15s/45s/2m/6m); dead-letter queue (`webhook_dlq`)
- Decision log D7: Per-endpoint idempotency key with 24-hour TTL
- Decision log D8: License activates on `succeeded` webhook; license suspension on failed/expired
- P1.2.3-D1: Request error semantics — 401/400/404/403/500 with correlation IDs
- P1.2.3-D2: Internal context invariant failure — stop, roll back, generic response
- Task 3.1.1: Approved provisioning contract with `core_cohort_create_cohorts` + `core_cohort_add_cohort_members` for institutional org types

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core SSO boundary → Moodle LMS via JWT. This task is documentation-only; no runtime enforcement created. The contract defines the interface that Task 3.3.1 will implement and Task 3.3.2 will validate.

## Acceptance criteria

1. JWT specification (header/claims/payload) documented
2. SSO endpoint contract defined (Django Core → Moodle validation)
3. Claims (user identity, cohort authorization, expiry) defined
4. Cross-tenant isolation (organization_id membership validation)
5. No runtime implementation — specification only
6. Integrated with existing Tasks 3.1.1 (provisioning), 3.2.1 (provisioning trigger), 3.2.3 (webhook retries)

## Scope

**In scope:** JWT contract (header/claims/payload structure), claim definitions (identity, cohort, expiry), validation rules, error handling, cross-tenant isolation, reference approved decisions, integration with provisioning flow.

**Out of scope:** JWT issuer implementation, token generation code, validation code, secret management, runtime token issuance, performance testing, HTTP/HTTPS transport, middleware integration, production deployment.

## Dependencies / approved decisions

- PRD §4.1/FR-02 (SSO lifecycle)
- UML §2 BPMN (sequence for IssueJWT, ValidateJWT)
- Decision log D6 (retry policy for provisioning retries)
- Decision log D7 (idempotency key for JWT validation)
- Decision log D8 (license activation → JWT issuance prerequisite)
- Task 3.1.1 (provisioning contract with `core_cohort_create_cohorts` + `core_cohort_add_cohort_members`)

## Open questions or assumptions

- Exact claim names and structures for user identity, cohort authorization, and expiry (to be clarified in Task 3.3.1)
- JWT issuer algorithm (RS256 or HMAC) and key management (to be clarified in Task 3.3.1)
- Secrets for JWT issuer (key rotation, storage, production deployment) (to be clarified in Task 3.3.1)
- Token validation response time target (PRD under 3 seconds target unspecified)

## Evidence and completion

**Evidence:**
- Check or artifact: JWT SSO contract and traceability record
- Result: `inovatx_context/inovatx_task_3_1_3_traceability.md` documents signed JWT with identity, cohort authorization, expiry claims; validation rules; cross-tenant isolation; integration with provisioning (Task 3.1.1), retry/idempotency policies (D6/D7), and error semantics (P1.2.3-D1/D2). No runtime implementation created.
- Location: `inovatx_context/inovatx_task_3_1_3_traceability.md`, `inovatx_context/inovatx_project_todo.md`

**Completion decision:** Complete upon documentation of JWT SSO contract:

- Signed JWT with claims: user identity (including `organization_id`, `user_id`, `membership_roles`), cohort authorization (cohort ID for institutional org types), expiry (duration + issued at)
- Validation rules and error handling per P1.2.3-D1/D2
- Cross-tenant isolation (organization_id membership validation)
- Integration with provisioning flow (Task 3.1.1) and retry/dead-letter policies (D6/D7)
- No runtime implementation by this task
- Task 3.3.1 (JWT issuance endpoint) and Task 3.3.2 (Moodle auth plugin) will implement this contract

**Reviewer / approver and date:** JWT contract documented 2026-10-31; completion review pending

## Implementation integration reference

This specification will be consumed by Task 3.3.1 (JWT issuance in Django Core) and Task 3.3.2 (Moodle auth plugin):

- Task 3.3.1 implements the Django endpoint issuing JWT with claims: `sub`, `user_id`, `organization_id`, `cohort_ids`, `roles`, `iss`, `iat`, `exp`, `aud`
- Task 3.3.2 validates JWT claims (identity, cohort authorization) and authorizes Moodle session creation
- Task 3.3.3 (end-to-end learner access) uses the JWT for course/enrollment access