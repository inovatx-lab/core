# INOVATX Core Platform & EdTech LMS Ecosystem
## Product Requirements Document (PRD)

---

## 1. Executive Summary & Vision

### 1.1 Executive Summary
INOVATX is a multi-tenant digital management platform, CRM, and service ecosystem designed to orchestrate diverse software applications, client subscriptions, and business operations. The flagship vertical under INOVATX is an advanced **EdTech Learning Management System (LMS)** targeting African educational institutions, students, parents, SMEs, and NGOs. 

The platform utilizes **Django** as the central hub (CRM, billing, user identity, client portal, multi-tenant database) and **Moodle** as the spoke for course execution and assessment. High-concurrency, interactive Socratic AI tutoring capabilities are handled through a dedicated **FastAPI AI Microservice**, ensuring scalable, human-like interactive learning experiences without jeopardizing main application stability.

### 1.2 Core Objectives
- **Centralized Operations:** Provide a single source of truth for user accounts, billing, organizational hierarchies, and subscription lifecycle management across all INOVATX verticals.
- **Decoupled Architecture:** Maintain an isolated yet tightly linked bridge between INOVATX Core (Django), the Learning Management System (Moodle), and the AI Infrastructure (FastAPI) behind a unified single-VPS Docker deployment.
- **Strict Data Isolation:** Guarantee 100% tenant data separation across multi-branch schools, SMEs, and individual clients using PostgreSQL Row-Level Security (RLS) and Django application-level defense-in-depth.
- **Socratic AI Coaching:** Implement an interactive past-paper and quiz coaching engine that dynamically guides students step-by-step rather than providing direct answers, monetized through tiered fair-use token allowances.

For the first-client MVP, `CRM_BASIC` is limited to global client/account tracking, tenant users' account overview, and a gateway into the tenant's Moodle learning platform. Broader CRM capabilities and advanced SME/NGO modules remain deferred.

---

## 2. System Architecture & Tech Stack

### 2.1 System Topology
The platform employs a **Hub-and-Spoke Decoupled Architecture** deployed on a single high-performance Virtual Private Server (VPS) via Docker Compose.

```
                         [ External Users / Clients ]
                                      │
                                      ▼
                      [ Nginx Reverse Proxy ]
               (SSL Termination / Domain Routing / Rate Limiting)
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
  [ INOVATX Core (Django) ]   [ Moodle LMS Engine ]    [ FastAPI AI Microservice ]
   app.inovatx.com             learn.inovatx.com        ai.inovatx.com (Private/Internal)
   (CRM, Auth, RLS DB,         (Interactive Quizzes,    (Socratic Prompt Engine,
    Billing, Subscriptions)     SCORM, Cohort Sync)      LLM Streaming, Webhooks)
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      │
                                      ▼
                       [ Database & Cache Layer ]
               ├── PostgreSQL (inovatx_db [RLS], moodle_db)
               └── Redis (Session Store, Task Queues, API Caching)
```

> Implementation decision: the public ingress will be standardized on Nginx. FastAPI should remain on a private internal network unless a separate security review explicitly approves a public route.

### 2.2 Technology Stack
* **Primary Core Framework:** Django 5.x (Python 3.12+)
* **Database Management:** PostgreSQL 16+ with Native Row-Level Security (RLS)
* **LMS Engine:** Moodle 4.x (PHP 8.2+ / Apache)
* **AI Engine:** FastAPI (Python 3.12+, AsyncIO, Pydantic v2)
* **Cache & Async Queue:** Redis 7.x + Celery
* **Containerization:** Docker & Docker Compose
* **Web Server / Reverse Proxy:** Nginx with Let's Encrypt SSL

---

## 3. Database Schema & Multi-Tenancy Architecture (Postgres RLS)

To accommodate Layer 07 (Clients and Users: Individuals, Schools, SMEs, NGOs) without requiring future structural database migrations, INOVATX implements a **Polymorphic Multi-Tenant Database Schema**.

### 3.1 Key Entity-Relationship Architecture

