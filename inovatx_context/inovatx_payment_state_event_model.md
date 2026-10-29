# Payment State and Event Model — Task 2.2.2

**Roadmap task:** 2.2.2 — Define payment state and event model  
**Phase / activity:** Phase 2 / Activity 2.2  
**Status:** Documented — contract only, no implementation  
**Traceability:** [Task 2.2.2 traceability record](inovatx_task_2_2_2_traceability.md)

## 1. Purpose and boundary

This document defines the payment state machine and payment event contract for INOVATX Core. It specifies:

- Payment status values and their meanings (separate from license and organization status per FR-06)
- Payment event types and payload schema (signed, versioned webhooks per NFR-04)
- Idempotency, replay protection, and dead-letter handling
- Error semantics for payment processing failures

This is a **documentation contract only**. No Django model changes, payment gateway integration, webhook handlers, or runtime enforcement is created by this task. The contract defines the interface that Task 2.2.3 (receipt-to-license activation) will build against.

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| PRD FR-06 | PRD §6.1 | Distinguish organization status, license status, and payment status. A non-final `valid_until` date must not be treated as the full lifecycle definition for a subscription or payment. |
| PRD Decision #2 | PRD §7 | License status values are separate from payment status values. |
| PRD Decision #3 | PRD §7 | Separate state machines for subscriptions and payments. A license is not equivalent to a payment outcome. |
| PRD NFR-04 | PRD §6.2 | Payment interfaces must use versioned payloads, signed webhooks, idempotency checks, replay protection, and dead-letter handling. |
| PRD Decision #7 | PRD §7 | Signed, versioned webhook payloads for payment events. Include event IDs, timestamps, idempotency keys, and replay protection. |
| UML §4 Recommended | UML State Machine | `Payment.status` modeled as `pending`, `succeeded`, `failed`, `cancelled` with an event log for retries and webhooks. |
| Decision log D6 | Phase 0 decision log | Max 5 retries with exponential backoff (5s, 15s, 45s, 2m, 6m). Dead-lettered events written to `webhook_dlq` table. |
| Decision log D7 | Phase 0 decision log | Per-endpoint idempotency key scope with 24-hour TTL. |
| Decision log D8 | Phase 0 decision log | License activates on `succeeded` webhook; `failed`/`expired` triggers immediate license suspension; daily batch reconciliation; 24-hour grace period for settlement delays. |

## 3. Payment states

| Status code | Meaning | Terminal? | Description |
|---|---|---|---|
| `pending` | Payment initiated, awaiting result | ❌ No | Payment has been initiated but no final outcome yet. |
| `succeeded` | Payment completed successfully | ✅ Yes | Funds received; license activation triggered (Task 2.2.3). |
| `failed` | Payment failed | ✅ Yes | Payment declined or errored; license suspension triggered per D8. |
| `cancelled` | Payment cancelled before completion | ✅ Yes | Payment cancelled by user, gateway, or platform; no license activation. |

**Key invariant:** Payment status is independent of license status. A `succeeded` payment does not automatically mean the license is `active` — license activation is a separate action (Task 2.2.3).

## 4. Payment event contract

### 4.1 Event types

| Event type | Description | Direction |
|---|---|---|
| `payment.initiated` | Payment request sent to gateway | Outbound |
| `payment.succeeded` | Payment confirmed successful | Inbound (webhook) |
| `payment.failed` | Payment failed | Inbound (webhook) |
| `payment.cancelled` | Payment cancelled | Inbound (webhook) |
| `payment.reconciled` | Daily batch reconciliation completed | Internal |

### 4.2 Event payload schema

All payment events use a versioned, signed envelope:

| Field | Type | Required | Description |
|---|---|---|---|
| `event_id` | UUID | Yes | Unique event identifier for idempotency and replay protection |
| `event_type` | string | Yes | One of the event types above |
| `event_version` | string | Yes | Schema version, e.g. `1.0` |
| `timestamp` | ISO-8601 UTC | Yes | Event generation timestamp |
| `organization_id` | UUID | Yes | Tenant organization owning the payment |
| `license_id` | UUID | Yes | Subscription license associated with the payment |
| `amount` | decimal | Yes | Payment amount in minor currency units |
| `currency` | string | Yes | ISO 4217 currency code, e.g. `UGX`, `KES`, `USD` |
| `gateway` | string | Yes | Payment gateway identifier, e.g. `mobile_money`, `card` |
| `gateway_reference` | string | No | Gateway transaction reference |
| `idempotency_key` | string | Yes | Idempotency key for deduplication (24-hour TTL) |
| `signature` | string | Yes | Cryptographic signature of the payload |
| `signature_algorithm` | string | Yes | Algorithm used, e.g. `HMAC-SHA256` |
| `correlation_id` | UUID | No | Request correlation ID for tracing |

### 4.3 Webhook security

| Requirement | Description |
|---|---|
| Signed payloads | All inbound payment webhooks must carry a verifiable cryptographic signature |
| Versioned | Event payloads carry `event_version`; consumers reject unknown versions |
| Idempotency | Events with duplicate `idempotency_key` within 24-hour TTL are rejected (D7) |
| Replay protection | `event_id` and `timestamp` prevent replay attacks; events older than tolerance window rejected |
| Dead-letter | Unprocessable events after max retries written to dead-letter queue (D6) |
| Tenant scoping | All payment events carry `organization_id`; access enforced per tenant isolation (P1.2.1-D1) |

