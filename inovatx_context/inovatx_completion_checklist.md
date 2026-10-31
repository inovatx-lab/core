# COMPLETION CHECKLIST — INOVATX FIRST-CLIENT GATE

Date: 2026-10-14
Target launch: 2026-12-01

This checklist is a phased approval gate. Each item must be explicitly approved before the work or transition it governs; an unchecked item blocks that applicable gate unless an accountable approver records a bounded exception.

### Gate applicability clarification — 2026-10-19

- The Phase 0–6 completion items in Section 4 are evaluated at the exit of their respective phases. A later-phase completion item is not a prerequisite for entering an earlier phase.
- Sections 1–3 contain scope, decision, and architecture/security approvals. This clarification does not mark those items approved or waive any approval required before work depends on them.
- Operational readiness and launch items are evaluated at their applicable readiness and launch gates. They are not evidence of Phase 0 completion.
- Phase 0 exit approval and authorization to begin Phase 1 remain separate decisions. This clarification does not authorize Phase 1.
- Approval basis: IBRAHIM SSEMAKULA, project owner / executive sponsor, selected the phased-gate interpretation in the 2026-10-19 project review interaction. No external approval-record reference is available in this workspace.

## 1. MVP SCOPE LOCK

- [ ] We are building only the first-client MVP for 2026-12-01.
- [ ] No phase II features, broader CRM expansion, SME/NGO product expansion, or broader platform work are included.
- [ ] The following are in scope: tenant-aware Django Core, the limited CRM_BASIC account-tracking/account-overview/Moodle-gateway slice, Moodle SSO/provisioning, AI Socratic coaching, fair-use enforcement, and payment-to-license activation.
- [ ] The following are out of scope until after first-client launch: CRM capabilities beyond the limited CRM_BASIC slice, project management, multi-branch analytics expansion, advanced SME/NGO modules, and non-essential AI features.

## 2. DECISION LOCK

- [ ] Role model is finalized: `system_admin` is global; `org_admin`, `instructor`, `student`, `parent`, and `sme_staff` are tenant membership roles. `instructor` is the canonical code for teachers, lecturers, mentors, and similar teaching roles.
- [ ] RBAC is defined by resource + action, not broad inheritance.
- [ ] Organization lifecycle is finalized: `pending`, `active`, `suspended`, `expired`, `cancelled`.
- [ ] Subscription lifecycle is finalized separately from organization lifecycle.
- [ ] Payment lifecycle is finalized separately from both: `pending`, `succeeded`, `failed`, `cancelled`.
- [ ] **Provisioning lifecycle is finalized: `pending`, `processing`, `succeeded`, `failed`, `dead_lettered` with max 3 retries at exponential backoff (1s, 5s, 25s).**
- [ ] AI allowance semantics are finalized: product interaction vs provider token are distinct, with a usage ledger, monthly reset, institutional seat pooling, and graceful downgrade rules.
- [ ] **AI exhaustion response: graceful downgrade to read-only static hints with upsell banner.**
- [ ] **Interaction-to-token mapping: 1 interaction = 5,000 tokens pre-reserved; post-call reconciliation.**
- [ ] **Critical vs. non-critical AI classification: `/socratic-eval` errors on exhaustion; `/hint` and ancillary endpoints downgrade to lightweight models.**
- [ ] **Mastery score sourcing: Moodle gradebook API at request time per topic.**

Task 1.1.2 records the allowed organization and license status values; lifecycle transitions remain for their assigned lifecycle tasks.
- [ ] FastAPI is defined as private/internal by default; any public exposure requires explicit approval and security review.
- [ ] Nginx is the standard public ingress; Traefik is not active unless a formal deployment decision says otherwise.

## 3. ARCHITECTURE AND SECURITY LOCK

- [ ] Tenant context is defined for all requests and background tasks.
- [ ] Celery tasks must resolve tenant context explicitly; fail-closed if missing or invalid.
- [ ] Every tenant-owned table is mapped to `organization_id` or equivalent tenant key.
- [ ] PostgreSQL RLS and Django app-level validation are both required.
- [ ] No solution bypasses RLS or RBAC.
- [ ] **Payment webhooks are signed and idempotent; max 5 retries with exponential backoff (5s, 15s, 45s, 2m, 6m).**
- [ ] **Failed payment webhooks are dead-lettered to webhook_dlq table with 2-hour SLA for manual review.**
- [ ] **Idempotency key is per-endpoint with 24-hour TTL.**
- [ ] **Moodle and AI sync events are versioned, signed, and replay-safe.**
- [ ] **Payment reconciliation job daily compares gateway status to local ledger (license activates on succeeded, suspends on failed/expired).**
- [ ] Secret handling is centralized in environment/config management; no secrets in code.

## 4. PHASE GATE LOCK

