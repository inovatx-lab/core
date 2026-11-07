# Task Traceability — 3.1.1 Moodle User Provisioning Contract

**Task ID and title:** 3.1.1 — Define Moodle user provisioning contract  
**Phase / activity:** Phase 2 / Activity 3.1  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A documented Moodle user provisioning contract specifying the Moodle REST API endpoints (`core_user_create_users`, `core_cohort_create_cohorts`, `core_cohort_add_cohort_members`), payload schema, organization-type branching logic (institutional vs individual), sync flow from Django → Moodle → Django, idempotency, retry, and error handling. This is a documentation contract only — no Celery tasks, Django views, Moodle API client code, or runtime enforcement is created by this task.

**PRD sources:**
- §4.1: Single Sign-On & User Provisioning Lifecycle — Django fires async Celery task to execute Moodle REST API (`core_user_create_users`); institutional accounts use `core_cohort_create_cohorts` + `core_cohort_add_cohort_members`; individual subscriptions enroll users into standard course groups.
- §4.2: Sync Protocol — Moodle sends completion/grade sync webhook back to Django.
- §4.1: Registration & Payment lifecycle — register at app.inovatx.com, complete payment via gateway.

**UML sources:**
- §2 BPMN: Sequence flow from Register → CompletePayment → ProcessPayment → SendReceipt → ReceiveReceipt → Enqueue → ProvisionUser → CreateMoodleUser → OrgType → CreateCohort/AddMembers (institutional) OR IndividualGroup (individual) → IssueJWT → Launch → ValidateJWT → CreateSession → Learn → CourseQuiz → SubmitAnswer → SendAIContext → Socratic → Stream → PresentFeedback → CourseQuiz → SendGrade → CompletionWebhook → End.
- §4 State Machine: Moodle provisioning states.

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only; Phase 3 authorization permits Tasks 3.1.1–3.3.3 effective 2026-10-31.
- Decision log D6: Webhook retry cap (max 5 retries, exponential backoff 5s/15s/45s/2m/6m); dead-letter queue (`webhook_dlq`).
- Decision log D7: Idempotency key per-endpoint with 24-hour TTL.
- Decision log D8: License activates on `succeeded` webhook; `failed`/`expired` triggers license suspension; daily batch reconciliation; 24-hour grace period.
- P1.2.3-D1: Request error semantics — 401 (unauthenticated), 400 (malformed selector), 404 (absent org or no matching membership), 403 (member denied), 500 (internal context invariant failure).
- P1.2.3-D2: Internal context invariant failure — stop, roll back, generic response with correlation ID.

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core provisioning boundary → Moodle LMS via REST API. This task creates no public route, Celery task, or runtime service. The contract defines the interface that Task 3.2.1 (Celery task for Moodle user creation) will implement.

## Acceptance criteria

1. Document Moodle API endpoints: `core_user_create_users`, `core_cohort_create_cohorts`, `core_cohort_add_cohort_members` with payload schemas
2. Define institutional vs individual org type provisioning paths
3. Specify idempotency key scope (per-endpoint, 24-hour TTL)
4. Specify retry policy: max 5 retries, exponential backoff intervals (5s, 15s, 45s, 2m, 6m)
5. Define dead-letter queue handling for terminal webhook failures
6. Define error semantics for provisioning conditions (400/403/404/500)
7. Reference approved decisions (PRD §4.1/FR-02, UML §2, Decision log D6/D7/D8)
8. No runtime implementation created — contract documentation only

## Scope

**In scope:** License lifecycle policy document; state machine definition; payment decoupling rules; transition guards; error semantics; directly related project documentation.

**Out of scope:** Celery task implementation; Moodle API client code; webhook handler views; license activation on payment (Task 2.2.3); Moodle provisioning on activation (this task's contract only); production deployment; additional domain entities.

## Approved implementation decisions

- The contract documents the interface only. No Celery tasks, Django views, or runtime enforcement is created by this task.
- Provisioning is triggered by `payment.succeeded` webhook → license `pending` → `active` (Task 2.2.3/Task 2.2.4).
- Institutional org types (`school`, `sme`, `ngo`, `enterprise`): create cohort → add members → issue JWT.
- Individual org type (`individual`): enroll in standard course group → issue JWT.
- `system_admin` is not provisioned to Moodle (not a membership role).
- Idempotency key per-endpoint with 24-hour TTL (D7).
- Max 5 retries with exponential backoff (5s, 15s, 45s, 2m, 6m); dead-letter to `webhook_dlq` (D6).
- Organization-scoped: `organization_id` must match user's membership (P1.2.1-D1).
- No secrets or signing keys included in the contract document.

## Evidence and completion

**Evidence:**
- Check or artifact: License lifecycle policy document, traceability record, roadmap update.
- Result: `inovatx_context/inovatx_moodle_provisioning_contract.md` documents all license states, allowed/prohibited transitions, payment decoupling, transition guards, error semantics, and references all approved design decisions. No executable state machine or runtime implementation created.
- Location: `inovatx_context/inovatx_moodle_provisioning_contract.md`, `inovatx_context/inovatx_task_3_1_1_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: This is a documentation-only task. No database, server, or runtime validation is required or claimed. The contract is a specification for Task 3.2.1 (Celery task for Moodle user creation).

**Completion decision:** Complete. All Task 3.1.1 deliverables implemented as a documented provisioning contract. No executable state machine, Celery task, or production deployment are included. Task 3.2.1 (Celery task for Moodle user creation) will implement the `payment.succeeded` → license activation transition based on this contract.

**Reviewer / approver and date:** Contract documented 2026-10-31; completion review pending.
