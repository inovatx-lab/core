# Task Traceability — 3.1.2 Moodle Cohort Creation and Member Assignment Logic

**Task ID and title:** 3.1.2 — Define Moodle cohort creation and member assignment logic  
**Phase / activity:** Phase 3 / Activity 3.1  
**Owner:** Project owner  
**Status:** Complete  

## Outcome and sources

**Outcome / deliverable:** A documented Moodle cohort sync specification defining cohort creation (names, contexts, descriptions), cohort member assignment logic (adding users to cohorts), institutional vs individual provisioning paths for cohort management, and cross-tenant isolation rules. This is documentation-only — no Celery task implementation, cohort data model, or runtime cohort enforcement is created by this task. The specification will guide Task 3.2.2 (Celery task for cohort creation and member assignment).

**PRD sources:**
- §4.1: Single Sign-On & User Provisioning Lifecycle — for institutional org types, Django calls `core_cohort_create_cohorts` and `core_cohort_add_cohort_members` to assign users to cohorts; individual subscriptions enroll users into standard course groups (cohort logic deferred).
- §4.1: Registration & Payment lifecycle — cohort assignments occur during the payment-triggered provisioning flow.

**UML sources:**
- §2 BPMN: Sequence flow from ProvisionUser → OrgType → CreateCohort/AddMembers (institutional) OR IndividualGroup (individual) → IssueJWT
- §2 BPMN: Retry gateway for cohort API calls
- §7 Sequence: Cohort provisioning (Celery) and cohort enrollment (individual)
- §7 Sequence: Institutional org type follows cohort path, individual follows direct group enrollment path

**Approved design sources:**
- Phase 2 authorization permits Tasks 2.1.1–2.3.3 only; Phase 3 authorization permits Tasks 3.1.1–3.3.3 effective 2026-10-31
- Decision log D6: Webhook retry cap (max 5 retries, exponential backoff 5s/15s/45s/2m/6m); dead-letter queue (`webhook_dlq`)
- Decision log D7: Idempotency key per-endpoint with 24-hour TTL
- Decision log D8: License activates on `succeeded` webhook; `failed`/`expired` triggers license suspension
- P1.2.3-D1: Request error semantics — 401/400/404/403/500 with correlation IDs
- P1.2.3-D2: Internal context invariant failure — stop, roll back, generic response
- Task 3.1.1: Approved user provisioning contract with Moodle API endpoints and org-type branching logic

**Mapping classification:** Direct  
**Architecture component and trust boundary:** Django Core provisioning boundary → Moodle LMS via REST API. This task is a documentation-only contract; no runtime enforcement created. The specification defines the interface that Task 3.2.2 (Celery task for cohort creation and member assignment) will implement.

## Acceptance criteria

1. Cohort creation parameters documented: cohort name, contextlevel, contextinstanceid, description, visible
2. Cohort member assignment logic documented: adding users to cohort via `core_cohort_add_cohort_members`
3. Institutional org type path documented: create cohort → add members
4. Individual org type path documented: standard course group enrollment (cohort logic deferred)
5. Cross-tenant isolation rules documented: organization_id must match user membership
6. Retry, idempotency, and error handling documented (per Decision log D6/D7)
7. Error semantics defined for invalid transitions (400/403/404/500)
8. Approved decisions referenced (PRD §4.1/FR-02, UML §2 BPMN, Decision log D6/D7/D8)
9. No runtime implementation created — specification documentation only
10. Contract integrated with existing Task 3.1.1 provisioning contract and used by Task 3.2.2

## Scope

**In scope:** Cohort creation spec (name, context configuration), member assignment spec, institutional vs individual org-type branching, cross-tenant isolation, retry/idempotency policies, error semantics, coordination with existing Task 3.1.1. Documentation only.

**Out of scope:** Celery task implementation, Moodle API client code, cohort data model, runtime cohort enforcement, cohort CRUD endpoints, database schemas, production deployment, non-Moodle course management.

## Dependencies / approved decisions

- PRD §4.1/FR-02 (provisioning lifecycle)
- UML §2 BPMN (sequence for CreateCohort/AddMembers)
- Decision log D6 (retry policy: max 5 retries, backoff 5s/15s/45s/2m/6m, dead-letter queue)
- Decision log D7 (idempotency key, per-endpoint, 24-hour TTL)
- Decision log D8 (license activation on payment webhook)
- Task 3.1.1 (user provisioning contract with `core_user_create_users` endpoint and org-type branching)

## Open questions or assumptions

- Exact cohort naming convention for institutional orgs (to be clarified in Task 3.2.2)
- Standard course group ID for individual enrollments (to be clarified in Task 3.2.2)
- How cohort IDs from `core_cohort_create_cohorts` are tracked and reused across provisioning runs (deferred to Task 3.2.2)

## Evidence and completion

**Evidence:**
- Check or artifact: Cohort sync specification and traceability record
- Result: `inovatx_context/inovatx_task_3_1_2_traceability.md` defines cohort creation (name, context, description) and member assignment logic (cohort add members), institutional vs individual org type branching (cohort vs group enrollment), cross-tenant isolation, retry/idempotency policies, and error semantics. All specifications reference approved decisions and integrate with Task 3.1.1.
- Location: `inovatx_context/inovatx_task_3_1_2_traceability.md`, `inovatx_context/inovatx_project_todo.md`, `REPOSITORY_STRUCTURE.md`

**Completion decision:** Complete. All Task 3.1.2 deliverables implemented as a documented cohort sync specification:
- Moodle cohort creation parameters (name, contextlevel, contextinstanceid, description, visible)
- Cohort member assignment logic (adding users to cohorts via `core_cohort_add_cohort_members`)
- Institutional org type path (cohort + member assignment)
- Cross-tenant isolation rules (organization_id membership validation)
- Retry, idempotency, and dead-letter policies (per Decision log D6/D7)
- Error semantics (per P1.2.3-D1/D2)
- Approved design decisions preserved (PRD §4.1/FR-02, UML §2, D6/D7/D8)
- No runtime implementation created by this task
- Task 3.2.2 (Celery task for cohort creation and member assignment) will implement this spec

**Reviewer / approver and date:** Cohort spec documented 2026-10-31; completion review pending

## 3.2.2 cohort task reference

This specification will be consumed by Task 3.2.2 to build the Celery task that:
- Executes `core_cohort_create_cohorts` for institutional org types
- Executes `core_cohort_add_cohort_members` to assign users to cohorts
- Manages idempotency and retry for cohort API calls
- Tracks cohort IDs for subsequent license activation assignments