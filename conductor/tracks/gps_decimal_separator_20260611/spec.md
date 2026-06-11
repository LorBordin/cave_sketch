# Spec: GPS Coordinate Decimal Separator Fix

## Overview

The Satellite Map page uses `st.number_input` for Latitude and Longitude fields. This widget delegates decimal separator handling to the browser locale, meaning users on some locales must use `,` while others must use `.`. This track replaces those inputs with `st.text_input` and custom parsing so that **both `,` and `.`** are accepted as decimal separators regardless of locale.

## Functional Requirements

### FR-1: Create `parse_coordinate()` in the library layer
- Create a function `parse_coordinate(value: str) -> float | None` in `cave_sketch/geo/coordinates.py`.
- Parsing rules:
  - Strip leading/trailing whitespace.
  - Replace `,` with `.` to normalize the decimal separator.
  - Attempt to parse the result as a `float`.
  - Return the `float` value on success, or `None` if the input cannot be parsed (e.g. empty string, letters, multiple dots).
- No Streamlit imports allowed.

### FR-2: Replace `number_input` with `text_input` for GPS coordinates
- In `app/components/gps_points.py`, replace the `st.number_input` calls for Latitude and Longitude with `st.text_input`.
- The text inputs display the raw string the user typed (e.g. `"45,123456"` or `"45.123456"`).
- On each render, parse the text value using `parse_coordinate()` and store the resulting `float` (or `None`) in the `known_points` list in session state.
- Default display value for new points: `"0.000000"` (using `.` as separator).

### FR-3: Inline validation feedback
- When a Latitude or Longitude field contains a value that `parse_coordinate()` returns `None` for, display an inline error message below the field (e.g. `st.error("Invalid coordinate")` or red caption text).
- The "Generate HTML Map" button validation (`validate_known_points()`) must also reject points with unparseable coordinates.

## Non-Functional Requirements

- `parse_coordinate()` must live in `cave_sketch/geo/coordinates.py` with full type annotations.
- Unit tests for `parse_coordinate()` covering: dot input, comma input, mixed valid inputs, empty string, whitespace-only, letters, multiple separators, negative coordinates.
- `uv run ruff check .`, `uv run mypy cave_sketch/`, and `uv run pytest` must all pass.

## Acceptance Criteria

1. Entering `"45,678901"` in the Latitude field is parsed as `45.678901`.
2. Entering `"12.345678"` in the Longitude field is parsed as `12.345678`.
3. Entering `"abc"` in either field shows an inline error and prevents map generation.
4. Entering `""` (empty) shows an inline error and prevents map generation.
5. Negative coordinates (e.g. `"-7,654321"`) are parsed correctly as `-7.654321`.
6. The dot (`.`) is the default display format for new/default points.

## Out of Scope

- Changing the GPS points data structure in session state beyond what's needed for text-based input.
- Adding coordinate range validation (e.g. lat must be -90..90). This can be a future enhancement.
- Changing the Station ID input (remains `text_input` as-is).
