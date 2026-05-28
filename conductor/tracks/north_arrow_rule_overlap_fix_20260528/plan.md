# Implementation Plan: North Arrow and Rule Overlap Fix

## Phase 1: Logic Refinement [checkpoint: 44920a7]
- [x] Task: Update placement logic tests
    - [x] Task: Add failing tests for vertical stacking (Arrow on top of Rule).
    - [x] Task: Add failing tests for center alignment.
    - [x] Task: Add failing tests for 3% padding constraint.
- [x] Task: Update `cave_sketch/survey/graphics/placement.py`
    - [x] Task: Refactor `corner_anchor` to return coordinates for both elements or a structured layout object.
    - [x] Task: Implement 3% padding calculation in corner scoring.
    - [x] Task: Implement vertical center alignment logic.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Logic Refinement' (Protocol in workflow.md)

## Phase 2: Integration & Fallback [checkpoint: 3d648bb]

### 2a: Update `placement.py`
- [x] Task: Update `get_dual_placement` signature [cd0aa5d]
    - [x] Add `ref_scale=None` as an optional keyword parameter.
    - [x] When `ref_scale` is provided: `rule_height = ref_scale * 0.01`, `vertical_gap = ref_scale * 0.02` (overrides explicit `vertical_gap` arg).
    - [x] When `ref_scale=None`: preserve existing behaviour (`rule_height_est = 2.0`, `vertical_gap` default = 2.0).
- [x] Task: Update `score_corners` to support element-sized penalty zones [cd0aa5d]
    - [x] Add optional `padding_x_units` / `padding_y_units` absolute parameters.
    - [x] When provided, use these instead of `width * padding_fraction` / `height * padding_fraction` for the penalty zone.
    - [x] Preserve existing fraction-based behaviour when the new params are not provided.
- [x] Task: Update `find_best_corner_with_padding` signature [cd0aa5d]
    - [x] Add optional `padding_x_units` / `padding_y_units` parameters and forward them to `score_corners`.
    - [x] Keep `padding_fraction` as default fallback so existing callers are unaffected.
- [x] Task: Add `compute_dual_layout(x, y, rule_length, arrow_len, ref_scale)` to `placement.py` [cd0aa5d]
    - [x] Compute `vertical_gap = ref_scale * 0.02`, `rule_height = ref_scale * 0.01`.
    - [x] Compute element footprint: `elem_w = max(rule_length, arrow_len)`, `elem_h = arrow_len + vertical_gap + rule_height`.
    - [x] Convert footprint + 3% margin to `padding_x_units` / `padding_y_units` and pass to `find_best_corner_with_padding`.
    - [x] Call `get_dual_placement(best_corner, ..., rule_width=rule_length, arrow_height=arrow_len, ref_scale=ref_scale)`.
    - [x] Return `(arrow_pos, rule_pos, None)` when a valid corner is found.
    - [x] Fallback — wide cave (`x_span >= y_span`): expand bottom by `elem_h + ref_scale * 0.03`; place pair at bottom-left of expanded strip; return `(arrow_pos, rule_pos, {"y_min": new_y_min})`.
    - [x] Fallback — tall cave (`y_span > x_span`): expand left by `elem_w + ref_scale * 0.03`; place pair at bottom-left of expanded strip; return `(arrow_pos, rule_pos, {"x_min": new_x_min})`.

### 2b: Update tests for `placement.py`
- [x] Task: Add `test_dual_placement_vertical_stack_scaled` to `tests/test_placement_refined.py` [cd0aa5d]
    - [x] Call `get_dual_placement` with `ref_scale=100`; verify `rule_height = 1.0` (100 * 0.01) and `vertical_gap = 2.0` (100 * 0.02) in computed positions.
    - [x] Existing `test_dual_placement_vertical_stack` (explicit `vertical_gap=2`) must still pass unchanged.
- [x] Task: Add `compute_dual_layout` tests to `tests/test_placement_refined.py` [cd0aa5d]
    - [x] `test_compute_dual_layout_returns_best_corner` — clear data, no fallback; verify arrow above rule and horizontally centered.
    - [x] `test_compute_dual_layout_fallback_wide_cave` — dense data, `x_span >= y_span`; verify `axes_exp["y_min"]` set, elements in expanded strip.
    - [x] `test_compute_dual_layout_fallback_tall_cave` — dense data, `y_span > x_span`; verify `axes_exp["x_min"]` set.
    - [x] `test_compute_dual_layout_element_sized_zones` — data point at corner of element footprint + 3% margin; verify that corner is penalised and a different one is chosen.

### 2c: Update `survey_plot.py`
- [x] Task: Update imports in `cave_sketch/survey/graphics/survey_plot.py` [cd0aa5d]
    - [x] Remove: `corner_anchor`, `find_best_corner`, `is_fallback_needed`.
    - [x] Add: `compute_dual_layout`.
- [x] Task: Replace inline placement block in `create_survey` with single `compute_dual_layout` call [cd0aa5d]
    - [x] Pass `rule_length`, `arrow_len = ref_scale * 0.07`, `ref_scale`.
    - [x] Apply `axes_expansion`: call `ax.set_ylim` if `"y_min"` key present, `ax.set_xlim` if `"x_min"` key present.
    - [x] Forward `arrow_pos` to `_add_north_arrow(coords=arrow_pos, ...)`.
    - [x] Forward `rule_pos` to `_add_rule(x_start=rule_pos[0], y_start=rule_pos[1], ...)`.

### 2d: Update `test_survey_plot_placement.py`
- [x] Task: Update `test_create_survey_uses_dynamic_placement` [cd0aa5d]
    - [x] Mock `compute_dual_layout` instead of `corner_anchor`, `find_best_corner`, `is_fallback_needed`.
    - [x] Verify `_add_north_arrow` called with `coords=arrow_pos` from mock.
    - [x] Verify `_add_rule` called with `x_start=rule_pos[0]`, `y_start=rule_pos[1]` from mock.
- [x] Task: Update `test_create_survey_fallback_behavior` [cd0aa5d]
    - [x] Mock `compute_dual_layout` returning `axes_exp = {"y_min": -50}`.
    - [x] Verify `ax.set_ylim` called with the expanded value.
    - [x] Add variant: `axes_exp = {"x_min": -50}`, verify `ax.set_xlim` called.

### 2e: Verify PDF output
- [x] Task: Generate sample PDFs for various cave shapes (long, wide, dense) and verify no overlap visually. [cd0aa5d]
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Integration & Fallback' (Protocol in workflow.md)
