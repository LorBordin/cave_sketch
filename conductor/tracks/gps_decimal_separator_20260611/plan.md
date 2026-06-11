# Plan: GPS Coordinate Decimal Separator Fix

## Phase 1: Parse Coordinate Utility

- [ ] Task: Write tests for `parse_coordinate()`
    - [ ] Create `tests/test_parse_coordinate.py`
    - [ ] Test dot decimal input (e.g. `"45.678901"` → `45.678901`)
    - [ ] Test comma decimal input (e.g. `"45,678901"` → `45.678901`)
    - [ ] Test negative coordinate with dot (e.g. `"-7.654321"` → `-7.654321`)
    - [ ] Test negative coordinate with comma (e.g. `"-7,654321"` → `-7.654321`)
    - [ ] Test integer input (e.g. `"45"` → `45.0`)
    - [ ] Test input with leading/trailing whitespace
    - [ ] Test empty string returns `None`
    - [ ] Test whitespace-only input returns `None`
    - [ ] Test letters input returns `None` (e.g. `"abc"`)
    - [ ] Test multiple dots returns `None` (e.g. `"45.67.89"`)
    - [ ] Test multiple commas returns `None` (e.g. `"45,67,89"`)
    - [ ] Run tests and confirm they fail (Red phase)

- [ ] Task: Implement `parse_coordinate()`
    - [ ] Create `cave_sketch/geo/coordinates.py` with `parse_coordinate(value: str) -> float | None`
    - [ ] Ensure no Streamlit imports
    - [ ] Full type annotations
    - [ ] Run tests and confirm they pass (Green phase)

- [ ] Task: Conductor - User Manual Verification 'Phase 1: Parse Coordinate Utility' (Protocol in workflow.md)

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
