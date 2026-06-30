# Implementation Plan: Prevent Scale Bar (Rule) Intersection in Section Plot

## Phase 1: Setup and Test Cases (Red Phase) [checkpoint: 1a557db]
- [x] Task: Set up test fixtures (a86163d)
    - [x] Locate the problematic sample DXF files in `tests/fixtures/scale_bar_test`.
    - [x] Configure the PDF generation settings (rule length to 100m, both files in same PDF).
- [x] Task: Write failing unit test (a86163d)
    - [x] Create or update test file for section rendering (e.g., `tests/test_survey_render.py` or similar).
    - [x] Write a test that asserts the bounding box of the scale bar does not intersect with the bounding box of the survey draw in the section plot using the provided DXF files.
    - [x] Verify the test fails on the current implementation.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Setup and Test Cases (Red Phase)' (Protocol in workflow.md)

## Phase 2: Implementation (Green Phase)
- [~] Task: Implement intersection prevention logic for section scale bar
    - [~] Identify where the map scale bar intersection prevention logic is located.
    - [~] Adapt or extract the algorithm for reuse in the section rendering logic.
    - [~] Apply the logic to the section's scale bar placement.
    - [~] Run unit tests and confirm they pass.
- [~] Task: Refactor and Verify
    - [~] Refactor the collision logic for clarity if needed.
    - [~] Ensure code passes `uv run ruff check .` and `uv run mypy cave_sketch/`.
    - [~] Run full test suite (`uv run pytest`) to ensure no regressions.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation (Green Phase)' (Protocol in workflow.md)
