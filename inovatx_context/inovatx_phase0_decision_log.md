# Phase 0 Decision Log — INOVATX Executive Pre-Build Sign-Off

**Phase:** 0 — Project Setup, Guardrails, and Baseline Architecture  
**Decision Date:** 2026-10-14  
**Status:** All 19 decision areas approved by executive sign-off

**Approval record:** The project owner has confirmed that the executive approved and signed this decision log. The signed approval instrument is not embedded in this Markdown file or the supplied Word reference; signer name and approval date are therefore not transcribed here. The approval status below records the project owner's confirmation and does not reproduce a signature.

## Executive Approval Register

| Decision | Executive status |
|---|---|
| D1: Provisioning Lifecycle States | [x] Approved |
| D2: AI Allowance Exhaustion Response | [x] Approved |
| D3: Interaction-to-Token Reconciliation | [x] Approved |
| D4: Critical vs. Non-Critical AI Classification | [x] Approved |
| D5: Mastery Score Sourcing | [x] Approved |
| D6: Webhook Retry Cap and Dead-Letter Handling | [x] Approved |
| D7: Idempotency Key Scope and TTL | [x] Approved |
| D8: Payment Reconciliation | [x] Approved |
| D9: SLOs with Concrete Targets | [x] Approved |
| D10: VPS Sizing | [x] Approved |
| D11: Backup, Restore, Rollback Procedures | [x] Approved |
| D12: Monitoring and Alerting | [x] Approved |
| D13: Log Retention | [x] Approved |
| D14: Secrets Rotation | [x] Approved |
| D15: Provisioning SLO Measurement Boundaries | [x] Approved |
| D16: AI First-Token Latency SLO Measurement Boundaries | [x] Approved |
| D17: AI Monthly Allowance Amount | [x] Approved |
| D18: Provisioning SLO vs Retry Policy Resolution | [x] Approved |
| D19: Browser-Observed AI Latency Tracking | [x] Approved |

The approved answers below record the adopted decisions. This register reflects the executive approval reported by the project owner; it is not a substitute for retaining the signed source record.

---

## D1: Provisioning Lifecycle States

**Question:** What are the defined states for the Moodle provisioning Celery task lifecycle?

**Approved Answer:** Adopt `pending`, `processing`, `succeeded`, `failed`, `dead_lettered` with max 3 retries at exponential backoff (1s, 5s, 25s) before dead-lettering.

**Rationale:** Three states (pending/processing/succeeded) cover the happy path; failed/dead_lettered handle errors with explicit visibility. Three retries at exponential backoff provides sufficient fault tolerance for transient API failures while bounding the failure surface.

**Phase 0 Owner:** Platform Engineering Lead

---

## D2: AI Allowance Exhaustion Response

**Question:** When a student or institution exhausts their monthly interaction allowance, what is the user-facing response?

**Approved Answer:** Graceful downgrade to read-only static hints with a visible upsell/notify banner.

**Rationale:** Maintains learning continuity (NFR-02 uptime implication) while clearly signaling fair-use limit. Students can continue learning without interruption but are prompted to upgrade or wait for the monthly reset.

**Phase 0 Owner:** Product Owner

---

## D3: Interaction-to-Token Reconciliation

**Question:** How are customer-facing interactions mapped to provider tokens, and when is the ledger reconciled?

**Approved Answer:** Pre-reserve 1 interaction = 5,000 tokens upfront, reconcile post-call.

**Rationale:** Prevents race conditions on pooled institutional allowances. Atomic ledger reservation before LLM call ensures concurrent requests don't exceed shared budget. Post-call reconciliation adjusts for actual consumption drift.

**Phase 0 Owner:** Platform Engineering Lead

---

## D4: Critical vs. Non-Critical AI Classification

**Question:** Which AI interactions downgrade when quotas are reached, and which error out?

**Approved Answer:** By endpoint: `/api/v1/socratic-eval` (critical) errors with clear message; `/api/v1/hint` and similar ancillary endpoints downgrade to lightweight models.

**Rationale:** The Socratic coaching endpoint is core learning functionality — students must understand when the feature is unavailable rather than receiving degraded service. Ancillary hint endpoints provide value-add and can gracefully degrade.

**Phase 0 Owner:** Product Owner

---

## D5: Mastery Score Sourcing

**Question:** Where does the student's "topic mastery score" come from, and how is it updated?

**Approved Answer:** Sourced from Moodle gradebook API at request time per topic; historical quiz scores per topic provide mastery context.

