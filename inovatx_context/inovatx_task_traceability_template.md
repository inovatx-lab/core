# Task-to-Requirement Traceability — INOVATX

**Roadmap task:** 0.3.2 — Define task-to-requirement traceability template
**Status:** Phase 0 planning artifact; mappings for future work are indexes, not task authorization
**Sources:** [Product requirements](inovatx_product_requirements_document_prd.md), [system models](inovatx_uml.md), and [project roadmap](inovatx_project_todo.md)

## 1. How to use this template

Complete one record for each active roadmap task before work begins, then update its evidence and outcome when the task closes. The mapping index in §3 supplies an initial source map for every task currently listed in the roadmap. It does not replace a task record, establish acceptance criteria, or authorize future-phase work.

- Cite exact PRD requirement IDs (for example, `FR-02`, `NFR-01`) and section numbers. Cite UML view numbers and relevant elements where available.
- Classify the mapping as **Direct** when a PRD requirement or UML element explicitly supports the task outcome. Classify it as **Derived** when the task is a governance, delivery, operational, or verification activity inferred from broader requirements, the roadmap, or a phase gate rather than stated as a standalone product requirement.
- Use **Gap** if no adequate source supports the requested outcome. Record the missing decision or requirement and obtain approval before treating the work as in scope.
- Do not turn recommended resolutions, open decisions, conceptual UML elements, or an indexed future task into approved requirements.
- For tasks with implementation, identify the architecture component and trust boundary. For documentation and governance tasks, identify the project artifact or accountable process instead.
- Keep acceptance criteria observable and task-sized. Evidence must identify the check performed and its actual result; distinguish a plan or static review from an executed test or approval.
- If task scope or sources change, update the record and resolve the discrepancy with the accountable owner before continuing.

## 2. Reusable task record

Copy and complete this block for the active task:

```text
Task ID and title:
Phase / activity:
Owner:
Status:

Outcome / deliverable:
PRD source(s): requirement ID(s), section(s), and relevant statement
UML source(s): view number(s), element(s), and relevant relationship
Mapping classification: Direct / Derived / Gap
Architecture component and trust boundary (or governance artifact):

Acceptance criteria:
1.
2.

In scope:
Out of scope:
Dependencies / approved decisions:
Open questions or assumptions:

Evidence:
- Check or artifact:
- Result:
- Location:

Completion decision:
Reviewer / approver and date (when required):
```

## 3. Initial mapping index for every roadmap task

The PRD section and requirement references and UML view numbers below are starting points for task-level records. Authors must confirm the relevant detail before work starts. A **Derived** entry means the roadmap task is not itself a standalone product requirement; it still needs the cited project objective, architectural basis, or approval gate.

