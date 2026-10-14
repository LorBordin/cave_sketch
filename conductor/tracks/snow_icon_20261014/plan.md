# Plan

## Phase 1: Snow icon
- [ ] Task: Write failing tests
    - [ ] Test `snow` icon strokes generation (6 arms, sized in meters)
    - [ ] Update `tests/test_kmz_export.py` to expect B_snow icon LineStrings; keep B_ice suppressed
    - [ ] Update `tests/test_style.py` for B_snow as icon
- [ ] Task: Implement
    - [ ] Add `snow` icon strokes in `cave_sketch/features/render_features.py`
    - [ ] Update `B_snow` in `cave_sketch/style.py`
    - [ ] Remove B_snow from the KMZ point suppression in `google_earth.py`; verify matplotlib/folium rendering and legibility of white
- [ ] Task: Verify (ruff, mypy, pytest), append DEVLOG.md entry
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Snow icon' (Protocol in workflow.md)
