# Moodle User Provisioning Contract — Task 3.1.1

**Roadmap task:** 3.1.1 — Define Moodle user provisioning contract  
**Phase / activity:** Phase 3 / Activity 3.1  
**Status:** Documented — contract only, no implementation  
**Traceability:** [Task 3.1.1 traceability record](inovatx_task_3_1_1_traceability.md)

## 1. Purpose and boundary

This document defines the Moodle user provisioning contract for INOVATX Core. It specifies:

- The Moodle REST API endpoints used for provisioning (`core_user_create_users`, `core_cohort_create_cohorts`, `core_cohort_add_cohort_members`)
- The user creation payload schema
- The organization-type branching logic (institutional vs individual)
- The sync flow from Django → Moodle → Django (grade/completion webhook)
- Error handling, retry, and idempotency rules

This is a **documentation contract only**. No Celery tasks, Django views, Moodle API client code, or runtime provisioning logic is created by this task. The contract defines the interface that Task 3.2.1 (Celery task for Moodle user creation) will build against.

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| PRD §4.1 | PRD §4.1 | Django fires async Celery task to execute Moodle REST API (`core_user_create_users`). Institutional accounts use `core_cohort_create_cohorts` + `core_cohort_add_cohort_members`; individual subscriptions enroll users into standard course groups. |
| PRD §4.2 | PRD §4.2 | Webhook: Moodle sends completion/grade sync back to Django. |
| UML §2 BPMN | UML §2 | Sequence: Register → Payment → ReceiveReceipt → Enqueue → ProvisionUser → CreateMoodleUser → OrgType → CreateCohort/AddMembers (institutional) OR IndividualGroup (individual) → IssueJWT → Launch → ValidateJWT → CreateSession → Learn → CourseQuiz → SendAIContext → Socratic → Stream → PresentFeedback → CourseQuiz → SendGrade → CompletionWebhook → End. |
| UML §4 | UML §4 | State machine flows for moodle provisioning states. |
| Decision log P1.2.3-D1 | Phase 0 decision log | Request error semantics — 401/400/404/403/500. |
| Decision log P1.2.3-D2 | Phase 0 decision log | Internal context invariant failure — stop, roll back, generic response with correlation ID. |
| Phase 0 decision log D6 | Phase 0 decision log | Max 5 retries with exponential backoff (5s, 15s, 45s, 2m, 6m); dead-lettered events written to `webhook_dlq` table. |
| Phase 0 decision log D7 | Phase 0 decision log | Per-endpoint idempotency key scope with 24-hour TTL. |
| Phase 0 decision log D8 | Phase 0 decision log | License activates on `succeeded` webhook; `failed`/`expired` triggers license suspension; daily batch reconciliation; 24-hour grace period for settlement delays. |

## 3. Provisioning flow

### 3.1 Trigger

A `payment.succeeded` webhook triggers license activation (`pending` → `active`) per Task 2.2.1 and Task 2.2.3. Once the license is `active`, Django enqueues a Celery task to provision the Moodle user account. Provisioning is **not** triggered on license creation — only on payment success.

### 3.2 Provisioning steps

| Step | Actor | Action | Moodle API endpoint |
|---|---|---|---|
| 1 | Django Celery worker | Create Moodle user account | `core_user_create_users` |
| 2a | Django Celery worker (institutional) | Create Moodle cohort | `core_cohort_create_cohorts` |
| 2b | Django Celery worker (institutional) | Add user to cohort | `core_cohort_add_cohort_members` |
| 2c | Django Celery worker (individual) | Enroll user in standard course group | Moodle enrol API (deferred to Task 3.2.2) |
| 3 | Django Core | Issue SSO JWT | Django internal (Task 3.3.1) |

### 3.3 Organization-type branching

| Org type | Provisioning path |
|---|---|
| `school` | Create cohort → Add members to cohort → Issue JWT |
| `sme` | Create cohort → Add members to cohort → Issue JWT |
| `ngo` | Create cohort → Add members to cohort → Issue JWT |
| `enterprise` | Create cohort → Add members to cohort → Issue JWT |
| `individual` | Enroll in standard course group → Issue JWT |

All org types except `individual` follow the institutional cohort path. `individual` follows the direct enrollment path per PRD §4.1.

## 4. Moodle API contract

### 4.1 Endpoint: `core_user_create_users`

**Purpose:** Create or update a Moodle user account for an INOVATX user.

| Field | Type | Required | Description |
|---|---|---|---|
| `users[0][username]` | string | Yes | Unique Moodle username (derived from Django UserProfile.user.username) |
| `users[0][password]` | string | Yes | Auto-generated secure password (not shared with user) |
| `users[0][firstname]` | string | Yes | User's first name |
| `users[0][lastname]` | string | Yes | User's last name |
| `users[0][email]` | string | Yes | User's email address |
| `users[0][auth]` | string | Yes | `manual` (SSO via JWT handles actual login) |
| `users[0][lang]` | string | No | `en` (default) |
| `users[0][timezone]` | string | No | User's timezone, default `UTC` |

**Response:** Array of user IDs created or updated.

### 4.2 Endpoint: `core_cohort_create_cohorts`

**Purpose:** Create a Moodle cohort for an organization.

| Field | Type | Required | Description |
|---|---|---|---|
| `cohorts[0][name]` | string | Yes | Cohort name (organization name + suffix) |
| `cohorts[0][contextlevel]` | string | Yes | `context` (system context) |
| `cohorts[0][contextinstanceid]` | int | Yes | System context instance ID |
| `cohorts[0][visible]` | int | Yes | `1` (visible) |
| `cohorts[0][description]` | string | No | Organization description |

