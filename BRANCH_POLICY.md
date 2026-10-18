# Branch Policy — INOVATX Core Platform

## Branch Protection Rules

### Main Branch (`main`)
- **Required**: 2 approving reviews from code owners
- **Required**: All CI checks pass (lint, typecheck, tests, security scan)
- **Required**: Linear history (no merge commits — use squash merge)
- **Required**: Signed commits
- **Block**: Force push, deletion

### Develop Branch (`develop`)
- **Required**: 1 approving review from code owner
- **Required**: All CI checks pass
- **Block**: Force push, deletion

### Feature/Bugfix Branches
- **Naming**: `feature/T<phase>.<activity>.<task>` (e.g., `feature/T0.2.1`)
- **Naming**: `bugfix/T<phase>.<activity>.<task>` (e.g., `bugfix/T1.2.2`)
- **Naming**: `hotfix/T<phase>.<activity>.<task>` (e.g., `hotfix/T5.1.1`)
- **Max age**: 5 days before must be rebased/merged
- **Cleanup**: Auto-delete after merge

## Commit Convention

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
| Type | Description |
|---|---|
| `feat` | New feature for a task |
| `fix` | Bug fix for a task |
| `refactor` | Code refactoring (no behavior change) |
| `test` | Adding or modifying tests |
| `docs` | Documentation changes |
| `chore` | Build, config, dependency updates |
| `security` | Security-related changes |

### Scope
Use the component name from the architecture:
- `core` — Django Core
- `moodle` — Moodle integration
- `ai` — FastAPI AI service
- `shared` — Shared utilities
- `infra` — Infrastructure/Docker
- `docs` — Documentation

### Examples
```
feat(core): add Organization model with RLS
fix(ai): handle provider timeout in SSE streaming
test(isolation): add tenant isolation integration tests
docs(phase0): update decision log with D17-D19
chore(infra): update docker-compose for FastAPI
```

## CI Pipeline Gates

Each PR must pass:

| Gate | Tool | Threshold |
|---|---|---|
| Lint | ruff | No errors |
| Typecheck | pyright/mypy | No errors |
| Unit Tests | pytest | 100% pass |
| Isolation Tests | pytest | 100% pass (tenant tests) |
| Security Scan | bandit | No HIGH/CRITICAL |
| Phase Gate | custom | Task evidence present |

## Code Owners (CODEOWNERS)

```
# Global owners
* @inovatx-lab/core-maintainers

# Core Django
/src/core/ @inovatx-lab/core-team

# Moodle integration
/src/moodle/ @inovatx-lab/moodle-team

# AI service
/src/ai/ @inovatx-lab/ai-team

# Infrastructure
/infrastructure/ @inovatx-lab/infra-team

# Documentation
/docs/ @inovatx-lab/product-team
```

## Phase Gate Enforcement

CI includes a **phase gate check** that validates:
1. All tasks in current phase have completion evidence
2. No code references future phase tasks
3. Decision log updated for any new design decisions
4. Completion checklist items checked off

This check blocks merges to `develop` if phase exit criteria are not met.