**Rationale:** Single source of truth for mastery is learning performance data. Avoids circular dependency between AI usage tracking and mastery scoring. Eliminates need for separate mastery update logic.

**Phase 0 Owner:** Product Owner

---

## D6: Webhook Retry Cap and Dead-Letter Handling

**Question:** What is the maximum retry count for failed webhooks, and what happens to dead-lettered events?

**Approved Answer:** Max 5 retries with exponential backoff (5s, 15s, 45s, 2m, 6m). Dead-lettered events are written to a `webhook_dlq` table; platform operations team is alerted with 2-hour SLA for manual review.

**Rationale:** Payment webhooks are critical; 5 retries provides 7+ minute window for recovery. Consistent policy across all webhook types reduces operational complexity. Dead-letter queue provides audit trail; 2-hour SLA ensures timely intervention.

**Phase 0 Owner:** Platform Engineering Lead

---

## D7: Idempotency Key Scope and TTL

**Question:** What is the idempotency key scope and how long are duplicate requests rejected?

**Approved Answer:** Per-endpoint, 24-hour TTL.

**Rationale:** Standard industry practice. 24 hours accounts for typical retry windows while bounding storage growth. Per-endpoint scope prevents cross-endpoint collisions while enabling granular retry policies.

**Phase 0 Owner:** Platform Engineering Lead

---

## D8: Payment Reconciliation

**Question:** How is payment status reconciled against license activation for edge cases?

**Approved Answer:** License activates on `succeeded` webhook; `failed` or `expired` triggers immediate license suspension; daily batch reconciliation job compares gateway status to local ledger; 24-hour grace period allowed for settlement delays.

**Rationale:** Matches PRD §7.3 recommended model. Daily batch provides safety net for missed webhooks while 24-hour grace period accommodates settlement delays for card payments.

**Phase 0 Owner:** Billing/Finance Lead

---

## D9: SLOs with Concrete Targets

**Question:** What are the concrete SLOs and percentiles?

**Approved Targets:**

| Metric | Target | Percentile |
|---|---|---|
| Payment-to-Moodle provisioning | < 3 seconds | p95 |
| AI first-token latency | < 1.5 seconds | p95 |
| System uptime (VPS prototype phase) | 99.5% | monthly |
| Backup completion | < 2 hours | p100 |
| Restore test | < 4 hours | p100 (quarterly) |
| RLS tenant isolation test suite | 100% pass | every build |

**Rationale:** Measurable targets enable objective pass/fail criteria. Provisioning latency directly impacts user experience; AI latency is core value proposition. Backup/restore SLAs ensure disaster recovery capability. RLS test suite is non-negotiable for multi-tenant data integrity.

**Phase 0 Owner:** Site Reliability Engineer

---

## D10: VPS Sizing

**Question:** What are the minimum VPS specs to support 500 concurrent quiz takers?

**Approved Answer:** 8 vCPUs, 16 GB RAM, 200 GB SSD NVMe.

**Rationale:** Each concurrent quiz session with AI streaming requires ~20-30 MB RAM; 500 sessions ≈ 15 GB RAM. 8 vCPUs handle async FastAPI + Django + Celery workers. 200 GB storage accommodates OS, containers, logs, and room for growth.

**Phase 0 Owner:** Platform Engineering Lead

---

## D11: Backup, Restore, Rollback Procedures

**Question:** What are the specific backup, restore, and rollback procedures?

**Approved Answer:**
- **Backup:** Daily full DB dump at 02:00 UTC; continuous WAL archiving every 15 min; 30-day retention.
- **Restore:** Documented restore procedure tested quarterly; RTO < 4 hours, RPO < 15 minutes.
- **Rollback:** Application-level rollback via Docker tag pinning; database rollback via latest pre-change backup; rollback window 2 hours.

**Rationale:** Daily full + 15-min WAL achieves 15-minute RPO. Quarterly restore tests verify recoverability. 2-hour rollback window balances safety with operational overhead.

**Phase 0 Owner:** Site Reliability Engineer

---

## D12: Monitoring and Alerting

**Question:** What metrics are monitored and what are alert thresholds?

**Approved Answer:**
- **Critical alerts (page immediately):** System down, DB unreachable, payment webhook failure rate > 5%.
- **Warning alerts (notify within 4h):** Provisioning latency > 5s, AI first-token > 3s, disk usage > 80%.
- **Notification channel:** Slack #platform-ops channel + email to on-call.
- **Alert owner:** Platform operations engineer (to be named at Phase 5).

