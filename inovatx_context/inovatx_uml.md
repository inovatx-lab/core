# INOVATX System Models

These diagrams translate the INOVATX PRD into eight system views. They are intentionally limited to facts stated in the PRD. Where the PRD does not define a relationship, lifecycle, permission, or protocol detail, this document marks it as unresolved rather than treating an assumption as a requirement.

## Modeling Conventions

- **Django Core**, **Moodle LMS**, and **FastAPI AI** are separate application boundaries in a hub-and-spoke architecture.
- Payment gateways and LLM providers are external systems. PostgreSQL, Redis, and Celery are infrastructure components.
- Organization types (`individual`, `school`, `sme`, `ngo`, `enterprise`) are data values, not user roles or actors.
- Mermaid has no native use-case or BPMN notation. The use-case view uses a boundary-and-association flowchart; the BPMN view uses participant subgraphs, events, and gateways. They communicate those concepts but are not formal UML Use Case or BPMN 2.0 exchange diagrams.
- Connections between human actors and use cases describe candidate goals, not a final authorization matrix. The PRD names roles but does not map every role to each permission.
- The Class Diagram is a conceptual code-structure proposal inferred from component responsibilities. It is not documentation of an existing implementation.
- **Target-state decision:** distinguish global `system_admin` from tenant-scoped `org_admin`, with other roles realized as membership-specific permissions rather than global user roles.
- **Target-state decision:** maintain separate lifecycle state machines for `Organization`, `SubscriptionLicense`, and `Payment` instead of treating `valid_until` as the full lifecycle definition.
- **Target-state decision:** treat AI allowance as a customer-facing interaction budget that is reconciled against provider-token usage in a usage ledger, while model fallback remains a non-critical interaction policy.
- **Target-state decision:** prefer a private FastAPI service path behind the Django/Moodle trust boundary, with Nginx as the only public reverse proxy and internal service-to-service authentication for AI requests.
- **Target-state decision:** use a single, explicit proxy choice—Nginx—unless the deployment architecture is separately updated to justify Traefik.

## 1. Use Case Diagram: Scope

The system boundary encloses the product responsibilities across Core, Moodle, and AI. External providers are outside it. Role-goal associations are deliberately broad: FR-04 requires distinct permissions, but the PRD does not provide the permission matrix.

```mermaid
flowchart LR
    subgraph Humans[Human Actors]
        Individual[Individual client]
        OrgManager[Organization manager or admin]
        Teacher[Teacher or instructor]
        Student[Student]
        Parent[Parent]
        SMEStaff[SME staff]
        SysAdmin[System administrator]
    end

    Payment[Payment gateway\nmobile money or card]
    LLM[LLM provider\nexternal or self-hosted]

    subgraph Platform[INOVATX Platform]
        subgraph Core[Django Core]
            UCRegister([Register account or organization])
            UCOrg([Manage organization and users])
            UCRoles([Apply role-based access])
            UCParent([Map parent and child accounts])
            UCBulk([Bulk-enroll users from CSV])
            UCPay([Complete payment])
            UCLicense([Manage subscription license])
            UCProvision([Provision Moodle user and cohort])
            UCSSO([Issue learning-hub SSO token])
            UCGrade([Receive completion or grade webhook])
        end

        subgraph LMS[Moodle LMS]
            UCLearn([Launch learning hub])
            UCCourse([Access courses and groups])
            UCQuiz([Attempt interactive quiz])
        end

        subgraph AI[FastAPI AI Service]
            UCCoach([Request Socratic coaching])
            UCStream([Stream feedback to quiz UI])
        end
    end

    Individual -. candidate goal association .-> UCRegister
    Individual -. candidate goal association .-> UCPay
    OrgManager -. candidate goal association .-> UCOrg
    OrgManager -. candidate goal association .-> UCBulk
    OrgManager -. candidate goal association .-> UCLicense
    SysAdmin -. candidate goal association .-> UCOrg
    SysAdmin -. candidate goal association .-> UCRoles
    Teacher -. role permissions not specified .-> UCCourse
    Student -. candidate goal association .-> UCLearn
    Student -. candidate goal association .-> UCQuiz
    Student -. candidate goal association .-> UCCoach
    Parent -. parent-child mapping specified; viewing rights not defined .-> UCParent
    SMEStaff -. SME role named; use cases not detailed .-> UCOrg

    Payment --> UCPay
    UCPay --> UCProvision
    UCProvision --> UCSSO
    UCSSO --> UCLearn
    UCLearn --> UCCourse
    UCCourse --> UCQuiz
    UCQuiz --> UCCoach
    UCCoach --> UCStream
    LLM --> UCCoach
    UCQuiz --> UCGrade
```

