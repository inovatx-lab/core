# AI Coding Guardrails and Phase-Lock Policy — INOVATX

**Roadmap task:** 0.3.1 — Define AI coding guardrails and phase lock policy
**Status:** Phase 0 governance document; it does not authorize product implementation
**Applies to:** Developers using generative AI for project analysis, documentation, code, tests, configuration, or review

## 1. Authority and scope

AI assistance does not change project authority, scope, or approval requirements.

- Use the PRD and UML as the product requirement and system-model sources of truth. Use the Phase 0 decision log for decisions that have been approved; an open or unresolved item is not an approved design.
- Use the roadmap to identify the active task and its deliverables. Use `AGENTS.md`, `BRANCH_POLICY.md`, and the phase sign-off documents for repository, delivery, and authorization constraints.
- A task authorizes only its stated deliverables within its approved phase. Phase 0 authorization permits definition and validation work only; it does not authorize application code, runnable infrastructure, production deployment, or first-client activation.
- If requirements conflict, an approval is unclear, a task lacks sufficient detail, or an AI suggestion depends on an unresolved decision, stop the affected work and request clarification. Do not let generated output resolve governance or product questions by implication.
- Keep each change limited to the active task. Do not include future-phase work, unrelated refactors, speculative abstractions, or implementation disguised as examples, prototypes, or scaffolding.

## 2. AI usage rules

### Permitted use

AI may assist with work that is already within the active task's authorization, including:

- locating and summarizing relevant project context;
- drafting or editing documentation against cited source material;
- proposing bounded code changes, tests, or validation steps for an authorized implementation task;
- explaining diagnostics and reviewing a diff for possible defects.

The developer remains responsible for choosing the approach, checking generated content, validating behavior, and approving the final change.

### Grounding and accuracy

- Provide only the minimum context needed, and identify the applicable task and source requirements.
- Require claims about product behavior or architecture to be traceable to an approved source. Label assumptions and unresolved items; never present an AI inference as a project decision.
- Verify APIs, dependency behavior, commands, configuration semantics, and security-sensitive claims against the repository or authoritative documentation before relying on them.
- Treat generated code, shell commands, migrations, configuration, and suggested tests as untrusted until reviewed and validated.
- Do not invent test results, citations, approval status, implementation evidence, or completion claims.

### Privacy and secrets

- Never include credentials, tokens, private keys, certificates, connection strings, personal data, or confidential customer information in prompts, generated examples, logs, or committed artifacts.
- Do not submit proprietary source or other non-public project data to an external AI service unless that service and the disclosure are explicitly approved under applicable organizational policy.
- Use redacted or synthetic examples when sensitive values are not necessary. If sensitive information is exposed, stop, follow the applicable incident and credential-rotation process, and remove it from outputs and history where possible.

### Security and architecture

- Preserve tenant isolation: tenant context must be explicit, missing or invalid context must fail closed, and neither PostgreSQL RLS nor application authorization may be bypassed.
- Keep FastAPI private/internal by default. Do not generate or expose a public AI route without explicit architecture approval and security review.
- Keep secrets out of source and generated artifacts. Use the approved secret-management approach; do not invent credentials or recommend committing local secret files.
- Preserve approved signature, idempotency, replay-safety, and observability requirements for payment, Moodle, and other integration events.
- Do not turn conceptual or unresolved UML elements into implementation requirements.

## 3. Developer checklist

### Before using AI

- [ ] Identify the active phase, roadmap task, requested deliverable, and task branch.
- [ ] Confirm the task is authorized by the applicable phase gate; Phase 0 work remains planning and validation only.
- [ ] Read the relevant PRD/UML sections, approved decisions, and repository instructions.
- [ ] Check whether the proposed work touches an open decision, a trust boundary, tenant isolation, secrets, or personal data; stop and seek the required approval if it does.
- [ ] Remove secrets, personal data, and unnecessary proprietary context from prompts.

### While using AI

- [ ] Keep the request bounded to the active task and state relevant constraints explicitly.
- [ ] Ask for source traceability and separation of facts, assumptions, and unresolved questions.
- [ ] Reject scope expansion, unsupported requirements, invented approvals, or recommendations that weaken security controls.
- [ ] Review every generated file, command, dependency, test, and configuration change before applying or executing it.
- [ ] Do not run destructive, privileged, externally publishing, or production-impacting commands based only on AI output.

### Before completing the task

- [ ] Confirm the diff contains only task-related changes and does not cross the phase lock.
- [ ] Check correctness, security, privacy, maintainability, and alignment with existing repository patterns.
- [ ] Run the smallest relevant validation available; report commands and results accurately, including checks that could not be run.
- [ ] Confirm tests and documentation reflect actual behavior and do not claim unsupported guarantees.
- [ ] Record completion evidence in the roadmap and leave unresolved decisions visible rather than silently choosing defaults.

## 4. Code generation protocol

1. **Frame the task.** State the active phase/task, exact deliverable, acceptance evidence, and explicitly excluded scope. If any of these are missing or conflicting, pause for clarification.
2. **Ground the request.** Identify relevant PRD/UML requirements, approved decision-log entries, and repository instructions. Separate binding requirements from assumptions and unresolved questions.
3. **Check authorization and risk.** Confirm the phase gate permits the proposed work. Identify sensitive data, tenant/security boundaries, external exposure, migrations, dependencies, and operational side effects. Obtain required approval before proceeding on restricted areas.
4. **Choose the smallest complete change.** Follow existing project patterns. Do not add speculative abstractions, future-phase hooks, dependencies, or unrelated cleanup.
5. **Generate a reviewable change.** Keep edits focused and explain any necessary deviation from established patterns. Include or update focused tests and directly related documentation when the active task calls for them.
6. **Review the result.** Inspect the complete diff. Check authorization, traceability, input validation, error handling, access control, tenant context, secret handling, and whether the implementation matches the stated contract.
7. **Validate.** Run the smallest relevant existing tests, lint, type-check, or build. Do not claim a check passed unless it was run successfully. If validation is unavailable, record the limitation and the evidence that was checked instead.
8. **Close with evidence.** Summarize the changed artifacts, trace each to the task, report validation results, and list unresolved questions. Update the roadmap only with evidence actually established.

## 5. Phase-lock and escalation rules

- Work may advance to another task only through the roadmap and branch policy; AI output cannot authorize a task or phase transition.
- Phase 0 documents and static validation must not be expanded into application features, production-ready infrastructure, deployment, or launch activity.
- Do not build against open decisions or unapproved architecture. Record the blocking question and route it to the accountable owner identified by project governance.
- A later phase may begin only after its required prior-phase exit criteria are evidenced and the next phase is explicitly authorized. Executive pre-build approval alone does not waive that gate.
- Stop and escalate if an AI-generated change appears to expose a private service, bypass tenant isolation or authorization, disclose sensitive data, or contradict an approved decision.

## 6. Completion evidence

For each task using AI assistance, retain evidence appropriate to that task: requirement/decision references, a focused diff, relevant validation output, and any unresolved blockers. Evidence must distinguish what was drafted or statically checked from what was executed or approved. This document is a governance control; its existence alone does not satisfy Phase 0 exit approval.
