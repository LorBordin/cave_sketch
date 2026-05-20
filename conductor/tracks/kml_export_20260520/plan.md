# Implementation Plan: KML Export for Google Earth

## Phase 1: Core KML Logic [checkpoint: d5a8792]
- [x] Task: Research KML structure and coordinate mapping for cave centerlines. d803e6b
- [x] Task: Implement KML generation logic in `cave_sketch/geo/kml.py`. 1a7df45
    - [x] Create base KML template.
    - [x] Implement coordinate transformation from affine georef to KML points.
- [x] Task: Add unit tests for KML generation in `tests/test_kml.py`. 1a7df45
- [x] Task: Conductor - User Manual Verification 'Phase 1: Core KML Logic' (Protocol in workflow.md) d5a8792

## Phase 2: UI Integration
- [ ] Task: Integrate KML export into the Streamlit app.
    - [ ] Add export button to `app/pages/2_satellite_map.py`.
    - [ ] Implement the download handler in `app/components/file_upload.py` or similar.
- [ ] Task: Manual verification of the generated KML in a viewer (e.g., Google Earth Web).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: UI Integration' (Protocol in workflow.md)

## Phase 3: Cleanup and Documentation
- [ ] Task: Run `uv run ruff check . --fix` and `uv run mypy cave_sketch/`.
- [ ] Task: Update `README.md` and `DEVLOG.md` with the new feature details.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Cleanup and Documentation' (Protocol in workflow.md)
