# Payment Receipt and Subscription Activation — Task 2.2.3

**Roadmap task:** 2.2.3 — Implement minimal payment receipt and subscription activation logic  
**Phase / activity:** Phase 2 / Activity 2.2  
**Status:** Implemented — end-to-end local test with mock gateway  
**Traceability:** [Task 2.2.3 traceability record](inovatx_task_2_2_3_traceability.md)

## 1. Purpose and boundary

This task implements the receipt-to-license activation flow: when a payment gateway sends a `payment.succeeded` webhook, the corresponding `SubscriptionLicense` transitions from `pending` to `active`. When a `payment.failed` webhook is received, the license transitions to `suspended`.

This is an implementation task that creates executable Django models, views, and tests. The implementation follows the license lifecycle policy (Task 2.2.1) and the payment state and event model (Task 2.2.2).

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| PRD FR-02 | PRD §6.1 | Payment receipt must trigger automated enrollment into Moodle cohorts within < 3 seconds. |
| PRD FR-06 | PRD §6.1 | Distinguish organization status, license status, and payment status. |
| PRD Decision #2 | PRD §7 | License status values separate from payment status values. |
| PRD Decision #3 | PRD §7 | Separate state machines for subscriptions and payments. |
| PRD NFR-04 | PRD §6.2 | Signed webhooks, idempotency checks, replay protection, dead-letter handling. |
| PRD Decision #7 | PRD §7 | Signed, versioned webhook payloads with event IDs, timestamps, idempotency keys, replay protection. |
| Decision log D6 | Phase 0 decision log | Max 5 retries, exponential backoff, dead-letter queue. |
| Decision log D7 | Phase 0 decision log | Per-endpoint idempotency key, 24-hour TTL. |
| Decision log D8 | Phase 0 decision log | License activates on `succeeded` webhook; `failed` triggers license suspension. |
| Task 2.2.1 | License lifecycle policy | License states and transitions including `pending` → `active`. |
| Task 2.2.2 | Payment state model | Payment states, event types, webhook security requirements. |

## 3. Implementation

### 3.1 Models

**`Payment`** (`core/models.py`):
- `id` (UUID PK)
- `organization` (FK to Organization)
- `license` (FK to SubscriptionLicense, nullable)
- `amount` (DecimalField, positive)
- `currency` (CharField, 3 chars)
- `gateway` (CharField: `mobile_money`, `card`)
- `gateway_reference` (CharField, nullable)
- `status` (CharField: `pending`, `succeeded`, `failed`, `cancelled`)
- `idempotency_key` (CharField, unique)
- `created_at`, `updated_at`

**`PaymentEvent`** (`core/models.py`):
- `id` (UUID PK)
- `payment` (FK to Payment, CASCADE)
- `event_type` (CharField: `payment.initiated`, `payment.succeeded`, `payment.failed`, `payment.cancelled`, `payment.reconciled`)
- `event_id` (UUID)
- `payload` (JSONField)
- `received_at` (DateTimeField)

### 3.2 Webhook endpoint

**`POST /api/v1/payments/webhook/`** (`core/views.py`):
- CSRF-exempt (external gateway callback)
- Validates HMAC-SHA256 signature (`X-INOVATX-Signature` header)
- Rejects invalid signatures with `401`
- Enforces idempotency via `event_id` (duplicate events return `200` with `duplicate` status)
- Creates `Payment` record (idempotent by `idempotency_key`)
- Creates `PaymentEvent` record
- On `payment.succeeded`: activates license (`pending` → `active`)
- On `payment.failed`: suspends license (`pending` → `suspended`)
- Returns payment and license status in response

### 3.3 URL route

**`api/v1/payments/webhook/`** (`config/urls.py`) — mapped to `views.payment_webhook`, name `payment-webhook`.

### 3.4 License activation logic

When `payment.succeeded` is received for a `pending` license:
1. Validate license exists in the organization
2. Validate `seat_capacity` ≥ 1
3. For `AI_PRO` products, validate AI allowances are positive
4. Set `license.status = active`
5. Save license

When `payment.failed` is received for a `pending` license:
1. Set `license.status = suspended`
2. Save license

## 4. Error semantics

| Condition | Response code | Error code |
|---|---|---|
| Invalid/missing signature | `401` | `invalid_signature` |
| Invalid JSON body | `400` | `invalid_json` |
| Missing required field | `400` | `missing_field` |
| Unknown event type | `400` | `invalid_event_type` |
| Organization not found | `404` | `organization_not_found` |
| License not found | `404` | `license_not_found` |
| Duplicate event (idempotency) | `200` | `duplicate` (in response body) |
| License activation failure | `400` | `activation_failed` |

## 5. Acceptance criteria

1. Payment and PaymentEvent Django models created with appropriate constraints
2. Payment webhook endpoint implemented with signature verification
3. Idempotency enforced via event_id deduplication
4. `payment.succeeded` activates pending license (`pending` → `active`)
5. `payment.failed` suspends pending license (`pending` → `suspended`)
6. Error semantics match P1.2.3-D1/D2 (401/400/404)
7. End-to-end tests pass with mock gateway (8 tests)
8. All 49 tests pass (41 existing + 8 new payment tests)

## 6. Test results

| Test | Result |
|---|---|
| payment.succeeded activates license | Pass |
| payment.succeeded idempotent duplicate | Pass |
| payment.failed suspends license | Pass |
| Invalid signature returns 401 | Pass |
| Missing required field returns 400 | Pass |
| Unknown event type returns 400 | Pass |
| Nonexistent license returns 404 | Pass |
| Nonexistent organization returns 404 | Pass |

## 7. Out of scope

- Payment gateway integration (mock gateway used in tests only)
- Webhook retry logic with exponential backoff (deferred to infrastructure)
- Dead-letter queue table (`webhook_dlq` — schema documented but not implemented)
- Moodle provisioning on license activation (Phase 3, Task 3.2.x)
- License renewal/re-expansion cycles
- Payment refunds or partial payments

## 8. Completion decision

Task 2.2.3 is complete. The receipt-to-license activation flow is implemented with:
- Payment and PaymentEvent models
- Payment webhook endpoint with signature verification and idempotency
- License activation (`pending` → `active`) on `payment.succeeded`
- License suspension (`pending` → `suspended`) on `payment.failed`
- 8 end-to-end tests passing with mock gateway
- All 49 tests passing (41 existing + 8 new)

**Implementation completed:** 2026-10-29  
**Completion review:** pending