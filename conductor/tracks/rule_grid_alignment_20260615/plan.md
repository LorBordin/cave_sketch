# Plan: Align Scale Bar to Grid Lines

## Phase 1: Grid-Snap Logic and Tests [checkpoint: 8bd0f00]

- [x] Task: Write Tests for Grid-Snap Helper (348157c)
    - [x] Create `tests/test_rule_grid_snap.py` with tests for a new `snap_to_grid` helper function
    - [x] Test snapping a horizontal ruler position to nearest grid line (rounding to nearest multiple of `grid_spacing`)
    - [x] Test snapping a vertical ruler position similarly
    - [x] Test that snapping is a no-op when `show_grid=False` (function not called)
    - [x] Test edge cases: position already on a grid line, position exactly between two grid lines
    - [x] Run tests and confirm they fail (Red Phase)

- [x] Task: Implement Grid-Snap Helper (5125a81)
    - [x] Add a `snap_rule_to_grid(rule_pos, grid_spacing, rule_orientation)` function in `cave_sketch/survey/graphics/grid.py` (or a suitable location)
    - [x] For horizontal orientation: snap `rule_pos[0]` (x) to nearest multiple of `grid_spacing`
    - [x] For vertical orientation: snap `rule_pos[1]` (y) to nearest multiple of `grid_spacing`
    - [x] Run tests and confirm they pass (Green Phase)

- [x] Task: Write Integration Tests for Grid-Aligned Rule in `create_survey` (829a421)
    - [x] In `tests/test_rule_grid_snap.py`, add integration tests that call `create_survey` with `show_grid=True` and verify the ruler's start position aligns to a grid line
    - [x] Add a test with `show_grid=False` verifying the ruler position is unchanged
    - [x] Run tests and confirm they fail (Red Phase)

- [x] Task: Integrate Grid-Snap into `create_survey` (48e7a12)
    - [x] In `cave_sketch/survey/graphics/survey_plot.py`, after `compute_dual_layout` returns `rule_pos`, apply `snap_rule_to_grid` when `config["show_grid"]` is `True`
    - [x] Adjust the north arrow position accordingly (offset from the snapped rule position)
    - [x] Run full test suite and confirm all tests pass (Green Phase)

- [x] Task: Conductor - User Manual Verification 'Phase 1: Grid-Snap Logic and Tests' (Protocol in workflow.md)

## Phase 2: Verification and Polish [checkpoint: b8fc6ab]

- [x] Task: Run Full Quality Gates (973cc78)
    - [x] Run `uv run ruff check .` and fix any linting errors
    - [x] Run `uv run mypy cave_sketch/` and fix any type errors
    - [x] Run `uv run pytest` and confirm all tests pass
    - [x] Review code for clarity and add/update docstrings as needed

- [x] Task: Conductor - User Manual Verification 'Phase 2: Verification and Polish' (Protocol in workflow.md)
