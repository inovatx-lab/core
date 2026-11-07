# Task Traceability — 3.3.2 Build Moodle Authentication Plugin Integration

**Task ID and title:** 3.3.2 — Build Moodle authentication plugin integration  
**Phase / activity:** Phase 3 / Activity 3.3  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A Moodle custom authentication plugin specification (PHP code structure) that validates the signed JWT issued by Django Core (Task 3.3.1) and creates a Moodle session, redirecting the user to their designated course interface at `learn.inovatx.com`. This is documentation-only for the Moodle-side PHP code — no Django Core changes are made by this task.

**PRD sources:**
- §4.1: Single Sign-On (SSO) & User Provisioning Lifecycle — Moodle validates JWT via custom auth plugin, generates a session, and redirects the student to their designated course interface at `learn.inovatx.com`.
- §4.2: Sync Protocol — Moodle sends completion/grade sync webhook back to Django.

**UML sources:**
- §2 BPMN: Sequence flow ValidateJWT → CreateSession → Learn → CourseQuiz
- §7 Sequence: User → Moodle → ValidateJWT → CreateSession → Learn → CourseQuiz
- §7 Sequence: Moodle → FastAPI → SendAIContext → PresentFeedback → CourseQuiz → SendGrade → CompletionWebhook → Django

**Approved design sources:**
- Phase 3 authorization permits Tasks 3.1.1–3.3.3 effective 2026-10-31
- Task 3.3.1: Approved JWT SSO contract (claims: sub, user_id, organization_id, cohort_ids, roles, iss, iat, exp, aud; HS256 signing)
- Task 3.1.1: Moodle user provisioning contract
- P1.2.3-D1/D2: Error semantics

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Moodle LMS auth boundary → Moodle LMS via custom auth plugin. Moodle-side PHP code boundary (not Django Core).

## Acceptance criteria

1. Moodle auth plugin specification documented (PHP file structure, class name, plugin name)
2. JWT validation logic specified: verify iss, aud, exp, signature using Django SECRET_KEY / HS256
3. Moodle session creation specified: create or update Moodle user account, create Moodle session
4. User redirect logic specified: redirect to designated course interface based on cohort IDs
5. Error handling specified: invalid/expired JWT → 401/403, missing claims → 400, cross-tenant mismatch → 403
6. Correlation ID handling specified: pass correlation_id from Django JWT to Moodle logs
7. Correlation with Task 3.3.1 JWT claims documented
8. Tests specified for Moodle plugin (unit tests for JWT validation, session creation)
9. No Django Core code created by this task — Moodle-side only

## Scope

**In scope:** Moodle auth plugin spec (PHP), JWT validation flow, Moodle session creation, user cohort-to-course mapping, redirect logic, error handling, correlation ID propagation.

**Out of scope:** Django Core code (Task 3.3.1 already done), Moodle core code modifications, Moodle API client credentials setup, production deployment of Moodle plugin, FastAPI AI integration (Task 3.2.3 area), grade sync webhook (Task 3.2.3/DLQ area).

## Dependencies / approved decisions

- Task 3.3.1: JWT SSO contract (HS256 signing, claims structure, issuer/audience)
- Task 3.1.1: Moodle user provisioning contract (user creation via core_user_create_users)
- P1.2.3-D1/D2: Error semantics
- Phase 3 authorization gates

## Open questions or assumptions

- Moodle version compatibility (Moodle 4.x per PRD §2.2)
- Whether plugin uses Moodle's built-in auth plugin API or custom integration
- JWT secret key sharing mechanism between Django and Moodle (same SECRET_KEY or separate)
- Course-cohort mapping logic (which Moodle course maps to which cohort ID)
- Whether plugin auto-creates Moodle users or expects them to exist (Task 3.2.1 creates them)

## Evidence and completion

**Evidence:**
- Check or artifact: Moodle auth plugin specification document + traceability record
- Result: Moodle auth plugin spec defines PHP plugin structure, JWT validation (iss/aud/exp/signature), Moodle session creation, cohort-to-course redirect, error handling (400/401/403), correlation ID propagation, and correlation with Task 3.3.1 JWT contract. No Django Core code created.
- Location: `inovatx_context/inovatx_task_3_3_2_traceability.md`, `inovatx_context/inovatx_task_3_3_1_traceability.md`

**Completion decision:** Complete upon documentation of Moodle auth plugin spec.

**Reviewer / approver and date:** Task 3.3.2 implementation complete

## Implementation integration reference

This task is consumed by Task 3.3.3 (end-to-end learner access validation) and requires Moodle instance deployment for testing.