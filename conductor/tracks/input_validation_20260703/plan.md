# Plan: Input File Format Validation (Android)

## Phase 1: Core Validation Logic

- [ ] Task: Write Tests — File Extension Validator
    - [ ] Create `FileValidatorTest.kt` in `android/app/src/test/java/com/cavesketch/app/util/`
    - [ ] Test `isAcceptedExtension(name, allowed)` with valid extensions (`.dxf`, `.csv`, `.DXF`, `.Csv`) returns true
    - [ ] Test `isAcceptedExtension` with invalid extensions (`.txt`, `.pdf`, `.png`, `.dxf.bak`, no extension) returns false
    - [ ] Test `isAcceptedJsonExtension(name)` with `.json` and `.JSON` returns true, others return false
    - [ ] Run tests and confirm they fail (Red)

- [ ] Task: Write Tests — DXF Header Validator
    - [ ] Test `isDxfHeaderValid(file)` with a file containing a valid DXF header (`0\nSECTION`) returns true
    - [ ] Test `isDxfHeaderValid` with an empty file returns false
    - [ ] Test `isDxfHeaderValid` with a plain text file returns false
    - [ ] Test `isDxfHeaderValid` with a binary file (random bytes) returns false
    - [ ] Run tests and confirm they fail (Red)

- [ ] Task: Implement — FileValidator utility
    - [ ] Create `FileValidator.kt` in `android/app/src/main/java/com/cavesketch/app/util/`
    - [ ] Implement `isAcceptedExtension(displayName: String, allowed: Set<String>): Boolean` — case-insensitive extension check
    - [ ] Implement `isDxfHeaderValid(file: File): Boolean` — reads first few lines to check for DXF magic marker
    - [ ] Define `SURVEY_EXTENSIONS = setOf("dxf", "csv")` and `JSON_EXTENSIONS = setOf("json")`
    - [ ] Run tests and confirm they pass (Green)

- [ ] Task: Conductor - User Manual Verification 'Phase 1: Core Validation Logic' (Protocol in workflow.md)

## Phase 2: Snackbar Infrastructure

- [ ] Task: Implement — SnackbarHost integration in SurveyPlotScreen
    - [ ] Add a `SnackbarHostState` to `SurveyPlotScreen` (or lift to a shared scaffold if needed)
    - [ ] Wire `SnackbarHost` into the Compose layout
    - [ ] Expose a `showSnackbar(message)` suspend function callable from file-picker callbacks via a coroutine scope
    - [ ] Verify visually that a test Snackbar renders correctly (then remove test trigger)

- [ ] Task: Implement — SnackbarHost integration in SatelliteScreen
    - [ ] Add a `SnackbarHostState` and `SnackbarHost` to `SatelliteScreen`
    - [ ] Wire Snackbar display for the satellite screen file picker callbacks

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Snackbar Infrastructure' (Protocol in workflow.md)

## Phase 3: Wire Validation into File Pickers

- [ ] Task: Write Tests — ViewModel validation behavior
    - [ ] Add tests to `SurveyPlotViewModelTest.kt` verifying that:
        - Setting a file with invalid extension does not update the file path state
        - Setting a file with valid extension updates the state normally
    - [ ] Add tests to `SatelliteViewModelTest.kt` verifying JSON extension validation
    - [ ] Run tests and confirm they fail (Red)

- [ ] Task: Implement — Extension validation in SurveyPlotScreen file pickers
    - [ ] Before calling `safeCopyUriToDir`, check `isAcceptedExtension(displayName, SURVEY_EXTENSIONS)`
    - [ ] On rejection: show Snackbar with "Unsupported file format. Please select a .dxf or .csv file.", do NOT update state
    - [ ] Apply to all 4 file picker callbacks (map, section, child map, child section)
    - [ ] Run tests and confirm they pass (Green)

- [ ] Task: Implement — DXF header validation after copy
    - [ ] After `safeCopyUriToDir` succeeds for a `.dxf` file, call `isDxfHeaderValid(copiedFile)`
    - [ ] On failure: delete the copied file, show Snackbar with "The selected file is not a valid DXF file.", do NOT update state
    - [ ] Apply to all DXF file picker callbacks
    - [ ] Run tests and confirm they pass (Green)

- [ ] Task: Implement — JSON extension validation in SatelliteScreen
    - [ ] Before copying each file in the multi-file JSON picker, check `isAcceptedExtension(displayName, JSON_EXTENSIONS)`
    - [ ] On rejection: show Snackbar with "Unsupported file format. Please select a .json file.", skip that file
    - [ ] Run tests and confirm they pass (Green)

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Wire Validation into File Pickers' (Protocol in workflow.md)

## Phase 4: Polish & Cleanup

- [ ] Task: Refactor — Review and clean up validation integration
    - [ ] Ensure no duplicate validation code across screens
    - [ ] Verify error messages are consistent across all pickers
    - [ ] Ensure the existing StateBanner and Toast error paths are not affected
    - [ ] Run full test suite and confirm all tests pass

- [ ] Task: Conductor - User Manual Verification 'Phase 4: Polish & Cleanup' (Protocol in workflow.md)
