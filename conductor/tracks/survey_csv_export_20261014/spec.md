# Spec: Download Survey CSV Files (Web & Android)

## Overview
Currently, while multiple surveys can be merged and shared via JSON in the Satellite section, the Survey Plot section does not allow downloading the parsed or merged survey data as CSV. Consequently, if a cave survey consists of more than 2 sub-surveys, users cannot iteratively merge them together. 

This track adds the capability to download the effective/merged CSV files (Map and/or Section) after generating the survey plot in both the Streamlit web application and the Android app. Cavers can then upload these exported CSV files as the "Main Survey" to merge subsequent child surveys (e.g., merging survey 1 + 2, then merging with 3, and so on).

## Functional Requirements
- **FR1 – Effective Survey CSVs Generation & Persistence:**
  - When generating a survey plot (whether single survey or merged parent + child):
    - Compute and persist the effective map CSV (`merged_map.csv` if child map merged, else parsed `map.csv` if present).
    - Compute and persist the effective section CSV (`merged_section.csv` if child section merged, else parsed `section.csv` if present).
    - Merged section CSV computation must mirror the section merge performed in `draw_survey()` (using `merge_surveys` with the chosen `section_protocol`).
- **FR2 – Webapp UI Download Buttons:**
  - In `app/pages/1_survey_plot.py`, underneath the survey preview and alongside "📥 Download PDF":
    - Display "📥 Download Map CSV" when an effective map CSV exists, named `<sanitized_survey_name>_map.csv`.
    - Display "📥 Download Section CSV" when an effective section CSV exists, named `<sanitized_survey_name>_section.csv`.
    - CSV files use MIME type `text/csv`.
- **FR3 – Android Python Bridge (`survey_bridge.py`):**
  - Update `generate_survey_plot` to return `section_csv_path` in the JSON result (alongside `pdf_path` and `map_csv_path`).
  - Introduce `effective_section_csv()` mirroring `effective_map_csv()`.
- **FR4 – Android Kotlin Model & State:**
  - In `SurveyPlotViewModel.kt`:
    - Update `PlotState.Success` to hold `pdfPath: String`, `mapCsvPath: String? = null`, and `sectionCsvPath: String? = null`.
    - Parse `map_csv_path` and `section_csv_path` from the bridge response.
- **FR5 – Android UI (`SurveyPlotScreen.kt`):**
  - Under `PlotState.Success`, display:
    - Existing "Save / Share PDF" button.
    - "Save / Share Map CSV" button (using `SaveShareButton` with `mimeType = "text/csv"`, display name `<surveyName>_map.csv`) if `mapCsvPath` is present.
    - "Save / Share Section CSV" button (using `SaveShareButton` with `mimeType = "text/csv"`, display name `<surveyName>_section.csv`) if `sectionCsvPath` is present.
  - Update `SessionCleanup.kt` to ensure any temporary merged/saved CSV files are properly tracked and cleaned up.

## Non-Functional Requirements
- Zero Streamlit imports in `cave_sketch/`.
- Full type annotations on all new Python functions.
- Python verification gates (`uv run ruff check .`, `uv run mypy cave_sketch/`, `uv run pytest`) must pass.
- Android unit tests for `SurveyPlotViewModelTest` must pass.
- Adhere to TDD.

## ⏸ Device Constraint & Environment Verification (Android Pause Point)
- Not all development machines have Android Studio or the Android SDK installed, or have a connected Android test device.
- The plan must include a dedicated verification phase and pause point:
  - If Android Studio / Android SDK and a test device/emulator are available, compile, run Android tests, and verify on-device.
  - If Android Studio or an Android test device is NOT available, pause the track after all possible non-device implementations (Python core, web UI, Android Kotlin code & JVM tests) are completed.

## Acceptance Criteria
1. Webapp: Generating a survey plot with Map and/or Section provides download buttons for Map CSV and/or Section CSV.
2. Webapp Iterative Merge: Downloading the merged CSVs from surveys A+B and re-uploading them as Main Survey allows successfully merging survey C.
3. Android: Bridge outputs both `map_csv_path` and `section_csv_path` when available.
4. Android: Successful plot generation displays Save/Share buttons for Map CSV and Section CSV alongside the PDF button.
5. All Python linting, typing, and pytest tests pass.

## Out of Scope
- Automatic multi-file batch merging in a single step (iterative chaining via CSV export/import is the intended design).
- Modifying the underlying DXF parser or internal CSV schema.
- Changes to Satellite JSON or KMZ formats.
