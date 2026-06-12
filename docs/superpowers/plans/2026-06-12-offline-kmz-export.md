# Offline-ready KMZ Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the satellite map's per-segment KML download with a compact, full-fidelity `.kmz` that loads fast in offline apps (OsmAnd, Locus Map) without freezing.

**Architecture:** A new pure function chains thousands of 2-point survey segments into a handful of long polylines per feature type. The existing `render_to_kml` is upgraded to emit those polylines as one `<MultiGeometry>` placemark per type with shared `<Style>` definitions, plus water polygons and point features. A thin `render_to_kmz` wrapper zips the KML. The satellite page is rewired to produce/download the KMZ, and the obsolete weak KML path is deleted.

**Tech Stack:** Python 3.11+, stdlib `xml.etree.ElementTree`, stdlib `zipfile`, pytest, Streamlit.

---

## File Structure

- **Create:** `cave_sketch/features/chaining.py` — pure segment-chaining logic (no I/O).
- **Create:** `tests/test_chaining.py` — unit tests for chaining.
- **Create:** `tests/test_kmz_export.py` — tests for the upgraded KML renderer + KMZ wrapper.
- **Modify:** `cave_sketch/backend_renders/google_earth.py` — upgrade `render_to_kml`, add `render_to_kmz`.
- **Modify:** `cave_sketch/backend_renders/__init__.py` — export `render_to_kmz`.
- **Modify:** `cave_sketch/satellite_view/map.py` — emit KMZ from all loaded JSON maps; drop the weak KML path.
- **Modify:** `app/pages/2_satellite_map.py` — KMZ download button.
- **Delete:** `cave_sketch/geo/kml.py`, `tests/test_kml.py`, `utility_scripts/test_kml_export.py`.

### Key data shapes (already produced by `export_map_data`)

A cave-map JSON is:
```python
{
  "name": str,
  "center": {"Latitude": float, "Longitude": float},
  "nodes": {node_id: {"lat": float, "lon": float, "type": str}},
  "lines": [{"from": {"lat": float, "lon": float, "id": str},
             "to":   {"lat": float, "lon": float, "id": str},
             "type": str}],
  "water_polygons": [{"coordinates": [[lat, lon], ...], "polygon_id": str}],
}
```

`chain_segments_by_type(lines)` returns `{line_type: [polyline, ...]}` where each
polyline is an ordered `[[lat, lon], ...]`.

---

## Task 1: Segment chaining (pure function)

**Files:**
- Create: `cave_sketch/features/chaining.py`
- Test: `tests/test_chaining.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_chaining.py`:

```python
from cave_sketch.features.chaining import chain_segments_by_type


def _seg(a, b, type_="L_wall"):
    """Build a line dict; node ids double as fake coords (lat=id, lon=0)."""
    return {
        "from": {"id": a, "lat": float(a), "lon": 0.0},
        "to": {"id": b, "lat": float(b), "lon": 0.0},
        "type": type_,
    }


def test_straight_line_becomes_one_polyline():
    lines = [_seg(1, 2), _seg(2, 3), _seg(3, 4)]
    result = chain_segments_by_type(lines)
    assert list(result.keys()) == ["L_wall"]
    polylines = result["L_wall"]
    assert len(polylines) == 1
    lats = [pt[0] for pt in polylines[0]]
    assert lats in ([1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0])


def test_reverse_duplicate_edges_counted_once():
    lines = [_seg(1, 2), _seg(2, 1), _seg(2, 3)]
    result = chain_segments_by_type(lines)
    polylines = result["L_wall"]
    assert len(polylines) == 1
    assert len(polylines[0]) == 3  # nodes 1,2,3 — no duplicate vertex


def test_y_junction_becomes_three_polylines():
    # center node 10 connects to 1, 2, 3
    lines = [_seg(10, 1), _seg(10, 2), _seg(10, 3)]
    result = chain_segments_by_type(lines)
    polylines = result["L_wall"]
    assert len(polylines) == 3
    for poly in polylines:
        assert len(poly) == 2  # each arm: junction + endpoint


def test_closed_loop_becomes_one_closed_polyline():
    lines = [_seg(1, 2), _seg(2, 3), _seg(3, 1)]
    result = chain_segments_by_type(lines)
    polylines = result["L_wall"]
    assert len(polylines) == 1
    poly = polylines[0]
    assert poly[0] == poly[-1]  # closed
    assert len(poly) == 4  # 1,2,3,1


def test_types_grouped_independently():
    lines = [_seg(1, 2, "L_wall"), _seg(3, 4, "A_water")]
    result = chain_segments_by_type(lines)
    assert set(result.keys()) == {"L_wall", "A_water"}
    assert len(result["L_wall"]) == 1
    assert len(result["A_water"]) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chaining.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cave_sketch.features.chaining'`

