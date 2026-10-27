# Task Traceability — 1.2.2 PostgreSQL RLS Baseline

**Task ID and title:** 1.2.2 — Implement RLS baseline and DB tests for tenant isolation
**Phase / activity:** Phase 1 / Activity 1.2
**Owner:** Project owner and technical/security owner
**Status:** Blocked — design approved; implementation awaits the Django schema and PostgreSQL test environment

## Outcome and sources

**Outcome / deliverable:** PostgreSQL RLS policies on tenant-owned Core tables and a passing tenant-isolation test suite executed as the non-privileged runtime role.

**PRD sources:**
- §3.2: transaction-local organization context, tenant coverage, RLS plus application validation, and fail-closed behavior.
- NFR-01: zero cross-tenant data access and PostgreSQL RLS boundary tests.

**UML sources:**
- §5 ERD: Organization, UserProfile membership, OrganizationMembershipRole, and SubscriptionLicense.
- §6 class view: Django Core and database responsibilities.
- §8 cloud architecture: PostgreSQL Core database boundary.

**Approved design sources:**
- Task 1.1.1 domain model, Task 1.1.3 schema baseline, and Task 1.2.1 tenant-context specification.
- Project-owner/technical-security-owner design approvals recorded in decisions P1.2.2-D1–D5 below, confirmed 2026-10-25.
- Phase 0 exit review: the role and policy approval condition was resolved by the project owner/technical-security owner under Task 1.2.2 decisions on 2026-10-25; actual implementation must use the established schema and approved grants.
- Project-owner-approved task ordering: document and approve the RLS design now; continue to Task 1.2.3, then proceed to the authorized Django application/model prerequisites before returning here for implementation and executable tests.

**Mapping classification:** Direct
**Architecture component and trust boundary:** Django Core, Celery, and PostgreSQL tenant boundary. This task implements database row filtering and verifies it using the runtime database identity; it does not authorize production deployment.

## Acceptance criteria

1. Apply the approved role separation: controlled setup-only bootstrap authority; `NOLOGIN` schema/object owner; controlled migration identity; and one shared, least-privileged Django/Celery runtime identity with no ownership, DDL, role-management, `TRUNCATE`, superuser, or `BYPASSRLS` privileges.
2. Enable and FORCE RLS on `Organization`, `UserProfile`, `OrganizationMembershipRole`, and `SubscriptionLicense`, using the approved tenant predicates and both `USING` and `WITH CHECK`.
3. Preserve the approved `SET LOCAL app.current_organization_id` context and the documented limitation that a custom GUC is not an independent defense against arbitrary SQL under a compromised runtime credential.
4. Verify cross-tenant read and write denial, missing-context behavior, organization-membership-role scoping, and transaction/connection reuse behavior using the runtime role or an equivalent role with identical grants and no RLS bypass or owner exemption.
5. Preserve the strict no-global-tenant-row policy, including for `system_admin`; document the global CRM directory as a separate access/authorization dependency.
6. Run the focused PostgreSQL integration suite against the actual Django schema and record the commands/results before closing the task.

## Approved design decisions

- **Role separation:** Use separate logical authorities for controlled database setup, a `NOLOGIN` schema/object owner, a controlled migration identity that may activate the owner role for migrations, and one shared Django/Celery runtime identity. Neither owner nor migrator credentials are configured in runtime services; the runtime identity cannot become the owner. Exact role identifiers and secret-delivery workflow are implementation/deployment details.
- **Runtime privileges:** Grant the runtime identity `SELECT`, `INSERT`, `UPDATE`, and `DELETE` only on the four approved Core tenant tables. Exclude ownership, DDL, role management, `TRUNCATE`, `REFERENCES`, `TRIGGER`, replication, superuser, and `BYPASSRLS`. The external Django authentication table is not included; its narrow grants depend on the approved `AUTH_USER_MODEL`.
- **Django startup metadata exception:** Task 1.3.1 separately approves runtime `SELECT` on `django_migrations`, plus database `CONNECT` and schema `USAGE`, only for Django's startup migration-history check. This infrastructure grant does not expand the tenant-table grant set or authorize auth/session table access.
- **RLS coverage:** Enable and FORCE RLS on `Organization`, `UserProfile`, `OrganizationMembershipRole`, and `SubscriptionLicense`. Scope `Organization` by its `id`; scope `UserProfile` and `SubscriptionLicense` by `organization_id`; scope role assignments through the parent `UserProfile` membership without adding a redundant tenant column.
- **RLS-compatible membership validation:** Set the syntactically valid selected organization as candidate transaction-local context, then perform only the matching authenticated-user/organization membership lookup under RLS. Do not query tenant business data until membership validation succeeds.
- **Policy form:** Runtime-targeted policies use both `USING` and `WITH CHECK`. Missing tenant context produces no matching rows and rejects writes; malformed context errors rather than falling back to an unscoped query.
- **Test identity:** Run tenant-boundary tests as the shared runtime identity, or an equivalent role with identical privileges and no table-owner exemption or RLS bypass.
- **GUC threat boundary:** The approved `SET LOCAL app.current_organization_id` design is defense in depth against missing tenant filters on normal application paths. It does not protect against arbitrary SQL executed with a compromised runtime credential, because that role can set a custom GUC. Do not claim otherwise.
- **Global administrator and directory:** `system_admin` receives no implicit all-tenant scope or global `Organization` rows. Global CRM directory access requires a separately approved organization-authorized mechanism; this task does not add an exception or design that workflow.

## Scope and dependencies

**In scope:** RLS implementation for the approved Core schema, runtime-role grants needed for the RLS baseline, and PostgreSQL tenant-isolation integration tests.

**Out of scope:** Changing the `AUTH_USER_MODEL` selected under Task 1.3.1-D1, implementing Django middleware or application authorization, defining support-access approval workflow, public/service deployment, secrets-delivery tooling, and production database provisioning.

**Implementation blockers:**
- The Task 1.3.1 Django project and built-in `auth.User` configuration now exist, but Core domain models and tenant tables have not yet been created.
- Task 1.1.3's remaining physical schema prerequisites belong to the authorized Django model work in Task 1.3.2.
- PostgreSQL 18.6 and the local database/role baseline are now reported as provisioned under Task 1.3.1. The Django migrations, actual Core schema, RLS policies, and tenant-table grants do not yet exist; no RLS test can be executed against the actual schema.
- The owner approved proceeding to Task 1.3.1 and the model prerequisites for Task 1.3.2 before returning to implement this task. No fixture-only test will be represented as validation of the actual Django schema.

## Evidence and completion

**Evidence:**
- Check or artifact: Approved design choices and repository/environment inspection.
- Result: Design decisions recorded; implementation blocked. A minimal Django 5.2 project exists and a local PostgreSQL role baseline is reported provisioned, but there are no Core tenant models/tables or RLS policies. The required actual-schema integration tests have not been run.
- Location: this record; `inovatx_phase0_decision_log.md`; `inovatx_tenant_context_specification.md`; `inovatx_phase0_exit_review.md`.
- Validation boundary: No RLS SQL, tenant-table grants, migrations, or tests have been implemented or executed. Local Task 1.3.1 database roles and baseline database/schema privileges do not count as evidence for RLS implementation.

**Completion decision:** Not complete. Resume implementation after the Django schema and a PostgreSQL test environment are available; close only after the actual-schema suite passes under the runtime identity.
**Reviewer / approver and date:** Design approval by project owner/technical-security owner, 2026-10-25; implementation review pending.
