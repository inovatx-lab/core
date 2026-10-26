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

**Rationale:** A person may be affiliated with multiple institutions, including as a parent or instructor, without needing duplicate login credentials. Organization-scoped membership provides the tenant context boundary while role assignments express that person's roles within each organization.

**Impact:** `UserProfile` is modeled as an organization membership, unique by user and organization. A role-assignment association is required. The PRD's singular `request.user.userprofile.organization_id` example must be refined by Task 1.2.1 to explicitly select and validate a membership for each request; implementation must fail closed when context is missing or invalid.

### P1.1.1-D2: Product-license cardinality and AI entitlement

**Decision:** Model at most one current license per organization and product; different product licenses may coexist. A license stores configured per-learner-seat monthly and daily interaction entitlements. Under D17, the Learner tier values are 1,000 monthly interactions and 50 daily interactions per learner seat. Actual interactions, reservations, and provider-token usage belong in a separate usage ledger, not mutable usage counters on the license.

**Rationale:** This distinguishes product entitlement from payment state and usage accounting, preserves multiple product entitlements, and follows approved D3/D17 interaction/token semantics.

**Impact:** The license model does not include `ai_tokens_used_current_month`. Renewal/payment history and the physical enforcement of current-license uniqueness must be finalized with the subscription lifecycle and schema tasks before implementation.

---

## Phase 1 Task 1.1.2 Decisions — Enum Taxonomy and Validation Rules

**Decision date:** 2026-10-25
**Status:** Project-owner decisions for Task 1.1.2; taxonomy approved 2026-10-25
**Approver:** Project owner, confirmed in the 2026-10-25 Task 1.1.2 planning interaction

### P1.1.2-D1: Canonical organization and membership-role codes

**Decision:** Use `individual`, `school`, `sme`, `ngo`, and `enterprise` as organization type codes. Use `org_admin`, `instructor`, `student`, `parent`, and `sme_staff` as organization membership-role codes. `system_admin` remains global and is not a membership role. `instructor` is the canonical code for teachers, lecturers, mentors, and similar teaching roles; do not create separate role codes for those titles.

**Rationale:** This preserves the PRD's organization classifications and membership roles while using one stable role code for equivalent teaching responsibilities.

**Impact:** Type and role codes identify classifications only. They do not enable deferred product modules or define authorization. Role permissions remain resource/action based and belong to the assigned RBAC task.

### P1.1.2-D2: First-client CRM_BASIC boundary

**Decision:** Include `EDTECH_LMS`, `CRM_BASIC`, and `AI_PRO` as product codes. Include `CRM_BASIC` in the first-client baseline only for global client/account tracking, tenant users' account overview, and a gateway into the tenant's Moodle learning platform. Broader CRM capabilities and advanced SME/NGO modules remain deferred.

**Rationale:** The minimal account and learning-platform gateway functions support centralized client operations without authorizing the broader CRM and SME/NGO expansion.

**Impact:** `CRM_BASIC` is an accepted product code for this bounded scope. The code alone does not grant features, permissions, cross-tenant access, activation, or payment behavior. Scope references in the PRD and completion checklist distinguish this slice from deferred expansion.

### P1.1.2-D3: Organization and license status code sets

**Decision:** Use `pending`, `active`, `suspended`, `expired`, and `cancelled` as the allowed status values for both `Organization.status` and `SubscriptionLicense.status`. Keep these statuses separate from payment status. A `pending` license exists but is not usable.

**Rationale:** The PRD and UML require distinct organization, license, and payment states; the owner approved a complete shared set of allowed values while preserving separate lifecycle meaning.

**Impact:** This approves enum values and the meaning of a pending license only. It does not approve state transitions, payment coupling, renewal/history behavior, or activation rules, which remain with their assigned lifecycle tasks.

### P1.1.2-D4: Product-specific seats and AI interaction entitlements

**Decision:** `seat_capacity` must be an integer greater than or equal to 1 and counts licensed units specific to the selected product. AI interaction entitlement fields apply only to `AI_PRO`; the D17 learner-seat baseline is 1,000 monthly interactions and 50 daily interactions.

**Rationale:** Product-specific seat units avoid assuming one capacity formula across LMS, CRM, and AI entitlements. Restricting the interaction allowance to AI_PRO identifies the AI product boundary while preserving D17's approved per-learner values.

**Impact:** These are logical validation and entitlement rules. Product-specific seat calculations, AI usage/pooling/reset behavior, and physical enforcement remain outside Task 1.1.2.

---

## Phase 1 Task 1.1.3 Decisions — Initial Database Schema Baseline