| Task | PRD source(s) | UML source(s) | Mapping |
|---|---|---|---|
| 0.1.1 | §§1.1–1.2, 6.1–6.2 | §1 | Derived — project objective and product scope |
| 0.1.2 | §§7–8; NFR-05 | §8 | Derived — phase governance and readiness |
| 0.1.3 | §§1–2, 6 | §§1–8 | Derived — source-of-truth governance |
| 0.2.1 | §§2.2, 8 | §8 | Derived — repository and delivery baseline |
| 0.2.2 | §§2.1–2.2 | §8 | Direct — target technology and topology |
| 0.2.3 | §§2.1–2.2, 5.1 | §8 | Direct — components, connections, and trust boundaries |
| 0.3.1 | §§6.1–6.2, 7 | Cross-view traceability | Derived — AI and phase-lock governance |
| 0.3.2 | §6; roadmap §2.2 | Cross-view traceability | Derived — task traceability governance |
| 0.3.3 | §§6.1–6.2; NFR-01, NFR-03–NFR-05 | §§5–8 | Derived — quality and verification controls |
| 1.1.1 | §3.1; FR-01, FR-05, FR-06 | §§5–6 | Direct — core entities and relationships |
| 1.1.2 | §3.1; FR-04–FR-06 | §§4–6 | Direct — roles, states, and constraints |
| 1.1.3 | §§3.1–3.2; NFR-01 | §§5, 8 | Direct — schema and RLS baseline |
| 1.2.1 | §3.2; FR-05, NFR-01, NFR-03 | §§6–8 | Direct — tenant context across requests and workers |
| 1.2.2 | §3.2; NFR-01 | §§5, 8 | Direct — PostgreSQL RLS and isolation tests |
| 1.2.3 | §3.2; FR-05, NFR-01 | §§6, 8 | Direct — authorization and tenant fail-closed behavior |
| 1.3.1 | §2.2 | §8 | Direct — Django technology baseline |
| 1.3.2 | §§2.1, 3.1; FR-01, FR-04–FR-06 | §§5–6 | Direct — Core models and administration |
| 1.3.3 | §§2.1, 6.1; FR-01, FR-02, FR-04–FR-06 | §§1, 7 | Direct — Core endpoint contracts |
| 2.1.1 | §3.1; FR-04, FR-05 | §§1, 6 | Direct — global and tenant-scoped permissions |
| 2.1.2 | §3.1; FR-01, FR-04, FR-05 | §§1, 5–6 | Direct — membership roles and boundaries |
| 2.1.3 | §§3.1–3.2; FR-04, FR-05 | §§1, 6–7 | Direct — permission enforcement |
| 2.2.1 | §3.1; FR-06 | §§4–6 | Direct — subscription/license lifecycle |
| 2.2.2 | §§4.2, 7; FR-06, NFR-04 | §§2, 4, 7 | Direct — payment states and integration events |
| 2.2.3 | §4.1; FR-02, FR-06 | §§2, 7 | Direct — payment receipt and activation |
| 2.3.1 | §4.1; FR-01 | §§1, 5, 7 | Direct — individual registration |
| 2.3.2 | §4.1; FR-01, FR-02 | §§1–2, 5, 7 | Direct — institutional onboarding and provisioning |
| 2.3.3 | §§3.1, 4.1; FR-01, FR-04, FR-05 | §§1, 5–6 | Direct — parent-child mapping and access |
| 3.1.1 | §4.1; FR-02 | §§2, 5, 7 | Direct — Moodle user provisioning contract |
| 3.1.2 | §§4.1–4.2; FR-02 | §§2, 5, 7 | Direct — cohort creation and assignment |
| 3.1.3 | §4.1; FR-02, FR-04 | §§1–2, 6–7 | Direct — signed SSO access contract |
| 3.2.1 | §4.1; FR-02, NFR-03 | §§2, 7–8 | Direct — asynchronous user provisioning |
| 3.2.2 | §4.1; FR-02, NFR-03 | §§2, 7–8 | Direct — asynchronous cohort provisioning |
| 3.2.3 | §4.2; NFR-03, NFR-04 | §§2, 7–8 | Direct — retry, replay safety, and failure handling |
| 3.3.1 | §4.1; FR-02, FR-04 | §§1, 6–7 | Direct — signed SSO token issuance |
| 3.3.2 | §4.1; FR-02, FR-04 | §§1, 7–8 | Direct — Moodle authentication integration |
| 3.3.3 | §4.1; FR-02, FR-04 | §§1–2, 7 | Direct — learner access through Moodle |
| 4.1.1 | §5.1; FR-03 | §§3, 7 | Direct — Socratic AI request/response contract |
| 4.1.2 | §5.2; FR-03, FR-07 | §§3, 5, 7 | Direct — model selection and allowance behavior |
| 4.1.3 | §§2.2, 5.1; NFR-04 | §§7–8 | Direct — provider configuration and secret boundary |
| 4.2.1 | §5.1; FR-03 | §§1, 3, 7 | Direct — Socratic evaluation endpoint |
| 4.2.2 | §5.1; FR-03 | §§3, 7 | Direct — stepwise Socratic response |
| 4.2.3 | §5.1; FR-03, NFR-04 | §§3, 7–8 | Direct — internal AI streaming contract |
| 4.3.1 | §5.2; FR-07 | §§3, 5, 7 | Direct — usage ledger and allowance tracking |
| 4.3.2 | §5.2; FR-07 | §§3, 5, 7 | Direct — seat-based allowance rules |
| 4.3.3 | §5.2; FR-07 | §§3, 7 | Direct — exhaustion and downgrade behavior |
| 5.1.1 | §§4.1, 7; FR-02, FR-06 | §§2, 4, 7 | Direct — receipt-to-license activation |
| 5.1.2 | §4.2; FR-02, NFR-03, NFR-04 | §§2, 7–8 | Direct — signed, replay-safe webhook handling |
| 5.1.3 | §§4.2, 7; NFR-03–NFR-05 | §§2, 8 | Derived — recovery process based on integration and readiness controls |
| 5.2.1 | §4.1; FR-01, FR-02, FR-04, FR-05 | §§1–2, 5, 7 | Direct — onboarding-to-learning path |
| 5.2.2 | §5.1; FR-03, FR-07 | §§3, 7 | Direct — AI evaluation and completion path |
| 5.2.3 | §3.2; NFR-01 | §§5, 8 | Direct — tenant isolation under load |
| 5.3.1 | §§2.2, 7; NFR-02, NFR-05 | §8 | Direct — service operations and measurable readiness |
| 5.3.2 | §7; NFR-05 | §8 | Direct — backup, restore, and recovery readiness |
| 5.3.3 | §8; NFR-05 | §8 | Derived — release gate and first-client readiness |
| 6.1.1 | §§3.1, 4.1; FR-01, FR-06 | §§1, 5–6 | Direct — initial tenant, user, and subscription data |
| 6.1.2 | §4.1; FR-01, FR-04, FR-05 | §§1–2, 5–6 | Direct — cohort membership and access |
| 6.1.3 | §§4.1, 5.1–5.2; FR-02, FR-03, FR-07 | §§1, 3, 7 | Direct — learner LMS and AI paths |
| 6.2.1 | §§1.2, 8; NFR-05 | §8 | Derived — launch activity; requires separate launch go/no-go |
| 6.2.2 | §§5.2, 7; FR-07, NFR-02, NFR-05 | §§3, 7–8 | Direct — usage, performance, and operations monitoring |
| 6.2.3 | §8; NFR-05 | §8 | Derived — change control during pilot; requires launch authorization |
| 6.3.1 | §§7–8; NFR-05 | §8 | Derived — blocker resolution under readiness gate |
| 6.3.2 | §8; NFR-05 | §8 | Derived — wider rollout readiness decision |
| 6.3.3 | §8; NFR-05 | §8 | Derived — release baseline and change control |

## 4. Reference conventions

- **PRD:** `§` refers to numbered sections/subsections of `inovatx_product_requirements_document_prd.md`; `FR-*` and `NFR-*` are requirement IDs in §6.
- **UML:** view numbers refer to `inovatx_uml.md`: 1 Use Case, 2 BPMN, 3 AI Flow Chart, 4 State Machine, 5 ERD, 6 Class Diagram, 7 Sequence Diagram, 8 Cloud Architecture. “Cross-view traceability” points to that document's cross-view mapping section.
- **Roadmap:** task IDs and scope refer to `inovatx_project_todo.md`. The roadmap is execution planning, not a replacement for product requirements or approval records.
- Where the PRD and UML differ, or the cited UML view is conceptual or marked unresolved, record the mismatch and seek an approved decision; do not silently prefer one interpretation.
