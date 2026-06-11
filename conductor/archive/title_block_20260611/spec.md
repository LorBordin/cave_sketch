# Spec: PDF Survey Title Block

## Overview

Add a technical title block (cartouche) to the PDF survey output. The title block is a bordered, blueprint-style box placed at the top of the page. It displays the cave name, surveyor name, date of survey, total surveyed length (m), and total depth (m). It replaces the current `fig.suptitle()` with a richer, professional header that does not overlap with the cave sketch.

## Functional Requirements

### FR-1: Title Block Content

The title block displays the following fields in a bordered, structured layout:

| Field | Source | Format |
|---|---|---|
| Cave name | Existing `survey.name` parameter | Text (as-is) |
| Surveyor | New text input from the user in the Streamlit UI | Text (free-form) |
| Date | Auto-populated from current date at generation time | DD/MM/YYYY |
| Total length | Computed from survey data (see FR-3) | `{value:.1f} m` |
| Total depth | Computed from section data (see FR-4) | `{value:.1f} m` or omitted |

### FR-2: Title Block Placement & Rendering

- The title block is rendered as a matplotlib `Axes` or figure-level annotation in the top margin of the A4 page.
- It replaces the current `fig.suptitle()` call.
- It must **not overlap** with the cave sketch subplots. The `fig.subplots_adjust(top=...)` value should be adjusted to leave sufficient room.
- The title block should have a visible border (rectangle) and use a clean, readable font.
- Layout: a single bordered box with the cave name prominently displayed (larger font), and the metadata fields (surveyor, date, length, depth) arranged below or beside it in a structured grid.

### FR-3: Total Length Computation

- **Definition**: Sum of Euclidean distances between all pairs of directly connected numeric-only stations (survey legs).
- **Station filtering**: Only stations whose `Node_Id` matches `^\d+$` (purely numeric) are considered. Polyline nodes (`xxPyy`) and block features are excluded.
- **Connectivity**: Two stations are "connected" if one appears in the other's `Links` list.
- **Each leg is counted once**: If station A links to B and B links to A, the distance A→B is counted only once.
- **Merge-aware**: When a child survey is merged with a parent, the total length must be computed **after** the merge, on the combined dataset. This ensures remapped station IDs and translated coordinates are used.
- **Data source**: Computed from the **plan (map) view** DataFrame.

### FR-4: Total Depth Computation

- **Definition**: `max(Y) - min(Y)` among all numeric-only stations in the **section view** DataFrame.
- **Station filtering**: Same as FR-3 — only purely numeric `Node_Id` values.
- **Merge-aware**: Computed **after** merge if a child survey is present.
- **Absent section**: If no section view data is available, the depth field is **omitted** from the title block (not shown as 0 or N/A).
- **Data source**: Computed from the **section view** DataFrame.

### FR-5: Surveyor Name UI Input

- A new text input field is added to the Streamlit survey plot page (`app/pages/1_survey_plot.py`).
- It is placed near the existing "Survey Name" input, grouped logically (e.g., immediately below it).
- Label: "Surveyor Name" (or "Nome rilevatore" if the UI is Italian).
- Default value: empty string.
- The value is passed through to `draw_survey()` and propagated to the rendering pipeline.

### FR-6: SurveyConfig Extension

- `SurveyConfig` gains a new field: `surveyor_name: str = ""`
- The title block rendering reads this field along with the computed length/depth.

## Non-Functional Requirements

- **NFR-1**: The title block must be legible when printed at 1:N scale on A4 paper.
- **NFR-2**: The title block rendering logic lives in `cave_sketch/survey/` (pure library, no Streamlit imports).
- **NFR-3**: All new public functions have full type annotations.
- **NFR-4**: The feature must pass `ruff check`, `mypy`, and `pytest`.

## Architecture Notes

- **Computation functions** (`compute_total_length`, `compute_total_depth`) should be placed in a new module `cave_sketch/survey/metrics.py`, operating on DataFrames.
- **Title block rendering** should be a new function in `cave_sketch/survey/graphics/title_block.py`, called from `renderer.py`.
- **`draw_survey()` signature change**: Must accept and propagate `surveyor_name` and computed metrics to the renderer.

## Acceptance Criteria

1. A PDF generated from a single survey with both plan and section views displays a bordered title block at the top with all 5 fields populated.
2. A PDF generated without a section view displays the title block with depth omitted.
3. A PDF generated from merged surveys computes length and depth from the merged data.
4. The title block does not overlap with any cave sketch content.
5. The surveyor name entered in the Streamlit UI appears in the PDF title block.
6. The date shown is the date of generation in DD/MM/YYYY format.
7. Total length matches manual calculation of sum of leg distances.
8. Total depth matches `max(Y) - min(Y)` of numeric stations in the section view.

## Out of Scope

- Extending the DXF parser to extract 3D Z-coordinates.
- Custom title block positioning (always top of page).
- Multi-language support for title block labels (hardcoded Italian or English TBD).
- Exporting title block metadata to JSON or KML.