```
+-----------------------------------------------------------------------+
|                              ORGANIZATION                             |
+-----------------------------------------------------------------------+
| id (UUID, PK)                                                         |
| name (VarChar)                                                        |
| org_type (Enum: 'individual', 'school', 'sme', 'ngo', 'enterprise')   |
| status (Enum: 'pending', 'active', 'suspended', 'expired', 'cancelled') |
| created_at (Timestamp)                                                |
+-----------------------------------------------------------------------+
                                   │ 1
                                   │
                                   │ N
+-----------------------------------------------------------------------+
|                              USER_PROFILE                             |
+-----------------------------------------------------------------------+
| id (UUID, PK)                                                         |
| user_id (FK -> auth_user.id)                                          |
| organization_id (FK -> organization.id)                               |
| phone_number (VarChar)                                                |
| created_at (Timestamp)                                                |
+-----------------------------------------------------------------------+
                                   │ 1
                                   │
                                   │ N
+-----------------------------------------------------------------------+
|                    ORGANIZATION_MEMBERSHIP_ROLE                       |
+-----------------------------------------------------------------------+
| id (UUID, PK)                                                         |
| user_profile_id (FK -> user_profile.id)                               |
| role_code (Enum: 'org_admin', 'instructor', 'student', 'parent',       |
|            'sme_staff')                                               |
+-----------------------------------------------------------------------+
+-----------------------------------------------------------------------+
|                           SUBSCRIPTION_LICENSE                        |
+-----------------------------------------------------------------------+
| id (UUID, PK)                                                         |
| organization_id (FK -> organization.id)                               |
| product_code (Enum: 'EDTECH_LMS', 'CRM_BASIC', 'AI_PRO')              |
| seat_capacity (Integer)                                               |
| moodle_cohort_id (VarChar, Nullable)                                  |
| status (Enum: 'pending', 'active', 'expired', 'suspended', 'cancelled') |
| ai_monthly_interaction_allowance_per_learner_seat (Integer, AI_PRO)   |
| ai_daily_interaction_cap_per_learner_seat (Integer, AI_PRO)           |
| valid_until (Timestamp)                                               |
+-----------------------------------------------------------------------+
```

Task 1.1.2 defines the canonical enum values and logical validation rules. AI interaction entitlement fields apply only to `AI_PRO`; the approved learner-seat baseline is 1,000 interactions per month and 50 per day. Product-specific seat units and physical enforcement are documented separately from this conceptual ERD.
`OrganizationMembershipRole` is unique per `(user_profile_id, role_code)`; global `system_admin` is not an organization membership role.
The logical relationships are one `Organization` to many `UserProfile` memberships, one `UserProfile` to zero or many `OrganizationMembershipRole` assignments, and one `Organization` to zero or many `SubscriptionLicense` records.
The initial physical schema baseline uses a UUID primary key for `OrganizationMembershipRole` and enforces uniqueness of `(user_profile_id, role_code)`. The initial license baseline has a unique `(organization_id, product_code)` pair and no renewal-history rows.

### 3.2 Row-Level Security (RLS) Implementation
1. **Tenant Identification:** Each tenant-scoped request must explicitly select an organization. After authentication and UUID syntax validation, Django begins a transaction and sets the selected organization as candidate transaction-local context. Because `UserProfile` is RLS-protected, the application then performs only a membership lookup constrained by both the authenticated user and selected organization. If no matching membership exists, it stops and rolls back; no tenant business-data query is permitted before membership validation. The selector transport is defined with the Core API contract. The singular `request.user.userprofile.organization_id` example must not be used for a user with multiple memberships.
2. **Transaction-Local Context:** The application establishes `SET LOCAL app.current_organization_id = '<UUID>'` inside the transaction performing tenant-owned database work, before the membership-validation query. This candidate setting is not proof of authorization; membership must be verified before tenant business queries. Do not retain tenant identity in connection- or session-scoped state.
3. **Postgres RLS Rule:**
   ```sql
   ALTER TABLE student_data ENABLE ROW LEVEL SECURITY;
   ALTER TABLE student_data FORCE ROW LEVEL SECURITY;

   CREATE POLICY tenant_isolation_policy ON student_data
   FOR ALL
   TO inovatx_app_role
   USING (organization_id = current_setting('app.current_organization_id')::uuid);
   ```
4. **Connection Pool Protection:** Transaction completion clears the `SET LOCAL` value. Request and task teardown must leave borrowed connections clean and must not rely on a connection-scoped tenant setting.
5. **Background Worker Context:** Each tenant-scoped Celery task must carry an explicit organization identifier and establish its own candidate transaction-local context. User-originated tasks preserve actor/membership identity when applicable; under that candidate context, the worker performs only the matching membership lookup and revalidates applicable authorization before tenant business operations. System/event-originated tasks preserve explicit provenance. Every execution attempt establishes its own context. A worker must not inherit a tenant from a request, shared thread, global state, or prior connection use.
6. **Tenant Coverage:** Every tenant-owned table in the Django database must carry an `organization_id` or an equivalent tenant key and be protected by PostgreSQL RLS plus Django application-level validation. The global `system_admin` role does not itself grant access to tenant-owned data or an implicit all-tenant context. Any assistance requiring access beyond an organization's normal roles and permissions must be requested from that organization; the request and approval workflow is not defined here.

