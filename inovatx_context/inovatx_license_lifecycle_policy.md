# Subscription License Lifecycle Policy — Task 2.2.1

**Roadmap task:** 2.2.1 — Define initial `SubscriptionLicense` state machine  
**Phase / activity:** Phase 2 / Activity 2.2  
**Status:** Documented — contract only, no implementation  
**Traceability:** [Task 2.2.1 traceability record](inovatx_task_2_2_1_traceability.md)

## 1. Purpose and boundary

This document defines the `SubscriptionLicense` state machine — the license lifecycle policy for INOVATX Core. It specifies:

- Allowed license status values and their meanings
- Valid state transitions, triggers, guards, and effects
- The separation between license lifecycle and payment lifecycle (FR-06, PRD Decision #3)
- Error semantics for invalid transitions

This is a **documentation contract only**. No Django model changes, state machine implementation, views, serializers, or runtime enforcement is created by this task. The policy defines the interface that Phase 3 implementation tasks (Task 2.2.3 receipt-to-license activation) will build against.

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| PRD FR-06 | PRD §6.1 | The system must distinguish between organization status, license status, and payment status. A non-final `valid_until` date must not be treated as the full lifecycle definition for a subscription or payment. |
| PRD Decision #2 | PRD §7 Approved Decisions | License status values are `pending`, `active`, `suspended`, `expired`, `cancelled`. `pending` means the entitlement exists but is not usable. Lifecycle transitions remain with the assigned lifecycle task. |
| PRD Decision #3 | PRD §7 Approved Decisions | Use separate state machines for subscriptions and payments. A license is not equivalent to a payment outcome; payment state should be tracked independently from license validity. |
| UML §4 | UML State Machine | Conceptual lifecycle proposal (not an approved transition contract): Pending → Active → Suspended/Expired/Cancelled with renewal and reinstatement paths. |
| UML §4 Note | UML State Machine | Approved status values only; transition behavior remains a proposal pending Task 2.2.1. |
| Enum Taxonomy §4 | Task 1.1.2 | Status codes are independent enums. Organization status must not substitute for license status. Payment status is separate. |
| P1.1.2-D3 | Phase 0 decision log | Organization and license status code sets are shared but lifecycles are separate. |

## 3. License states

| Status code | Meaning | Usable? | Description |
|---|---|---|---|
| `pending` | Entitlement exists but not usable | ❌ No | License row created but not yet activated. No Moodle provisioning, no AI access, no learning hub launch. |
| `active` | Entitlement is usable | ✅ Yes | License fully active. Moodle cohorts provisioned, AI interactions allowed per allowance, SSO JWT issuable. |
| `suspended` | Entitlement temporarily blocked | ❌ No | License blocked by org admin action, policy violation, or payment issue. Moodle access revoked, AI interactions blocked. Can be reinstated. |
| `expired` | Entitlement reached end of term | ❌ No | License reached `valid_until` without renewal. Moodle access revoked, AI interactions blocked. Can be renewed to active. |
| `cancelled` | Entitlement terminated permanently | ❌ No | License terminated by org admin or platform. Cannot be reactivated. A new license row must be created for a new entitlement. |

**Key invariant:** `pending` means the entitlement exists but is not usable. No feature access is granted until the license transitions to `active`.

## 4. State transition contract

### 4.1 Allowed transitions

| From → To | Trigger | Guard / precondition | Effect / action |
|---|---|---|---|
| `pending` → `active` | Payment confirmed + activation requested | Payment status = `succeeded`; license `seat_capacity` ≥ 1; for `AI_PRO`, AI allowances are positive and explicit | Set `status = active`; enable Moodle provisioning; enable SSO JWT issuance; enable AI interaction allowance |
| `pending` → `suspended` | Verification blocked / onboarding failed | License is `pending`; activation prerequisites not met | Set `status = suspended`; no feature access; record suspension reason |
| `active` → `suspended` | Org admin action or policy violation | License is `active`; requesting actor has `org_admin` role in the license's organization | Set `status = suspended`; revoke Moodle access; block AI interactions; invalidate existing SSO sessions |
| `active` → `expired` | Subscription term reached `valid_until` | License is `active`; current UTC time ≥ `valid_until` | Set `status = expired`; revoke Moodle access; block AI interactions; invalidate existing SSO sessions |
| `expired` → `active` | Renewal completed | License is `expired`; new payment confirmed; new `valid_until` set in future | Set `status = active`; update `valid_until`; re-enable Moodle provisioning; re-enable AI interactions |
| `suspended` → `active` | Reinstated after review | License is `suspended`; requesting actor has `org_admin` role; suspension cause resolved | Set `status = active`; re-enable Moodle access; re-enable AI interactions |
| `suspended` → `cancelled` | Organization terminated | License is `suspended`; requesting actor has `org_admin` role; org status = `cancelled` | Set `status = cancelled`; permanent termination; no reinstatement possible |
| `expired` → `cancelled` | Organization terminated | License is `expired`; requesting actor has `org_admin` role; org status = `cancelled` | Set `status = cancelled`; permanent termination |
| `active` → `cancelled` | Organization terminated | License is `active`; requesting actor has `org_admin` role; org status = `cancelled` | Set `status = cancelled`; permanent termination; revoke all access immediately |

### 4.2 Prohibited transitions

| Transition | Reason |
|---|---|
| Any → `pending` | `pending` is an initial creation state only; no re-entry allowed |
| `cancelled` → Any | `cancelled` is a terminal state; no transitions out |
| `pending` → `expired` | `pending` licenses have no active term to expire |
| `suspended` → `expired` | Suspension is an admin action, not time-driven |
| `expired` → `suspended` | Expiration is time-driven, not admin-driven |
| Any → Any not listed above | All unlisted transitions are invalid |

### 4.3 Payment decoupling

| Rule | Description |
|---|---|
| License ≠ Payment | A license state transition does not imply a payment state change, and vice versa (PRD Decision #3). |
| `active` requires payment | Transition to `active` requires payment status = `succeeded`, but license activation is a separate action from payment recording. |
| Payment failure does not auto-suspend | Payment webhook `failed` does not automatically transition license to `suspended`. License suspension is an explicit admin or policy action. |
| `valid_until` is not lifecycle | A non-final `valid_until` date must not be treated as the full lifecycle definition (FR-06). Status transitions require explicit action or time-driven expiration. |

## 5. Transition guards and authorization

| Guard | Description |
|---|---|
| Org admin authorization | `active` → `suspended`, `suspended` → `active`, `suspended` → `cancelled`, `active` → `cancelled`, `expired` → `cancelled` require the requesting user to have `org_admin` role in the license's organization. |
| Payment confirmation | `pending` → `active` requires payment status = `succeeded` recorded independently. |
| Seat capacity | `pending` → `active` requires `seat_capacity` ≥ 1. |
| AI allowance | `pending` → `active` for `AI_PRO` requires positive explicit monthly and daily allowances. |
| Time-driven expiration | `active` → `expired` occurs when current UTC time ≥ `valid_until` and no renewal is in progress. |

## 6. Error semantics

| Condition | Response code | Behavior |
|---|---|---|
| Invalid state transition | `400` | Reject with error code `invalid_transition`; current state and target state included |
| Unauthorized transition actor | `403` | Reject with error code `permission_denied`; `org_admin` required for admin transitions |
| License not found | `404` | Uniform outcome; no disclosure of existence |
| Missing tenant context | `401`/`400`/`404` | Per P1.2.3-D1 authentication and organization selector semantics |
| Internal state invariant failure | `500` | Stop, roll back, generic response with correlation ID (P1.2.3-D2) |

## 7. Acceptance criteria

1. License states documented: `pending`, `active`, `suspended`, `expired`, `cancelled`
2. `pending` explicitly defined as "entitlement exists but not usable"
3. All allowed state transitions specified with triggers, guards, and effects
4. All prohibited transitions enumerated
5. Payment lifecycle explicitly separated from license lifecycle (PRD Decision #3)
6. `valid_until` not treated as full lifecycle definition (FR-06)
7. Transition authorization guards specified (`org_admin` for admin actions)
8. Error semantics defined for invalid transitions (400/403/404/500)
9. State machine references approved decisions (PRD FR-06, Decisions #2/#3, UML §4, Enum Taxonomy §4, P1.1.2-D3)
10. No runtime implementation created — contract documentation only

## 8. Traceability mapping

| Policy element | PRD source | UML source | Approved decision |
|---|---|---|---|
| License status values | FR-06 | §4 State Machine | PRD Decision #2 |
| `pending` = not usable | FR-06 | §4 State Machine | PRD Decision #2 |
| License ≠ payment lifecycle | FR-06 | §4 State Machine | PRD Decision #3 |
| `valid_until` is not full lifecycle | FR-06 | §4 State Machine | FR-06, UML §5 |
| Allowed transitions | FR-06 | §4 State Machine (conceptual) | Task 2.2.1 contract |
| Prohibited transitions | FR-06 | §4 State Machine | Task 2.2.1 contract |
| `org_admin` guard for admin transitions | FR-04/FR-05 | §1 Use Case | P1.1.2-D1, P1.1.2-D2 |
| Error semantics | §3.2 Failure handling | N/A | P1.2.3-D1/D2 |
| Separate org/license statuses | Enum Taxonomy §4 | §4 State Machine | P1.1.2-D3 |

## 9. Completion decision

Task 2.2.1 deliverable is complete as a documented license lifecycle policy:

- License states defined with meanings and usability status
- Allowed transitions specified with triggers, guards, and effects
- Prohibited transitions enumerated
- Payment lifecycle decoupled from license lifecycle
- `valid_until` explicitly not treated as full lifecycle definition
- Transition authorization guards defined
- Error semantics for invalid transitions defined
- Approved design decisions preserved (PRD FR-06, Decisions #2/#3, UML §4, Enum Taxonomy §4, P1.1.2-D3)
- No executable implementation created by this task
- Task 2.2.3 (receipt-to-license activation) will implement the `pending` → `active` transition

**License lifecycle policy documented:** 2026-10-29  
**Completion review:** pending

## 10. Open questions

- None blocking Task 2.2.1 contract documentation.
- License renewal history/versioning is deferred (per P1.1.3-D4 initial license uniqueness).
- Exact payment webhook-to-license-activation timing belongs to Task 2.2.3.
- Moodle provisioning on `active` transition belongs to Phase 3 (Task 3.2.x).