# Spec: Input File Format Validation (Android)

## Overview

Add pre-flight file format validation to the Android app so that invalid files (wrong extension or corrupt DXF content) are caught **before** being sent to the Python rendering engine. When an invalid file is detected, the user receives immediate feedback via a Material Snackbar rather than a cryptic error from the Python layer.

The Streamlit web app already has adequate validation (extension filtering via `st.file_uploader(type=["dxf"])` and `DXFStructureError` handling with `st.error()`) and is **out of scope** for this track.

## Functional Requirements

### FR-1: File Extension Validation at Selection Time
- When the user selects a file via any `FilePickerRow` in the Survey Plot screen, the app must check the file extension **before** copying it to the working directory.
- Accepted extensions: `.dxf` and `.csv` (case-insensitive).
- If the extension is neither `.dxf` nor `.csv`, the file must be **rejected** and a Snackbar shown.

### FR-2: DXF Structure Validation After Copy
- After a `.dxf` file is successfully copied to the working directory, the app must perform a lightweight structural validation to confirm it is a valid DXF file.
- This validation should read the first few bytes/lines of the file to check for the DXF magic marker (the string `0` followed by `SECTION` on the next line, which is the standard DXF file header signature).
- This check runs on the Kotlin side **before** invoking the Python bridge, avoiding the overhead of Chaquopy startup for obviously invalid files.
- If the file fails the structural check, the copied file must be cleaned up and a Snackbar shown.

### FR-3: Snackbar Error Feedback
- All validation errors must be communicated to the user via a Material3 **Snackbar** displayed at the bottom of the screen.
- The Snackbar must show a clear, user-friendly message:
  - Wrong extension: `"Unsupported file format. Please select a .dxf or .csv file."`
  - Invalid DXF structure: `"The selected file is not a valid DXF file."`
- The Snackbar must auto-dismiss after a standard duration (~4 seconds) and also be dismissible via swipe.

### FR-4: File Picker MIME Filtering
- Update all `FilePickerRow` instances used for DXF/CSV input to pass a more restrictive MIME type array instead of `*/*`.
- Since Android has no standard MIME type for `.dxf`, use `application/octet-stream` alongside `*/*` as a fallback, but combine with the extension check from FR-1 to ensure only valid files proceed.
- **Note:** Due to Android MIME type limitations for DXF, the picker may still need to show all files (`*/*`), but the extension validation from FR-1 acts as the hard gate.

### FR-5: Satellite Screen JSON Validation
- Apply the same extension validation to the JSON file picker on the Satellite screen: reject files that don't have a `.json` extension with an appropriate Snackbar message: `"Unsupported file format. Please select a .json file."`

## Non-Functional Requirements

- **NFR-1:** Validation must complete in < 100ms to feel instantaneous to the user.
- **NFR-2:** No new third-party dependencies — use only Android SDK / Kotlin standard library.
- **NFR-3:** Validation logic must be unit-testable (pure functions for extension/header checks).

## Acceptance Criteria

1. Selecting a file with an unsupported extension (e.g., `.txt`, `.pdf`, `.png`) in any file picker on the Survey Plot screen shows a Snackbar and does not update the file path state.
2. Selecting a non-DXF file renamed to `.dxf` triggers the structural validation, shows a Snackbar, and cleans up the temp file.
3. Selecting a valid `.dxf` file proceeds normally with no Snackbar.
4. Selecting a valid `.csv` file proceeds normally with no Snackbar.
5. Selecting a non-JSON file in the Satellite screen's JSON picker shows a Snackbar and does not update state.
6. All validation Snackbars auto-dismiss and are swipe-dismissible.
7. Existing error handling (StateBanner for Python processing errors, Toast for copy failures) remains unchanged.
8. All new validation logic has unit tests.

## Out of Scope

- Streamlit web app validation improvements
- TopoDroid-specific layer validation (checking that the DXF has expected layers like STATION, LEG, etc.)
- File size limits
- CSV content/schema validation