- Evaluate each phase completion item at that phase's exit. Do not mark a phase complete before its evidence and approval exist.
- [x] Phase 0 is complete: repo baseline, source-of-truth docs, project guardrails, AI-grounding rules, and exit criteria are signed off. Exit approved 2026-10-25; see `inovatx_phase0_exit_review.md`. Host-side branch protection verification remains a bounded follow-up due before merging to `develop` or `main`.
- [x] Phase 1 is complete: model layer, migration baseline, tenant isolation design baseline, and Django foundation are documented and validated. Exit approved 2026-10-28; see `inovatx_phase1_exit_review.md`. Task 1.2.2 RLS implementation remains blocked on Django schema and PostgreSQL test environment and must be completed with passing tenant-isolation tests before Phase 2 work begins.
- [ ] Phase 2 is complete: RBAC matrix (Task 2.1.1) documented; tenant-scoped membership rules (Task 2.1.2) documented; Django permission enforcement (Task 2.1.3) implemented and tested; license lifecycle policy (Task 2.2.1) documented; payment state and event model (Task 2.2.2) documented; receipt-to-license activation (Task 2.2.3) implemented and tested; individual registration (Task 2.3.1) implemented and tested; institutional onboarding (2.3.2) and parent-child mapping (2.3.3) remain. Exit pending Phase 2 completion.
- [ ] Phase 3 is complete: Moodle provisioning and SSO are validated.
- [ ] Phase 4 is complete: AI orchestration, fair-use logic, and streaming are validated.
- [ ] Phase 5 is complete: end-to-end payment + LMS + AI path is validated and readiness is signed off.
- [ ] Phase 6 is complete: pilot launch is controlled and go/no-go is explicitly approved.

## 5. AI-GROUNDING GUARDRAILS

- [ ] Every generated artifact is traceable to a PRD requirement or UML element.
- [ ] No implementation work is allowed outside the active phase.
- [ ] One issue per task; no mixed unrelated scope in a single change.
- [ ] No speculative abstraction or broad refactor for future work.
- [ ] Every task has evidence: passing tests, checks, or explicit validation output.
- [ ] No public AI route without security approval.
- [ ] No code comments or plans reference future phases or out-of-scope features.

## 6. OPERATIONS AND READINESS LOCK

- [ ] Initial SLOs are defined for provisioning latency and AI first-token latency.
- [ ] **SLO: Payment-to-Moodle provisioning < 3 seconds (p95).**
- [ ] **Provisioning SLO measurement: start = payment webhook validated + license succeeded; end = Moodle user + cohort + SSO JWT returned; continuous through retries; p95.**
- [ ] **SLO: AI first-token latency < 1.5 seconds (p95).**
- [ ] **AI first-token SLO measurement: start = FastAPI receives Socratic eval request from Moodle; end = first byte sent via SSE; continuous through retries; p95.**
- [ ] **AI Learner tier allowance: 1,000 interactions/month, daily cap 50/day.**
- [ ] **Provisioning SLO: first-attempt <3s p95; recovery (with retries) <30s p95 with pending status.**
- [ ] **AI latency tracking: both service-side first-byte <1.5s p95 AND browser-observed first-token recorded as secondary metric.**
- [ ] **SLO: System uptime 99.5% monthly (VPS prototype phase).**
- [ ] **SLO: Backup completion < 2 hours (p100).**
- [ ] **SLO: Restore test RTO < 4 hours, RPO < 15 minutes (quarterly).**
- [ ] **SLO: RLS tenant isolation test suite 100% pass (every build).**
- [ ] **VPS sizing: 8 vCPUs, 16 GB RAM, 200 GB SSD NVMe.**
- [ ] Backup, restore, and rollback procedures are defined.
- [ ] **Backup: Daily full DB dump at 02:00 UTC; continuous WAL archiving every 15 min; 30-day retention.**
- [ ] **Restore: Documented procedure tested quarterly; RTO < 4h, RPO < 15min.**
- [ ] **Rollback: Application rollback via Docker tag pinning; database rollback via latest pre-change backup; 2-hour rollback window.**
- [ ] Monitoring and health checks are defined for critical paths.
- [ ] **Critical alerts (page immediately): System down, DB unreachable, payment webhook failure rate > 5%.**
- [ ] **Warning alerts (notify within 4h): Provisioning latency > 5s, AI first-token > 3s, disk usage > 80%.**
- [ ] **Notification channel: Slack #platform-ops + email to on-call.**
- [ ] **Alert owner: Platform operations engineer (to be named at Phase 5).**
- [ ] **Log retention: 90 days operational at /var/log/inovatx/ with logrotate; 365 days for audit/security events (payment webhooks, RLS access denials, AI allowance exhaustion).**
- [ ] **Secrets rotation: LLM API keys 90-day (14-day overlap); JWT signing secret 30-day (7-day overlap with key versioning); Payment gateway keys 180-day.**
- [ ] Pilot launch checklist is approved.
- [ ] Launch owner and escalation path are assigned.
- [ ] Go/no-go decision is documented before first-client activation.

## 7. SIGN-OFF

Approved by: IBRAHIM SSEMAKULA
Role: FOUNDER
Date: 2026-10-17

If any box remains unchecked, work does not proceed. This is the point of no return before the build starts.