**Included scope:** registration, organization and user administration, role boundaries, parent-child mapping, institutional CSV enrollment, payment, licenses, Moodle account/cohort provisioning, SSO launch, course/quiz use, Socratic feedback, and grade/completion synchronization.

**Open scope boundary:** the PRD does not specify detailed CRM or project-management use cases for the future SME/NGO expansion, or permissions for each named actor.

## 2. BPMN: Business Process

This BPMN-inspired view centers on paid onboarding and Moodle provisioning, then shows the learning and coaching continuation. The PRD specifies payment receipt as the trigger for asynchronous provisioning, institutional versus individual enrollment, and exponential-backoff retries for failed payment webhooks or Moodle API calls. It does not specify payment reconciliation or the detailed exception/end states.

```mermaid
flowchart TB
    Start((Start)) --> Register
    subgraph UserLane[User or organization administrator]
        Register[Submit registration and organization details]
        CompletePayment[Complete payment using mobile money or card]
        Launch[Select Launch Learning Hub]
        Learn[Use Moodle course or quiz]
        SubmitAnswer[Submit quiz response or working]
    end

    subgraph GatewayLane[Payment gateway]
        ProcessPayment[Process payment]
        SendReceipt[Send payment receipt or webhook]
    end

    subgraph CoreLane[Django Core and Celery]
        ReceiveReceipt[Receive payment receipt]
        Enqueue[Enqueue asynchronous provisioning task]
        RetryGate{Payment webhook or Moodle API call failed?}
        Backoff[Retry with exponential backoff]
        OrgType{Institutional organization?}
        CreateCohort[Create Moodle cohort]
        AddMembers[Assign users to cohort]
        IndividualGroup[Enroll individual in standard course group]
        ProvisionUser[Create Moodle user]
        IssueJWT[Issue signed SSO JWT with identity, cohort authorization, expiry]
        CompletionWebhook[Receive Moodle completion or grade webhook]
        End((Provisioned / process complete))
    end

    subgraph MoodleLane[Moodle LMS]
        CreateMoodleUser[Create or update Moodle account]
        ValidateJWT[Validate JWT with custom auth plugin]
        CreateSession[Create Moodle session and redirect]
        CourseQuiz[Serve course, group, and quiz]
        SendAIContext[Dispatch question, rubric, answer, mastery context to FastAPI]
        PresentFeedback[Present streamed feedback in quiz UI]
        SendGrade[Send completion or grade event]
    end

    subgraph AILane[FastAPI AI service]
        Socratic[Orchestrate Socratic evaluation]
        Stream[Stream feedback using SSE]
    end

    Register --> CompletePayment --> ProcessPayment --> SendReceipt --> ReceiveReceipt --> Enqueue
    Enqueue --> ProvisionUser --> CreateMoodleUser
    CreateMoodleUser --> OrgType
    OrgType -->|Yes: school or other institution| CreateCohort --> AddMembers --> IssueJWT
    OrgType -->|No: individual subscription| IndividualGroup --> IssueJWT
    IssueJWT --> Launch
    Launch --> ValidateJWT --> CreateSession --> Learn --> CourseQuiz
    CourseQuiz --> SubmitAnswer --> SendAIContext --> Socratic --> Stream --> PresentFeedback
    PresentFeedback --> CourseQuiz
    CourseQuiz --> SendGrade --> CompletionWebhook --> End

    CreateMoodleUser -. API error .-> RetryGate
    ReceiveReceipt -. webhook failure .-> RetryGate
    RetryGate -->|Yes| Backoff --> Enqueue
    RetryGate -->|No| End
```

