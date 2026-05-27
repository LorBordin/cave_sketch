# Implementation Plan: Ensure Station ID Visibility

## Phase 1: Implement Z-Order and Auto-Placement for Station IDs
- [ ] Task: Evaluate and potentially update dependencies
    - [ ] Evaluate if a library like `adjustText` is required for robust auto-placement in matplotlib.
    - [ ] If required, add it via `uv add` and update `conductor/tech-stack.md`.
- [ ] Task: Write failing tests for station ID visibility
    - [ ] Create/update tests in `tests/` (e.g., related to the renderer or plot generation) to verify the `zorder` property of rendered text objects is correctly set.
- [ ] Task: Implement Z-Order and Auto-Placement fixes
    - [ ] Modify the plotting logic (e.g., in `cave_sketch/survey/graphics/survey_plot.py`) to ensure station IDs are drawn with a high `zorder` so they appear on top.
    - [ ] Implement auto-placement logic for station IDs relative to their markers to prevent direct overlap.
- [ ] Task: Conductor - User Manual Verification 'Implement Z-Order and Auto-Placement for Station IDs' (Protocol in workflow.md)