- [ ] **Step 3: Write the implementation**

Create `cave_sketch/features/chaining.py`:

```python
from collections import defaultdict
from typing import Any, Dict, List

Coord = List[float]


def chain_segments_by_type(
    lines: List[Dict[str, Any]],
) -> Dict[str, List[List[Coord]]]:
    """Chain 2-point survey segments into long polylines, grouped by feature type.

    Each input line is ``{"from": {"id","lat","lon"}, "to": {...}, "type": str}``.
    Reverse-duplicate edges (a->b and b->a) are collapsed. Within a type, segments
    are merged into maximal polylines that split at junctions (degree != 2).

    Returns ``{type: [polyline, ...]}`` where a polyline is ``[[lat, lon], ...]``.
    """
    by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for line in lines:
        by_type[line["type"]].append(line)

    return {line_type: _chain_one_type(segs) for line_type, segs in by_type.items()}


def _chain_one_type(segs: List[Dict[str, Any]]) -> List[List[Coord]]:
    coords: Dict[str, Coord] = {}
    adj: Dict[str, set] = defaultdict(set)
    edges: set = set()  # frozenset({a, b})

    for s in segs:
        a, b = str(s["from"]["id"]), str(s["to"]["id"])
        coords[a] = [s["from"]["lat"], s["from"]["lon"]]
        coords[b] = [s["to"]["lat"], s["to"]["lon"]]
        if a == b:
            continue
        edge = frozenset((a, b))
        if edge in edges:
            continue
        edges.add(edge)
        adj[a].add(b)
        adj[b].add(a)

    visited: set = set()
    polylines: List[List[Coord]] = []

    def walk(start: str, nxt: str) -> List[str]:
        path = [start, nxt]
        visited.add(frozenset((start, nxt)))
        prev, cur = start, nxt
        while len(adj[cur]) == 2 and cur != start:
            nbrs = [n for n in adj[cur] if n != prev]
            if not nbrs:
                break
            nn = nbrs[0]
            edge = frozenset((cur, nn))
            if edge in visited:
                break
            visited.add(edge)
            path.append(nn)
            prev, cur = cur, nn
        return path

    # 1) Chains anchored at endpoints/junctions (degree != 2).
    for node in list(adj.keys()):
        if len(adj[node]) == 2:
            continue
        for nbr in list(adj[node]):
            if frozenset((node, nbr)) in visited:
                continue
            path = walk(node, nbr)
            polylines.append([coords[n] for n in path])

    # 2) Leftover pure cycles (all degree 2).
    for edge in edges:
        if edge in visited:
            continue
        a, b = tuple(edge)
        path = walk(a, b)
        polylines.append([coords[n] for n in path])

    return polylines
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_chaining.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/features/chaining.py tests/test_chaining.py
git commit -m "feat(features): chain survey segments into polylines by type"
```

---

## Task 2: Upgrade `render_to_kml` to compact MultiGeometry output

**Files:**
- Modify: `cave_sketch/backend_renders/google_earth.py`
- Test: `tests/test_kmz_export.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kmz_export.py`:

```python
import xml.etree.ElementTree as ET

from cave_sketch.backend_renders.google_earth import render_to_kml


def _sample_map():
    return {
        "name": "Test Cave",
        "center": {"Latitude": 46.0, "Longitude": 10.0},
        "nodes": {
            "1": {"lat": 46.0, "lon": 10.0, "type": "L_wall"},
            "2": {"lat": 46.001, "lon": 10.0, "type": "L_wall"},
            "3": {"lat": 46.002, "lon": 10.0, "type": "L_wall"},
            "B1": {"lat": 46.0005, "lon": 10.0005, "type": "BLOCK"},
        },
        "lines": [
            {"from": {"id": "1", "lat": 46.0, "lon": 10.0},
             "to": {"id": "2", "lat": 46.001, "lon": 10.0}, "type": "L_wall"},
            {"from": {"id": "2", "lat": 46.001, "lon": 10.0},
             "to": {"id": "3", "lat": 46.002, "lon": 10.0}, "type": "L_wall"},
        ],
        "water_polygons": [
            {"coordinates": [[46.0, 10.0], [46.0, 10.001],
                             [46.001, 10.001], [46.0, 10.0]], "polygon_id": "1"},
        ],
    }


def test_lines_collapse_into_one_multigeometry_per_type():
    kml = render_to_kml([_sample_map()])
    root = ET.fromstring(kml)
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    # Two segments, same type -> exactly ONE MultiGeometry placemark.
    multigeoms = root.findall(".//k:MultiGeometry", ns)
    assert len(multigeoms) == 1
    linestrings = multigeoms[0].findall("k:LineString", ns)
    assert len(linestrings) == 1  # chained into a single polyline


def test_shared_line_style_defined_once_and_referenced():
    kml = render_to_kml([_sample_map()])
    root = ET.fromstring(kml)
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    styles = [s.get("id") for s in root.findall(".//k:Style", ns) if s.get("id")]
    assert "line_L_wall" in styles
    assert styles.count("line_L_wall") == 1
    styleurls = [u.text for u in root.findall(".//k:styleUrl", ns)]
    assert "#line_L_wall" in styleurls


def test_water_polygon_and_point_rendered():
    kml = render_to_kml([_sample_map()])
    root = ET.fromstring(kml)
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    assert len(root.findall(".//k:Polygon", ns)) == 1
    assert len(root.findall(".//k:Point", ns)) == 1  # the BLOCK node


def test_output_is_well_formed_and_small_placemark_count():
    kml = render_to_kml([_sample_map()])
    root = ET.fromstring(kml)  # raises if malformed
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    # 1 line-type placemark + 1 polygon + 1 point = 3, far fewer than segments.
    assert len(root.findall(".//k:Placemark", ns)) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_kmz_export.py -v`
Expected: FAIL — the current `render_to_kml` emits one placemark per segment (no `MultiGeometry`, no `line_L_wall` style, no point from nodes).

- [ ] **Step 3: Rewrite `render_to_kml`**

Replace the entire contents of `cave_sketch/backend_renders/google_earth.py` with:

```python
import xml.etree.ElementTree as ET
from typing import Any, Dict, List
from xml.dom import minidom

from cave_sketch.features.chaining import chain_segments_by_type
from cave_sketch.features.render_features import extract_features_from_json
from cave_sketch.style import STYLE_MAP

_COLOR_MAP = {
    "blue": "ffff0000",
    "red": "ff0000ff",
    "green": "ff00ff00",
    "black": "ff000000",
    "yellow": "ff00ffff",
    "gray": "ff888888",
    "white": "ffffffff",
    "indigo": "ff82004b",
    "deepskyblue": "ffffbf00",
    "aliceblue": "fffff8f0",
    "saddlebrown": "ff13458b",
}


def _kml_color(color: str, opacity: float = 1.0) -> str:
    """Convert a color name + opacity to a KML AABBGGRR color string."""
    base = _COLOR_MAP.get(color.lower(), "ffffffff")
    alpha = int(opacity * 255)
    return f"{alpha:02x}{base[2:]}"


def render_to_kml(map_list: List[Dict[str, Any]], layer_name: str = "All Maps") -> str:
    """Render one or more cave-map JSONs into a compact KML string.

    Line segments are chained into polylines and grouped into a single
    ``<MultiGeometry>`` placemark per feature type with a shared ``<Style>``.
    Water polygons and point-type nodes are emitted as individual placemarks.
    """
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    ET.SubElement(doc, "name").text = layer_name

    defined_styles: set = set()

    def ensure_line_style(line_type: str) -> str:
        style_id = f"line_{line_type}"
        if style_id not in defined_styles:
            spec = STYLE_MAP.get(line_type, {})
            style = ET.SubElement(doc, "Style", id=style_id)
            line_style = ET.SubElement(style, "LineStyle")
            ET.SubElement(line_style, "color").text = _kml_color(spec.get("color", "black"))
            ET.SubElement(line_style, "width").text = str(spec.get("weight", 2))
            defined_styles.add(style_id)
        return style_id

    def ensure_point_style(point_type: str) -> str:
        style_id = f"point_{point_type}"
        if style_id not in defined_styles:
            spec = STYLE_MAP.get(point_type, {})
            style = ET.SubElement(doc, "Style", id=style_id)
            icon_style = ET.SubElement(style, "IconStyle")
            ET.SubElement(icon_style, "color").text = _kml_color(spec.get("color", "black"))
            ET.SubElement(icon_style, "scale").text = str(spec.get("markersize", 4) / 4)
            defined_styles.add(style_id)
        return style_id

    for map_data in map_list:
        folder = ET.SubElement(doc, "Folder")
        ET.SubElement(folder, "name").text = map_data.get("name", "Unnamed Map")

        # --- LINES: chained, one MultiGeometry placemark per type ---
        chained = chain_segments_by_type(map_data.get("lines", []))
        for line_type, polylines in chained.items():
            style_id = ensure_line_style(line_type)
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = line_type
            ET.SubElement(placemark, "styleUrl").text = f"#{style_id}"
            multigeom = ET.SubElement(placemark, "MultiGeometry")
            for polyline in polylines:
                line = ET.SubElement(multigeom, "LineString")
                ET.SubElement(line, "tessellate").text = "1"
                ET.SubElement(line, "coordinates").text = " ".join(
                    f"{lon},{lat},0" for lat, lon in polyline
                )

        # --- POLYGONS (water): individual placemarks (few) ---
        features = extract_features_from_json(map_data)
        for poly in features.get("polygons", []):
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = poly.get("popup", "")
            style = ET.SubElement(placemark, "Style")
            poly_style = ET.SubElement(style, "PolyStyle")
            ET.SubElement(poly_style, "color").text = _kml_color(
                poly.get("fill_color", "blue"), poly.get("fill_opacity", 0.3)
            )
            ET.SubElement(poly_style, "fill").text = "1"
            ET.SubElement(poly_style, "outline").text = "1"
            line_style = ET.SubElement(style, "LineStyle")
            ET.SubElement(line_style, "color").text = _kml_color(
                poly.get("edge_color", poly.get("fill_color", "blue")), 1.0
            )
            ET.SubElement(line_style, "width").text = "1"
            polygon = ET.SubElement(placemark, "Polygon")
            outer = ET.SubElement(polygon, "outerBoundaryIs")
            ring = ET.SubElement(outer, "LinearRing")
            ET.SubElement(ring, "coordinates").text = " ".join(
                f"{lon},{lat}" for lat, lon in poly["coords"]
            )

        # --- POINTS: point-type nodes as individual placemarks (few) ---
        for node_id, node in map_data.get("nodes", {}).items():
            spec = STYLE_MAP.get(node.get("type", ""), {})
            if spec.get("type") != "point":
                continue
            style_id = ensure_point_style(node["type"])
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = f"{node['type']} ({node_id})"
            ET.SubElement(placemark, "styleUrl").text = f"#{style_id}"
            point = ET.SubElement(placemark, "Point")
            ET.SubElement(point, "coordinates").text = f"{node['lon']},{node['lat']},0"

    rough_string = ET.tostring(kml, "utf-8")
    return minidom.parseString(rough_string).toprettyxml(indent="  ")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_kmz_export.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/backend_renders/google_earth.py tests/test_kmz_export.py
git commit -m "feat(kml): emit compact MultiGeometry KML with shared styles and points"
```

---

## Task 3: Add `render_to_kmz` wrapper

**Files:**
- Modify: `cave_sketch/backend_renders/google_earth.py`
- Modify: `cave_sketch/backend_renders/__init__.py`
- Test: `tests/test_kmz_export.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_kmz_export.py`:

```python
import zipfile

from cave_sketch.backend_renders.google_earth import render_to_kmz


def test_render_to_kmz_writes_zip_with_doc_kml(tmp_path):
    out = tmp_path / "cave.kmz"
    returned = render_to_kmz([_sample_map()], str(out))
    assert returned == str(out)
    assert out.exists()
    with zipfile.ZipFile(out) as zf:
        assert "doc.kml" in zf.namelist()
        content = zf.read("doc.kml").decode("utf-8")
    assert "<kml" in content
    assert "MultiGeometry" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_kmz_export.py::test_render_to_kmz_writes_zip_with_doc_kml -v`
Expected: FAIL — `ImportError: cannot import name 'render_to_kmz'`

- [ ] **Step 3: Add the implementation**

Add to the top imports of `cave_sketch/backend_renders/google_earth.py` (alongside the existing imports):

```python
import zipfile
```

Append this function to the end of `cave_sketch/backend_renders/google_earth.py`:

```python
def render_to_kmz(
    map_list: List[Dict[str, Any]], output_path: str, layer_name: str = "All Maps"
) -> str:
    """Render cave-map JSONs to a compressed ``.kmz`` (a zip containing doc.kml).

    Returns the output path.
    """
    kml_str = render_to_kml(map_list, layer_name=layer_name)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_str)
    return output_path
```