**Rationale:** Critical alerts require immediate human intervention. Warnings provide early warning for degradation. Multiple notification channels ensure alert delivery. On-call ownership rotates during pilot.

**Phase 0 Owner:** Site Reliability Engineer

---

## D13: Log Retention

**Question:** How long are logs retained and where are they stored?

**Approved Answer:** 90 days in local volume `/var/log/inovatx/` with logrotate; 365 days for audit/security events (payment webhooks, RLS access denials, AI allowance exhaustion).

**Rationale:** 90-day operational window supports troubleshooting. 365-day retention satisfies audit/compliance requirements for financial and security events. Centralized log directory simplifies management.

**Phase 0 Owner:** Site Reliability Engineer

---

## D14: Secrets Rotation

**Question:** What is the secrets rotation cadence and process?

**Approved Answer:**
- LLM provider API keys: 90-day rotation with 14-day overlap.
- JWT signing secret: 30-day rotation with 7-day overlap (supporting key versioning for graceful transition).
- Payment gateway keys: 180-day rotation.

**Rationale:** LLM keys have highest exposure due to cost; 90-day rotation balances security with operational overhead. JWT rotation at 30 days aligns with common security standards. Payment keys rotate less frequently as they are merchant keys with external rotation processes.

**Phase 0 Owner:** Security Engineer

---

## D15: Provisioning SLO Measurement Boundaries

**Question:** What are the exact start and end points for measuring the "Payment-to-Moodle provisioning < 3 seconds" SLO?

**Approved Answer:**
- **Start:** Django receives and validates payment webhook, license status transitions to `succeeded`
- **End:** Celery task completes Moodle user creation + cohort assignment (if institutional) + Django issues signed SSO JWT returned to client
- **Included:** Payment validation, Celery task queuing/execution, Moodle REST API calls, JWT generation
- **Excluded:** Payment gateway processing time, user browser redirect, Moodle session creation/render
- **Retry handling:** Timer runs continuously through Celery retries (3x, 1s/5s/25s); SLO violation recorded if all retries fail

**Rationale:** Measures end-to-end user-perceived latency from confirmed payment to learnable access. Excludes external factors (payment gateway, network) while capturing all system-controlled steps. Continuous timer through retries reflects actual user experience.

**Phase 0 Owner:** Site Reliability Engineer

---

## D16: AI First-Token Latency SLO Measurement Boundaries

**Question:** What are the exact start and end points for measuring the "AI first-token latency < 1.5 seconds" SLO?

**Approved Answer:**
- **Start:** FastAPI receives the Socratic evaluation request from Moodle (includes question stem, rubric solution, student response/working, topic mastery context)
- **End:** FastAPI sends the first byte of the AI-generated response to Moodle via the Server-Sent Events (SSE) connection
- **Included:** Request validation, context assembly, model selection, provider API call, first token generation
- **Excluded:** Moodle network transmission time, browser rendering/display time
- **Retry handling:** Timer runs continuously through provider retry attempts (if implemented); SLO violation recorded if all retry attempts exceed threshold or fail completely

**Rationale:** Measures the core AI service latency from request receipt to first token output, matching the PRD's "first token stream" requirement. Excludes external network factors while capturing all AI service-controlled steps. Continuous timer through retries reflects actual user-perceived latency when transient provider failures occur.

**Phase 0 Owner:** Site Reliability Engineer

---

## D17: AI Monthly Allowance Amount

**Question:** What is the monthly AI interaction allowance per learner for the Learner tier?

**Approved Answer:** 1,000 interactions/month per learner seat, with a daily cap of 50 interactions/day.

**Rationale:** Study pattern analysis (8 hours/day × 20 days/month × 6 interactions/hour = 960 minimum) + 4% headroom. The 1,000-interaction Learner tier at $7.99/month covers the pilot's educational usage requirement while enabling 960 full-study-day coverage with 40 interactions buffer. Daily caps prevent a single busy day from consuming the entire monthly allowance.

**Phase 0 Owner:** Product Owner

---

## D18: Provisioning SLO vs Retry Policy Resolution

**Question:** How is the conflict between the 3-second provisioning p95 SLO and the 1s/5s/25s exponential backoff retries resolved?

**Approved Answer:** The 3-second SLO measures **first-attempt completion latency**. Retries are tracked separately as a **recovery objective**: p95 successful completion including retries must be achieved within 30 seconds, with user-visible pending status during retries.

**Rationale:** A retry with 5s or 25s backoff cannot meet a 3-second first-attempt target. Separating first-attempt latency (user-facing performance expectation) from eventual completion (recovery metric) enables accurate SLO reporting and separate alerting. Users see a pending state during retry with explicit progress indication.

