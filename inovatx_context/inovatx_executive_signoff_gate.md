# INOVATX — Executive Pre-Build Sign-Off

**Decision:** Authorize Phase 0 only  
**Decision date:** ____________________  
**Target first-client launch:** 2026-12-01  
**Status:** ☐ Go  ☐ No-go  ☐ Conditional go

## Purpose

This is the executive authorization gate before project preparation begins. Approval authorizes **Phase 0 definition and validation work only**. It does not authorize product implementation, production deployment, or first-client activation. Those require their own phase exit reviews and approvals.

## Decisions required for a Phase 0 go

Mark each item **Approved**, **Open**, or **Not applicable**. Any **Open** item means **No-go** unless an accountable owner, due date, and explicit condition are recorded below.

| Decision area | Required executive outcome | Status |
|---|---|---|
| First-client scope | Approve only the first-client MVP. Defer CRM expansion beyond the limited CRM_BASIC first-client scope, project management, broader SME/NGO modules, and non-essential AI features. | ☐ Approved ☐ Open |
| Roles and access | Approve global `system_admin`, tenant-scoped `org_admin`, and membership-scoped roles; authorization is checked by resource, action, and tenant. | ☐ Approved ☐ Open |
| Lifecycle ownership | Require separate, defined lifecycles for organization, subscription/license, payment, and provisioning. | ☐ Approved ☐ Open |
| AI allowance | Require an auditable interaction allowance distinct from provider-token usage, with defined pooling, exhaustion, reset, and fallback behavior. | ☐ Approved ☐ Open |
| Trust boundaries | Approve Nginx as public ingress and FastAPI as private/internal by default. Any public AI exposure requires separate security approval. | ☐ Approved ☐ Open |
| Events and webhooks | Require signed, versioned, idempotent, replay-safe event handling with observable retries and a recovery path. | ☐ Approved ☐ Open |
| Tenant isolation | Require PostgreSQL RLS plus application authorization; tenant context is explicit in requests and worker tasks, and missing context fails closed. | ☐ Approved ☐ Open |
| Operational readiness | Require named owners, measurable critical-path targets, monitoring, backup/restore, rollback, and incident escalation before launch approval. | ☐ Approved ☐ Open |

**First-client CRM_BASIC scope clarification — 2026-10-25:** the project owner approved a limited CRM_BASIC first-client scope of global client/account tracking, tenant users' account overview, and a gateway into the tenant's Moodle learning platform. Broader CRM capabilities remain deferred.

## Pre-Defined Resolutions

Each decision area above has been pre-defined with concrete specifications. The following resolutions are documented in `inovatx_phase0_decision_log.md` and are ready for executive approval:

### Lifecycle Ownership — Provisioning Lifecycle
- States: `pending`, `processing`, `succeeded`, `failed`, `dead_lettered`
- Retry policy: 3 retries at exponential backoff (1s, 5s, 25s)
- Celery task updates: task state maps directly to these statuses

### AI Allowance — Exhaustion & Classification
- Exhaustion response: Graceful downgrade to read-only static hints with upsell banner
- Interaction-to-token mapping: 1 interaction = 5,000 tokens pre-reserved
- Critical endpoints (`/socratic-eval`): Error with clear message on exhaustion
- Non-critical endpoints (`/hint`, etc.): Downgrade to lightweight model
- Mastery score source: Moodle gradebook API at request time

### Events and Webhooks — Retry & Dead-Letter
- Max retries: 5 with exponential backoff (5s, 15s, 45s, 2m, 6m)
- Dead-letter: `webhook_dlq` table with 2-hour SLA for manual review
- Idempotency: Per-endpoint, 24-hour TTL

### Payment Reconciliation
- License activation: on `succeeded` webhook only
- Suspension: on `failed` or `expired`
- Daily batch reconciliation job with 24-hour settlement grace period

### Operational Readiness — SLOs (p95 unless noted)
- Payment-to-Moodle provisioning: < 3 seconds
- **Provisioning SLO measurement: start = payment validated + license succeeded; end = Moodle user + cohort + SSO JWT returned; continuous through retries**
- AI first-token latency: < 1.5 seconds
- **AI first-token SLO measurement: start = FastAPI receives Socratic eval request from Moodle; end = first byte sent via SSE; continuous through retries**
- System uptime: 99.5% monthly
- Backup completion: < 2 hours
- Backup/restore test RTO: < 4 hours, RPO: < 15 min

### VPS Sizing
- 8 vCPUs, 16 GB RAM, 200 GB SSD NVMe

### Backup, Restore, Rollback
- Daily full dump at 02:00 UTC; WAL archiving every 15 min; 30-day retention
- Rollback: Docker tag pinning; 2-hour window

### Monitoring & Alerting
- Critical: System down, DB unreachable, webhook failure rate > 5%
- Warning: Provisioning latency > 5s, AI first-token > 3s, disk > 80%
- Channels: Slack #platform-ops + on-call email

### Log Retention
- Operational logs: 90 days at `/var/log/inovatx/`
- Audit/security events: 365 days

### Secrets Rotation
- LLM API keys: 90 days (14-day overlap)
- JWT signing secret: 30 days (7-day overlap)
- Payment gateway keys: 180 days

## Authorization boundary

A **Go** authorizes the team to complete Phase 0 deliverables: confirm source-of-truth documents, close or assign the decisions above, establish repository and delivery guardrails, and define evidence-based exit criteria.

A **Go does not authorize** implementation work in Phases 1–6. Each later phase requires completion evidence and an explicit phase-exit approval. The first-client launch requires a separate go/no-go decision.

## Open Conditions

