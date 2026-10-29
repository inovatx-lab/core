# Task Traceability — 2.2.2 Payment State and Event Model

**Task ID and title:** 2.2.2 — Define payment state and event model  
**Phase / activity:** Phase 2 / Activity 2.2  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A documented payment state machine and payment event contract specifying payment status values (`pending`, `succeeded`, `failed`, `cancelled`), payment event types and versioned signed payload schema, webhook security requirements (signature, idempotency, replay protection), retry/dead-letter policy, and error semantics. This is a documentation contract only — no Django model changes, payment gateway integration, or webhook handlers are created by this task.

**PRD sources:**
- §6.1: FR-02 (payment receipt triggers Moodle provisioning), FR-06 (Subscription & Payment Lifecycle — distinguish org status, license status, payment status)
- §6.2: NFR-03 (High Availability — automatic retries with exponential backoff for failed payment webhooks), NFR-04 (Integration Contracts & Webhooks — signed webhooks, idempotency checks, replay protection, dead-letter handling)
- §7 Approved Decisions #2/#3: License status separate from payment status; separate state machines for subscriptions and payments
- §7 Approved Decision #7: Webhook Contracts — signed, versioned webhook payloads with event IDs, timestamps, idempotency keys, replay protection

**UML sources:**
- §2 BPMN: Payment receipt as trigger for asynchronous provisioning; retry gate for webhook failures
- §4 State Machine: Payment.status modeled as `pending`, `succeeded`, `failed`, `cancelled` with event log
- §7 Sequence Diagram: Payment flow/webhooks between Django and external payment gateways
- §8 Cloud Architecture: Django payment flow/webhooks to external payment gateways

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only.
- Decision log D6: Webhook retry cap and dead-letter handling (max 5 retries, exponential backoff 5s/15s/45s/2m/6m, `webhook_dlq` table)
- Decision log D7: Idempotency key scope and TTL (per-endpoint, 24-hour TTL)
- Decision log D8: Payment reconciliation (license activates on `succeeded` webhook; `failed`/`expired` triggers license suspension; daily batch reconciliation; 24-hour grace period)
- P1.2.1-D1: Explicit organization selection and tenant context validation

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core payment processing boundary. This task creates no public route, webhook handler, or runtime service. The contract defines the interface that Task 2.2.3 (receipt-to-license activation) will implement.

## Acceptance criteria

1. Document payment states: `pending`, `succeeded`, `failed`, `cancelled` with meanings and terminal status
2. Define payment status as separate from license and organization status (FR-06, Decision #3)
3. Document payment event types and versioned signed payload schema
4. Specify webhook security: signed payloads, idempotency keys, replay protection
5. Define retry policy: max 5 retries, exponential backoff intervals (D6)
6. Define dead-letter handling for terminal webhook failures (D6)
7. Define idempotency key scope: per-endpoint, 24-hour TTL (D7)
8. Document error semantics: 400/401/404/409/500 for payment processing conditions
9. Reference approved decisions (NFR-03/NFR-04, Decision #7, D6/D7/D8, P1.2.1-D1)
10. No runtime implementation created — contract documentation only

## Scope

**In scope:** Payment state and event model document; payment status values; event types and payload schema; webhook security requirements; retry/dead-letter policy; error semantics; directly related project documentation.

**Out of scope:** Django Payment/PaymentEvent model implementation; payment gateway integration; webhook handler views; webhook signature verification; license activation on payment (Task 2.2.3); Moodle provisioning on payment success (Phase 3); refund/partial payment handling; production deployment.

## Approved implementation decisions

- The contract documents the interface only. No Django models, webhook handlers, or runtime enforcement is created by this task.
- Payment status values: `pending`, `succeeded`, `failed`, `cancelled` (UML §4 Recommended).
- `succeeded`, `failed`, `cancelled` are terminal states; `pending` is the initial state.
- Payment status is independent of license status and organization status (FR-06, Decision #3).
- A `succeeded` payment does not automatically activate the license; activation is a separate action (Task 2.2.3, Decision D8).
- Payment events use versioned, signed envelopes with event IDs, timestamps, idempotency keys (Decision #7, NFR-04).
- Idempotency key scope: per-endpoint, 24-hour TTL (D7).
- Retry policy: max 5 retries with exponential backoff (5s, 15s, 45s, 2m, 6m); dead-letter to `webhook_dlq` table (D6).
- Failed payment triggers license suspension per Decision D8.
- Daily batch reconciliation with 24-hour grace period for settlement delays (D8).
- All payment events carry `organization_id` for tenant-scoped access (P1.2.1-D1).
- No secrets, credentials, or signing keys included in the contract document.

## Evidence and completion

**Evidence:**
- Check or artifact: Payment state and event model document, traceability record, roadmap update.
- Result: `inovatx_context/inovatx_payment_state_event_model.md` documents payment states, event types, versioned signed payload schema, webhook security requirements, retry/dead-letter policy, error semantics, and references all approved design decisions. No executable webhook handler or runtime implementation created.
- Location: `inovatx_context/inovatx_payment_state_event_model.md`, `inovatx_context/inovatx_task_2_2_2_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: This is a documentation-only task. No database, server, or runtime validation is required or claimed. The contract is a specification for Task 2.2.3 (receipt-to-license activation).

**Completion decision:** Complete. All Task 2.2.2 deliverables implemented as a documented payment state and event model. No executable webhook handlers, Django models, or production deployment are included. Task 2.2.3 (receipt-to-license activation) will implement payment-to-license activation based on this contract.

**Reviewer / approver and date:** Contract documented 2026-10-29; completion review pending.