# Implementation Plan: North Symbol Placement Fix

## Phase 1: Bounding Box and Corner Analysis
- [ ] Task: Add failing tests for corner analysis
    - [ ] Sub-task: Test `find_best_corner(x_coords, y_coords)` — given post-rotation X/Y arrays, returns one of `{"top-left", "top-right", "bottom-left", "bottom-right"}`.
    - [ ] Sub-task: Test the tie-breaking priority (bottom-left > bottom-right > top-left > top-right).
    - [ ] Sub-task: Test that the fallback case is triggered when all corners exceed the 50% density threshold.
- [ ] Task: Implement corner analysis logic in `cave_sketch/survey/graphics/placement.py` (new file)
    - [ ] Sub-task: Implement `compute_data_bbox(x, y) -> (x_min, x_max, y_min, y_max)`.
    - [ ] Sub-task: Implement `score_corners(x, y, zone_fraction=0.20) -> dict[str, float]` — returns a free-space score per corner.
    - [ ] Sub-task: Implement `find_best_corner(x, y) -> str` — selects winner using score + tie-break priority.
    - [ ] Sub-task: Implement `corner_anchor(corner, x_min, x_max, y_min, y_max, inset_fraction=0.02) -> (float, float)` — returns the anchor coordinate for the symbol.
    - [ ] Sub-task: Implement `is_fallback_needed(scores) -> bool` — returns True when all corners exceed the 50% density threshold.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Bounding Box and Corner Analysis' (Protocol in workflow.md)

## Phase 2: North Symbol Integration
- [ ] Task: Add failing tests for North symbol placement
    - [ ] Sub-task: Test that `create_survey` in `cave_sketch/survey/graphics/survey_plot.py` places the North symbol at the corner returned by `find_best_corner`.
    - [ ] Sub-task: Test that the scale rule is placed in the same corner as the North symbol.
    - [ ] Sub-task: Test that the fallback expands the axes limits rather than overlapping the sketch.
- [ ] Task: Integrate dynamic placement in `cave_sketch/survey/graphics/survey_plot.py`
    - [ ] Sub-task: **After** rotation is applied to `df` (line ~38), call `find_best_corner` on the rotated X/Y arrays and `corner_anchor` to compute symbol coordinates.
    - [ ] Sub-task: Pass the computed coordinates to `_add_north_arrow` and `_add_rule` instead of the current hardcoded offsets.
    - [ ] Sub-task: Implement fallback: if `is_fallback_needed`, extend `ax.set_xlim` / `ax.set_ylim` to accommodate the symbol outside the data range.
    - [ ] Sub-task: Ensure `rule_orientation` is set appropriately based on the chosen corner (horizontal rule for top/bottom corners, vertical for left/right corners).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: North Symbol Integration' (Protocol in workflow.md)