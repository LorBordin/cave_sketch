# Implementation Plan: Section Scale Bar Grid-Snap Collision Fix

## Phase 1: Reproduce and Write Tests (Red Phase) [checkpoint: 0f4c6cd]
- [x] Task: Write failing test for grid-snap collision (e252e11)
    - [x] Add a `show_grid=True` variant of the existing `test_section_scale_bar_no_intersection` test.
    - [x] Create a new test `test_grid_snap_skipped_on_collision` that verifies: when grid-snapping would push the scale bar into survey data, the snap is skipped and the original collision-free position is preserved.
    - [x] Run the tests and confirm they fail on the current implementation (Red phase).
- [x] Task: Conductor - User Manual Verification 'Phase 1: Reproduce and Write Tests (Red Phase)' (Protocol in workflow.md) (0f4c6cd)

## Phase 2: Fix Grid-Snap Collision Logic (Green Phase) [checkpoint: 6c866c5]
- [x] Task: Implement post-snap collision re-check in `survey_plot.py` (934ea79)
    - [x] After `snap_rule_to_grid()` is called, re-check whether the snapped position causes overlap with survey data points (reuse the collision-checking logic from `placement.py`).
    - [x] If the snapped position causes a collision, revert to the original pre-snap `rule_pos` (and `arrow_coord`).
    - [x] Ensure this logic works for both horizontal and vertical rule orientations.
    - [x] Run the failing tests and confirm they now pass (Green phase).
- [x] Task: Refactor and verify (dce3009)
    - [x] Review the code for clarity and extract a helper function if needed (e.g., `check_collision_at_position()`).
    - [x] Run `uv run ruff check .`, `uv run mypy cave_sketch/`, and `uv run pytest` to confirm everything passes.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Fix Grid-Snap Collision Logic (Green Phase)' (Protocol in workflow.md) (6c866c5)
