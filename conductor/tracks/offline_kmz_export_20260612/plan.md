# Implementation Plan: Offline-ready KMZ Export

**Goal:** Replace the satellite map's per-segment KML download with a compact, full-fidelity `.kmz` that loads fast in offline apps (OsmAnd, Locus Map) without freezing.

**Architecture:** A new pure function chains thousands of 2-point survey segments into a handful of long polylines per feature type. `render_to_kml` is upgraded to emit those polylines as one `<MultiGeometry>` placemark per type with shared `<Style>` definitions, plus water polygons and point nodes. A thin `render_to_kmz` wrapper zips the KML. The satellite page is rewired to produce/download the KMZ, and the obsolete weak KML path is deleted.

**Tech Stack:** Python 3.11+, stdlib `xml.etree.ElementTree`, stdlib `zipfile`, pytest, Streamlit. Run tests with `uv run pytest`.

---

## Phase 1: Segment Chaining [checkpoint: 105f546]

- [x] Task: Write tests for `chain_segments_by_type` [9591501]
    - [ ] Create `tests/test_chaining.py`
    - [ ] Straight line of N nodes → 1 polyline with N vertices
    - [ ] Reverse-duplicate edges (`a→b` and `b→a`) → counted once (no duplicate vertex)
    - [ ] Y-junction (center node to 3 endpoints) → 3 polylines
    - [ ] Closed loop → 1 closed polyline (first vertex == last)
    - [ ] Mixed types → grouped independently per type
    - [ ] Run `uv run pytest tests/test_chaining.py -v` and confirm they FAIL (module missing)
- [x] Task: Implement `chain_segments_by_type` in `cave_sketch/features/chaining.py` [9591501]
    - [ ] Create new pure module (no I/O), sibling to `features/geometry.py`
    - [ ] Signature: `chain_segments_by_type(lines) -> {type: [polyline,...]}` where a polyline is `[[lat, lon], ...]`
    - [ ] Input line shape: `{"from": {"id","lat","lon"}, "to": {"id","lat","lon"}, "type": str}`
    - [ ] Group by type; per type build an undirected graph, dedupe edges via `frozenset({from_id,to_id})`
    - [ ] Walk maximal chains starting at endpoints/junctions (degree ≠ 2) through degree-2 nodes
    - [ ] Emit leftover all-degree-2 components as closed polylines
    - [ ] Run `uv run pytest tests/test_chaining.py -v` and confirm PASS
    - [ ] Commit: `feat(features): chain survey segments into polylines by type`
- [x] Task: Conductor - User Manual Verification 'Phase 1: Segment Chaining' (Protocol in workflow.md) [105f546]

## Phase 2: Compact KML + KMZ Export [checkpoint: 07de82b]

- [x] Task: Write tests for the upgraded `render_to_kml` [affa383]
    - [ ] Create `tests/test_kmz_export.py` with a sample map JSON (lines of one type + a water polygon + a BLOCK point node)
    - [ ] Two same-type segments → exactly ONE `<MultiGeometry>` placemark containing one chained `<LineString>`
    - [ ] Shared `<Style id="line_L_wall">` defined once and referenced via `<styleUrl>#line_L_wall`
    - [ ] Water polygon → one `<Polygon>`; BLOCK node → one `<Point>`
    - [ ] Output is well-formed XML and total placemark count ≪ segment count
    - [ ] Run and confirm FAIL (current renderer is per-segment)
- [x] Task: Rewrite `render_to_kml` in `cave_sketch/backend_renders/google_earth.py` [affa383]
    - [ ] Lines: call `chain_segments_by_type(map_data["lines"])`; emit one MultiGeometry placemark per type with shared `<Style id="line_{type}">` (color/weight from `STYLE_MAP`)
    - [ ] Polygons: reuse `extract_features_from_json` water polygons as individual placemarks (existing inline-style logic)
    - [ ] Points: iterate `map_data["nodes"]`; for nodes whose `STYLE_MAP[type]["type"] == "point"`, emit `<Point>` placemarks with shared `<Style id="point_{type}">`
    - [ ] Extend the color map to cover all `STYLE_MAP` colors (indigo, deepskyblue, aliceblue, saddlebrown)
    - [ ] Run `uv run pytest tests/test_kmz_export.py -v` and confirm PASS
    - [ ] Commit: `feat(kml): emit compact MultiGeometry KML with shared styles and points`
