# Review and Quality Gates — INOVATX

**Roadmap task:** 0.3.3 — Define review and quality gates
**Status:** Phase 0 governance artifact; defines intended review and validation evidence, not configured CI or implementation approval
**Applies to:** Task reviews, pull requests, milestone reviews, and phase exit decisions

## 1. Gate principles

- Review every task against its active roadmap scope, traceability record, approved decisions, and phase authorization.
- Evidence must match the work performed. A written plan or static inspection is not an executed test; a passing test is not an approval.
- A required gate that is not applicable must be marked **N/A** with a reason. A required gate that cannot be run remains **Not run** and blocks completion unless the accountable reviewer explicitly accepts a documented, bounded exception.
- Record defects and unmet criteria. Do not mark a task, milestone, or phase complete while a blocking issue or required evidence remains outstanding.
- These checklists describe the intended quality process. CI tools, branch protections, reviewers, and checks are not considered configured merely because this document or `BRANCH_POLICY.md` names them.

## 2. Review rubric

For each applicable criterion, record **Pass**, **Fail**, or **N/A**, with concise evidence. Any **Fail** in a blocking criterion prevents approval.

| Criterion | Review questions | Gate |
|---|---|---|
| Authorization and scope | Is this work part of the active task and phase? Does it avoid future-phase, out-of-scope, and unrelated changes? | Blocking |
| Traceability and correctness | Is the change mapped to cited PRD/UML sources or an approved governance decision? Does it satisfy the stated acceptance criteria without inventing requirements? | Blocking |
| Security and privacy | Are authentication, authorization, tenant context, RLS, data handling, secret handling, and trust boundaries preserved where relevant? Are integration signatures, idempotency, and replay controls respected? | Blocking |
| Functional behavior | Are expected behavior, invalid inputs, failure paths, retries, and boundary conditions handled and evidenced as applicable? | Blocking |
| Verification | Are the smallest relevant tests, lint, type checks, builds, or static checks run and passing? Are unavailable or skipped checks disclosed accurately? | Blocking |
| Maintainability | Does the change follow existing patterns, avoid unnecessary dependencies and abstractions, and remain focused? | Required |
| Documentation and operations | Are directly affected contracts, instructions, runbooks, risks, and unresolved decisions updated where required? | Required |
| Reviewability and evidence | Is the diff understandable, is task evidence attached, and are approval and remaining risks recorded? | Blocking |

### Blocking issue levels

- **Blocker:** Any change that violates scope/phase authorization, exposes a prohibited trust boundary, weakens tenant or access isolation, leaks sensitive data, or makes a critical path unsafe or unusable. Stop; do not merge or advance the gate.
- **Major:** A correctness, security, reliability, or required-evidence failure that can affect a supported path or acceptance criterion. Fix and revalidate before approval.
- **Minor:** A bounded issue that does not invalidate acceptance or materially weaken safety. Record it with an owner and due point; reviewers decide whether it can be deferred.
- **Observation:** Non-blocking improvement or follow-up. Do not expand the active task to address it unless required by acceptance criteria.

## 3. Task and pull-request validation checklist

Complete for each change before requesting approval:

### Scope and source

- [ ] Active phase, task ID, acceptance criteria, and branch are identified.
- [ ] Task-to-requirement traceability record cites the applicable PRD/UML or approved decision and identifies gaps.
- [ ] The diff contains no unapproved future-phase work, unrelated refactor, or undocumented design decision.
- [ ] Required approvals for open decisions, security-sensitive changes, or external exposure are present.

### Change quality

- [ ] The complete diff is reviewed for correctness, consistency, and unintended changes.
- [ ] Relevant positive, negative, boundary, and failure behavior is covered by focused checks or documented analysis.
- [ ] Error paths are explicit; no silent success-shaped fallback, swallowed error, or unsafe default is introduced.
- [ ] Security and privacy criteria in the review rubric are addressed, including tenant context and secret handling where relevant.
- [ ] User-facing, API, data, and operational documentation affected by the change is updated.

### Verification and approval

- [ ] Relevant existing tests pass; test output or report is linked.
- [ ] Applicable lint, type-check, build, migration/schema, integration, and security checks pass or are marked N/A with rationale.
- [ ] Any unavailable or skipped check is disclosed with impact, owner, and mitigation; no result is inferred.
- [ ] Blocking and major findings are resolved and rechecked.
- [ ] Reviewer decision, residual risks, and completion evidence are recorded.
- [ ] Phase/milestone status is updated only after its required evidence and approvals exist.

## 4. Milestone review checklists

These are entry/exit checklists for each roadmap milestone. Task-level reviews still use §3. The Phase 0 entries are documentation/planning checks only; later entries are future gates and do not authorize work before the relevant phase approval.

### Milestone 0.1 — Project formally scoped and protected from drift

- [ ] Project goal, release target, scope, exclusions, and success criteria are recorded in the approved project artifacts.
- [ ] Phase gates and decision authority are documented; unresolved approval conditions are visible.
- [ ] PRD and UML are identified as product source documents with their roles and status.
- [ ] Governance and source references are cross-checked for contradictions.
- [ ] Evidence is documentary review; no product implementation is implied.