**Response:** Array of cohort IDs created.

### 4.3 Endpoint: `core_cohort_add_cohort_members`

**Purpose:** Add users to a Moodle cohort.

| Field | Type | Required | Description |
|---|---|---|---|
| `members[0][cohortid]` | int | Yes | Cohort ID |
| `members[0][userid]` | int | Yes | User ID from `core_user_create_users` response |

**Response:** Success indicator.

## 5. Payload example

**Institutional (school) user provisioning request:**

```json
{
  "event_type": "user.provision",
  "organization_id": "d61b0766-1133-4ab1-9011-020a8aef81ce",
  "organization_type": "school",
  "organization_name": "Green Valley School",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "student_user",
  "email": "student@example.com",
  "firstname": "Jane",
  "lastname": "Doe",
  "correlation_id": "f4g5h6i7-j8k9-0l12-m3n4-o5p6q7r8s9t0"
}
```

**Individual user provisioning request:**

```json
{
  "event_type": "user.provision",
  "organization_id": "d61b0766-1133-4ab1-9011-020a8aef81ce",
  "organization_type": "individual",
  "organization_name": "Jane Doe Individual",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "jane_doe",
  "email": "jane@example.com",
  "firstname": "Jane",
  "lastname": "Doe",
  "correlation_id": "f4g5h6i7-j8k9-0l12-m3n4-o5p6q7r8s9t0"
}
```

## 6. Idempotency and retry policy

| Rule | Value | Source |
|---|---|---|
| Max retries | 5 | Decision log D6 |
| Backoff intervals | 5s, 15s, 45s, 2m, 6m | Decision log D6 |
| Idempotency key | Per provisioning request | Decision log D7 |
| Idempotency TTL | 24 hours | Decision log D7 |
| Dead-letter queue | `webhook_dlq` table | Decision log D6 |
| Duplicate detection | By event UUID | P1.2.3-D1 |

A `core_user_create_users` call that returns an existing user (same username/email) is treated as idempotent success — no error, no duplicate user created.

## 7. Error handling

| Condition | Response | Behavior |
|---|---|---|
| Moodle API unreachable | Retry | Up to 5 retries with exponential backoff (D6) |
| Moodle API returns error | Dead-letter | Write to `webhook_dlq` after max retries (D6) |
| Invalid user data | Reject | 400 equivalent; do not create partial user |
| Duplicate user (same username) | Idempotent success | Treat as already provisioned |
| Cross-tenant user mismatch | Reject | 403; organization_id must match user's membership |
| System admin provisioning | Reject | `system_admin` is not a Moodle user |

## 8. Traceability mapping

| Contract element | PRD source | UML source | Approved decision |
|---|---|---|---|
| `core_user_create_users` endpoint | FR-02, §4.1 | §2 BPMN: ProvisionUser | FR-02, Task 2.2.3 |
| `core_cohort_create_cohorts` endpoint | FR-02, §4.1 | §2 BPMN: CreateCohort | FR-02, Task 2.2.3 |
| `core_cohort_add_cohort_members` endpoint | FR-02, §4.1 | §2 BPMN: AddMembers | FR-02, Task 2.2.3 |
| Institutional vs individual branch | §4.1 | §2 BPMN: OrgType gateway | FR-01, Task 2.3.2 |
| Retry policy | NFR-03 | N/A | Decision log D6 |
| Dead-letter queue | NFR-04 | N/A | Decision log D6 |
| Idempotency key + TTL | NFR-04 | N/A | Decision log D7 |
| License activation prerequisite | FR-06 | §4.1 | Decision log D8, Task 2.2.3 |
| SSO JWT issuance | FR-02 | §2 BPMN: IssueJWT | Task 3.3.1 |

## 9. Acceptance criteria

1. `core_user_create_users` endpoint and payload schema documented
2. `core_cohort_create_cohorts` endpoint and payload schema documented
3. `core_cohort_add_cohort_members` endpoint and payload schema documented
4. Institutional org type path (cohort + members) specified
5. Individual org type path (course group enrollment) specified
6. Idempotency and retry policy documented (max 5 retries, exponential backoff, DLQ)
7. Error semantics defined for invalid transitions (400/403/404/500)
8. Cross-tenant isolation maintained (organization_id must match user membership)
9. `system_admin` excluded from Moodle provisioning (not a membership role)
10. Approved decisions referenced (PRD §4.1/FR-02, UML §2, Decision log D6/D7/D8)
11. No runtime implementation created — contract documentation only

## 10. Completion decision

Task 3.1.1 deliverable is complete as a documented provisioning contract:

- Moodle API endpoints and payload schemas specified for user creation, cohort creation, and cohort membership
- Institutional vs individual provisioning paths documented
- Idempotency, retry, and dead-letter policy specified per Decision log D6/D7
- Error semantics defined for all provisioning conditions
- Cross-tenant isolation preserved (organization_id membership validation)
- `system_admin` excluded from Moodle user provisioning
- Approved design decisions preserved (PRD §4.1/FR-02, UML §2, D6/D7/D8)
- No executable implementation created by this task
- Task 3.2.1 (Celery task for Moodle user creation) will implement this contract

**Provisioning contract documented:** 2026-10-31  
**Completion review:** pending

## 11. Open questions

- None blocking Task 3.1.1 contract documentation.
- Exact cohort naming convention for institutional orgs to be clarified in Task 3.2.2.
- Standard course group ID for individual enrollments deferred to Task 3.2.2.
- Webhook signature verification for Moodle → Django grade sync deferred to Task 3.2.3.
