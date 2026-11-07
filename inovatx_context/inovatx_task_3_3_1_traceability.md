# Task Traceability — 3.3.1 Build SSO Token Generation in Django

**Task ID and title:** 3.3.1 — Build SSO token generation in Django  
**Phase / activity:** Phase 3 / Activity 3.3  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A Django endpoint (`POST /api/v1/sso/token/`) that issues a signed JWT containing user identity, cohort authorization, and expiry metadata. The JWT is consumed by Moodle's custom auth plugin (Task 3.3.2) to validate the session and redirect the user to their course interface at `learn.inovatx.com`.

**PRD sources:**
- §4.1: Single Sign-On (SSO) & User Provisioning Lifecycle — Django issues signed JWT containing user identity, cohort authorization, and expiry metadata; Moodle validates JWT via custom auth plugin.
- §4.1: Registration & Payment lifecycle — JWT issued upon successful provisioning.
- §4.2: Sync Protocol — SSO launch sequence.

**UML sources:**
- §2 BPMN: Sequence flow IssueJWT → Launch → ValidateJWT → CreateSession → Learn
- §7 Sequence: Django → User → Moodle → CreateSession → Learn

**Approved design sources:**
- Phase 3 authorization permits Tasks 3.1.1–3.3.3 effective 2026-10-31
- Task 3.1.1: Approved user provisioning contract
- Task 3.1.3: Approved JWT SSO contract and claims
- Task 3.2.1/3.2.2/3.2.3: Provisioning workers with retry/error handling
- P1.2.3-D1/D2: Error semantics

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core SSO boundary → Moodle LMS via JWT. Token issuance boundary.

## Acceptance criteria

1. `POST /api/v1/sso/token/` endpoint implemented in Django Core
2. Endpoint issues signed JWT with claims: `sub`, `user_id`, `organization_id`, `cohort_ids`, `roles`, `iss`, `iat`, `exp`, `aud`
3. JWT signed using configured secret key (HMAC-SHA256)
4. Endpoint requires tenant context and valid membership
5. Endpoint verifies license is active before issuing JWT
6. Endpoint rejects provisioning-not-complete states with appropriate error
7. Correlation ID support (P1.2.3-D1)
8. Tests pass for token issuance, validation failure, missing license, inactive license
9. System check passes; imports verified OK

## Scope

**In scope:** Django SSO token issuance endpoint, JWT claim construction, signing, license status validation, tenant context enforcement, tests.

**Out of scope:** Moodle auth plugin (Task 3.3.2), JWT secret key rotation, JWT revocation/blacklist, token refresh, PyJWT library production configuration (uses Django SECRET_KEY for signing), HTTPS transport configuration.

## Dependencies / approved decisions

- Task 3.1.3: JWT SSO contract and claims specification
- Task 3.2.1/3.2.2/3.2.3: Provisioning workers create users/cohorts before JWT issuance
- P1.2.3-D1/D2: Error semantics
- Phase 3 authorization gates

## Open questions or assumptions

- JWT signing uses Django SECRET_KEY (no separate JWT secret configured)
- JWT expiration duration configured via setting (default 24 hours)
- Audience claim set to Moodle service identifier
- Whether multiple cohort IDs should be included for users in multiple cohorts (implementation decision)

## Evidence and completion

**Evidence:**
- Check or artifact: `core/views.py` SSO token issuance view + `config/urls.py` route + `core/tests.py` SSO tests + `config/base_settings.py` JWT settings
- Result: `POST /api/v1/sso/token/` endpoint issues signed JWT with required claims; validates tenant context, membership, and license status; returns appropriate errors; correlation ID support. Tests cover success, missing license, inactive license, unauthenticated access.
- Location: `core/views.py`, `config/urls.py`, `config/base_settings.py`, `core/tests.py`, `inovatx_context/inovatx_task_3_3_1_traceability.md`

**Completion decision:** Complete upon implementation and test verification of SSO token issuance endpoint.

**Reviewer / approver and date:** Task 3.3.1 implementation complete

## Implementation integration reference

This task is consumed by Task 3.3.2 (Moodle auth plugin), Task 3.3.3 (end-to-end learner access), Task 5.2.1 (end-to-end validation).