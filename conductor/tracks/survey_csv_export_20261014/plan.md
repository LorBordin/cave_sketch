# Implementation Plan: Download Survey CSV Files (Web & Android)

## Phase 1: Survey Core & Python Bridge Logic [checkpoint: f31593a]
- [x] Task: TDD - Write tests for effective section CSV generation and Python bridge [b88bd19]
    - [x] Add unit tests verifying `effective_section_csv` and `effective_map_csv` when merging
    - [x] Add unit tests for `survey_bridge.py` verifying that `generate_survey_plot` returns both `map_csv_path` and `section_csv_path` in its JSON output
- [x] Task: Implement effective section CSV logic and update Python bridge [2295794]
    - [x] Implement `effective_section_csv` function in `android/app/src/main/python/survey_bridge.py`
    - [x] Update `generate_survey_plot` to call `effective_section_csv` and include `section_csv_path` in the result dictionary
- [x] Task: Conductor - User Manual Verification 'Phase 1: Survey Core & Python Bridge Logic' (Protocol in workflow.md) [f31593a]

## Phase 2: Streamlit Webapp CSV Download Integration [checkpoint: 0ce0adc]
- [x] Task: TDD - Write tests for webapp survey CSV download persistence [382652b]
    - [x] Add tests verifying session state and output path resolution for effective map and section CSVs
- [x] Task: Implement CSV download buttons in `app/pages/1_survey_plot.py` [dd661cf]
    - [x] Compute and save `merged_section.csv` when child section is merged (mirroring `merged_map.csv`)
    - [x] Store `effective_map_csv` and `effective_section_csv` in `st.session_state`
    - [x] Add download buttons for Map CSV (`<sanitized_name>_map.csv`) and Section CSV (`<sanitized_name>_section.csv`) under preview
    - [x] Verify iterative survey merging workflow (Upload A+B -> Generate -> Download CSV -> Upload as Main -> Upload C -> Merge)
- [x] Task: Conductor - User Manual Verification 'Phase 2: Streamlit Webapp CSV Download Integration' (Protocol in workflow.md) [0ce0adc]

## Phase 3: Android ViewModel & UI Implementation
- [x] Task: TDD - Write JVM unit tests for Android ViewModel [05e8b20]
    - [x] Update `SurveyPlotViewModelTest.kt` to test parsing of `map_csv_path` and `section_csv_path` into `PlotState.Success`
- [x] Task: Implement Android ViewModel and UI changes [ec36923]
    - [x] Update `PlotState.Success` in `SurveyPlotViewModel.kt` to include `mapCsvPath` and `sectionCsvPath`
    - [x] Update `SurveyPlotScreen.kt` to add "Save / Share Map CSV" and "Save / Share Section CSV" buttons using `SaveShareButton`
    - [x] Update `SessionCleanup.kt` to ensure `merged_section.csv` is included in the session cleanup file list
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Android ViewModel & UI Implementation' (Protocol in workflow.md)

## Phase 4: Android Environment Check & Verification (Pause Point)
- [ ] Task: Verify Android Studio and device connectivity (PAUSE POINT)
    - [ ] Check if Android SDK / Android Studio is installed and `./gradlew` is available
    - [ ] Check if an Android physical device or emulator is connected (`adb devices`)
    - [ ] If Android Studio or an Android test device is NOT available, pause track development, update metadata with status note, and halt for resumption on an Android-equipped laptop
- [ ] Task: Execute Android build and test verification (on Android-capable environment)
    - [ ] Run `./gradlew :app:testDebugUnitTest :app:assembleDebug`
    - [ ] Install debug APK and verify CSV export and iterative merge on Android device
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Android Environment Check & Verification' (Protocol in workflow.md)

## Phase 5: Documentation & Final Verification
- [ ] Task: Update documentation
    - [ ] Update user documentation in `docs/` describing how to merge >2 surveys by downloading and re-uploading CSV files
- [ ] Task: Mandatory verification & DEVLOG updates
    - [ ] Run `uv run ruff check .`
    - [ ] Run `uv run mypy cave_sketch/`
    - [ ] Run `uv run pytest`
    - [ ] Append entries to root `DEVLOG.md` and `android/DEVLOG.md`
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Documentation & Final Verification' (Protocol in workflow.md)
