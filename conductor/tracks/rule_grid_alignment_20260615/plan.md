# Plan: Align Scale Bar to Grid Lines

## Phase 1: Grid-Snap Logic and Tests

- [ ] Task: Write Tests for Grid-Snap Helper
    - [ ] Create `tests/test_rule_grid_snap.py` with tests for a new `snap_to_grid` helper function
    - [ ] Test snapping a horizontal ruler position to nearest grid line (rounding to nearest multiple of `grid_spacing`)
    - [ ] Test snapping a vertical ruler position similarly
    - [ ] Test that snapping is a no-op when `show_grid=False` (function not called)
    - [ ] Test edge cases: position already on a grid line, position exactly between two grid lines
    - [ ] Run tests and confirm they fail (Red Phase)

- [ ] Task: Implement Grid-Snap Helper
    - [ ] Add a `snap_rule_to_grid(rule_pos, grid_spacing, rule_orientation)` function in `cave_sketch/survey/graphics/grid.py` (or a suitable location)
    - [ ] For horizontal orientation: snap `rule_pos[0]` (x) to nearest multiple of `grid_spacing`
    - [ ] For vertical orientation: snap `rule_pos[1]` (y) to nearest multiple of `grid_spacing`
    - [ ] Run tests and confirm they pass (Green Phase)

- [ ] Task: Write Integration Tests for Grid-Aligned Rule in `create_survey`
    - [ ] In `tests/test_rule_grid_snap.py`, add integration tests that call `create_survey` with `show_grid=True` and verify the ruler's start position aligns to a grid line
    - [ ] Add a test with `show_grid=False` verifying the ruler position is unchanged
    - [ ] Run tests and confirm they fail (Red Phase)

- [ ] Task: Integrate Grid-Snap into `create_survey`
    - [ ] In `cave_sketch/survey/graphics/survey_plot.py`, after `compute_dual_layout` returns `rule_pos`, apply `snap_rule_to_grid` when `config["show_grid"]` is `True`
    - [ ] Adjust the north arrow position accordingly (offset from the snapped rule position)
    - [ ] Run full test suite and confirm all tests pass (Green Phase)

- [ ] Task: Conductor - User Manual Verification 'Phase 1: Grid-Snap Logic and Tests' (Protocol in workflow.md)

## Phase 2: Verification and Polish

- [ ] Task: Run Full Quality Gates
    - [ ] Run `uv run ruff check .` and fix any linting errors
    - [ ] Run `uv run mypy cave_sketch/` and fix any type errors
    - [ ] Run `uv run pytest` and confirm all tests pass
    - [ ] Review code for clarity and add/update docstrings as needed

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Verification and Polish' (Protocol in workflow.md)