**Decision date:** 2026-10-25
**Status:** Project-owner decisions for Task 1.1.3
**Approver:** Project owner, confirmed in the 2026-10-25 Task 1.1.3 planning interaction

### P1.1.3-D1: Documentation-only migration plan

**Decision:** Task 1.1.3 delivers a documented target schema baseline and ordered migration plan. It does not create executable migration files, run database schema checks, or claim that a database exists.

**Rationale:** The Django application/models and runnable database context are established by later authorized Phase 1 tasks. The roadmap's migration-file/schema-check evidence is therefore deferred to those implementation tasks.

**Impact:** Record the schema and sequence now. Create and validate migrations only after the Django app and its database configuration exist.

### P1.1.3-D2: Client/account entity

**Decision:** `Organization` is the client/account record for CRM_BASIC. Do not add a separate `Client` or `Account` entity to the initial schema.

**Rationale:** Organization already represents the tenant/client boundary and supports the approved limited CRM_BASIC scope without duplicating client identity.

**Impact:** Global client/account tracking and tenant account overview use `Organization`; access must still follow separately approved authorization and tenant-isolation rules.

### P1.1.3-D3: Role-assignment identity

**Decision:** Give `OrganizationMembershipRole` a UUID primary key and enforce uniqueness on `(user_profile_id, role_code)`.

**Rationale:** A surrogate row key provides a straightforward identity for the association while the unique pair prevents duplicate assignment of the same role to a membership.

**Impact:** Update the schema baseline and domain/ERD descriptions. Database enforcement is planned but not implemented in Task 1.1.3.

### P1.1.3-D4: Initial license uniqueness

**Decision:** Enforce one initial license row per `(organization_id, product_code)`. Renewal history/versioning is excluded from this baseline and remains deferred to Task 2.2.1.

**Rationale:** This directly implements the approved Task 1.1.1 current-license cardinality without inventing a history model.

**Impact:** The initial unique constraint may need a reviewed migration if Task 2.2.1 later approves multiple historical rows.

### P1.1.3-D5: AI entitlement column representation

**Decision:** Keep the monthly and daily AI entitlement columns on `SubscriptionLicense`. They are nullable for non-`AI_PRO` products and both must be present and positive for `AI_PRO`.

**Rationale:** This uses the approved license entity without adding an unspecified entitlement table and encodes product applicability explicitly.

**Impact:** Represent the rule as a conditional database CHECK constraint in the target schema. Actual allowance use, pooling, reservations, and reconciliation remain separate.

### P1.1.3-D6: Enum persistence and enforcement

**Decision:** Store enum values as strings, validate them through Django model choices, and enforce allowed values with PostgreSQL CHECK constraints. Do not use PostgreSQL-native ENUM types for the initial baseline.

**Rationale:** This provides application-level validation and database-level integrity while keeping approved value changes manageable through migrations.

**Impact:** Document the intended choices and checks; do not claim they are enforced until executable models/migrations are applied and schema checks pass.

## Phase 1 Task 1.2.1 Decisions — Tenant Context for Requests and Workers

**Decision date:** 2026-10-25
**Status:** Project-owner decisions for Task 1.2.1; tenant-context specification approved 2026-10-25
**Approver:** Project owner, confirmed in the 2026-10-25 Task 1.2.1 planning interaction

### P1.2.1-D1: Explicit request organization selection

**Decision:** A tenant-scoped request must explicitly select an organization UUID. After authentication and selector syntax validation, establish the selected organization as candidate transaction-local context and perform only a `UserProfile` lookup matching both the authenticated user and selected organization under RLS. Do not access tenant business data until the membership is validated. Defer the selector's route/header/session transport to Task 1.3.3.

**Rationale:** One global user may have memberships in multiple organizations; neither a singular profile nor an implicit default can safely select the tenant.

**Impact:** Request identifiers are selectors, not authorization. The eventual API contract must preserve explicit selection and membership validation. The scoped membership lookup is the only tenant query permitted before membership validation; it is required because `UserProfile` is RLS-protected.

### P1.2.1-D2: Explicit worker context and execution-time authorization

**Decision:** Every tenant-scoped worker task carries an explicit organization identifier. User-originated tasks preserve actor/membership identifiers when applicable and revalidate membership and applicable authorization when executed. System/event-originated tasks preserve explicit provenance. Tasks must not inherit ambient request, thread, process, or connection tenant state.

**Rationale:** Queued work can execute after the initiating membership or authorization changes; payload identity alone is not permission, and tenant state must not leak across asynchronous work.

**Impact:** Each execution attempt resolves its own context. The detailed role/permission matrix and task-specific service identity are not defined here.

### P1.2.1-D3: Transaction-local tenant database context

