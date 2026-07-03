# Specification: Section Scale Bar Grid-Snap Collision Fix

## Overview
The section scale bar (vertical rule) placement algorithm correctly finds a collision-free position, but the subsequent grid-snapping step (`snap_rule_to_grid()`) can shift the rule's Y coordinate to the nearest grid multiple, pushing it back into overlap with the survey data. This only manifests when `show_grid=True` (the default on both web and Android), making it the actual root cause of the overlap bug reported on the Android app.

The original `section_rule_fix_20260630` track fixed collision detection but tested only with `show_grid=False`, missing this code path.

## Root Cause
In `survey_plot.py` lines 96–102, after `compute_dual_layout()` returns a collision-free `rule_pos`, the grid-snap logic unconditionally moves the rule to the nearest grid-aligned position without re-checking for collisions.

## Functional Requirements
- After grid-snapping the rule position, re-check whether the snapped position causes any overlap with the survey data points.
- If the snapped position causes a collision, skip the grid snap and keep the original collision-free position (collision-free placement takes priority over grid alignment).
- This logic must work for both horizontal and vertical rule orientations.

## Non-Functional Requirements
- The change must be covered by unit tests that specifically test the `show_grid=True` path.
- No measurable rendering latency increase.
- The fix must pass `ruff check`, `mypy`, and `pytest`.

## Acceptance Criteria
1. Updated test `test_section_scale_bar_no_intersection` includes a `show_grid=True` variant.
2. A new test specifically verifies that grid-snapping does not reintroduce collisions.
3. Manual verification on the Android app confirms the section scale bar no longer overlaps the survey drawing with grid enabled.
4. All existing tests continue to pass.

## Out of Scope
- Changing the grid-snap algorithm itself.
- Modifying the visual style of the scale bar or grid.
- Any Android-specific code changes (the fix is in the shared Python library).
