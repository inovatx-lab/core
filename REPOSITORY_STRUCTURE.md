# Repository Structure — INOVATX

## Current documentation-first workspace

This workspace currently contains project governance, architecture, and Phase 1 domain-specification documents. The product source tree and runtime infrastructure have not been created here; planning documents and model specifications must not be treated as implemented application code.

```text
INOVEXA/
├── AGENTS.md
├── BRANCH_POLICY.md
├── REPOSITORY_STRUCTURE.md
├── docker-compose.yml           # Phase 0 planning skeleton; not runnable
├── .gitignore
└── inovatx_context/
    ├── inovatx_completion_checklist.md
    ├── inovatx_core_enum_taxonomy.md
    ├── inovatx_initial_schema_migration_plan.md
    ├── inovatx_phase0_exit_review.md
    ├── inovatx_phase1_core_domain_model.md
    ├── inovatx_architecture_baseline.md
    ├── inovatx_ai_coding_guardrails.md
    ├── inovatx_cost_capacity_failure_analysis.md
    ├── inovatx_executive_signoff_gate.md
    ├── inovatx_environment_baseline.md
    ├── inovatx_phase0_decision_log.md
    ├── inovatx_product_requirements_document_prd.md
    ├── inovatx_project_todo.md
    ├── inovatx_review_quality_gates.md
    ├── inovatx_task_traceability_template.md
    ├── inovatx_task_1_1_1_traceability.md
    ├── inovatx_task_1_1_2_traceability.md
    ├── inovatx_task_1_1_3_traceability.md
    ├── inovatx_uml.md
    ├── memory.md                 # Session handoff only; not a project source of truth
    └── docx/
        ├── INOVEXA Core PRD.docx
        ├── INOVATX_Project_Map.pptx
        └── Phase 0 Decision Log.docx
```

The Markdown files in `inovatx_context/` are the working project context. The Word and PowerPoint files are supplied reference artifacts; confirm their contents against the Markdown sources before treating them as authoritative. The root Compose file is a planning artifact under Task 0.2.2, not a runnable stack.

## Git and branches

This workspace is initialized as a Git repository. Its `origin` is `https://github.com/inovatx-lab/core.git`; local `main` and `develop` branches are established. On 2026-10-25, all local branches were published to that remote and verified by matching their remote refs to the local branch tips.

See [BRANCH_POLICY.md](BRANCH_POLICY.md) for the intended branch names, protections, commit convention, and CI gates. That document describes policy; it is not evidence that branches or host-side protections have been configured.

GitHub branch-protection settings remain an external follow-up. They must be verified on GitHub and are not claimed as configured here.

## Future implementation layout

The application and infrastructure layout is not established by the current workspace. Add those directories only through their approved roadmap tasks and phase gates; do not assume the prior proposed `src/`, `tests/`, or `infrastructure/` tree exists.
