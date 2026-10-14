# Specification: Entrance Symbol Orientation & Rotation Preservation

## Overview
When generating PDF cave survey plots via the web application (`draw_survey`), point symbols such as cave entrances (`B_entrance`) and water flow (`B_water-flow`) lose their DXF orientation and always point upward (0° rotation). In contrast, satellite views (HTML and KMZ) display the correct orientation. This specification addresses the loss of rotation data during DataFrame-to-survey conversions and ensures symbol orientations remain aligned under magnetic declination.

## Root Cause
- `cave_sketch.survey.survey._df_to_survey` iterates through the survey DataFrame to create `SurveyPoint` instances, but does not extract or pass the `Rotation` column. All points default to `rotation=0.0`.
- When `render_survey` converts the survey back into a DataFrame via `_survey_to_df`, the `Rotation` column is overwritten with `0.0`, resulting in unrotated symbols in the PDF output.
- Furthermore, `cave_sketch.geo.declination.apply_magnetic_variation` rotates coordinate positions (X, Y) by `-variation_deg`, but leaves the `Rotation` column untouched.

## Functional Requirements
1. **Preserve Rotation in `_df_to_survey`**:
   - Extract the `Rotation` field from the DataFrame if present and valid (`pd.notna(row["Rotation"])`).
   - Pass the parsed float value to `SurveyPoint(..., rotation=...)`.
2. **Magnetic Variation on Symbol Rotation**:
   - In `apply_magnetic_variation`, adjust the `Rotation` column by `-variation_deg` (modulo 360°) when the column exists, maintaining consistency between rotated survey geometry and symbol directions.
3. **Regression Test Fixture**:
   - Keep `tests/fixtures/sample_entrance.dxf` in the repository test suite.
   - Add unit and integration tests verifying that `parse_dxf`, `_df_to_survey`, and `draw_survey` preserve the ~170.17° rotation for `B_entrance`.
4. **Verification in PDF Pipeline**:
   - Ensure the rendered features from `draw_survey` for `sample_entrance.dxf` produce icon strokes oriented toward the cave entrance (~170.17°) rather than pointing straight up.

## Non-Functional Requirements
- Mandatory quality checks: `uv run ruff check .`, `uv run mypy cave_sketch/`, and `uv run pytest`.
- No Streamlit imports inside `cave_sketch/`.
- Maintain backward compatibility with older CSV files lacking a `Rotation` column (gracefully default to 0.0).

## Out of Scope
- Redefining icon vector shapes in `cave_sketch/style_icons.py`.
- Changes to the Android Kotlin UI layer (Android uses the shared Python core via symlinked bridge).