- [x] Task: Add `render_to_kmz` wrapper [affa383]
    - [ ] Add failing test: `render_to_kmz(map_list, output_path)` writes a zip containing `doc.kml` with `<kml`/`MultiGeometry` content
    - [ ] Implement `render_to_kmz` in `google_earth.py` using `zipfile.ZipFile(..., ZIP_DEFLATED)` writing `doc.kml`; returns the output path
    - [ ] Export it from `cave_sketch/backend_renders/__init__.py`
    - [ ] Run `uv run pytest tests/test_kmz_export.py -v` and confirm PASS
    - [ ] Commit: `feat(kml): add render_to_kmz zip wrapper`
- [x] Task: Conductor - User Manual Verification 'Phase 2: Compact KML + KMZ Export' (Protocol in workflow.md) [07de82b]

## Phase 3: Satellite Pipeline & UI Integration [checkpoint: 726c9a9]

- [x] Task: Rewire `draw_map` to export KMZ [feb5ad1]
    - [ ] In `cave_sketch/satellite_view/map.py`, replace the `geo.kml`/`GeoPoint`/`CaveSurvey`/`SurveyLine` imports with `from cave_sketch.backend_renders import render_to_folium, render_to_kmz`
    - [ ] Build `json_maps_to_combine` (current + additional) BEFORE the KMZ export
    - [ ] Load each combined JSON and call `render_to_kmz(combined_data, output_path.replace(".html",".kmz"), layer_name=map_name)`
    - [ ] Return `(html_map, json_path, kmz_path)` (third value is now `.kmz`)
    - [ ] Delete the obsolete `_export_to_kml` helper function
    - [ ] Run `uv run pytest tests/test_satellite_map.py -v`; update any test referencing `_export_to_kml`/`.kml`
    - [ ] Commit: `feat(satellite): export combined KMZ instead of per-segment KML`
- [x] Task: Update the satellite-map page download button [5ce58bf]
    - [ ] In `app/pages/2_satellite_map.py`, rename the unpacked `kml_path` → `kmz_path` and the session key to `st.session_state.kmz_path`
    - [ ] Change the button to `"📥 Download KMZ Map"` with `file_name=f"{sanitized_name}.kmz"`
    - [ ] Confirm the file parses: `uv run python -c "import ast; ast.parse(open('app/pages/2_satellite_map.py').read()); print('ok')"`
    - [ ] Commit: `feat(ui): replace KML download with KMZ on satellite map page`
- [x] Task: Conductor - User Manual Verification 'Phase 3: Satellite Pipeline & UI Integration' (Protocol in workflow.md) [726c9a9]

## Phase 4: Cleanup & Verification

- [ ] Task: Remove the obsolete weak KML path
    - [ ] Confirm no remaining importers: `grep -rn "geo.kml\|export_kml" --include="*.py" . | grep -v "/.venv/"` (only the files about to be deleted)
    - [ ] `git rm cave_sketch/geo/kml.py tests/test_kml.py utility_scripts/test_kml_export.py`
    - [ ] Run `uv run pytest -q` and confirm all pass with no import errors
    - [ ] Commit: `chore: remove obsolete per-segment KML exporter`
- [ ] Task: Full verification
    - [ ] `uv run ruff check cave_sketch app tests` → clean
    - [ ] `uv run mypy cave_sketch` → clean (project is `strict = false`)
    - [ ] `uv run pytest -q` → all pass
    - [ ] Regenerate the previously-problematic survey's KMZ in the app, then `unzip -p <file>.kmz doc.kml | grep -c '<Placemark'` → small number (not thousands)
    - [ ] Field test: load the `.kmz` in Locus (fast, full fidelity incl. filled water + points) and OsmAnd (fast, lines + points; water may be outline-only — accepted)
    - [ ] Record outcome in `DEVLOG.md`
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Cleanup & Verification' (Protocol in workflow.md)
