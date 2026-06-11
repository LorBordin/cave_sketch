# Plan: GPS Coordinate Decimal Separator Fix

## Phase 1: Parse Coordinate Utility [checkpoint: 5556092]

- [x] Task: Write tests for `parse_coordinate()` [d296a19]
    - [x] Create `tests/test_parse_coordinate.py`
    - [x] Test dot decimal input (e.g. `"45.678901"` → `45.678901`)
    - [x] Test comma decimal input (e.g. `"45,678901"` → `45.678901`)
    - [x] Test negative coordinate with dot (e.g. `"-7.654321"` → `-7.654321`)
    - [x] Test negative coordinate with comma (e.g. `"-7,654321"` → `-7.654321`)
    - [x] Test integer input (e.g. `"45"` → `45.0`)
    - [x] Test input with leading/trailing whitespace
    - [x] Test empty string returns `None`
    - [x] Test whitespace-only input returns `None`
    - [x] Test letters input returns `None` (e.g. `"abc"`)
    - [x] Test multiple dots returns `None` (e.g. `"45.67.89"`)
    - [x] Test multiple commas returns `None` (e.g. `"45,67,89"`)
    - [x] Run tests and confirm they fail (Red phase)

- [x] Task: Implement `parse_coordinate()` [12525f8]
    - [x] Create `cave_sketch/geo/coordinates.py` with `parse_coordinate(value: str) -> float | None`
    - [x] Ensure no Streamlit imports
    - [x] Full type annotations
    - [x] Run tests and confirm they pass (Green phase)

- [x] Task: Conductor - User Manual Verification 'Phase 1: Parse Coordinate Utility' (Protocol in workflow.md) [5556092]

## Phase 2: UI Integration & Validation

- [ ] Task: Replace `number_input` with `text_input` in GPS component
    - [ ] Modify `app/components/gps_points.py` to use `st.text_input` for Latitude and Longitude
    - [ ] Import and use `parse_coordinate()` from `cave_sketch.geo.coordinates`
    - [ ] Store parsed `float` values in `known_points` session state
    - [ ] Default display value for new points: `"0.000000"`

- [ ] Task: Add inline validation feedback
    - [ ] Show inline error (e.g. `st.caption` with red styling or `st.error`) below each field when `parse_coordinate()` returns `None`
    - [ ] Update `validate_known_points()` to reject points with unparseable coordinates

- [ ] Task: Conductor - User Manual Verification 'Phase 2: UI Integration & Validation' (Protocol in workflow.md)
