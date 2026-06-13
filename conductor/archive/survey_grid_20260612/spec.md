# Spec: Survey Grid Overlay

## Overview
Add a proportional grid overlay to both the **plan** (map) and **section** survey plots. The grid provides a visual spatial reference that helps cavers quickly estimate cave proportions and distances without needing to measure against the scale bar.

The grid spacing dynamically scales as **half the rule length**. For example, if the scale bar is set to 20m, the grid draws lines every 10m; if set to 50m, every 25m.

## Functional Requirements

### FR-1: Grid Rendering
- Draw a regular grid of **horizontal and vertical lines** on both the plan and section subplots.
- Grid spacing = `rule_length / 2` (in survey data units / meters).
- Grid lines must be rendered **behind** all cave survey features (lowest z-order).
- Grid lines use **light gray dotted lines** (`color='lightgray'`, `linestyle=':'`) for minimal visual weight.
- Grid lines must cover the full visible extent of the survey data on each axis.

### FR-2: Grid Alignment
- Grid lines are aligned to clean multiples of the grid spacing (e.g., 0, 10, 20, 30... not 3.7, 13.7, 23.7).
- This ensures the grid reads as a consistent, well-anchored reference.

### FR-3: No Grid Labels
- The grid does **not** display distance labels on its lines. The existing scale bar already provides scale context.

### FR-4: UI Toggle
- Add a **"Show grid" checkbox** in the Streamlit survey settings panel.
- The checkbox is **enabled by default** (`True`).
- The toggle value is stored in `session_state` and passed through to the rendering pipeline via `SurveyConfig`.

### FR-5: Grid Is Always Axis-Aligned
- Grid lines are **always horizontal and vertical** on the plot, regardless of any cave rotation (`rotation_deg`).
- When the user rotates the cave, the cave data rotates but the grid remains fixed to the plot axes. This provides a stable visual reference frame.
- Implementation: the grid is drawn using the post-rotation data extents, so it naturally stays axis-aligned.

## Non-Functional Requirements
- Grid rendering must not noticeably slow down plot generation.
- Grid lines must not obscure cave detail at any scale.

## Acceptance Criteria
1. When `show_grid=True` (default), both plan and section plots display a grid with spacing = `rule_length / 2`.
2. Grid lines are light gray dotted, rendered behind all survey elements.
3. Grid lines are aligned to clean multiples of the spacing value.
4. Toggling "Show grid" off in the UI removes the grid from both plots.
5. The grid adapts when the user changes the rule length.
6. Grid remains axis-aligned (horizontal/vertical) when cave rotation is applied.
7. All existing tests continue to pass.

## Out of Scope
- Grid distance labels along edges.
- Customizable grid spacing independent of the rule.
- Grid on satellite/HTML map views.
