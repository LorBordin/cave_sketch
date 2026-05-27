# Implementation Plan: North Symbol Visibility for Section Renders

## Phase 1: Investigation and Testing
- [ ] Task: Identify the rendering module and function responsible for drawing the north symbol (likely in `cave_sketch/survey/graphics/north.py` or `cave_sketch/survey/renderer.py`).
- [ ] Task: Identify where the view selection (plan vs. section) is evaluated during PDF generation.
- [ ] Task: Write failing unit test(s) verifying that the north symbol drawing function is bypassed or returns early when only the section view is requested.
    - [ ] Locate or create the test file for the relevant rendering module (e.g., `tests/test_renderer.py`).
    - [ ] Create a test case simulating a PDF generation with `plan_view=False` and `section_view=True`.
    - [ ] Assert that the north symbol is not present in the output or that the rendering function is not called.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Investigation and Testing' (Protocol in workflow.md)

## Phase 2: Implementation
- [ ] Task: Modify the backend rendering logic to conditionally draw the north symbol.
    - [ ] Update the drawing routine to check the current view configuration.
    - [ ] Ensure the north symbol is skipped if the configuration indicates a section-only render.
- [ ] Task: Run all automated tests (`uv run pytest`) and ensure the newly written tests pass (Green Phase).
- [ ] Task: Run linting and static analysis (`uv run ruff check .` and `uv run mypy cave_sketch/`) to ensure code quality.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation' (Protocol in workflow.md)