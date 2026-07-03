# Plan: Input File Format Validation (Android)

## Phase 1: Core Validation Logic [checkpoint: 227cb1e]

- [x] Task: Write Tests — File Extension Validator (eb0f77c)
    - [x] Create `FileValidatorTest.kt` in `android/app/src/test/java/com/cavesketch/app/util/`
    - [x] Test `isAcceptedExtension(name, allowed)` with valid extensions (`.dxf`, `.csv`, `.DXF`, `.Csv`) returns true
    - [x] Test `isAcceptedExtension` with invalid extensions (`.txt`, `.pdf`, `.png`, `.dxf.bak`, no extension) returns false
    - [x] Test `isAcceptedJsonExtension(name)` with `.json` and `.JSON` returns true, others return false
    - [x] Run tests and confirm they fail (Red)

- [x] Task: Write Tests — DXF Header Validator (eb0f77c)
    - [x] Test `isDxfHeaderValid(file)` with a file containing a valid DXF header (`0\nSECTION`) returns true
    - [x] Test `isDxfHeaderValid` with an empty file returns false
    - [x] Test `isDxfHeaderValid` with a plain text file returns false
    - [x] Test `isDxfHeaderValid` with a binary file (random bytes) returns false
    - [x] Run tests and confirm they fail (Red)

- [x] Task: Implement — FileValidator utility (270801a)
    - [x] Create `FileValidator.kt` in `android/app/src/main/java/com/cavesketch/app/util/`
    - [x] Implement `isAcceptedExtension(displayName: String, allowed: Set<String>): Boolean` — case-insensitive extension check
    - [x] Implement `isDxfHeaderValid(file: File): Boolean` — reads first few lines to check for DXF magic marker
    - [x] Define `SURVEY_EXTENSIONS = setOf("dxf", "csv")` and `JSON_EXTENSIONS = setOf("json")`
    - [x] Run tests and confirm they pass (Green)

- [x] Task: Conductor - User Manual Verification 'Phase 1: Core Validation Logic' (Protocol in workflow.md) (227cb1e)

## Phase 2: Snackbar Infrastructure [checkpoint: aaf8ba8]

- [x] Task: Implement — SnackbarHost integration in SurveyPlotScreen (d0860bd)
    - [x] Add a `SnackbarHostState` to `SurveyPlotScreen` (or lift to a shared scaffold if needed)
    - [x] Wire `SnackbarHost` into the Compose layout
    - [x] Expose a `showSnackbar(message)` suspend function callable from file-picker callbacks via a coroutine scope
    - [x] Verify visually that a test Snackbar renders correctly (then remove test trigger)

- [x] Task: Implement — SnackbarHost integration in SatelliteScreen (d0860bd)
    - [x] Add a `SnackbarHostState` and `SnackbarHost` to `SatelliteScreen`
    - [x] Wire Snackbar display for the satellite screen file picker callbacks

- [x] Task: Conductor - User Manual Verification 'Phase 2: Snackbar Infrastructure' (Protocol in workflow.md) (aaf8ba8)

## Phase 3: Wire Validation into File Pickers [checkpoint: 8a97c95]

- [x] Task: Write Tests — ViewModel validation behavior (4557365)
    - [x] Add tests to `SurveyPlotViewModelTest.kt` verifying that:
        - [x] Setting a file with invalid extension does not update the file path state
        - [x] Setting a file with valid extension updates the state normally
    - [x] Add tests to `SatelliteViewModelTest.kt` verifying JSON extension validation
    - [x] Run tests and confirm they fail (Red)

- [x] Task: Implement — Extension validation in SurveyPlotScreen file pickers (2d85f1c)
    - [x] Before calling `safeCopyUriToDir`, check `isAcceptedExtension(displayName, SURVEY_EXTENSIONS)`
    - [x] On rejection: show Snackbar with "Unsupported file format. Please select a .dxf or .csv file.", do NOT update state
    - [x] Apply to all 4 file picker callbacks (map, section, child map, child section)
    - [x] Run tests and confirm they pass (Green)

- [x] Task: Implement — DXF header validation after copy (2d85f1c)
    - [x] After `safeCopyUriToDir` succeeds for a `.dxf` file, call `isDxfHeaderValid(copiedFile)`
    - [x] On failure: delete the copied file, show Snackbar with "The selected file is not a valid DXF file.", do NOT update state
    - [x] Apply to all DXF file picker callbacks
    - [x] Run tests and confirm they pass (Green)

- [x] Task: Implement — JSON extension validation in SatelliteScreen (2d85f1c)
    - [x] Before copying each file in the multi-file JSON picker, check `isAcceptedExtension(displayName, JSON_EXTENSIONS)`
    - [x] On rejection: show Snackbar with "Unsupported file format. Please select a .json file.", skip that file
    - [x] Run tests and confirm they pass (Green)

- [x] Task: Conductor - User Manual Verification 'Phase 3: Wire Validation into File Pickers' (Protocol in workflow.md) (8a97c95)

## Phase 4: Polish & Cleanup

- [~] Task: Refactor — Review and clean up validation integration
    - [ ] Ensure no duplicate validation code across screens
    - [ ] Verify error messages are consistent across all pickers
    - [ ] Ensure the existing StateBanner and Toast error paths are not affected
    - [ ] Run full test suite and confirm all tests pass

- [ ] Task: Conductor - User Manual Verification 'Phase 4: Polish & Cleanup' (Protocol in workflow.md)
