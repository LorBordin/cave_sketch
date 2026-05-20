# Implementation Plan: KML Export for Google Earth

## Phase 1: Core KML Logic [checkpoint: d5a8792]
- [x] Task: Research KML structure and coordinate mapping for cave centerlines. d803e6b
- [x] Task: Implement KML generation logic in `cave_sketch/geo/kml.py`. 1a7df45
    - [x] Create base KML template.
    - [x] Implement coordinate transformation from affine georef to KML points.
- [x] Task: Add unit tests for KML generation in `tests/test_kml.py`. 1a7df45
- [x] Task: Conductor - User Manual Verification 'Phase 1: Core KML Logic' (Protocol in workflow.md) d5a8792

## Phase 2: UI Integration [checkpoint: 72e2833]
- [x] Task: Integrate KML export into the Streamlit app. 8a0903e
    - [x] Add export button to `app/pages/2_satellite_map.py`.
    - [x] Implement the download handler in `app/components/file_upload.py` or similar.
- [x] Task: Manual verification of the generated KML in a viewer (e.g., Google Earth Web). 8a0903e
- [x] Task: Conductor - User Manual Verification 'Phase 2: UI Integration' (Protocol in workflow.md) 72e2833

## Phase 3: Cleanup and Documentation [checkpoint: c42c12a]
- [x] Task: Run `uv run ruff check . --fix` and `uv run mypy cave_sketch/`. 4a19768
- [x] Task: Update `README.md` and `DEVLOG.md` with the new feature details. c42c12a
- [x] Task: Conductor - User Manual Verification 'Phase 3: Cleanup and Documentation' (Protocol in workflow.md) c42c12a