> Implementation note: Missing, invalid, or unauthorized tenant context must fail closed. Cross-tenant reads or writes are blocked by policy enforcement and application-layer validation. The tenant failure policy in Task 1.2.3 defines denial semantics; the exact API error schema remains with Task 1.3.3. `student_data` and `inovatx_app_role` in the sample policy above are illustrative only. The Task 1.2.2 design decision log approves separated bootstrap, schema-owner, migrator, and runtime authorities, plus strict tenant-only RLS for the four initial Core tenant tables; exact role/table identifiers depend on the Django schema. Because the runtime role can change a custom GUC, this context mechanism does not independently protect against arbitrary SQL under a compromised runtime credential. Executable policies and actual-schema tests remain pending until the Django schema and PostgreSQL test environment exist.
---

## 4. Decoupled Moodle LMS Integration

### 4.1 Single Sign-On (SSO) & User Provisioning Lifecycle
1. **Registration & Payment:** User or Institutional Admin registers at `app.inovatx.com` and completes payment via local mobile money or card gateways.
2. **Automated Moodle Account Creation:** Django fires an asynchronous Celery task to execute Moodle REST API (`core_user_create_users`).
3. **Cohort Association:** 
   * For institutional accounts (Schools), Django calls `core_cohort_create_cohorts` and assigns users via `core_cohort_add_cohort_members`.
   * For individual subscriptions, users are enrolled directly into standard course groups.
4. **Seamless Redirection (SSO):**
   * When clicking "Launch Learning Hub", INOVATX issues a signed JWT token containing user identity, cohort authorization, and expiration metadata.
   * Moodle validates the JWT via a custom auth plugin, generates a session, and redirects the student to their designated course interface at `learn.inovatx.com`.

### 4.2 Sync Protocol (Webhooks)
```
+----------------+                +-------------------+                +----------------+
| INOVATX Django |                |    Moodle Engine  |                | FastAPI Engine |
+-------+--------+                +---------+---------+                +-------+--------+
        |                                   |                                  |
        | 1. Create User & Sync Cohort API  |                                  |
        |---------------------------------->|                                  |
        |                                   |                                  |
        | 2. Redirect User via SSO JWT      |                                  |
        |---------------------------------->|                                  |
        |                                   | 3. Quiz Submission / Event       |
        |                                   |--------------------------------->|
        |                                   |                                  |
        |                                   | 4. Socratic AI Feedback Stream   |
        |                                   |<---------------------------------|
        | 5. Webhook: Sync Completion/Grade |                                  |
        |<----------------------------------|                                  |
```

---

## 5. FastAPI Socratic AI Microservice

### 5.1 Architecture & Workflow
The AI Engine operates as an asynchronous FastAPI sub-application optimized for multi-turn Socratic interaction.

1. **Question Context Injection:** When a student encounters a problem or submits an incorrect response inside a Moodle quiz, Moodle dispatches an async payload to FastAPI (`/api/v1/ai/socratic-eval`).
2. **Prompt Orchestration:** FastAPI combines:
   * The question stem and past-paper rubric solution.
   * The student's submitted working/answer.
   * System Prompt (Socratic Directive: *Guide step-by-step; never give the direct final answer*).
   * Student's historical mastery score for the topic.
3. **Streaming Response:** The AI streams real-time feedback back into the quiz UI via Server-Sent Events (SSE).

### 5.2 Token Budgeting & Tiered Model Management
- **Centralized Key Management:** All API keys (OpenAI, Anthropic, or self-hosted LLMs) reside strictly inside environment variables in the FastAPI container. End-users do not provide keys.
- **Token Allowance Ledger:**
  - Standard Student Plan: 500 Socratic Interactions / Month.
  - Institutional Plan: Pooled organization-wide allowance calculated per active student seat.
  - The platform will maintain a usage ledger to reserve, consume, and reconcile allowance atomically, rather than relying only on a mutable monthly counter.
- **Fallback Logic:** If high-tier model quotas are reached, FastAPI automatically downgrades non-critical interactions to lighter models (e.g., Llama-3/Qwen) to maintain 100% service uptime while capping costs.
- **Network Access Policy:** FastAPI should be exposed only on the internal Docker network by default. Moodle or Django should call it through authenticated server-to-server communication; public access must be explicitly reviewed and rate-limited if required.
- **Allowance Semantics:** Customer-facing `interactions` will be mapped to internal token accounting and provider cost tracking. Allowance exhaustion should result in a defined, non-ambiguous response such as graceful downgrade, lockout, or a user-visible limit notice.

> Implementation decision: `interaction` is the product-level unit, while tokens represent cost and provider usage measurement. The system must reconcile both for fair-use enforcement and financial reporting.

---

## 6. Functional & Non-Functional Requirements

