# Spec: Align Scale Bar to Grid Lines

## Overview

The PDF survey plots (both plan and section views) render a scale bar (ruler) and a proportional grid overlay where `grid_spacing = rule_length / 2`, meaning the ruler should visually span exactly 2 grid squares. However, the ruler is currently placed at positions determined by the placement system (`get_dual_placement` in `placement.py`), which uses a 2% inset from the *data bounding box*. Since grid lines are snapped to clean multiples of `grid_spacing`, the ruler's start/end edges typically fall between grid lines, making it visually unclear that the ruler equals two grid cells.

## Problem

The ruler's start position (from `get_dual_placement`) is based on a percentage offset from the data bounding box corners, while grid lines are at absolute multiples of `grid_spacing`. These two coordinate systems don't align, causing a visual mismatch between the ruler and the grid — the ruler "floats" between grid lines.

## Functional Requirements

1. **Grid-Snapped Rule Placement:** When the grid is enabled (`show_grid=True`), the ruler's starting edge must be snapped to the nearest grid line. Specifically:
   - For horizontal rulers (plan view): snap the left edge's X coordinate to the nearest multiple of `grid_spacing`.
   - For vertical rulers (section view): snap the bottom edge's Y coordinate to the nearest multiple of `grid_spacing`.
   - The snapped position should be the grid line closest to the position computed by the existing placement system, ensuring the ruler stays in the chosen corner.

2. **Ruler Ends on Grid Line:** Since `rule_length = 2 × grid_spacing`, snapping the start to a grid line automatically guarantees the end also falls on a grid line.

3. **Fallback When Grid is Disabled:** When `show_grid=False`, the ruler placement remains exactly as-is — no grid-snapping is applied.

4. **Non-Overlap Constraint Preserved:** The existing placement system (`compute_dual_layout` → `get_dual_placement`) determines which corner to use and computes the initial position. The grid-snapping is a small positional adjustment applied *after* placement, not a replacement of it. The corner choice, fallback expansion, and north-arrow stacking logic remain unchanged.

5. **Both Views:** The alignment fix applies to both the plan subplot (horizontal ruler) and section subplot (vertical ruler).

## Non-Functional Requirements

- No new user-facing configuration is introduced; the snapping is automatic when the grid is shown.
- The existing ruler segmentation (5 segments) and visual style remain unchanged.
- The north arrow position adjusts correspondingly (it is stacked above/beside the ruler).

## Acceptance Criteria

1. With `show_grid=True`, the ruler's leading edge (left for horizontal, bottom for vertical) sits exactly on a grid line in both plan and section views.
2. The ruler's trailing edge sits exactly on a grid line 2 squares later.
3. With `show_grid=False`, ruler placement is identical to current behavior.
4. The ruler does not overlap with cave survey data (existing placement logic still governs corner choice).
5. All existing tests continue to pass.

## Out of Scope

- Changing the grid spacing derivation (`rule_length / 2`).
- Modifying the satellite map view (no grid/ruler there).
- Changing the ruler's visual style, segment count, or label formatting.
- Changing the placement corner-selection algorithm.
- Any changes to user-facing configuration in the Streamlit UI.