**Phase 0 Owner:** Site Reliability Engineer

---

## D19: Browser-Observed AI Latency Tracking

**Question:** Must browser-observed AI first-token latency also be tracked and SLO'd?

**Approved Answer:** Yes. Track both:
- **Service-side latency:** FastAPI first SSE byte → SLO <1.5s p95
- **Browser-observed latency:** Learner perceives additional network + render delay; record p95 browser-observed first token as a secondary metric

**Rationale:** Network latency, DNS resolution, TLS handshake, and browser rendering add to learner experience beyond FastAPI's control. Second metric enables detection of frontend performance issues and accurate SLA communication with learners.

**Phase 0 Owner:** Site Reliability Engineer

---

## Sign-Off

| Approver | Role | Decision | Date |
|---|---|---|---|
| | Executive sponsor | [x] Approved ☐ No-go ☐ Conditional go | |
| | Product owner | [x] Approved ☐ No-go ☐ Conditional go | |
| | Technical/security owner | [x] Approved ☐ No-go ☐ Conditional go | |

**Gate Rule:** All 19 decision areas must be marked Approved before implementation begins.

---

## Governance Clarification: Completion Checklist Gate Applicability

**Decision date:** 2026-10-19
**Status:** Approved interpretation; formal exit approval remains separate
**Approver:** IBRAHIM SSEMAKULA, project owner / executive sponsor, as confirmed in the 2026-10-19 review interaction. No external approval-record reference is available in this workspace.

**Decision:** Apply the completion checklist by phase and readiness gate:

- Phase 0–6 completion items are evaluated at the exit of their respective phase. Completion of a later phase is not a prerequisite to entering an earlier phase.
- Scope, decision, and architecture/security items in Sections 1–3 retain their independent approval requirements. This clarification neither checks nor waives any of them.
- Operational readiness and launch items apply at their relevant readiness and launch gates, not as evidence of Phase 0 completion.
- Phase 0 exit approval and explicit authorization for Phase 1 are separate decisions. This clarification does not authorize Phase 1.

**Rationale:** The checklist includes completion criteria for later phases and launch, while the executive gate requires a separate exit review and approval for each phase. Applying those criteria at their respective gates avoids requiring future work to be complete before an earlier phase can begin, without waiving any independent pre-build approvals.

**Impact:** Reviewers should assess only the checklist items applicable to the gate under review, keep all other items open, and record the applicable evidence and approvals. The Phase 0 exit review is recorded as approved; this does not grant Phase 1 authorization or claim that host-side branch protections are configured.

---

## Phase 1 Task 1.1.1 Decisions — Core Domain Model

**Decision date:** 2026-10-25
**Status:** Project-owner decisions for Task 1.1.1; domain model approved 2026-10-25
**Approver:** Project owner, confirmed in the 2026-10-25 Task 1.1.1 planning interaction

### P1.1.1-D1: User identity and organization membership

**Decision:** Keep one global login identity and allow it to have memberships in multiple organizations. Represent each membership once per `(auth_user, organization)` pair. Allow multiple organization-scoped role assignments per membership; do not impose a student-only single-organization rule. The global `system_admin` role is not an organization membership role.

**Rationale:** A person may be affiliated with multiple institutions, including as a parent or teacher, without needing duplicate login credentials. Organization-scoped membership provides the tenant context boundary while role assignments express that person's roles within each organization.

**Impact:** `UserProfile` is modeled as an organization membership, unique by user and organization. A role-assignment association is required. The PRD's singular `request.user.userprofile.organization_id` example must be refined by Task 1.2.1 to explicitly select and validate a membership for each request; implementation must fail closed when context is missing or invalid.

### P1.1.1-D2: Product-license cardinality and AI entitlement

**Decision:** Model at most one current license per organization and product; different product licenses may coexist. A license stores configured per-learner-seat monthly and daily interaction entitlements. Under D17, the Learner tier values are 1,000 monthly interactions and 50 daily interactions per learner seat. Actual interactions, reservations, and provider-token usage belong in a separate usage ledger, not mutable usage counters on the license.

**Rationale:** This distinguishes product entitlement from payment state and usage accounting, preserves multiple product entitlements, and follows approved D3/D17 interaction/token semantics.

**Impact:** The license model does not include `ai_tokens_used_current_month`. Renewal/payment history and the physical enforcement of current-license uniqueness must be finalized with the subscription lifecycle and schema tasks before implementation.