### 6.1 Functional Requirements
* **FR-01 (Multi-Tenant Onboarding):** The system must allow individual registration, parent-child account mapping, and bulk CSV enrollment for educational institutions.
* **FR-02 (Automated Provisioning):** Payment receipt must trigger automated enrollment into Moodle cohorts within < 3 seconds.
* **FR-03 (Socratic Feedback):** The AI engine must return step-by-step guidance within < 1.5 seconds latency (first token stream).
* **FR-04 (Role-Based Access Control):** System admins, org managers, instructors, parents, and students must have distinct permission boundaries in both Django and Moodle.
* **FR-05 (Membership-Based Authorization):** Authorization must be enforced by role and organization membership. A global system role (`system_admin`) is distinct from a tenant-scoped org role (`org_admin`), and permissions must be granted by resource and action rather than broad inheritance.
* **FR-06 (Subscription & Payment Lifecycle):** The system must distinguish between organization status, license status, and payment status. A non-final `valid_until` date must not be treated as the full lifecycle definition for a subscription or payment.
* **FR-07 (Usage Ledger & Fair-Use Enforcement):** The system must maintain a ledger of AI interactions and provider token usage to enforce monthly allowance limits, model fallback rules, and institutional pool calculations across active student seats.

### 6.2 Non-Functional Requirements
* **NFR-01 (Data Security & Isolation):** Zero cross-tenant data access. Automated database integration tests must verify PostgreSQL RLS boundary enforcement on every build.
* **NFR-02 (Scalability):** The system must support at least 500 concurrent quiz takers on a standard VPS through asynchronous FastAPI request processing and Redis caching.
* **NFR-03 (High Availability):** Background workers (Celery/Redis) must implement automatic retries with exponential backoff for failed payment webhooks or Moodle API calls.
* **NFR-04 (Integration Contracts & Webhooks):** Payment, Moodle, AI, and grade synchronization interfaces must use versioned payloads, signed webhooks, idempotency checks, replay protection, and dead-letter handling for irreversible failures.
* **NFR-05 (SLOs & Operational Readiness):** The platform must define measurable service-level targets for provisioning, AI first-token latency, system uptime, backups, and restoration procedures before production deployment.

---

## 7. Target-State Implementation Decisions

The following decisions resolve the main ambiguities in the PRD and should be treated as implementation guidance for the build phase.

1. **Role and Authorization Model:** `system_admin` is global and is not a membership role. Use `org_admin`, `instructor`, `student`, `parent`, and `sme_staff` as organization-scoped membership role codes. `instructor` is the canonical code for teachers, lecturers, mentors, and similar teaching roles. Permission grants remain resource/action based and are not defined by the role code alone.
2. **Organization and License Status Values:** Use `pending`, `active`, `suspended`, `expired`, and `cancelled` as the allowed values for both `Organization.status` and `SubscriptionLicense.status`, with the two lifecycles kept separate from each other and from `Payment.status`. For a license, `pending` means the entitlement exists but is not usable. Lifecycle transitions remain with the assigned lifecycle task.
3. **Subscription & Payment Lifecycle:** Use separate state machines for subscriptions and payments. A license is not equivalent to a payment outcome; payment state should be tracked independently from license validity.
4. **AI Allowance Semantics:** Define customer-facing `interactions` distinct from internal provider `tokens`. Maintain a usage ledger to reserve and reconcile allowance atomically, with institutional pool calculations based on active seat capacity and a fixed billing reset window.
5. **AI Network Path:** Keep FastAPI on a private internal network behind the public edge. Moodle and Django should access it through authenticated internal service channels; public exposure must be explicitly approved and rate-limited if absolutely required.
6. **Proxy Standardization:** Use Nginx as the public reverse proxy and TLS entry point. Traefik should be removed as an active design choice unless there is a deliberate operational reason to switch.
7. **Webhook Contracts:** Use signed, versioned webhook payloads for payment events, Moodle completion updates, and AI/grade synchronization events. Include event IDs, timestamps, idempotency keys, and replay protection.
8. **Tenant Coverage & RLS:** Every tenant-owned table must enforce `organization_id` or equivalent tenant scoping and must pass both RLS and Django application checks. Celery tasks must resolve tenant context explicitly before database operations.
9. **Operational Readiness:** Define SLOs for first-token latency, provisioning latency, uptime, backups, and restoration testing before production deployment. A single-VPS prototype is acceptable for validation, but production-grade service guarantees require a documented architecture and redundancy plan.
10. **Data Model Expansion:** Add first-class entities for payment events, AI interaction logs, usage ledger entries, enrollments, and grade records if they are required for operational control, fairness enforcement, or reporting.

---

## 8. Operational Roadmap & Future Expansion

* **Phase I (Immediate Target):** Prototype deployment of Django Core, PostgreSQL with RLS, Moodle Engine setup, SSO integration, and interactive quiz integration with Socratic FastAPI engine.
* **Phase II:** Expansion to institutional multi-branch reporting, parent real-time analytics dashboards, and mobile money payment automated reconciliation queues.
* **Phase III:** Generalization of INOVATX CRM & Project Management layers for SME and NGO client onboarding beyond EdTech.