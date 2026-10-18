# INOVATX Project Guidelines

## Read the project context

Before implementation, consult the project documents in `inovatx_context/`:

1. [Product requirements](inovatx_context/inovatx_product_requirements_document_prd.md) — product scope, requirements, and target architecture.
2. [System models](inovatx_context/inovatx_uml.md) — modeled components, relationships, and explicitly unresolved details.
3. [Phase 0 decision log](inovatx_context/inovatx_phase0_decision_log.md) — recorded decisions and their rationale.
4. [Project roadmap](inovatx_context/inovatx_project_todo.md) — phases, tasks, scope, and AI-grounding guardrails.
5. [Executive sign-off gate](inovatx_context/inovatx_executive_signoff_gate.md) — authorization boundary and phase approval requirements.
6. [Completion checklist](inovatx_context/inovatx_completion_checklist.md) — first-client scope, architecture, security, and readiness gates.
7. [Cost, capacity, and failure analysis](inovatx_context/inovatx_cost_capacity_failure_analysis.md) — estimates, assumptions, risks, and items requiring validation.
8. [AI coding guardrails](inovatx_context/inovatx_ai_coding_guardrails.md) — mandatory AI-use rules, developer checklist, code-generation protocol, and phase lock.
9. [Task traceability template](inovatx_context/inovatx_task_traceability_template.md) — required task-to-PRD/UML mapping format and roadmap mapping index.
10. [Review and quality gates](inovatx_context/inovatx_review_quality_gates.md) — code review rubric, validation checklist, and milestone gates.

Use [BRANCH_POLICY.md](BRANCH_POLICY.md) for branch, commit, and CI conventions, and [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) for the intended repository layout. Treat the context documents as planning and requirements sources, not proof that the described application or infrastructure already exists.

## Mandatory AI and task guardrails

- Before AI-assisted project work, read and follow the AI coding guardrails, task traceability template, and review/quality gates listed above. These documents are mandatory project instructions, not optional reference material.
- Every task must have a completed traceability record before work begins and review/validation evidence before it is marked complete. Use the roadmap mapping index as a starting point, not as authorization for future tasks.
- The active phase and task remain the scope boundary. AI assistance, a completed checklist, or an approved decision does not authorize work in a later phase; require the applicable phase-exit evidence and explicit authorization.
- When these instructions conflict with a project source or an approval gate, stop the affected work and request clarification. Do not infer an approval or waive a gate.

## Scope and decision rules

- Trace implementation work to a PRD requirement or UML element and the active roadmap task and phase. Keep each task focused; do not add speculative abstractions, unrelated refactors, or future-phase work.
- The sign-off documents contain phase and approval gates. Check the relevant approval and exit criteria before implementation; an approval recorded in one document does not override open, unchecked, or conflicting gates elsewhere. If authorization or source-of-truth status is ambiguous, stop and request clarification.
- Record design decisions not covered by the approved requirements in the Phase 0 decision log, including rationale and impact.
- Treat UML items identified as unresolved or conceptual as proposals, not settled implementation requirements.

## Architecture and security guardrails

- Preserve tenant isolation: use explicit tenant context, fail closed when it is missing or invalid, and do not bypass PostgreSQL RLS or application-level authorization.
- Keep FastAPI private/internal by default. Any public exposure requires explicit approval and security review. Use Nginx as public ingress unless an approved architecture decision changes this.
- Keep payment and integration events signed, idempotent, replay-safe, and observable as specified in the approved decisions.
- Never put secrets in source code, documentation examples, or generated artifacts.

## Implementation and verification

- Read existing code and project configuration before choosing paths, dependencies, commands, or implementation patterns. The documented repository layout is a target layout and may differ from the files currently present.
- For third-party libraries, check whether a relevant skill is available and follow the applicable skill and project-specific requirements before integrating the library.
- Make the smallest complete change that satisfies the active task. Add or update focused tests and directly related documentation.
- Verify changes with the smallest relevant available tests, lint, type-check, or build command. Report what was run and any checks that could not be run; do not claim completion without evidence.

## Available workflow skills

The following skills are available in the user's global skill directory; invoke them when their described workflow applies:

- `/architect` — before a complex feature.
- `/imprint` — after building a UI component.
- `/review` — for a production-readiness review or before a demo.
- `/recover` — after a build or correction fails and needs diagnosis.
- `/remember` — use `save` to preserve multi-session work and `restore` when resuming it.

If a referenced skill is unavailable in another environment, check the user's `~/.agents/skills/` directory or install the skill into the workspace at `.agents/skills/<skill-name>/SKILL.md` (or another supported workspace skill location). A skill's folder must contain a valid `SKILL.md` with matching `name` and a useful `description`; reopen/reload the workspace if the host does not discover a newly installed skill.