**Decision:** Establish tenant database context using the PRD's `SET LOCAL` model within the transaction performing tenant-owned work. Do not retain tenant identity in connection- or session-scoped state.

**Rationale:** Transaction scope limits the lifetime of tenant context and reduces leakage risk on reused connections and worker retries.

**Impact:** Each request unit of work and worker execution attempt must establish context before tenant queries; transaction completion clears it. This decision does not select database roles, grants, or RLS policies.

### P1.2.1-D4: Global administrator and organization assistance boundary

**Decision:** Global `system_admin` status does not by itself grant tenant-owned data access or create an implicit all-tenant context. Any assistance requiring access beyond an organization's normal roles and permissions must be requested from that organization.

**Rationale:** The global role and tenant membership are distinct; cross-tenant access must not arise from an unstated bypass.

**Impact:** The access-request, approval, grant, scope, duration, revocation, and audit workflow remains undefined and out of scope for Task 1.2.1. No support or impersonation access is authorized by this decision.

## Phase 1 Task 1.2.2 Decisions — PostgreSQL RLS Baseline

**Decision date:** 2026-10-25
**Status:** RLS design approved; executable baseline and tests are blocked on the Django schema and PostgreSQL test environment
**Approver:** Project owner and technical/security owner, confirmed in the 2026-10-25 Task 1.2.2 design interaction

### P1.2.2-D1: Separate bootstrap, schema-owner, migration, and runtime authorities

**Decision:** Use a controlled setup-only bootstrap authority; a `NOLOGIN` schema/object-owner role; a separate controlled migration identity that may activate the owner role for migrations; and one shared, least-privileged runtime identity for Django and Celery. Do not configure the bootstrap, owner, or migration credentials in runtime services. Runtime must not own tenant tables, assume owner privileges, or have `SUPERUSER`, `BYPASSRLS`, DDL, or role-management privileges.

**Rationale:** Separate setup and schema-change authority from normal data access, so the runtime identity cannot bypass row security through ownership or elevated role attributes.

**Impact:** Exact role identifiers, bootstrap commands, credential delivery, and deployment workflow remain implementation/deployment details. The runtime grant baseline is limited to `SELECT`, `INSERT`, `UPDATE`, and `DELETE` on the four approved Core tenant tables; exclude `TRUNCATE`, `REFERENCES`, `TRIGGER`, replication, DDL, ownership, and role management. The external Django authentication table and its grants are not selected by this decision.

### P1.2.2-D2: RLS coverage and tenant predicates

**Decision:** Enable and FORCE RLS on `Organization`, `UserProfile`, `OrganizationMembershipRole`, and `SubscriptionLicense`. Define runtime-targeted policies with both `USING` and `WITH CHECK`. Scope `Organization` by `id`, `UserProfile` and `SubscriptionLicense` by `organization_id`, and `OrganizationMembershipRole` through its parent `UserProfile.organization_id`. Do not add a redundant organization column to the approved role-assignment schema.

**Rationale:** Apply the same tenant boundary to all four approved tenant-owned entities while preserving the schema and membership cardinality accepted in Tasks 1.1.1 and 1.1.3.

**Impact:** Missing tenant context must match no rows and reject writes; malformed values must error rather than fall back to unscoped access. Physical table names and executable policy expressions depend on the Django model/app schema.

### P1.2.2-D3: Runtime role test identity

**Decision:** Execute tenant-isolation integration tests using the shared runtime identity, or an equivalent role with the same grants and without table ownership, owner exemption, or RLS bypass.

**Rationale:** Tests under a superuser, `BYPASSRLS` identity, or unforced table owner would not verify the application's actual security boundary.

**Impact:** Test coverage must include cross-tenant reads, cross-tenant insert/update rejection, missing context, membership-role relationship scoping, and transaction/connection reuse. Tests must run against the actual Django schema before Task 1.2.2 can be closed.

### P1.2.2-D4: Custom-GUC threat boundary and global directory

**Decision:** Retain the PRD's transaction-local `SET LOCAL app.current_organization_id` mechanism. Explicitly treat it as defense in depth for normal application paths, not as independent protection from arbitrary SQL executed with a compromised runtime credential, because the runtime role can set a custom GUC. Keep strict tenant-only RLS on `Organization`; `system_admin` receives no implicit cross-organization organization rows.

**Rationale:** The existing PRD context mechanism is approved, but its security guarantee must not be overstated. The strict directory boundary preserves the Task 1.2.1 decision that global role status alone does not grant tenant-data access.

**Impact:** Retain authenticated membership validation, parameterized ORM/query use, least-privilege database grants, and runtime-role RLS tests. Global CRM directory access remains a separate organization-authorized access/authorization dependency; this task adds no exception or access workflow.

