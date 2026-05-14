# Implementation Plan: Phase 2b - Pre-commit hooks

## Objective
Implement Phase 2b of the refactoring plan by adding `pre-commit` configuration to the project, adding `pre-commit` as a development dependency, and updating documentation.

## Key Files & Context
- `pyproject.toml`: To add `pre-commit` to `[project.optional-dependencies]` dev group.
- `.pre-commit-config.yaml`: To be created with hooks for `ruff`, `ruff-format`, `mypy`, trailing whitespace, and end-of-file newlines.
- `README.md` (and `README.it.md`): To add developer setup instructions.
- `specs/code_refactoring_plan.md`: To mark Phase 2b as complete.
- `DEVLOG.md`: To log the session actions.

## Implementation Steps
1. **Update `pyproject.toml`:**
   - Add `"pre-commit"` to the list under `[project.optional-dependencies] dev = [...]`.
   - Run `uv sync` or `uv lock` to update the lockfile if necessary, but uv will handle it automatically.

2. **Create `.pre-commit-config.yaml`:**
   - Define the following repositories and hooks:
     - `ruff` (for linting and autofix)
     - `ruff-format` (for formatting)
     - `mypy` (specifically scoped to `cave_sketch/` as per requirements, possibly by setting `files: ^cave_sketch/`)
     - `trailing-whitespace` and `end-of-file-fixer` from `pre-commit/pre-commit-hooks`.

3. **Format & Fix Existing Files:**
   - Execute `uv run pre-commit run --all-files`.
   - If any hooks fail and auto-fix, run again to ensure success. If manual fixes are needed, apply them.

4. **Update Documentation:**
   - Add setup instruction `uv run pre-commit install` to the developer section of both `README.md` and `README.it.md`.

5. **Conclude Phase 2:**
   - Update `specs/code_refactoring_plan.md` to check off the "Job 2b — pre-commit hooks" boxes.
   - Append an entry to `DEVLOG.md` noting the completion of Phase 2b.

## Verification & Testing
- Ensure `.pre-commit-config.yaml` is syntactically valid.
- Ensure `uv run pre-commit run --all-files` exits with a `0` status code.
- Verify `README.md` and `README.it.md` have the correct setup instructions.
- Verify Phase 2 is marked as completed in the specs.