**Process notes:** The success path is explicit in the PRD, but the failed-payment outcome, retry count/limits, duplicate-event handling, dead-letter handling, and manual recovery process are not defined. The “No” exit from the retry gateway indicates an unspecified terminal/error outcome, not a prescribed business result. The under-three-second provisioning target is a requirement, but its start/end measurement points and percentile are unspecified.

## 3. Flow Chart: Socratic AI Logic

The flow represents only stated orchestration and fallback behavior. It does not invent a quota-exhaustion response or an exact ordering for usage accounting, prompt creation, and model selection.

```mermaid
flowchart TD
    Moodle[Moodle quiz submits question, rubric solution, student working or answer, topic mastery] --> Receive[FastAPI receives Socratic evaluation request]
    Receive --> Context[Combine problem context, student response, mastery score, and Socratic directive]
    Context --> Policy[Apply model and allowance policies\nexact evaluation order unspecified]
    Policy --> HighTier{High-tier model quota reached?}
    HighTier -->|No| HighModel[Use selected high-tier model]
    HighTier -->|Yes| Fallback[Downgrade non-critical interaction to a lighter model]
    HighModel --> Generate[Generate guided, step-by-step feedback\nwithout giving the direct final answer]
    Fallback --> Generate
    Generate --> FirstToken[Stream first response token\nPRD target: under 1.5 seconds]
    FirstToken --> SSE[Continue streaming feedback using SSE]
    SSE --> QuizUI[Return feedback to Moodle quiz UI]

    AllowanceNote[Allowance requirements: 500 standard-plan interactions per month; institutional pool calculated per active student seat. Schema tracks tokens. Exact counting, enforcement, and exhausted-allowance behavior are unspecified.]
    Policy -. unresolved quota rules .-> AllowanceNote
    SecretNote[Provider API keys remain in FastAPI environment variables; end users do not supply keys.]
    HighModel -. credentials boundary .-> SecretNote
```

**Unspecified logic:** whether the monthly allowance is checked before or after model selection; how “interaction” maps to tokens; how pooled allowance is calculated and reserved concurrently; what response is returned when a student or institution exhausts the allowance; how critical versus non-critical interactions are classified; retry/timeout behavior for provider failures; and how mastery scores are obtained and updated.

## 4. State Machine: Statuses

The PRD explicitly defines the organization status enum, but the implementation needs a fuller lifecycle model. The state diagram below is the recommended target state model after resolving the open decisions: it distinguishes organization status from subscription and payment state, and it defines a suspension and reinstatement path including renewal and expiry behavior.

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Active : enrollment approved
    Pending --> Suspended : verification blocked / onboarding failed
    Active --> Suspended : org admin action or policy violation
    Active --> Expired : subscription expired
    Expired --> Active : renewal completed
    Suspended --> Active : reinstated after review
    Suspended --> Cancelled : organization terminated
    Active --> Cancelled : cancellation or closure
    Cancelled --> [*]
    Expired --> [*]

    state "pending" as Pending
    state "active" as Active
    state "suspended" as Suspended
    state "expired" as Expired
    state "cancelled" as Cancelled