Update `cave_sketch/backend_renders/__init__.py` to:

```python
from .folium import render_to_folium as render_to_folium
from .google_earth import render_to_kml as render_to_kml
from .google_earth import render_to_kmz as render_to_kmz
from .matplotlib import render_to_matplotlib as render_to_matplotlib
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_kmz_export.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/backend_renders/google_earth.py cave_sketch/backend_renders/__init__.py tests/test_kmz_export.py
git commit -m "feat(kml): add render_to_kmz zip wrapper"
```

---

## Task 4: Rewire `draw_map` to export KMZ and drop the weak KML path

**Files:**
- Modify: `cave_sketch/satellite_view/map.py`
- Test: `tests/test_satellite_map.py` (verify still passes)

- [ ] **Step 1: Replace imports**

In `cave_sketch/satellite_view/map.py`, replace these lines (near the top):

```python
from cave_sketch.backend_renders import render_to_folium
from cave_sketch.dxf.models import CaveSurvey, SurveyLine
from cave_sketch.features.geometry import rotate_points
from cave_sketch.features.render_features import extract_features_from_json
from cave_sketch.geo.kml import export_kml
from cave_sketch.geo.models import GeoPoint
```

with:

```python
from cave_sketch.backend_renders import render_to_folium, render_to_kmz
from cave_sketch.features.geometry import rotate_points
from cave_sketch.features.render_features import extract_features_from_json
```

- [ ] **Step 2: Replace the KML export block inside `draw_map`**

In `draw_map`, replace this block:

```python
    # Export current map as JSON (different path to avoid conflicts)
    json_output_path = output_path.replace(".html", ".json")
    json_path = export_map_data(map_df, map_name, json_output_path)

    # Export KML
    kml_output_path = output_path.replace(".html", ".kml")
    kml_path = _export_to_kml(map_df, map_name, kml_output_path)

    # Prepare list of all JSON maps to combine
    json_maps_to_combine = [json_path]
    if additional_json_maps:
        json_maps_to_combine.extend(additional_json_maps)

    # Create HTML map; only rotate the first JSON (the current one)
    html_map = create_html_map(
        json_maps_to_combine,
        output_path,
    )

    return html_map, json_path, kml_path
```

with:

```python
    # Export current map as JSON (different path to avoid conflicts)
    json_output_path = output_path.replace(".html", ".json")
    json_path = export_map_data(map_df, map_name, json_output_path)

    # Prepare list of all JSON maps to combine
    json_maps_to_combine = [json_path]
    if additional_json_maps:
        json_maps_to_combine.extend(additional_json_maps)

    # Export KMZ (offline artifact) from all combined maps
    kmz_output_path = output_path.replace(".html", ".kmz")
    combined_data = []
    for path in json_maps_to_combine:
        with open(path, "r", encoding="utf-8") as f:
            combined_data.append(json.load(f))
    kmz_path = render_to_kmz(combined_data, kmz_output_path, layer_name=map_name)

    # Create HTML map; only rotate the first JSON (the current one)
    html_map = create_html_map(
        json_maps_to_combine,
        output_path,
    )

    return html_map, json_path, kmz_path
```

- [ ] **Step 3: Delete the obsolete `_export_to_kml` helper**

In `cave_sketch/satellite_view/map.py`, delete the entire `_export_to_kml` function (the block starting `def _export_to_kml(df: pd.DataFrame, map_name: str, output_path: str) -> str:` through its closing `return output_path`).

- [ ] **Step 4: Run satellite map tests to verify nothing broke**

Run: `uv run pytest tests/test_satellite_map.py -v`
Expected: PASS. If any test referenced `_export_to_kml` or a `.kml` return value, update it to call/inspect the KMZ path instead (the third return value is now a `.kmz` file path).

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/satellite_view/map.py tests/test_satellite_map.py
git commit -m "feat(satellite): export combined KMZ instead of per-segment KML"
```

---

## Task 5: Update the satellite map page download button

**Files:**
- Modify: `app/pages/2_satellite_map.py`

- [ ] **Step 1: Update the draw_map call and session key**

In `app/pages/2_satellite_map.py`, replace:

```python
        html_map, json_path, kml_path = draw_map(
            map_path=str(st.session_state.merged_map_csv or st.session_state.map_csv),
            gps_points=st.session_state.known_points,
            output_path=str(html_path),
            map_name="Current Cave",
            additional_json_maps=st.session_state.uploaded_json_paths,
            rotation_angle=rotation_angle,
        )
        st.session_state.current_json_path = json_path
        st.session_state.html_path = html_path
        st.session_state.kml_path = kml_path
