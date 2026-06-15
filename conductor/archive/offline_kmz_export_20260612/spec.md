# Spec: Offline-ready KMZ Export

## Overview
The satellite-map page produces three artifacts: an interactive HTML map (folium), a KML file, and a CaveSketch-internal JSON. The goal is to deliver an artifact that loads a cave map into common **offline** map apps — specifically **OsmAnd** and **Locus Map** — without requiring an internet connection and without freezing the app.

Two findings from brainstorming reframed the work:

1. **"Offline" is about the artifact, not the basemap.** The cave drawing is just vector geometry with real lat/lon. The satellite *imagery* underneath is the map app's responsibility (OsmAnd/Locus carry their own offline maps / cached tiles). We only deliver the cave vectors in a format those apps read natively. Bundling satellite imagery is **out of scope** (weight + legal grey area of redistributing Google tiles).

2. **The current KML already loads offline — but freezes Locus.** The real blocker is a performance bug, not the format.

### Root cause of the Locus freeze
The downloaded KML (e.g. `un_altro_buco_nell_acqua.kml`) is **~1.9 MB with ~6,211 `<Placemark>` elements**, each holding a trivial **2-point** `<LineString>` (one survey segment), and roughly **half are reverse duplicates** (`3→2` and `2→3` are the same edge emitted twice). Locus instantiates one interactive map object per placemark → ~6,211 objects → UI freeze. Google Earth (desktop GPU renderer) batches geometry and is unaffected. Neither KMZ nor the existing `render_to_kml` fixes this — both emit one placemark per segment.

## Functional Requirements

### FR-1: Segment Chaining
- A pure function chains 2-point survey segments into long polylines, grouped by feature type.
- Reverse-duplicate edges (`a→b` and `b→a`) are collapsed to a single edge.
- Within a type, segments merge into maximal polylines that split at junctions (graph degree ≠ 2); pure cycles become closed polylines.
- Result: thousands of segments collapse into a handful of polylines (~6,211 placemarks → ~5–7).

### FR-2: Compact KML Output
- One shared `<Style id="...">` per feature type, referenced via `<styleUrl>` (no inline `<Style>` per placemark).
- One `<Placemark>` containing a `<MultiGeometry>` per line type, holding all chained polylines of that type.
- Water polygons rendered as individual `<Polygon>` placemarks (few; no explosion risk).
- Point-type nodes (`BLOCK`, `B_ice`, `B_snow`) rendered as individual `<Point>` placemarks.

### FR-3: KMZ Packaging
- A thin wrapper zips the KML string into a `.kmz` (a zip archive containing `doc.kml`) using stdlib `zipfile`.

### FR-4: Satellite Pipeline Integration
- `draw_map` produces the KMZ from **all** loaded JSON maps (matching the HTML map's combine behavior), not just the current one.
- KMZ generation makes **zero network calls**.

### FR-5: UI
- The satellite-map page's third download button becomes **"📥 Download KMZ Map"**, producing `{sanitized_name}.kmz`.

### FR-6: Remove the Obsolete Weak KML Path
- Delete `cave_sketch/geo/kml.py` (`export_kml`), `tests/test_kml.py`, and `utility_scripts/test_kml_export.py`.
- `cave_sketch/geo/models.py` (GeoPoint) and `cave_sketch/geo/georef.py` are independent and remain.

## Acceptance Criteria
1. `chain_segments_by_type` correctly handles straight lines, Y-junctions, closed loops, reverse-duplicate edges, and per-type grouping.
2. The generated KML contains one MultiGeometry placemark per line type with a single shared style each.
3. Water polygons and point-type nodes render in the KML.
4. A regenerated KMZ for the previously-problematic survey reports a small placemark count (single/double digits), not thousands.
5. The satellite-map page downloads a `.kmz` built from all loaded JSON maps.
6. The weak KML exporter and its tests/script are removed; the full test suite passes.
7. Field check: the `.kmz` opens quickly (no freeze) in both Locus and OsmAnd; Locus shows full fidelity (walls, filled water, points); OsmAnd shows lines + points.

## Out of Scope
- Bundling satellite imagery / offline raster tiles (`.mbtiles`/`.sqlitedb`).
- GPX export.
- Douglas–Peucker vertex thinning (object count, not vertex count, was the problem).
- Dash patterns for lines (standard KML `LineStyle` has no dash attribute; lines render solid).

## Accepted Limitations
- **OsmAnd polygon fidelity:** water areas may render as outlines rather than filled in OsmAnd; Locus renders them filled. Accepted baseline.
- **Streamlit offline load** was not empirically confirmed; KMZ *generation* itself makes zero network calls.