```

**Status coverage:** The PRD explicitly supports `pending`, `active`, and `suspended` for `Organization`. The recommended target-state model adds `expired` and `cancelled` because a subscription and organization lifecycle cannot be treated as complete if it lacks renewal, cancellation, and reinstatement semantics. These are not source PRD states; they are design decisions made to resolve the missing lifecycle questions.

**Recommended design decisions:**
- `Organization.status` and `SubscriptionLicense.status` should remain separate. `valid_until` alone is not a complete lifecycle.
- `Payment.status` should be modeled separately as `pending`, `succeeded`, `failed`, and `cancelled` with an event log for retries and webhooks.
- Moodle provisioning tasks should have a retry / dead-letter lifecycle distinct from the license lifecycle.
- AI interaction usage should be tracked in a ledger, not inferred only from a current-month counter.

## 5. ERD: Database

The ERD contains the entities and relationships explicitly described in the PRD. The authentication user represents Django's `auth_user` reference; no extra profile fields are assumed for it.

```mermaid
 erDiagram
    AUTH_USER ||--o{ USER_PROFILE : "has organization memberships"
    ORGANIZATION ||--o{ USER_PROFILE : "has memberships"
    USER_PROFILE ||--o{ ORGANIZATION_MEMBERSHIP_ROLE : "has role assignments"
    ORGANIZATION ||--o{ SUBSCRIPTION_LICENSE : "has product licenses"

    AUTH_USER {
        integer id PK
    }

    ORGANIZATION {
        uuid id PK
        varchar name
        enum org_type "individual | school | sme | ngo | enterprise"
        enum status "active | suspended | pending"
        timestamp created_at
    }

    USER_PROFILE {
        uuid id PK
        integer user_id FK
        uuid organization_id FK
        varchar phone_number
        timestamp created_at
    }

    ORGANIZATION_MEMBERSHIP_ROLE {
        uuid user_profile_id FK
        enum role_code
    }

    SUBSCRIPTION_LICENSE {
        uuid id PK
        uuid organization_id FK
        enum product_code "EDTECH_LMS | CRM_BASIC | AI_PRO"
        integer seat_capacity
        varchar moodle_cohort_id "nullable"
        enum status
        integer ai_monthly_interaction_allowance_per_learner_seat
        integer ai_daily_interaction_cap_per_learner_seat
        timestamp valid_until
    }
```

**Database and isolation constraints:** the PRD places Django application data in PostgreSQL database `inovatx_db` with RLS and Moodle data in `moodle_db`. Because a user may have memberships in multiple organizations, tenant context must be selected from an explicitly identified and validated `UserProfile` membership; the PRD's singular `request.user.userprofile.organization_id` example must not be implemented literally. Middleware injects the validated organization using `SET LOCAL`; tenant tables enable and force RLS; policies compare `organization_id` with the session setting; request teardown resets borrowed connections. Missing, invalid, or unauthorized membership context must fail closed. `student_data` is used as an RLS example, but its schema and relationship are not defined.

**Resolved cardinality for Task 1.1.1:** one auth user may have memberships in multiple organizations, with at most one `UserProfile` per `(user_id, organization_id)`. One membership may have multiple organization-scoped role assignments. An organization may have multiple product licenses, with at most one current license per `(organization_id, product_code)`. These are recorded as project-owner decisions P1.1.1-D1 and P1.1.1-D2 in the Phase 0 decision log. Physical constraints, role enums, and lifecycle behavior remain assigned to their roadmap tasks.

**Schema omissions, not added as requirements:** payments, invoices, renewals, refunds, parent-child links, branches, enrollment records, courses, quizzes, assessments, grades, AI interactions, token-usage ledger entries, audit events, and webhook deliveries. These may be necessary implementation entities, but the PRD does not specify them.

## 6. Class Diagram: Code Structure

This is a conceptual decomposition of responsibilities named in the PRD, not a claim about existing source files or final class names. Django is the central hub; Moodle and the AI service remain separate applications.

```mermaid
classDiagram
    class DjangoCore {
        +identity and organization management
        +billing and subscription management
        +tenant-scoped request handling
    }
    class Organization {
        +id: UUID
        +name: string
        +org_type: enum
        +status: enum
    }
    class UserProfile {
        +id: UUID
        +user_id: FK
        +organization_id: FK
        +phone_number: string
    }
    class OrganizationMembershipRole {
        +user_profile_id: FK
        +role_code: enum
    }
    class SubscriptionLicense {
        +id: UUID
        +organization_id: FK
        +product_code: enum
        +seat_capacity: integer
        +moodle_cohort_id: string?
        +status: enum
        +ai_monthly_interaction_allowance_per_learner_seat: integer
        +ai_daily_interaction_cap_per_learner_seat: integer
        +valid_until: timestamp
    }
    class TenantContextMiddleware {
        +derive organization context
        +set transaction-local PostgreSQL setting
        +reset connection on teardown
    }
    class MoodleProvisioningTask {
        +create or sync Moodle users
        +create institutional cohorts
        +assign cohort members
        +retry with exponential backoff
    }
    class MoodleRESTClient {
        +core_user_create_users()
        +core_cohort_create_cohorts()
        +core_cohort_add_cohort_members()
    }
    class SSOIssuer {
        +issue signed JWT
        +include identity, cohort authorization, expiry
    }
    class MoodleAuthPlugin {
        +validate SSO JWT
        +create Moodle session
    }
    class MoodleEngine {
        +courses, groups, cohorts, quizzes
        +send AI evaluation context
        +send completion or grade webhook
    }
    class SocraticEvaluationRequest {
        +question stem
        +rubric solution
        +student working or answer
        +topic mastery context
    }
    class SocraticOrchestrator {
        +assemble Socratic prompt
        +apply model fallback policy
        +stream feedback using SSE
    }
    class LLMProviderAdapter {
        +call configured model provider
        +use credentials from environment
    }

    DjangoCore --> Organization : manages
    DjangoCore --> UserProfile : manages
    UserProfile --> OrganizationMembershipRole : assigned roles
    DjangoCore --> SubscriptionLicense : manages
    TenantContextMiddleware ..> DjangoCore : protects tenant requests
    MoodleProvisioningTask --> MoodleRESTClient : provisions through
    MoodleProvisioningTask ..> SubscriptionLicense : reads license context
    DjangoCore --> MoodleProvisioningTask : enqueues
    DjangoCore --> SSOIssuer : issues launch token
    SSOIssuer --> MoodleAuthPlugin : signed JWT
    MoodleAuthPlugin --> MoodleEngine : creates session
    MoodleEngine --> SocraticEvaluationRequest : submits context
    SocraticEvaluationRequest --> SocraticOrchestrator : input
    SocraticOrchestrator --> LLMProviderAdapter : selects and calls
    SocraticOrchestrator --> MoodleEngine : SSE feedback
    MoodleEngine --> DjangoCore : completion or grade webhook
```

**Boundary notes:** RLS is enforced by PostgreSQL as well as application-level tenant scoping. The Django middleware is responsible for tenant-context injection as described; the PRD does not state how Celery background tasks establish tenant context. Moodle API client/task class boundaries and FastAPI request/orchestration/provider classes are reasonable conceptual representations, not prescribed source-code APIs.

## 7. Sequence Diagram: Interaction

Two scenarios share one sequence view: paid onboarding and learning launch, followed by quiz coaching and completion reporting. The exact payment gateway API and webhook security are not defined.

```mermaid
sequenceDiagram
    autonumber
    actor User as User or organization administrator
    participant Django as INOVATX Django Core
    participant Gateway as Payment gateway
    participant Celery as Celery worker
    participant Moodle as Moodle LMS
    participant FastAPI as FastAPI AI service
    participant LLM as LLM provider

    Note over User,Moodle: Onboarding, provisioning, and SSO launch
    User->>Django: Register and select subscription
    Django->>Gateway: Initiate or record mobile-money/card payment
    Gateway-->>Django: Payment receipt or webhook
    Django->>Celery: Enqueue Moodle provisioning task
    Celery->>Moodle: Create Moodle user via core_user_create_users
    alt Institutional organization
        Celery->>Moodle: Create cohort via core_cohort_create_cohorts
        Celery->>Moodle: Assign members via core_cohort_add_cohort_members
    else Individual subscription
        Celery->>Moodle: Enroll user in standard course group
    end
    User->>Django: Select Launch Learning Hub
    Django-->>User: Return signed JWT with identity, cohort authorization, expiry
    User->>Moodle: Present JWT to custom authentication plugin
    Moodle->>Moodle: Validate JWT and create session
    Moodle-->>User: Redirect to designated course interface

    Note over User,LLM: Quiz coaching and completion/grade synchronization
    User->>Moodle: Submit quiz response or working
    Moodle->>FastAPI: Send question, rubric, response, mastery context
    FastAPI->>LLM: Request Socratic feedback using configured provider
    LLM-->>FastAPI: Stream generated guidance
    FastAPI-->>Moodle: Stream feedback to quiz UI using SSE
    Moodle-->>User: Display step-by-step guidance
    Moodle->>Django: Send completion or grade webhook
```

**Interaction details not specified:** payment webhook authentication and idempotency; Moodle API credentials; SSO JWT issuer/audience, signing-key rotation, replay protection, and exact claims; whether the user browser or Moodle mediates the AI connection; authentication between Moodle and FastAPI; webhook retries and event schemas; and whether grade reporting is synchronous or asynchronous.

## 8. Cloud Architecture: Infrastructure

The PRD describes a single high-performance VPS running a Docker Compose deployment. The architecture below includes only named components and links. A single VPS is not, by itself, evidence of high availability or capacity for the stated concurrency target.

```mermaid
flowchart TB
    Users[External users and clients]
    Payment[External payment gateways\nmobile money and card]
    Providers[External or self-hosted LLM providers]
    Certs[Let's Encrypt certificates]

    subgraph VPS[Single VPS: Docker Compose deployment]
        Proxy[Nginx reverse proxy\nTLS termination, domain routing, rate limiting]

        subgraph Apps[Application containers]
            Django[Django Core\napp.inovatx.com\nCRM, identity, billing, subscriptions]
            Moodle[Moodle LMS\nlearn.inovatx.com\nquizzes, SCORM, cohorts]
            FastAPI[FastAPI AI service\nai.inovatx.com described as internal\nSocratic orchestration and SSE]
            Worker[Celery worker\nasync Moodle provisioning and retries]
        end

        subgraph Data[Database and cache containers]
            CoreDB[(PostgreSQL 16+\ninovatx_db\nRLS tenant data)]
            MoodleDB[(PostgreSQL 16+\nmoodle_db)]
            Redis[(Redis 7+\nsessions, task queues, API caching)]
        end
    end

    Users --> Proxy
    Certs --> Proxy
    Proxy -->|app.inovatx.com| Django
    Proxy -->|learn.inovatx.com| Moodle
    Proxy -.->|AI route/exposure unresolved| FastAPI

    Django --> CoreDB
    Django --> Redis
    Django -->|enqueue tasks| Redis
    Worker -->|consume tasks| Redis
    Worker -->|Moodle REST API| Moodle
    Worker --> CoreDB
    Moodle --> MoodleDB
    Moodle -->|quiz context; route/security unspecified| FastAPI
    FastAPI -->|provider request; keys in FastAPI environment| Providers
    Django -->|payment flow/webhooks| Payment
    Moodle -->|completion or grade webhook| Django
```

**Infrastructure and security constraints from the PRD:** Nginx is the specified web server/reverse proxy, although the topology also names Traefik as an alternative. TLS uses Let's Encrypt. PostgreSQL is version 16+ and Redis is version 7+. Core tenant data uses PostgreSQL RLS plus Django defense-in-depth. FastAPI holds provider credentials in environment variables; end users do not provide keys. Celery retries failed payment webhooks and Moodle API calls with exponential backoff.

**Deployment gaps:** no VPS sizing, container network policy, database backup/restore, disaster-recovery design, monitoring/alerting, log retention, deployment/upgrade strategy, secrets rotation, or horizontal scaling model is specified. The 500-concurrent-quiz-taker target and “100% service uptime” fallback goal need capacity and availability designs beyond what is shown for one VPS.

## Cross-View Traceability

| PRD requirement or statement | Represented in |
| --- | --- |
| FR-01: individual onboarding, parent-child mapping, bulk CSV enrollment | Use cases; ERD omission notes for parent-child schema |
| FR-02: payment receipt triggers Moodle provisioning under 3 seconds | BPMN; sequence; performance caveat |
| FR-03: Socratic feedback and under-1.5-second first token | Use cases; flow chart; sequence |
| FR-04: distinct roles and boundaries in Django and Moodle | Use cases; class view; unresolved role mapping |
| NFR-01: PostgreSQL RLS tenant isolation | ERD; class view; cloud architecture |
| NFR-02: 500 concurrent quiz takers | Cloud architecture; capacity gap |
| NFR-03: exponential-backoff retries | BPMN; class view; cloud architecture |
| Signed JWT Moodle SSO | Use cases; BPMN; class view; sequence |
| Token allowances and model fallback | Flow chart; ERD; sequence; unresolved policy details |
| Single-VPS Docker Compose topology | Cloud architecture |

## Recommended Resolutions to Open Decisions

These actions resolve the major design ambiguities while staying aligned with the PRD. They are the recommended target-state decisions to carry into implementation planning.

1. **Role and authorization mapping:** define a global `system_admin` role and a tenant-scoped `org_admin` role. Normalize `teacher` to `instructor` where product language differs, and treat `student`, `parent`, and `sme_staff` as tenant-scoped membership roles. Enforce permissions by action and resource in Django and Moodle rather than allowing every role to inherit every admin capability.
2. **Organization lifecycle:** keep the PRD states `pending`, `active`, and `suspended` as the minimum lifecycle, and add explicit `expired` and `cancelled` states for product flow completeness. Define `pending → active` as onboarding approval, `active → suspended` as policy or compliance action, `suspended → active` as reinstatement, and `active → cancelled` / `expired` as closure or renewal failure.
3. **Subscription and payment lifecycle:** create separate state machines for `SubscriptionLicense` and `Payment`. Model payment as `pending`, `succeeded`, `failed`, and `cancelled`; model license as `active`, `expired`, `suspended`, or `cancelled`. Keep `valid_until` as a data field, not as the whole lifecycle model.
4. **AI allowance semantics:** map customer-facing `interactions` to internal token accounting. Use a usage ledger to reserve, consume, and reconcile allowance atomically, with monthly reset rules based on billing period. Define the institutional pool as an organization-license calculation derived from active seat capacity rather than ad hoc counts. Downgrade only non-critical interactions when quotas are exhausted.
5. **AI network path:** keep FastAPI on a private network inside the VPS deployment; do not route the AI service publicly unless there is a separate security review. Prefer authenticated server-to-server traffic from Moodle or Django, and use Nginx only as the public edge gateway. If the browser must reach FastAPI, enforce a signed, short-lived user-scoped token and rate limiting.
6. **Integration contracts:** define versioned payload schemas and signed webhook contracts for payment, Moodle, AI, and grade events. Require event IDs, timestamp validation, retry-backoff policies, idempotency, and a dead-letter queue for irreversible failures.
7. **Tenant boundary coverage:** inventory all tenant-owned tables and enforce `organization_id`-based RLS on each. Fail closed if tenant context is missing, and require Celery tasks to resolve tenant context explicitly rather than relying on a global or shared connection thread. Pair RLS with app-level checks and integration tests.
8. **Data model extensions:** add first-class tables for `Payment`, `PaymentEvent`, `AIInteraction`, `UsageLedger`, `Enrollment`, and `GradeRecord` if these are business-critical. Parent-child links and branch-level memberships should also be explicit once the product scope is confirmed.
9. **Operational targets:** define SLOs with percentile targets for provisioning and first-token latency. For example, measure provisioning from verified payment receipt to Moodle enrollment complete, and first-token latency from request acceptance to the first token emitted by the AI service. Add concrete VPS sizing, load-test targets, backup/restore procedures, and alerting requirements before production deployment.
10. **Proxy choice:** standardize on **Nginx** for public ingress, TLS termination, and domain routing. Remove Traefik from the architecture unless there is an explicit operational reason to adopt it, because the PRD already identifies Nginx as the stack’s web server and reverse proxy.
