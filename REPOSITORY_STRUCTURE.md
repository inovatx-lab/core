# Repository Structure — INOVATX

## Current workspace

This workspace contains project governance and architecture documents plus the minimal Django local foundation created under Task 1.3.1. Core domain models/admin and runtime infrastructure have not been implemented; planning documents and model specifications must not be treated as application behavior.

```text
INOVEXA/
├── AGENTS.md
├── BRANCH_POLICY.md
├── REPOSITORY_STRUCTURE.md
├── README.md                    # Local Django development instructions
├── requirements.txt             # Django and PostgreSQL driver
├── manage.py
├── config/                       # Django project settings and entry points
│   ├── __init__.py
│   ├── asgi.py
│   ├── base_settings.py
│   ├── migration_settings.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                         # Django Core app skeleton; no domain models yet
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
├── docker-compose.yml           # Phase 0 planning skeleton; not runnable
├── .gitignore
└── inovatx_context/
    ├── inovatx_completion_checklist.md
    ├── inovatx_core_api_contract.md     # Task 1.3.3 Core API contract document
    ├── inovatx_core_enum_taxonomy.md
    ├── inovatx_initial_schema_migration_plan.md
    ├── inovatx_phase0_exit_review.md
    ├── inovatx_phase1_core_domain_model.md
    ├── inovatx_tenant_context_specification.md
    ├── inovatx_tenant_failure_policy.md
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
    ├── inovatx_task_1_2_1_traceability.md
    ├── inovatx_task_1_2_2_traceability.md
    ├── inovatx_task_1_2_3_traceability.md
    ├── inovatx_task_1_3_1_traceability.md
    ├── inovatx_uml.md
    ├── memory.md                 # Session handoff only; not a project source of truth
    └── docx/
        ├── INOVEXA Core PRD.docx
        ├── INOVATX_Project_Map.pptx
        └── Phase 0 Decision Log.docx
```

The Markdown files in `inovatx_context/` are the working project context, including the Phase 1 Task 1.3.3 Core API contract document. The Word and PowerPoint files are supplied reference artifacts; confirm their contents against the Markdown sources before treating them as authoritative. The root Compose file is a planning artifact under Task 0.2.2, not a runnable stack. Django's default settings use only runtime credentials; `config.migration_settings` is reserved for migrations and activates the validated schema-owner role. Neither settings module falls back to SQLite. PostgreSQL-backed migration and runtime startup checks remain pending.

## Git and branches

This workspace is initialized as a Git repository. Its `origin` is `https://github.com/inovatx-lab/core.git`; local `main` and `develop` branches are established. On 2026-10-25, all local branches were published to that remote and verified by matching their remote refs to the local branch tips.

See [BRANCH_POLICY.md](BRANCH_POLICY.md) for the intended branch names, protections, commit convention, and CI gates. That document describes policy; it is not evidence that branches or host-side protections have been configured.

GitHub branch-protection settings remain an external follow-up. They must be verified on GitHub and are not claimed as configured here.

## Future implementation layout

The application and infrastructure layout is not established by the current workspace. Add those directories only through their approved roadmap tasks and phase gates; do not assume the prior proposed `src/`, `tests/`, or `infrastructure/` tree exists.
