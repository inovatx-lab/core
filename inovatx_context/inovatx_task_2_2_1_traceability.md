# Task Traceability — 2.2.1 Subscription License State Machine

**Task ID and title:** 2.2.1 — Define initial `SubscriptionLicense` state machine  
**Phase / activity:** Phase 2 / Activity 2.2  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A documented `SubscriptionLicense` state machine — license lifecycle policy specifying allowed status values (`pending`, `active`, `suspended`, `expired`, `cancelled`), valid state transitions with triggers/guards/effects, prohibited transitions, payment lifecycle decoupling, transition authorization guards, and error semantics. This is a documentation contract only — no Django model changes, state machine implementation, or runtime enforcement is created by this task.

**PRD sources:**
- §6.1: FR-06 (Subscription & Payment Lifecycle — distinguish org status, license status, payment status; `valid_until` is not full lifecycle)
- §7 Approved Decisions #2: License status values `pending`, `active`, `suspended`, `expired`, `cancelled`; `pending` means not usable; transitions deferred to lifecycle task
- §7 Approved Decisions #3: Separate state machines for subscriptions and payments; license ≠ payment outcome

**UML sources:**
- §4 State Machine: Conceptual lifecycle proposal (transitions, status values); explicitly marked as proposal, not approved contract
- §5 ERD: `SubscriptionLicense` model with `status` field and `valid_until`

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only.
- P1.1.2-D3: Organization and license status code sets are shared but lifecycles are separate.
- Enum Taxonomy §4 (Task 1.1.2): Status codes are independent enums; `pending` means entitlement exists but not usable; transitions deferred to lifecycle tasks.
- PRD FR-06: `valid_until` date must not be treated as full lifecycle definition.

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core subscription license lifecycle. This task creates no public route, state machine implementation, or runtime service. The contract defines the interface that Task 2.2.3 (receipt-to-license activation) will implement.

## Acceptance criteria

1. Document license states: `pending`, `active`, `suspended`, `expired`, `cancelled` with meanings and usability
2. Define `pending` as entitlement exists but not usable
3. Specify all allowed state transitions with triggers, guards, and effects
4. Enumerate all prohibited transitions
5. Decouple payment lifecycle from license lifecycle (PRD Decision #3)
6. Specify that `valid_until` is not the full lifecycle definition (FR-06)
7. Define transition authorization guards (`org_admin` for admin transitions)
8. Define error semantics for invalid transitions (400/403/404/500)
9. Reference approved decisions (PRD FR-06, Decisions #2/#3, UML §4, Enum Taxonomy §4, P1.1.2-D3)
10. No runtime implementation created — contract documentation only

## Scope

**In scope:** License lifecycle policy document; state machine definition; payment decoupling rules; transition guards; error semantics; directly related project documentation.

**Out of scope:** Django model changes; state machine enforcement code; payment webhook handling; Moodle provisioning on activation; renewal history/versioning; production deployment; additional domain entities.

## Approved implementation decisions

- The contract documents the interface only. No executable state machine, Django model changes, or runtime enforcement is created by this task.
- License states: `pending`, `active`, `suspended`, `expired`, `cancelled` (PRD Decision #2).
- `pending` means entitlement exists but is not usable; no feature access until `active`.
- Allowed transitions: pending→active, pending→suspended, active→suspended, active→expired, expired→active, suspended→active, suspended→cancelled, expired→cancelled, active→cancelled.
- `cancelled` is terminal; no transitions out. `pending` is initial creation state only; no re-entry.
- Payment lifecycle is separate from license lifecycle (PRD Decision #3). Payment confirmation is required for `pending`→`active` but is a separate action.
- `valid_until` is not the full lifecycle definition (FR-06); status transitions require explicit action or time-driven expiration.
- `org_admin` authorization required for admin transitions (active→suspended, suspended→active, suspended→cancelled, active→cancelled, expired→cancelled).
- Error semantics per P1.2.3-D1/D2: 400 invalid transition, 403 unauthorized actor, 404 not found, 500 internal invariant failure.
- Organization status and license status are independent; one does not substitute for the other (P1.1.2-D3, Enum Taxonomy §4).
- No secrets, credentials, or connection strings included in the contract document.

## Evidence and completion

**Evidence:**
- Check or artifact: License lifecycle policy document, traceability record, roadmap update.
- Result: `inovatx_context/inovatx_license_lifecycle_policy.md` documents all license states, allowed/prohibited transitions, payment decoupling, transition guards, error semantics, and references all approved design decisions. No executable state machine or runtime implementation created.
- Location: `inovatx_context/inovatx_license_lifecycle_policy.md`, `inovatx_context/inovatx_task_2_2_1_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`.
- Validation boundary: This is a documentation-only task. No database, server, or runtime validation is required or claimed. The contract is a specification for Task 2.2.3 (receipt-to-license activation).

**Completion decision:** Complete. All Task 2.2.1 deliverables implemented as a documented license lifecycle policy. No executable state machine, Django model changes, or production deployment are included. Task 2.2.3 (receipt-to-license activation) will implement the `pending` → `active` transition based on this contract.

**Reviewer / approver and date:** Contract documented 2026-10-29; completion review pending.