```

with:

```python
        html_map, json_path, kmz_path = draw_map(
            map_path=str(st.session_state.merged_map_csv or st.session_state.map_csv),
            gps_points=st.session_state.known_points,
            output_path=str(html_path),
            map_name="Current Cave",
            additional_json_maps=st.session_state.uploaded_json_paths,
            rotation_angle=rotation_angle,
        )
        st.session_state.current_json_path = json_path
        st.session_state.html_path = html_path
        st.session_state.kmz_path = kmz_path
```

- [ ] **Step 2: Update the download button**

In the same file, replace:

```python
    with open(st.session_state.kml_path, "rb") as kml_f_bin:
        col3.download_button(
            "📥 Download KML Map", kml_f_bin, file_name=f"{sanitized_name}.kml"
        )
```

with:

```python
    with open(st.session_state.kmz_path, "rb") as kmz_f_bin:
        col3.download_button(
            "📥 Download KMZ Map", kmz_f_bin, file_name=f"{sanitized_name}.kmz"
        )
```

- [ ] **Step 3: Verify the app imports cleanly**

Run: `uv run python -c "import ast; ast.parse(open('app/pages/2_satellite_map.py').read()); print('ok')"`
Expected: prints `ok`

- [ ] **Step 4: Commit**

```bash
git add app/pages/2_satellite_map.py
git commit -m "feat(ui): replace KML download with KMZ on satellite map page"
```

---

## Task 6: Remove the obsolete weak KML path

**Files:**
- Delete: `cave_sketch/geo/kml.py`
- Delete: `tests/test_kml.py`
- Delete: `utility_scripts/test_kml_export.py`

- [ ] **Step 1: Confirm nothing still imports the weak exporter**

Run: `grep -rn "geo.kml\|geo\.kml import\|export_kml" --include="*.py" . | grep -v "/.venv/"`
Expected: only matches inside the three files about to be deleted. If any *other* file matches, stop and fix that reference first.

- [ ] **Step 2: Delete the files**

```bash
git rm cave_sketch/geo/kml.py tests/test_kml.py utility_scripts/test_kml_export.py
```

- [ ] **Step 3: Run the full test suite**

Run: `uv run pytest -q`
Expected: all tests pass, no import errors, no reference to the deleted module.

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: remove obsolete per-segment KML exporter"
```

---

## Task 7: Full verification

- [ ] **Step 1: Lint, type-check, and full test suite**

Run:
```bash
uv run ruff check cave_sketch app tests
uv run mypy cave_sketch
uv run pytest -q
```
Expected: ruff clean, mypy clean (project is `strict = false`), all tests pass.

- [ ] **Step 2: Regenerate the problem file and confirm placemark collapse**

Confirm the placemark explosion is gone, end to end:

1. Start the app: `uv run streamlit run app/app.py`
2. Reproduce the original case: load the same survey that previously produced
   `un_altro_buco_nell_acqua.kml`, go to the Satellite Map page, generate, and click
   **📥 Download KMZ Map**.
3. Inspect the downloaded file (it is a zip):
   ```bash
   unzip -p ~/Downloads/un_altro_buco_nell_acqua.kmz doc.kml | grep -c '<Placemark'
   ```
   Expected: a small number (single/double digits), not thousands. Compare against the
   old file for the record:
   ```bash
   grep -c '<Placemark' ./un_altro_buco_nell_acqua.kml   # the old artifact: ~6211
   ```

- [ ] **Step 3: Field verification (manual, the real proof)**

- Load the generated `.kmz` into **Locus Map**: confirm it opens quickly (no freeze) and
  shows walls, water areas (filled), and point features.
- Load the same `.kmz` into **OsmAnd**: confirm it opens quickly and shows lines + points.
  (Per the spec, water polygons may render as outlines rather than filled in OsmAnd — this
  is the accepted baseline.)
- Record the outcome in `DEVLOG.md`.

---

## Notes / accepted limitations

- **Dash patterns** (e.g. `L_chimney`, `L_pit`) are not represented — standard KML
  `LineStyle` has no dash attribute, so those lines render solid. The old exporter
  ignored them too. Out of scope.
- **OsmAnd polygon fidelity:** water areas may show as outlines, not filled, in OsmAnd.
  Locus renders them filled. Accepted baseline.
- **Streamlit offline load** was not empirically confirmed; KMZ *generation* itself makes
  zero network calls.
