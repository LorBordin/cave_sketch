# Implementation Plan: Entrance Symbol Orientation & Rotation Preservation

## Phase 1: Core Rotation Preservation & Magnetic Variation [checkpoint: dfdd132]

- [x] Task: TDD - Preserve symbol rotation in `_df_to_survey` (28a810e)
    - [x] Write unit tests demonstrating that converting a DataFrame with a `Rotation` column into a `CaveSurvey` via `_df_to_survey` retains the rotation values on `SurveyPoint` objects, defaulting to 0.0 when missing
    - [x] Implement rotation preservation in `_df_to_survey` in `cave_sketch/survey/survey.py`
    - [x] Verify unit tests pass and code quality checks are satisfied
- [x] Task: TDD - Adjust symbol rotation in `apply_magnetic_variation` (7435353)
    - [x] Write unit tests verifying that applying magnetic variation updates both coordinate geometry and the `Rotation` column by `-variation_deg` (modulo 360°)
    - [x] Implement `Rotation` adjustment in `cave_sketch/geo/declination.py`
    - [x] Verify unit tests pass
- [x] Task: Conductor - User Manual Verification 'Core Rotation Preservation & Magnetic Variation' (Protocol in workflow.md) (dfdd132)

## Phase 2: End-to-End Regression Testing & PDF Survey Verification

- [x] Task: Automated regression test using `tests/fixtures/sample_entrance.dxf` (58d30d9)
    - [x] Write integration test validating `parse_dxf` parses `B_entrance` with ~170.17° rotation
    - [x] Validate `draw_survey` retains this rotation in the rendered feature strokes (verifying apex points toward the entrance rather than north)
    - [x] Confirm backward compatibility with surveys lacking rotation data
- [x] Task: Verification and documentation (9e198d0)
    - [x] Run full project verification: `ruff check`, `mypy cave_sketch/`, `pytest`
    - [x] Document changes in `DEVLOG.md` according to project rules
- [~] Task: Conductor - User Manual Verification 'End-to-End Regression Testing & PDF Survey Verification' (Protocol in workflow.md)
