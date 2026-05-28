# Specification: North Arrow and Rule Overlap Fix

## Overview
This track fixes a layout bug where the North arrow and the scale rule can overlap with each other or with the cave sketch. It refines the placement logic to ensure a clear, professional survey plot. A new high-level function `compute_dual_layout` in `placement.py` encapsulates all placement decisions (corner selection, element positioning, fallback) so that `survey_plot.py` remains thin.

## Functional Requirements

### Element Stacking & Alignment
- The scale rule must be placed below the North arrow.
- The North arrow must be horizontally centered relative to the width of the scale rule.
- `vertical_gap` between the two elements scales with `ref_scale`: `vertical_gap = ref_scale * 0.02`.
- `rule_height` (used for layout math) scales with `ref_scale`: `rule_height = ref_scale * 0.01`.

### No-Overlap: Enhanced Corner Scoring
The corner-scoring heuristic must use the **actual element footprint** rather than a fixed 20% zone fraction, so the penalty zone reflects where the arrow+rule pair will actually land:
- Element footprint: `elem_w = max(rule_length, arrow_len)`, `elem_h = arrow_len + vertical_gap + rule_height`.
- Penalty is applied to any corner whose footprint zone (element size + 3% of axes range margin) contains any sketch data point.
- `score_corners` is updated to accept optional `padding_x_units` / `padding_y_units` absolute parameters; when provided these replace the fraction-based penalty zone.

### No-Overlap: Sketch Avoidance
A minimum margin of **3% of the axes range** is maintained between the combined arrow+rule bounding box and any sketch data point.

### `compute_dual_layout` — High-Level Placement Function
A single function in `placement.py` with signature:

```
compute_dual_layout(x, y, rule_length, arrow_len, ref_scale) -> (arrow_pos, rule_pos, axes_expansion)
```

Responsibilities:
1. Computes scaled `vertical_gap` and `rule_height`.
2. Computes element footprint and passes it as absolute padding units to `find_best_corner_with_padding`.
3. Calls `get_dual_placement` with the best corner and scaled gaps.
4. Returns `axes_expansion = None` if a valid corner was found.
5. If no corner is valid, triggers fallback (see below) and returns `axes_expansion` dict.

Parameter mapping from `survey_plot.py`:
- `rule_width` argument of `get_dual_placement` ← `rule_length`
- `arrow_height` argument of `get_dual_placement` ← `arrow_len` (= `ref_scale * 0.07`)

### Fallback Behaviour
When all corners are crowded (no valid corner with 3% clearance):
- **Wide cave** (`x_span ≥ y_span`): expand the bottom axis by `elem_h + ref_scale * 0.03`. Return `axes_expansion = {"y_min": new_y_min}`. Place the pair at the bottom-left of the expanded strip using `get_dual_placement`.
- **Tall cave** (`y_span > x_span`): expand the left axis by `elem_w + ref_scale * 0.03`. Return `axes_expansion = {"x_min": new_x_min}`. Place the pair at the bottom-left of the expanded strip using `get_dual_placement`.

### `survey_plot.py` Simplification
`create_survey` calls `compute_dual_layout` once and forwards the results directly to `_add_rule` and `_add_north_arrow`. The old inline logic (`corner_anchor`, `find_best_corner`, `is_fallback_needed`, offset hacks) is removed.

## Non-Functional Requirements
- Maintain rendering performance for large surveys.
- Consistent visual style across all PDF exports.
- No breaking changes: `ref_scale` is added to `get_dual_placement` as `ref_scale=None` (optional); existing callers that pass `vertical_gap` explicitly are unaffected. `padding_x_units` / `padding_y_units` are added to `score_corners` and `find_best_corner_with_padding` as optional kwargs; fraction-based behaviour is preserved when omitted.

## Acceptance Criteria
- [x] North arrow and scale rule are vertically stacked (Arrow on top). *(Phase 1)*
- [x] North arrow is horizontally centered relative to the scale rule. *(Phase 1)*
- [ ] `vertical_gap` and `rule_height` scale with `ref_scale` — no hardcoded data-unit values.
- [ ] Corner scoring uses the actual element footprint + 3% margin as the penalty zone.
- [ ] No overlap between North arrow, scale rule, and cave sketch in generated PDFs.
- [ ] Fallback expands the bottom axis for wide caves and the left axis for tall caves.
- [ ] `survey_plot.py` calls only `compute_dual_layout`; old placement helpers are removed from its imports.

## Out of Scope
- Changing the graphical design of the North symbol or scale rule.
- Adding other annotations (text, legends) beyond these two.
- Strict pixel-level bounding box intersection checks (the enhanced heuristic is sufficient).