| Open decision or condition | Accountable owner | Due date | Approval required to close |
|---|---|---|---|
| D1: Provisioning lifecycle states (pending/processing/succeeded/failed/dead_lettered; 3 retries, 1s/5s/25s backoff) | Platform Engineering Lead | 2026-10-18 | Confirm states and retry policy match PRD §7.2 |
| D2: AI allowance exhaustion response (graceful downgrade to read-only static hints + upsell banner) | Product Owner | 2026-10-18 | Confirm user experience matches fair-use policy |
| D3: Interaction-to-token reconciliation (1 interaction = 5,000 tokens pre-reserved, post-call reconcile) | Platform Engineering Lead | 2026-10-18 | Confirm atomic reservation prevents race conditions |
| D4: Critical vs. non-critical AI classification (by endpoint: /socratic-eval errors, /hint downgrades) | Product Owner | 2026-10-18 | Confirm endpoint classification is operationally sound |
| D5: Mastery score sourcing (Moodle gradebook API at request time) | Product Owner | 2026-10-18 | Confirm no circular dependency with AI usage tracking |
| D6: Webhook retry cap and dead-letter handling (5 retries, 5s/15s/45s/2m/6m backoff, webhook_dlq table, 2h SLA) | Platform Engineering Lead | 2026-10-18 | Confirm dead-letter queue design and SLA |
| D7: Idempotency key scope and TTL (per-endpoint, 24-hour TTL) | Platform Engineering Lead | 2026-10-18 | Confirm TTL balances retry windows and storage |
| D8: Payment reconciliation (license on succeeded, suspend on failed/expired, daily batch, 24h grace) | Billing/Finance Lead | 2026-10-18 | Confirm reconciliation logic matches financial controls |
| D9: SLOs with concrete targets (provisioning <3s p95, AI first-token <1.5s p95, uptime 99.5% monthly, backup <2h, restore RTO <4h RPO <15min) | Site Reliability Engineer | 2026-10-18 | Confirm SLOs are achievable and measurable |
| D10: VPS sizing (8 vCPUs, 16 GB RAM, 200 GB SSD NVMe) | Platform Engineering Lead | 2026-10-18 | Confirm sizing supports 500 concurrent quiz takers |
| D11: Backup, restore, rollback procedures (daily full at 02:00 UTC, WAL every 15min, 30-day retention, rollback via Docker tag pinning, 2h window) | Site Reliability Engineer | 2026-10-18 | Confirm backup/restore/rollback procedures are complete |
| D12: Monitoring and alerting (critical: system down/DB unreachable/webhook failure >5%; warning: provisioning >5s/AI first-token >3s/disk >80%; Slack #platform-ops + on-call email) | Site Reliability Engineer | 2026-10-18 | Confirm alert thresholds and notification channels |
| D13: Log retention (90 days operational at /var/log/inovatx/, 365 days audit/security events) | Site Reliability Engineer | 2026-10-18 | Confirm retention meets compliance requirements |
| D14: Secrets rotation (LLM keys 90d/14d overlap, JWT signing 30d/7d overlap, payment keys 180d) | Security Engineer | 2026-10-18 | Confirm rotation cadence and overlap periods |
| D15: Provisioning SLO measurement boundaries (start: payment validated + license succeeded; end: Moodle user + cohort + SSO JWT returned; continuous through retries; p95) | Site Reliability Engineer | 2026-10-18 | Confirm boundaries capture user-perceived latency end-to-end |
| D16: AI first-token latency SLO measurement boundaries (start: FastAPI receives Socratic evaluation request from Moodle; end: first byte sent via SSE; continuous through retries; p95) | Site Reliability Engineer | 2026-10-18 | Confirm boundaries capture AI service latency end-to-end |
| D17: AI monthly allowance amount (1,000 interactions/month per Learner seat, daily cap 50/day) | Product Owner | 2026-10-25 | Confirm allowance matches study pattern (48 interactions/day × 20 days) |
| D18: Provisioning SLO vs retry resolution (first-attempt latency SLO <3s p95; recovery SLO successful completion <30s p95 with user-visible pending status) | Site Reliability Engineer | 2026-10-25 | Confirm separation of performance vs recovery metrics |
| D19: Browser-observed AI latency tracking (track both service-side first-byte <1.5s p95 AND browser-observed first-token as secondary metric) | Site Reliability Engineer | 2026-10-25 | Confirm dual-latency measurement approach |

## Executive approval

**Decision rationale / conditions:**  
____________________________________________________________________________  
____________________________________________________________________________

| Approver | Role | Decision | Signature | Date |
|---|---|---|---|---|
|  | Executive sponsor | [x] Go ☐ No-go ☐ Conditional go |  |  |
|  | Product owner | [x] Go ☐ No-go ☐ Conditional go |  |  |
|  | Technical/security owner | [x] Go ☐ No-go ☐ Conditional go |  |  |

**Gate rule:** No implementation begins until Phase 0 exit criteria are met and the next phase is explicitly authorized. No first-client activation occurs without a separate launch go/no-go approval.

## Phase 1 authorization record

**Decision date:** 2026-10-25
**Approver:** IBRAHIM SSEMAKULA, Project Owner / Executive Sponsor
**Decision:** Phase 1 authorized, limited to roadmap Tasks 1.1.1–1.3.3
**Conditions:** This authorizes only Phase 1 deliverables. It does not authorize Phase 2+, production deployment, a runnable full-stack deployment, or launch. Any task that depends on an unresolved design decision must pause until that decision is approved.
**Approval basis:** The project owner confirmed the authorization wording in the 2026-10-25 project review interaction. This does not amend the earlier Phase 0-only pre-build authorization; it records the separate subsequent phase authorization.
