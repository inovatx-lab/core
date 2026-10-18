# Repository Structure — INOVATX

## Current Phase 0 workspace

This is the current documentation-first workspace layout. The product source tree and runtime infrastructure have not been created here; they must not be treated as existing implementation.

```text
INOVEXA/
├── AGENTS.md
├── BRANCH_POLICY.md
├── REPOSITORY_STRUCTURE.md
├── .gitignore
└── inovatx_context/
    ├── inovatx_completion_checklist.md
    ├── inovatx_cost_capacity_failure_analysis.md
    ├── inovatx_executive_signoff_gate.md
    ├── inovatx_phase0_decision_log.md
    ├── inovatx_product_requirements_document_prd.md
    ├── inovatx_project_todo.md
    ├── inovatx_uml.md
    └── docx/
        ├── INOVEXA Core PRD.docx
        ├── INOVATX_Project_Map.pptx
        └── Phase 0 Decision Log.docx
```

The Markdown files in `inovatx_context/` are the working project context. The Word and PowerPoint files are supplied reference artifacts; confirm their contents against the Markdown sources before treating them as authoritative.

## Git and branches

This workspace is initialized as a local Git repository. Its `origin` is `https://github.com/inovatx-lab/core.git`, and the local `main` and `develop` branches are established. The remote currently advertises no branches; local work has not been pushed.

See [BRANCH_POLICY.md](BRANCH_POLICY.md) for the intended branch names, protections, commit convention, and CI gates. That document describes policy; it is not evidence that branches or host-side protections have been configured.

GitHub branch-protection settings and publication of the local branches remain external follow-ups. They must be verified on GitHub and are not claimed as configured here.

## Future implementation layout

The application and infrastructure layout is not established by the current workspace. Add those directories only through their approved roadmap tasks and phase gates; do not assume the prior proposed `src/`, `tests/`, or `infrastructure/` tree exists.
