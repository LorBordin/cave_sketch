# Plan

## Phase 1: Snow icon [checkpoint: 981b59f]
- [x] Task: Write failing tests [3567305]
    - [x] Test `snow` icon strokes generation (6 arms, sized in meters)
    - [x] Update `tests/test_kmz_export.py` to expect B_snow icon LineStrings; keep B_ice suppressed
    - [x] Update `tests/test_style.py` for B_snow as icon
- [x] Task: Implement [d6c3e42]
    - [x] Add `snow` icon strokes in `cave_sketch/features/render_features.py`
    - [x] Update `B_snow` in `cave_sketch/style.py`
    - [x] Remove B_snow from the KMZ point suppression in `google_earth.py`; verify matplotlib/folium rendering and legibility of white
- [x] Task: Verify (ruff, mypy, pytest), append DEVLOG.md entry [dfe9ace]
- [x] Task: Conductor - User Manual Verification 'Phase 1: Snow icon' (Protocol in workflow.md)
