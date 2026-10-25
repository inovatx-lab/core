# Task Traceability — 1.1.1 Core Domain Model

**Task ID and title:** 1.1.1 — Finalize `Organization`, `UserProfile`, and `SubscriptionLicense` structure
**Phase / activity:** Phase 1 / Activity 1.1
**Owner:** Project owner; technical reviewer to be assigned
**Status:** Complete

## Outcome and sources

**Outcome / deliverable:** An approved domain-model specification with entity fields, relationships, cardinalities, and task-level constraints for the three roadmap entities.

**PRD sources:**
- §3.1: Organization, UserProfile, and SubscriptionLicense entity/field baseline.
- FR-01: individual registration, parent-child mapping, and institutional enrollment.
- FR-05: authorization by role and organization membership; global `system_admin` distinct from tenant-scoped `org_admin`.
- FR-06: Organization, license, and payment statuses are distinct; `valid_until` is not a complete license or payment lifecycle.
- §7 decisions 2–3: separate organization, license, and payment lifecycles; customer-facing interaction allowance distinct from provider-token usage.

**UML sources:**
- §5 ERD: conceptual entity relationships and fields.
- §6 class diagram: conceptual Core entity responsibilities.
- §5 cardinality caveat: user-to-organization membership cardinality was unresolved in the UML baseline and is resolved for this task by the project-owner decision below.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django Core domain model; tenant-owned Organization, membership, and license data are stored in the Core PostgreSQL database. This task defines the model only and does not implement RLS.

## Acceptance criteria

1. Define fields, types, nullability, relationships, cardinality, and model-level invariants for `Organization`, `UserProfile`, and `SubscriptionLicense`, grounded in the PRD and approved decisions.
2. Distinguish global login identity, organization-scoped memberships and roles, product entitlement, payment state, and AI usage accounting.
3. Identify enum values or persistence constraints that belong to Task 1.1.2 or Task 1.1.3 rather than inventing unresolved decisions.
4. Record the owner-approved membership and license-cardinality decisions in the decision log and align the UML where it currently marks them unresolved.

## Scope

**In scope:** Domain structure and field definitions for the three roadmap entities; the minimal organization-scoped role-assignment relationship required to represent multiple roles per membership; approved membership and license cardinalities.

**Out of scope:** Django ORM implementation, migrations, RLS policies/tests, authorization behavior, payment entities/history, parent-child relationship modeling, Moodle provisioning implementation, and AI usage-ledger implementation.

## Approved decisions and dependencies

- One global login identity may have memberships in multiple organizations; no role-specific single-organization restriction is introduced.
- A membership is unique per `(user, organization)` and can have multiple organization-scoped role assignments.
- One current license entitlement exists per `(organization, product)`; separate products may coexist. Renewal/payment history is outside this task.
- License entitlement records configured per-learner monthly and daily interaction limits. Actual interactions, reservations, and provider-token usage belong in a separate usage ledger.
- Exact status and role enum values, validation constraints, and physical database constraints are assigned to Task 1.1.2 and Task 1.1.3 as appropriate.
- Any remaining model decision not covered by the cited requirements or the approved choices must be escalated before finalizing the model.

## Evidence and completion

**Evidence:**
- Check or artifact: Task 1.1.1 domain-model specification and aligned UML/decision-log updates.
- Result: Project owner approved the model as documented on 2026-10-25. `git diff --check` passed; the changed documentation was reviewed for alignment with the cited PRD, UML, and approved decisions.
- Location: `inovatx_phase1_core_domain_model.md`, `inovatx_uml.md`, and `inovatx_phase0_decision_log.md`.

**Completion decision:** Complete; the approved domain-model specification satisfies the task acceptance criteria.
**Reviewer / approver and date:** Project owner, 2026-10-25.
