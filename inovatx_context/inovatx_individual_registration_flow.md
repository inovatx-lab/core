# Individual Registration Flow — Task 2.3.1

**Roadmap task:** 2.3.1 — Implement individual registration path  
**Phase / activity:** Phase 2 / Activity 2.3  
**Status:** Implemented — end-to-end local test with successful registration  
**Traceability:** [Task 2.3.1 traceability record](inovatx_task_2_3_1_traceability.md)

## 1. Purpose and boundary

This task implements the individual registration endpoint and flow for INOVATX Core. When an individual user registers:

1. A Django `User` is created (username, email, password)
2. An `Organization` is created (type=`individual`, status=`pending`)
3. A `UserProfile` is created linking the user to the organization
4. An `OrganizationMembershipRole` is created with `role_code=org_admin` (the registrant owns their organization)
5. A `SubscriptionLicense` is created with `status=pending` (awaiting payment activation)

No tenant context is required — the user does not yet belong to an organization. The endpoint is open (no authentication required) and secured by input validation and unique constraints.

This is an implementation task that creates an executable Django view, URL route, and tests.

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| PRD FR-01 | PRD §6.1 | The system must allow individual registration, parent-child account mapping, and bulk CSV enrollment for educational institutions. |
| PRD §4.1 | PRD §4.1 | User or Institutional Admin registers at `app.inovatx.com` and completes payment via local mobile money or card gateways. |
| UML §2 BPMN | UML §2 | Register → CompletePayment → ProcessPayment → SendReceipt → ReceiveReceipt → Enqueue flow. Registration is separate from payment. |
| UML §9 | UML Class Diagram | Included scope: registration, organization and user administration, role boundaries. |
| Task 2.2.1 | License lifecycle policy | License `pending` means entitlement exists but is not usable; activation happens on payment success (Task 2.2.3). |
| Task 2.2.2 | Payment state model | Payment status is separate from license status; `succeeded` payment triggers license activation. |

## 3. Implementation

### 3.1 Endpoint

**`POST /api/v1/register/`** (`core/views.py` — `individual_register`):
- CSRF-exempt (open registration endpoint, no session yet)
- No tenant context required (user has no organization yet)
- Accepts JSON body: `username`, `password`, `email`, `phone_number`, `organization_name`
- Creates: User, Organization (individual, pending), UserProfile, OrganizationMembershipRole (org_admin), SubscriptionLicense (pending)
- Returns 201 with created resources, or error response (400/409)

### 3.2 URL route

**`api/v1/register/`** (`config/urls.py`) — mapped to `views.individual_register`, name `individual-register`.

### 3.3 Registration flow

```
POST /api/v1/register/
  → validate required fields
  → check duplicate username/email (409 if taken)
  → create User (Django auth_user)
  → create Organization (individual, pending)
  → create UserProfile (user + organization)
  → create OrganizationMembershipRole (org_admin)
  → create SubscriptionLicense (pending, seat_capacity=1, EDTECH_LMS)
  → return 201 with resource IDs
```

## 4. Error semantics

| Condition | Response code | Error code |
|---|---|---|
| Invalid JSON body | `400` | `invalid_json` |
| Missing required field | `400` | `missing_field` |
| Duplicate username | `409` | `duplicate_username` |
| Duplicate email | `409` | `duplicate_email` |
| Registration failure (DB constraint) | `400` | `registration_failed` |

## 5. Acceptance criteria

1. Individual registration endpoint implemented at `POST /api/v1/register/`
2. Creates User, Organization (individual, pending), UserProfile, OrganizationMembershipRole (org_admin), SubscriptionLicense (pending)
3. No tenant context required (open endpoint)
4. Duplicate username/email rejected with 409
5. Missing required fields rejected with 400
6. Invalid JSON rejected with 400
7. License created in `pending` status (awaiting payment activation per Task 2.2.3)
8. Registration tests pass (5 tests)
9. All 54 tests pass (41 existing + 8 payment + 5 registration)

## 6. Test results

| Test | Result |
|---|---|
| Successful individual registration | Pass |
| Duplicate username returns 409 | Pass |
| Duplicate email returns 409 | Pass |
| Missing required field returns 400 | Pass |
| Invalid JSON returns 400 | Pass |

## 7. Out of scope

- Parent-child account mapping (Task 2.3.3)
- Institutional onboarding path (Task 2.3.2)
- Payment processing (Task 2.2.3 — separate webhook endpoint)
- Moodle provisioning on registration (Phase 3)
- SSO JWT issuance (Phase 3)

## 8. Completion decision

Task 2.3.1 is complete. The individual registration endpoint is implemented with:
- `POST /api/v1/register/` endpoint creating user, org, profile, role, and pending license
- Input validation and duplicate detection
- 5 registration tests passing
- All 54 tests passing (41 existing + 8 payment + 5 registration)

**Implementation completed:** 2026-10-31  
**Completion review:** pending