### P1.2.2-D5: Implementation dependency and task order

**Decision:** Record and approve the RLS design now, but defer executable policies and tenant-isolation tests until the Django application/model schema and a PostgreSQL test environment are available. Proceed first to the authorized Task 1.3.1 and model prerequisites for Task 1.3.2, then return to Task 1.2.2.

**Rationale:** The repository currently has no Django project or model tables, and the available environment has no PostgreSQL server/client or Docker. Fixture-only tests or guessed table names would not satisfy the actual-schema test requirement.

**Impact:** Task 1.2.2 remains blocked and incomplete. Do not claim RLS implementation or passing tests until the actual schema suite passes under the runtime identity. The initial sequence in this decision was subsequently updated by P1.2.3-D6.

## Phase 1 Task 1.2.3 Decisions — Tenant Failure Policy

**Decision date:** 2026-10-25
**Status:** Policy decisions and documentation approved; implementation tests remain pending the application/database environment
**Approver:** Project owner and technical/security owner, confirmed in the 2026-10-25 Task 1.2.3 planning interaction

### P1.2.3-D1: Request error semantics and organization privacy

**Decision:** Reject unauthenticated requests through the authentication layer with `401`; reject missing or malformed organization UUID selectors with `400`; return the same `404` outcome for an absent organization and for an organization with no matching authenticated-user membership; and return `403` for a member denied a resource/action.

**Rationale:** Separate authentication, selector syntax, membership, and action authorization failures while preventing organization-existence disclosure.

**Impact:** The request transport and exact API error envelope remain with Task 1.3.3. No denial permits a default-organization or unscoped fallback.

### P1.2.3-D2: Internal context invariant failure

**Decision:** If application code reaches tenant business data without validated transaction-local context, or context disagrees with the validated organization, stop, roll back, return a generic `500` with a correlation identifier, and emit a sanitized operational/security event.

**Rationale:** Missing internal context is a server invariant failure, not a client authorization choice; exposing database/policy details or continuing unscoped is unsafe.

**Impact:** The application must not broadly catch database errors or reinterpret absent RLS rows as permission to run an unscoped query.

### P1.2.3-D3: Permanent worker context failures

**Decision:** Missing/malformed organization context, invalid provenance, mismatched actor/membership/organization, or no-longer-valid membership/authorization is a permanent worker failure with no automatic retry and no tenant business operation. Use the task's existing terminal/dead-letter mechanism where applicable. Transient infrastructure failures may follow their approved retry policy, with context rebuilt and revalidated on every attempt.

**Rationale:** Retrying invalid authority cannot repair it and can repeat unsafe work; transient recovery remains governed by the separately approved retry policy.

**Impact:** Do not introduce new task lifecycle states or treat a context failure as a transient database/network error.

### P1.2.3-D4: Sanitized audit and operational events

**Decision:** Emit minimal structured security events for tenant-selector rejection, membership denial, internal context invariant failure, and invalid worker context. Include timestamp, event category, source component, and request/task correlation ID; include actor/organization identifiers only when validated and needed. Do not log credentials, tokens, full payloads, learner content, raw SQL, or database exception details.

**Rationale:** Support investigation without leaking tenant information or secrets through logs.

**Impact:** Apply the already-approved 365-day audit/security-event retention. This decision adds no alert thresholds.

### P1.2.3-D5: RLS-compatible membership validation order

**Decision:** After authentication and organization UUID syntax validation, establish the selected organization as candidate transaction-local context. Under RLS, perform only the membership lookup constrained by authenticated user ID and selected organization ID. If no matching membership exists, stop and roll back; do not access tenant business data. Apply the same sequence to user-originated worker membership revalidation.

**Rationale:** The approved RLS baseline protects `UserProfile`; membership validation must occur within the selected tenant context rather than through an unscoped query.

**Impact:** This refines the Task 1.2.1 context contract. Candidate context is not authorization; the membership must still match, and the custom-GUC threat limitation approved under P1.2.2-D4 remains.

### P1.2.3-D6: Continue Activity 1.2 before Django prerequisites

**Decision:** After committing and pushing the Task 1.2.2 RLS design checkpoint, proceed to Task 1.2.3 before moving to Task 1.3.1/model prerequisites. Task 1.2.2 remains blocked until the actual Django schema and PostgreSQL test environment are available.

**Rationale:** The project owner directed continuation through the remaining Activity 1.2 security-contract task before starting Activity 1.3.

**Impact:** This updates the earlier sequencing recorded under P1.2.2-D5. It does not remove the implementation prerequisites or authorize claiming Task 1.2.2 complete.