### Milestone 0.2 — Ready to build the first working slice

- [ ] Actual repository layout and branch strategy are documented separately from future target layout.
- [ ] Environment and Compose artifacts are explicitly labeled planning-only unless independently validated and approved for execution.
- [ ] Architecture components, trust boundaries, principal flows, and unresolved decisions are mapped to PRD/UML.
- [ ] AI coding guardrails, phase lock, traceability, and review/validation gates are documented.
- [ ] Phase 0 exit criteria and open conditions have evidence and named approval state; this checklist alone does not grant Phase 1 authorization.

### Milestone 1.1 — Base platform and data contracts

- [ ] Domain entities, fields, constraints, and lifecycle definitions map to approved PRD/UML requirements.
- [ ] Migration/schema changes have reviewable forward and rollback considerations.
- [ ] Tenant ownership and data access assumptions are explicit.
- [ ] Model/schema validation and focused automated tests pass.
- [ ] No tenant-isolation claim is accepted without executable evidence appropriate to the implementation.

### Milestone 2.1 — Tenant, user, and valid subscription

- [ ] Global and tenant-scoped role boundaries are explicit and enforced by resource/action.
- [ ] Positive and negative authorization cases are tested for relevant user journeys.
- [ ] Subscription, organization, and payment state transitions remain distinct and validated.
- [ ] Receipt/activation behavior is tested using the approved integration boundary or controlled mock.
- [ ] Tenant boundary, idempotency, and audit evidence are reviewed where applicable.

### Milestone 3.1 — Moodle provisioning and signed access

- [ ] Moodle user/cohort contracts and SSO claims are versioned, documented, and tied to approved requirements.
- [ ] Authentication, signature validation, expiry, replay protection, and least privilege are reviewed.
- [ ] Provisioning retry, duplicate, partial-failure, and dead-letter behavior is tested or explicitly deferred with approval.
- [ ] Individual and institutional paths are exercised using controlled test accounts.
- [ ] End-to-end launch evidence confirms the intended first-user access path.

### Milestone 4.1 — AI coaching for a pilot cohort

- [ ] AI request/response contracts and model/provider behavior are documented and validated.
- [ ] FastAPI remains private unless separately approved; learner-facing SSE behavior follows the resolved architecture decision.
- [ ] Prompt and response behavior is evaluated against Socratic coaching requirements and does not claim untested safety.
- [ ] Usage reservation, reconciliation, allowance limits, fallback, and exhaustion behavior have focused tests.
- [ ] Latency and capacity claims are supported by measurements under recorded test conditions.
- [ ] Provider credentials and learner data are protected and excluded from logs/artifacts as required.

### Milestone 5.1 — Critical paths proven before first-client launch

- [ ] Payment signatures, idempotency, replay handling, retry limits, reconciliation, and failure recovery are validated.
- [ ] Registration-to-learning and AI-to-completion paths have repeatable end-to-end test evidence.
- [ ] Tenant isolation tests pass, including concurrent conditions where specified.
- [ ] Monitoring, alerting, backup, restore, rollback, and runbook procedures have evidence appropriate to the approved readiness criteria.
- [ ] Critical defects and operational risks have accountable owners and disposition.
- [ ] First-client checklist and required launch approvals are complete before any activation.

### Milestone 6.1 — Ready for a small first-client cohort

- [ ] Initial organization, user, subscription, and cohort data are validated with least-privilege access.
- [ ] Pilot learner LMS and AI journeys have recorded test results and sign-off.
- [ ] Pilot scope, change freeze, monitoring ownership, incident/escalation route, and rollback plan are approved.
- [ ] A separate launch go/no-go is recorded before pilot activation.
- [ ] Post-launch issues, usage, and performance are monitored against approved thresholds; no wider rollout is inferred from pilot success.

## 5. CI and branch policy relationship

`BRANCH_POLICY.md` lists intended CI gates: Ruff lint, Pyright/Mypy type-check, pytest unit and tenant-isolation tests, Bandit security scan, and a phase-evidence check. Treat these as **proposed repository policy** until the workflows, tools, branch rules, and required reviewers are actually configured and verified. Apply only checks relevant to the change, while preserving the policy's stated blocking thresholds.

For any exception, record the unmet gate, reason, risk, compensating control, accountable approver, expiry or follow-up point, and affected task. An exception cannot override executive, phase, security, or launch authorization.

## 6. Review record

Use this record for a task, pull request, or milestone review:

```text
Review subject / task / milestone:
Reviewer(s) and date:
Active phase and authorization reference:
Traceability record:

Rubric results:
- Authorization and scope:
- Traceability and correctness:
- Security and privacy:
- Functional behavior:
- Verification:
- Maintainability:
- Documentation and operations:
- Reviewability and evidence:

Checks run and results:
Checks not run / N/A and rationale:
Findings by level, owner, and disposition:
Residual risks / approved exceptions:
Decision: Approved / Changes required / Blocked
Evidence links:
```
