# Institutional Registration Flow — Task 2.3.2

**Roadmap task:** 2.3.2 — Implement institutional onboarding path  
**Phase / activity:** Phase 2 / Activity 2.3  
**Status:** Implemented — end-to-end local test with successful institutional registration  
**Traceability:** [Task 2.3.2 traceability record](inovatx_task_2_3_2_traceability.md)

## 1. Purpose and boundary

This task implements the institutional registration endpoint and flow for INOVATX Core. When an institutional user (school, SME, NGO, or enterprise) registers:

1. A Django `User` is created (username, email, password)
2. An `Organization` is created (type=`school`/`sme`/`ngo`/`enterprise`, status=`pending`)
3. A `UserProfile` is created linking the user to the organization
4. An `OrganizationMembershipRole` is created with `role_code=org_admin` (the registrant owns their organization)
5. A `SubscriptionLicense` is created with `status=pending` (awaiting payment activation) and institutional seat capacity

No tenant context is required — the user does not yet belong to an organization. The endpoint is open (no authentication required) and secured by input validation and unique constraints.

Institutional org types: `school`, `sme`, `ngo`, `enterprise`.  
Individual org type (`individual`) is handled by `individual_register` (Task 2.3.1).

## 2. Approved design sources

| Decision | Source | Content |
|---|---|---|
| PRD FR-01 | PRD §6.1 | The system must allow institutional registration and bulk CSV enrollment for educational institutions. |
| PRD §4.1 | PRD §4.1 | User or Institutional Admin registers at `app.inovatx.com` and completes payment via local mobile money or card gateways. |
| UML §2 BPMN | UML §2 | Register → CompletePayment → ProcessPayment → SendReceipt → ReceiveReceipt → Enqueue flow. Registration is separate from payment. OrgType gate: institutional → CreateCohort → AddMembers; individual → IndividualGroup. |
| UML §9 | UML Class Diagram | Included scope: registration, organization and user administration, role boundaries. |
| Task 2.2.1 | License lifecycle policy | License `pending` means entitlement exists but is not usable; activation happens on payment success (Task 2.2.3). |
| Task 2.2.2 | Payment state model | Payment status is separate from license status; `succeeded` payment triggers license activation. |

## 3. Implementation

### 3.1 Endpoint

**`POST /api/v1/register/institutional/`** (`core/views.py` — `institutional_register`):
- CSRF-exempt (open registration endpoint, no session yet)
- No tenant context required (user has no organization yet)
- Accepts JSON body: `username`, `password`, `email`, `phone_number`, `organization_name`, `organization_type`, optional `seat_capacity`
- Validates `organization_type` is institutional (`school`, `sme`, `ngo`, `enterprise`) — rejects `individual` with 400
- Creates: User, Organization (institutional, pending), UserProfile, OrganizationMembershipRole (org_admin), SubscriptionLicense (pending)
- Returns 201 with created resources, or error response (400/409)

### 3.2 URL route

**`api/v1/register/institutional/`** (`config/urls.py`) — mapped to `views.institutional_register`, name `institutional-register`.

### 3.3 Registration flow

```
POST /api/v1/register/institutional/
  → validate required fields (incl. organization_type)
  → validate organization_type is institutional (not individual)
  → check duplicate username/email (409 if taken)
  → create User (Django auth_user)
  → create Organization (institutional type, pending)
  → create UserProfile (user + organization)
  → create OrganizationMembershipRole (org_admin)
  → create SubscriptionLicense (pending, seat_capacity from request, default 50)
  → return 201 with resource IDs
```

## 4. Error semantics

| Condition | Response code | Error code |
|---|---|---|
| Invalid JSON body | `400` | `invalid_json` |
| Missing required field | `400` | `missing_field` |
| Non-institutional org type | `400` | `invalid_org_type` |
| Duplicate username | `409` | `duplicate_username` |
| Duplicate email | `409` | `duplicate_email` |
| Registration failure (DB constraint) | `400` | `registration_failed` |

## 5. Acceptance criteria

1. Institutional registration endpoint implemented at `POST /api/v1/register/institutional/`
2. Creates User, Organization (institutional, pending), UserProfile, OrganizationMembershipRole (org_admin), SubscriptionLicense (pending)
3. No tenant context required — open endpoint for unregistered users
4. Institutional org types accepted: `school`, `sme`, `ngo`, `enterprise`
5. Individual org type (`individual`) rejected with 400
6. Duplicate username/email rejected with 409
7. Missing required fields rejected with 400
8. Invalid JSON rejected with 400
9. License created in `pending` status (awaiting payment activation per Task 2.2.3)
10. Institutional seat capacity configurable (default 50)
11. Registration tests pass (8 tests)
12. All 61 tests pass (41 existing + 8 payment + 5 individual registration + 7 institutional registration)

## 6. Test results

| Test | Result |
|---|---|
| Successful institutional registration | Pass |
| Institutional org types (sme, ngo, enterprise) | Pass |
| Individual org type rejected | Pass |
| Duplicate username returns 409 | Pass |
| Duplicate email returns 409 | Pass |
| Missing required field returns 400 | Pass |
| Invalid JSON returns 400 | Pass |

## 7. Out of scope

- Parent-child account mapping (Task 2.3.3)
- Individual registration path (Task 2.3.1 — separate endpoint)
- Payment processing (Task 2.2.3 — separate webhook endpoint)
- Moodle provisioning on registration (Phase 3)
- SSO JWT issuance (Phase 3)
- Cohort creation and member assignment (Phase 3, per UML BPMN)

## 8. Completion decision

Task 2.3.2 is complete. The institutional registration endpoint is implemented with:
- `POST /api/v1/register/institutional/` endpoint creating user, org, profile, role, and pending license
- Institutional org type validation (rejects `individual`)
- Input validation and duplicate detection
- 8 registration tests passing
- All 61 tests passing (41 existing + 8 payment + 5 individual + 7 institutional)

**Implementation completed:** 2026-10-31  
**Completion review:** pending