## 5. Payment processing flow

```
[Payment Initiated]
       │
       ▼
[Payment Gateway Processes]
       │
   ┌───┴───┐
   │       │
 Success  Failure
   │       │
   ▼       ▼
[succeeded] [failed]
   │       │
   ▼       ▼
[license activation] [license suspension]
 (Task 2.2.3)        (per Decision D8)
```

### 5.1 Success path

1. Payment gateway sends `payment.succeeded` webhook to Django Core
2. Django validates signature, idempotency key, and tenant context
3. If valid and not duplicate, record `Payment` as `succeeded`
4. Enqueue license activation (Task 2.2.3) — `pending` → `active` transition
5. Trigger Moodle provisioning (Phase 3, Task 3.2.x)

### 5.2 Failure path

1. Payment gateway sends `payment.failed` webhook
2. Django validates signature and idempotency
3. Record `Payment` as `failed`
4. Trigger license suspension per Decision D8 (failed payment → immediate license suspension)
5. Dead-letter after max retries if webhook processing fails

### 5.3 Retry and dead-letter

| Parameter | Value | Source |
|---|---|---|
| Max retries | 5 | Decision log D6 |
| Backoff intervals | 5s, 15s, 45s, 2m, 6m | Decision log D6 |
| Idempotency TTL | 24 hours (per endpoint) | Decision log D7 |
| Dead-letter queue | `webhook_dlq` table | Decision log D6 |
| Reconciliation | Daily batch, 24-hour grace period | Decision log D8 |

## 6. Error semantics

| Condition | Response code | Behavior |
|---|---|---|
| Invalid signature | `401` | Reject webhook; do not process |
| Missing idempotency key | `400` | Reject with error code `missing_idempotency_key` |
| Duplicate idempotency key | `409` | Reject with error code `duplicate_event`; return original result |
| Invalid event version | `400` | Reject with error code `unsupported_version` |
| Tenant context missing | `401`/`400`/`404` | Per P1.2.3-D1 |
| Webhook processing failure (retriable) | Retry | Up to 5 retries with exponential backoff (D6) |
| Webhook processing failure (terminal) | Dead-letter | Write to `webhook_dlq`; alert operations (D6) |
| Internal invariant failure | `500` | Stop, roll back, generic response with correlation ID (P1.2.3-D2) |

## 7. Acceptance criteria

1. Payment status values documented: `pending`, `succeeded`, `failed`, `cancelled`
2. Payment status explicitly separate from license and organization status (FR-06, Decision #3)
3. Payment event types and versioned payload schema documented
4. Webhook security requirements specified (signed, idempotent, replay-protected)
5. Retry and dead-letter policy documented (max 5 retries, exponential backoff, DLQ)
6. Idempotency key scope and TTL specified (per-endpoint, 24-hour TTL)
7. Error semantics defined for payment processing (400/401/404/409/500)
8. Payment processing flow documented (success, failure, reconciliation paths)
9. Approved decisions referenced (NFR-04, Decision #7, D6, D7, D8)
10. No runtime implementation created — contract documentation only

## 8. Traceability mapping

| Model element | PRD source | UML source | Approved decision |
|---|---|---|---|
| Payment status values | FR-06 | §4 State Machine | UML §4 Recommended |
| Payment ≠ license lifecycle | FR-06 | §4 State Machine | PRD Decision #3 |
| Signed versioned webhooks | NFR-04 | N/A | PRD Decision #7 |
| Event IDs, timestamps, idempotency keys | NFR-04 | N/A | PRD Decision #7 |
| Max 5 retries, exponential backoff | NFR-03 | N/A | Decision log D6 |
| Dead-letter queue | NFR-04 | N/A | Decision log D6 |
| Idempotency TTL 24 hours | NFR-04 | N/A | Decision log D7 |
| License activation on succeeded | FR-02 | §2 BPMN | Decision log D8 |
| Failed payment → license suspension | FR-06 | N/A | Decision log D8 |
| Tenant-scoped payment events | NFR-01 | §7 Cloud Architecture | P1.2.1-D1 |

## 9. Completion decision

Task 2.2.2 deliverable is complete as a documented payment state and event model:

- Payment states defined with meanings and terminal status
- Payment status explicitly decoupled from license and organization status
- Payment event types and versioned signed payload schema documented
- Webhook security requirements specified (signature, idempotency, replay protection)
- Retry and dead-letter policy documented per Decision log D6/D7
- Error semantics defined for all payment processing conditions
- Approved decisions preserved (PRD FR-06, NFR-04, Decisions #2/#3/#7, UML §4, D6/D7/D8)
- No executable implementation created by this task
- Task 2.2.3 (receipt-to-license activation) will implement payment-to-license activation

**Payment state and event model documented:** 2026-10-29  
**Completion review:** pending

## 10. Open questions

- None blocking Task 2.2.2 contract documentation.
- Exact payment gateway API integration belongs to Task 2.2.3.
- Webhook signature verification algorithm and key management belong to implementation tasks.
- Payment refund/partial payment handling is deferred beyond first-client scope.