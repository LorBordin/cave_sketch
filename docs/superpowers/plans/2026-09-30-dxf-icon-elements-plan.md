# DXF Icon Elements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render `L_water-flow`, `B_water-flow`, `B_continuation`, `B_entrance` (currently invisible) and fix `B_blocks` (currently dropped) as real TopoDroid-style vector icons, identically across the matplotlib survey plot, the Folium satellite HTML view, and the KML/KMZ Google Earth export — on both the webapp and the Android app, which share one backend package.

**Architecture:** One vector shape definition per icon (`cave_sketch/style_icons.py`), consumed by three renderers: a matplotlib custom marker `Path`, an inline SVG string for Folium, and a pre-rasterized PNG bundled into KMZ exports. `STYLE_MAP` gains a new `"icon"` point type and an optional `"line_decoration"` key on line types; two shared helpers in `render_features.py` (segment canonicalization + compass bearing) let both feature-extraction functions emit one rotated decoration marker per line segment without duplicate/opposing arrows.

**Tech Stack:** Python, matplotlib (`Path`, `PathPatch`, `MarkerStyle`, `Affine2D`), Folium (`DivIcon`), `ezdxf`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-30-dxf-icon-elements-design.md`

## Global Constraints

- Icon PNG assets must live under `cave_sketch/assets/icons/` (inside the package tree), never at the repo root — only `cave_sketch/` is visible through the Android Chaquopy symlink (`android/app/src/main/python/cave_sketch -> ../../../../../cave_sketch`).
- Any code that locates icon assets must resolve the path via `Path(__file__).resolve().parent / "assets" / "icons"` (relative to the installed package) — never a repo-root-relative or CWD-relative path, since Android ships only the packaged `cave_sketch` subtree.
- `L_water-flow` gets exactly one chevron decoration per DXF polyline segment — not a continuously repeating pattern (rejected alternative, see spec Decisions table).
- `B_ice` / `B_snow` stay on the existing plain-marker / color-tinted-pushpin path — no icon shapes were provided for them; do not touch their `STYLE_MAP` entries or rendering branches.
- Icon colors are exactly as given in the spec's Icon Shape Definitions table (`tan`, `firebrick`, `mediumpurple`, `steelblue`) — approximated from screenshots, not to be re-derived or second-guessed during implementation.
- No new runtime dependencies — matplotlib, folium, and ezdxf are already present in both the webapp's environment and `android/app/build.gradle`'s Chaquopy `pip` block.

## Review Focus

- A single-segment (2-point) `L_water-flow` polyline must produce exactly one decoration, not zero (an off-by-one in the dedup logic) or two (both directions surviving the dedup). Test added in Task 5.
- `extract_features_from_json` called with a `map_data` dict that has no `"nodes"` key at all (not merely an empty one) must return an empty points list, not raise `KeyError`. Test added in Task 6.
- A line-decoration segment whose neighbor node ID isn't present in the coordinate index (the same "dangling link" case already tolerated for plain lines) must be skipped silently, not crash the whole extraction. Test added in Task 5.
- Every color referenced by an `"icon"`-type `STYLE_MAP` entry or by a `style_icons.ICONS` definition must be a real, renderable color name — a typo would silently render invisible/black in a browser with no error surfaced anywhere. Test added in Task 3.
- Two independent `L_water-flow` polylines in the same survey (different DXF polyline groups, so overlapping local vertex indices like both containing a "`P0`"/"`P1`" pair) must each get their own decoration and must not cross-contaminate through the shared dedup set. Test added in Task 5.

---

## Task 1: Vector icon shape definitions

**Files:**
- Create: `cave_sketch/style_icons.py`
- Test: `tests/test_style_icons.py`

**Interfaces:**
- Produces: `ICONS: Dict[str, IconDef]` (icon names: `"block"`, `"entrance"`, `"continuation"`, `"water_flow_point"`, `"water_flow_chevron"`); `icon_to_matplotlib_path(name: str) -> matplotlib.path.Path`; `icon_to_svg_path_d(name: str, viewbox_size: float = 32.0) -> str`. Both functions raise `KeyError` for an unknown `name`. Both produce shapes centered at `(0, 0)` with their larger bounding-box dimension normalized to `1.0` (matplotlib) or `viewbox_size` (SVG).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_style_icons.py`:

```python
import pytest
from matplotlib.path import Path as MplPath

from cave_sketch.style_icons import ICONS, icon_to_matplotlib_path, icon_to_svg_path_d


@pytest.mark.parametrize("name", list(ICONS.keys()))
def test_icon_to_matplotlib_path_is_centered_and_bounded(name):
    path = icon_to_matplotlib_path(name)
    assert isinstance(path, MplPath)
    xs = [v[0] for v in path.vertices]
    ys = [v[1] for v in path.vertices]
    assert max(abs(x) for x in xs) <= 0.51
    assert max(abs(y) for y in ys) <= 0.51


@pytest.mark.parametrize("name", list(ICONS.keys()))
def test_icon_to_matplotlib_path_move_and_close_counts(name):
    path = icon_to_matplotlib_path(name)
    icon = ICONS[name]
    move_count = sum(1 for c in path.codes if c == MplPath.MOVETO)
    close_count = sum(1 for c in path.codes if c == MplPath.CLOSEPOLY)
    assert move_count == len(icon.subpaths)
    assert close_count == sum(1 for sub in icon.subpaths if sub.closed)


@pytest.mark.parametrize("name", list(ICONS.keys()))
def test_icon_to_svg_path_d_has_expected_commands(name):
    d = icon_to_svg_path_d(name, viewbox_size=32.0)
    icon = ICONS[name]
    assert d.count("M ") == len(icon.subpaths)
    assert d.count("Z") == sum(1 for sub in icon.subpaths if sub.closed)


def test_unknown_icon_name_raises_key_error():
    with pytest.raises(KeyError):
        icon_to_matplotlib_path("does_not_exist")
    with pytest.raises(KeyError):
        icon_to_svg_path_d("does_not_exist")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_style_icons.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cave_sketch.style_icons'`

- [ ] **Step 3: Implement `cave_sketch/style_icons.py`**

```python
"""Vector definitions for TopoDroid-style point/line icons.

Each icon is defined once, in an arbitrary local unit coordinate space
(vertices are re-centered and re-scaled by the helpers below, so the raw
coordinates below don't need to be pre-centered), and consumed by three
renderers: matplotlib custom markers (survey plot), inline SVG (Folium
satellite HTML), and rasterized PNGs (KML/KMZ, generated offline by
scripts/generate_icon_assets.py). Traced by eye from icon_samples/*.jpg.
"""
from typing import Dict, List, Tuple

from matplotlib.path import Path as MplPath

Vertex = Tuple[float, float]


class SubPath:
    __slots__ = ("vertices", "closed")

    def __init__(self, vertices: List[Vertex], closed: bool):
        self.vertices = vertices
        self.closed = closed


class IconDef:
    __slots__ = ("subpaths", "color")

    def __init__(self, subpaths: List[SubPath], color: str):
        self.subpaths = subpaths
        self.color = color


ICONS: Dict[str, IconDef] = {
    "block": IconDef(
        subpaths=[
            SubPath([(0.05, 0.55), (0.55, 1.00), (1.00, 0.35), (0.60, 0.05)], closed=True),
            SubPath([(0.05, 0.55), (1.00, 0.35)], closed=False),
            SubPath([(0.55, 1.00), (0.60, 0.05)], closed=False),
        ],
        color="tan",
    ),
    "entrance": IconDef(
        subpaths=[
            SubPath([(0.0, 0.35), (1.0, 1.0), (0.55, 0.0)], closed=True),
        ],
        color="firebrick",
    ),
    "continuation": IconDef(
        subpaths=[
            SubPath(
                [
                    (0.30, 1.00), (0.10, 0.92), (0.05, 0.80), (0.20, 0.72),
                    (0.45, 0.78), (0.65, 0.95), (0.80, 1.00), (0.95, 0.85),
                    (0.90, 0.60), (0.70, 0.45), (0.55, 0.30), (0.50, 0.15),
                    (0.50, 0.00),
                ],
                closed=False,
            ),
        ],
        color="firebrick",
    ),
    "water_flow_point": IconDef(
        subpaths=[
            SubPath([(0.05, 0.30), (0.05, 0.60), (0.35, 0.85)], closed=False),
            SubPath(
                [
                    (0.05, 0.60), (0.25, 0.55), (0.40, 0.65), (0.55, 0.55),
                    (0.65, 0.40), (0.80, 0.30), (0.90, 0.15), (1.00, 0.05),
                ],
                closed=False,
            ),
        ],
        color="mediumpurple",
    ),
    "water_flow_chevron": IconDef(
        subpaths=[
            SubPath([(0.0, 0.9), (1.0, 0.5), (0.0, 0.1)], closed=False),
        ],
        color="steelblue",
    ),
}


def _normalized_subpaths(name: str) -> List[Tuple[List[Vertex], bool]]:
    """Return `name`'s sub-paths translated to be centered at (0, 0) and
    scaled so the larger dimension of their combined bounding box spans 1.0."""
    icon = ICONS[name]
    all_x = [x for sub in icon.subpaths for (x, _) in sub.vertices]
    all_y = [y for sub in icon.subpaths for (_, y) in sub.vertices]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    cx, cy = (min_x + max_x) / 2, (min_y + max_y) / 2
    span = max(max_x - min_x, max_y - min_y) or 1.0
    scale = 1.0 / span
    result = []
    for sub in icon.subpaths:
        norm = [((x - cx) * scale, (y - cy) * scale) for (x, y) in sub.vertices]
        result.append((norm, sub.closed))
    return result


def icon_to_matplotlib_path(name: str) -> MplPath:
    """Build a matplotlib Path for the named icon, centered at the origin
    with its larger bounding-box dimension spanning 1.0. Raises KeyError
    for an unknown icon name (from the ICONS lookup in _normalized_subpaths)."""
    vertices: List[Vertex] = []
    codes: List[int] = []
    for verts, closed in _normalized_subpaths(name):
        vertices.append(verts[0])
        codes.append(MplPath.MOVETO)
        for pt in verts[1:]:
            vertices.append(pt)
            codes.append(MplPath.LINETO)
        if closed:
            vertices.append(verts[0])
            codes.append(MplPath.CLOSEPOLY)
    return MplPath(vertices, codes)


def icon_to_svg_path_d(name: str, viewbox_size: float = 32.0) -> str:
    """Build an SVG `d` path string for the named icon, centered and scaled
    to fit a `viewbox_size` x `viewbox_size` viewBox with the origin at its
    center. Raises KeyError for an unknown icon name."""
    half = viewbox_size / 2.0
    parts: List[str] = []
    for verts, closed in _normalized_subpaths(name):
        x0, y0 = verts[0]
        parts.append(f"M {half + x0 * viewbox_size:.2f} {half - y0 * viewbox_size:.2f}")
        for (x, y) in verts[1:]:
            parts.append(f"L {half + x * viewbox_size:.2f} {half - y * viewbox_size:.2f}")
        if closed:
            parts.append("Z")
    return " ".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_style_icons.py -v`
Expected: PASS (all parametrized cases)

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/style_icons.py tests/test_style_icons.py
git commit -m "feat(style): add vector icon shape definitions for TopoDroid symbols"
```

---

## Task 2: Fix DXF block-name whitelist (root cause of the `B_blocks` bug)

**Files:**
- Modify: `cave_sketch/dxf/parser.py:170` (`_get_features`)
- Test: `tests/test_dxf_parser.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `_get_features(msp)` now recognizes `B_ice`, `B_snow`, `B_blocks`, `B_water-flow`, `B_continuation`, `B_entrance` (removes the dead `"BLOCK"` entry, which never matched a real DXF block name).

- [ ] **Step 1: Write the failing tests**

Add `import ezdxf` and `from cave_sketch.dxf.parser import _get_features` to the imports at the top of `tests/test_dxf_parser.py` (it already imports `Path` and `parse_dxf`), then add:

```python
def test_get_features_includes_all_target_block_names():
    doc = ezdxf.new()
    msp = doc.modelspace()
    names = ["B_ice", "B_snow", "B_blocks", "B_water-flow", "B_continuation", "B_entrance"]
    for name in names:
        doc.blocks.new(name=name)
        msp.add_blockref(name, insert=(0, 0))

    blocks = _get_features(msp)

    assert {b["Type"] for b in blocks} == set(names)


def test_get_features_ignores_unknown_block_names():
    doc = ezdxf.new()
    msp = doc.modelspace()
    doc.blocks.new(name="SOME_OTHER_BLOCK")
    msp.add_blockref("SOME_OTHER_BLOCK", insert=(0, 0))

    assert _get_features(msp) == []


def test_parse_dxf_includes_new_block_types():
    survey = parse_dxf(Path("tests/fixtures/sample_v14.dxf"))
    point_types = {p.point_type for p in survey.points}
    assert "B_blocks" in point_types
    assert "B_water-flow" in point_types
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_dxf_parser.py -v`
Expected: `test_get_features_includes_all_target_block_names` FAILS (only `B_ice`/`B_snow` found, `B_blocks` etc. missing); `test_parse_dxf_includes_new_block_types` FAILS (`B_blocks`/`B_water-flow` not in `point_types`).

- [ ] **Step 3: Fix the whitelist**

In `cave_sketch/dxf/parser.py`, change line 170:

```python
    valid_block_names = {"B_ice", "BLOCK", "B_snow"}
```

to:

```python
    valid_block_names = {"B_ice", "B_snow", "B_blocks", "B_water-flow", "B_continuation", "B_entrance"}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_dxf_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/dxf/parser.py tests/test_dxf_parser.py
git commit -m "fix(dxf): parse B_blocks, B_water-flow, B_continuation, B_entrance blocks

The whitelist checked for a literal block name 'BLOCK', which never
appears in any real DXF (the actual name is always B_blocks) — these
four block types were silently dropped before parsing even finished."
```

---

## Task 3: `STYLE_MAP` entries for the new/fixed elements

**Files:**
- Modify: `cave_sketch/style.py`
- Test: `tests/test_style.py` (new file)

**Interfaces:**
- Consumes: `cave_sketch.style_icons.ICONS` (Task 1) — for the color-validity check only.
- Produces: `STYLE_MAP["B_blocks"]`, `["B_continuation"]`, `["B_entrance"]`, `["B_water-flow"]` with `"type": "icon"`, `"icon"` (a key into `style_icons.ICONS`), `"color"`, `"size"`. `STYLE_MAP["L_water-flow"]` with `"type": "line"`, `"color": "steelblue"`, `"linestyle": "solid"`, `"weight": 1`, `"line_decoration": "water_flow_chevron"`, `"decoration_size": 4`. The old `"BLOCK"` key no longer exists.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_style.py`:

```python
import matplotlib.colors as mcolors

from cave_sketch.style import STYLE_MAP
from cave_sketch.style_icons import ICONS


def test_block_key_renamed():
    assert "BLOCK" not in STYLE_MAP
    assert STYLE_MAP["B_blocks"]["type"] == "icon"
    assert STYLE_MAP["B_blocks"]["icon"] == "block"


def test_new_icon_entries_reference_valid_icons():
    for stype in ["B_blocks", "B_continuation", "B_entrance", "B_water-flow"]:
        entry = STYLE_MAP[stype]
        assert entry["type"] == "icon"
        assert entry["icon"] in ICONS


def test_water_flow_line_entry():
    entry = STYLE_MAP["L_water-flow"]
    assert entry["type"] == "line"
    assert entry["line_decoration"] == "water_flow_chevron"
    assert entry["decoration_size"] > 0


def test_all_style_map_colors_are_renderable():
    for stype, entry in STYLE_MAP.items():
        color = entry.get("color")
        if color:
            assert mcolors.is_color_like(color), f"{stype!r} has an unrenderable color {color!r}"
    for name, icon in ICONS.items():
        assert mcolors.is_color_like(icon.color), f"icon {name!r} has an unrenderable color {icon.color!r}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_style.py -v`
Expected: FAIL (`KeyError: 'B_blocks'`, etc. — none of the new entries exist yet)

- [ ] **Step 3: Update `cave_sketch/style.py`**

Replace the `"BLOCK"` entry (current lines 32-37):

```python
    "BLOCK": {
        "color": "saddlebrown",
        "marker": "o",  # square marker
        "markersize": 4,
        "type": "point",
    },
```

with:

```python
    "B_blocks": {"type": "icon", "icon": "block", "color": "tan", "size": 5},
    "B_continuation": {"type": "icon", "icon": "continuation", "color": "firebrick", "size": 6},
    "B_entrance": {"type": "icon", "icon": "entrance", "color": "firebrick", "size": 7},
    "B_water-flow": {"type": "icon", "icon": "water_flow_point", "color": "mediumpurple", "size": 4},
    "L_water-flow": {
        "type": "line",
        "color": "steelblue",
        "linestyle": "solid",
        "weight": 1,
        "line_decoration": "water_flow_chevron",
        "decoration_size": 4,
    },
```

(Leave every other entry — `station`, `L_wall`, `L_slope`, `L_chimney`, `L_border`, `L_pit`, `L_wall-presumed`, `A_water`, `B_ice`, `B_snow`, `connector` — untouched.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_style.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/style.py tests/test_style.py
git commit -m "feat(style): add STYLE_MAP entries for water-flow, continuation, entrance, blocks"
```

---

## Task 4: Icon points in `extract_features_from_df` (survey plot data path)

**Files:**
- Modify: `cave_sketch/features/render_features.py` (`extract_features_from_df`, lines 86-99)
- Test: `tests/test_render_features.py`

**Interfaces:**
- Consumes: `STYLE_MAP[typ]["type"] == "icon"` (Task 3).
- Produces: `features["points"]` entries for icon types now look like `{"coords": [y, x], "icon": str, "color": str, "size": float, "popup": str}` (no `"marker"` key) instead of the plain-marker shape. Existing `"point"`-type entries (`B_ice`/`B_snow`) are unchanged and keep `"marker"`/no `"icon"` key.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_features.py`:

```python
def test_extract_features_icon_point():
    df = pd.DataFrame([
        {"Node_Id": "B_blocks_0", "X": 5.0, "Y": 3.0, "Links": "-", "Type": "B_blocks"},
    ])

    features = extract_features_from_df(df)

    assert len(features["points"]) == 1
    point = features["points"][0]
    assert point["coords"] == [3.0, 5.0]
    assert point["icon"] == "block"
    assert point["color"] == "tan"
    assert "marker" not in point
    assert point["popup"] == "B_blocks (B_blocks_0)"


def test_extract_features_plain_point_unaffected():
    df = pd.DataFrame([
        {"Node_Id": "B_ice_0", "X": 1.0, "Y": 2.0, "Links": "-", "Type": "B_ice"},
    ])

    features = extract_features_from_df(df)

    assert len(features["points"]) == 1
    point = features["points"][0]
    assert "icon" not in point
    assert point["marker"] == "."
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_render_features.py -v`
Expected: FAIL (`point["icon"]` raises `KeyError`, since the current code always builds `"marker"`/`"markersize"` and never checks for `"icon"`)

- [ ] **Step 3: Update `extract_features_from_df`**

In `cave_sketch/features/render_features.py`, replace the point-handling block (current lines 86-99):

```python
        # --- New block: handle standalone point features ---
        style_type = STYLE_MAP.get(typ, {}).get("type", "line")
        if style_type == "point":
            style = STYLE_MAP.get(typ, {"color": "black", "marker": "o", "markersize": 6})
            features["points"].append(
                {
                    "coords": [y, x],  # lat/lon-like
                    "color": style.get("color", "black"),
                    "marker": style.get("marker", "o"),
                    "size": style.get("markersize", 6),
                    "popup": f"{typ} ({nid})",
                }
            )
            continue  # skip to next row
```

with:

```python
        # --- New block: handle standalone point features (plain markers and icons) ---
        style_type = STYLE_MAP.get(typ, {}).get("type", "line")
        if style_type in ("point", "icon"):
            style = STYLE_MAP.get(typ, {"color": "black", "marker": "o", "markersize": 6})
            point_feature = {
                "coords": [y, x],  # lat/lon-like
                "color": style.get("color", "black"),
                "popup": f"{typ} ({nid})",
            }
            if style_type == "icon":
                point_feature["icon"] = style["icon"]
                point_feature["size"] = style.get("size", 6)
            else:
                point_feature["marker"] = style.get("marker", "o")
                point_feature["size"] = style.get("markersize", 6)
            features["points"].append(point_feature)
            continue  # skip to next row
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_render_features.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/features/render_features.py tests/test_render_features.py
git commit -m "feat(render-features): emit icon-style points from survey DataFrame"
```

---

## Task 5: Line decorations in `extract_features_from_df` (water-flow chevrons, survey plot)

**Files:**
- Modify: `cave_sketch/features/render_features.py` (imports, `extract_features_from_df`)
- Test: `tests/test_render_features.py`

**Interfaces:**
- Consumes: `STYLE_MAP[typ].get("line_decoration")` (Task 3).
- Produces: a new private helper `_canonical_segment_order(node_a: str, node_b: str) -> Tuple[str, str]` (reused by Task 7), and `features["line_decorations"]`: a list of `{"coords": [mid_y, mid_x], "angle_rad": float, "icon": str, "color": str, "size": float}`, one per unique polyline segment whose line type has `line_decoration` set, deduplicated and canonically directed so opposite traversals of the same segment don't produce two opposing arrows.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_render_features.py`:

```python
import math

import pytest


def test_extract_features_water_flow_line_decoration_dedup_and_direction():
    df = pd.DataFrame([
        {"Node_Id": "0P0", "X": 0.0, "Y": 0.0, "Links": "0P1", "Type": "L_water-flow"},
        {"Node_Id": "0P1", "X": 10.0, "Y": 0.0, "Links": "0P0-0P2", "Type": "L_water-flow"},
        {"Node_Id": "0P2", "X": 10.0, "Y": 10.0, "Links": "0P1", "Type": "L_water-flow"},
    ])

    features = extract_features_from_df(df)

    assert len(features["lines"]) == 4  # both traversal directions still drawn as plain lines
    assert len(features["line_decorations"]) == 2  # deduplicated to one per segment

    dec_a = next(d for d in features["line_decorations"] if d["coords"] == [0.0, 5.0])
    assert dec_a["icon"] == "water_flow_chevron"
    assert dec_a["angle_rad"] == pytest.approx(0.0)  # 0P0(0,0) -> 0P1(10,0): +x direction

    dec_b = next(d for d in features["line_decorations"] if d["coords"] == [5.0, 10.0])
    assert dec_b["angle_rad"] == pytest.approx(math.pi / 2)  # 0P1(10,0) -> 0P2(10,10): +y direction


def test_extract_features_water_flow_single_segment_yields_one_decoration():
    df = pd.DataFrame([
        {"Node_Id": "0P0", "X": 0.0, "Y": 0.0, "Links": "0P1", "Type": "L_water-flow"},
        {"Node_Id": "0P1", "X": 4.0, "Y": 0.0, "Links": "0P0", "Type": "L_water-flow"},
    ])

    features = extract_features_from_df(df)

    assert len(features["line_decorations"]) == 1


def test_extract_features_water_flow_missing_neighbor_no_crash():
    df = pd.DataFrame([
        {"Node_Id": "0P0", "X": 0.0, "Y": 0.0, "Links": "0P1", "Type": "L_water-flow"},
    ])

    features = extract_features_from_df(df)

    assert features["line_decorations"] == []
    assert features["lines"] == []


def test_extract_features_two_water_flow_polylines_do_not_cross_contaminate():
    df = pd.DataFrame([
        {"Node_Id": "0P0", "X": 0.0, "Y": 0.0, "Links": "0P1", "Type": "L_water-flow"},
        {"Node_Id": "0P1", "X": 4.0, "Y": 0.0, "Links": "0P0", "Type": "L_water-flow"},
        {"Node_Id": "1P0", "X": 100.0, "Y": 100.0, "Links": "1P1", "Type": "L_water-flow"},
        {"Node_Id": "1P1", "X": 104.0, "Y": 100.0, "Links": "1P0", "Type": "L_water-flow"},
    ])

    features = extract_features_from_df(df)

    assert len(features["line_decorations"]) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_render_features.py -v`
Expected: FAIL with `KeyError: 'line_decorations'`

- [ ] **Step 3: Implement the canonicalization helper and line decorations**

In `cave_sketch/features/render_features.py`, add `math` to the imports (top of file currently has `import re` then `from typing import ...` then `import pandas as pd` then the `STYLE_MAP` import):

```python
import math
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from cave_sketch.style import STYLE_MAP

_POLYLINE_NODE_RE = re.compile(r"^(\d+)P(\d+)$")


def _canonical_segment_order(node_a: str, node_b: str) -> Tuple[str, str]:
    """Order two polyline node IDs (format '{i}P{j}') so the lower vertex
    index comes first, preserving the DXF's original vertex direction (the
    direction the polyline — and its flow-direction convention — was drawn
    in). Falls back to lexical order for non-polyline IDs or IDs from
    different polylines, which should not occur for line_decoration types."""
    match_a = _POLYLINE_NODE_RE.match(node_a)
    match_b = _POLYLINE_NODE_RE.match(node_b)
    if match_a and match_b and match_a.group(1) == match_b.group(1):
        idx_a, idx_b = int(match_a.group(2)), int(match_b.group(2))
        return (node_a, node_b) if idx_a < idx_b else (node_b, node_a)
    return (node_a, node_b) if node_a < node_b else (node_b, node_a)
```

Then, in `extract_features_from_df`, initialize the new features list and a dedup set right after the existing `features: Dict[str, list] = {...}` line:

```python
    features: Dict[str, list] = {"lines": [], "polygons": [], "points": [], "line_decorations": []}
    decorated_segments = set()
```

Then extend the line-building block (the `if style_type == "line":` branch inside the neighbor loop) to also emit a decoration:

```python
                if style_type == "line":
                    style = STYLE_MAP.get(typ, STYLE_MAP["L_wall"])
                    features["lines"].append(
                        {
                            "coords": [[y, x], [y2, x2]],
                            "color": style.get("color", "black"),
                            "weight": style.get("weight", 1),
                            "dash": None if style.get("linestyle", "solid") == "solid" else [3, 7],
                            "popup": f"{typ} ({nid}-{nbr})",
                        }
                    )

                    decoration_icon = style.get("line_decoration")
                    if decoration_icon:
                        seg_key = frozenset({nid, nbr})
                        if seg_key not in decorated_segments:
                            decorated_segments.add(seg_key)
                            from_id, _ = _canonical_segment_order(nid, nbr)
                            if from_id == nid:
                                fx, fy, tx, ty = x, y, x2, y2
                            else:
                                fx, fy, tx, ty = x2, y2, x, y
                            features["line_decorations"].append(
                                {
                                    "coords": [(fy + ty) / 2, (fx + tx) / 2],
                                    "angle_rad": math.atan2(ty - fy, tx - fx),
                                    "icon": decoration_icon,
                                    "color": style.get("color", "black"),
                                    "size": style.get("decoration_size", 4),
                                }
                            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_render_features.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/features/render_features.py tests/test_render_features.py
git commit -m "feat(render-features): add direction-canonicalized water-flow line decorations"
```

---

## Task 6: Fix missing points in `extract_features_from_json` (Folium satellite view bug)

**Files:**
- Modify: `cave_sketch/features/render_features.py` (`extract_features_from_json`)
- Test: `tests/test_render_features.py`

**Interfaces:**
- Consumes: `STYLE_MAP[ntype]["type"] in ("point", "icon")` (Task 3).
- Produces: `extract_features_from_json` now also returns a populated `"points"` list (previously always empty), built from `map_data["nodes"]` (dict-of-dicts or list-of-dicts, both shapes supported), in the same shape as Task 4's df-based points (`"icon"` key for icon types, `"marker"` key otherwise).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_render_features.py`:

```python
from cave_sketch.features.render_features import extract_features_from_json


def test_extract_features_from_json_points_dict_shape():
    map_data = {
        "name": "Test Map",
        "nodes": {"5": {"lat": 5.0, "lon": 5.0, "type": "B_blocks"}},
        "lines": [],
        "water_polygons": [],
    }

    features = extract_features_from_json(map_data)

    assert len(features["points"]) == 1
    point = features["points"][0]
    assert point["coords"] == [5.0, 5.0]
    assert point["icon"] == "block"


def test_extract_features_from_json_points_list_shape():
    map_data = {
        "name": "Test Map",
        "nodes": [{"id": "5", "lat": 5.0, "lon": 5.0, "type": "B_ice"}],
        "lines": [],
        "water_polygons": [],
    }

    features = extract_features_from_json(map_data)

    assert len(features["points"]) == 1
    assert features["points"][0]["marker"] == "."


def test_extract_features_from_json_points_skips_non_point_types():
    map_data = {
        "name": "Test Map",
        "nodes": {"1": {"lat": 1.0, "lon": 1.0, "type": "L_wall"}},
        "lines": [],
        "water_polygons": [],
    }

    features = extract_features_from_json(map_data)

    assert features["points"] == []


def test_extract_features_from_json_missing_nodes_key_no_crash():
    map_data = {"name": "Test Map", "lines": [], "water_polygons": []}

    features = extract_features_from_json(map_data)

    assert features["points"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_render_features.py -v`
Expected: FAIL (`features["points"]` is always `[]`, but the dict-shape/list-shape tests expect one entry)

- [ ] **Step 3: Implement the points builder**

In `cave_sketch/features/render_features.py`, add a `"points"` key to the returned `features` dict in `extract_features_from_json` (currently `{"lines": [], "polygons": []}`) and append a new block after the existing `# Lines` loop, before the `return features` statement:

```python
def extract_features_from_json(map_data: Dict[str, Any]) -> Dict[str, list]:
    """
    Extract abstract features (lines, polygons, points) with styles,
    independent of rendering backend.
    """
    features: Dict[str, List[Dict[str, Any]]] = {"lines": [], "polygons": [], "points": []}

    # Polygons
    for water_polygon in map_data.get("water_polygons", []):
        coords = water_polygon["coordinates"]
        features["polygons"].append(
            {
                "coords": coords,
                "fill_color": "blue",
                "fill_opacity": 0.3,
                "edge_color": "blue",
                "popup": f"{map_data['name']}: Water Area {water_polygon.get('polygon_id', '')}",
            }
        )

    # Lines
    for line in map_data.get("lines", []):
        line_type = line["type"]
        style = STYLE_MAP.get(line_type, {"color": "black", "type": "line"})
        color = style.get("color", "black")
        weight = style.get("weight", 1)
        linestyle = style.get("linestyle", "solid")

        dash = None
        if linestyle == (0, (1, 1)):
            dash = [5, 5]
        elif linestyle == (0, (1, 2)):
            dash = [3, 7]

        pt_from = [line["from"]["lat"], line["from"]["lon"]]
        pt_to = [line["to"]["lat"], line["to"]["lon"]]

        features["lines"].append(
            {
                "coords": [pt_from, pt_to],
                "color": color,
                "weight": weight,
                "dash": dash,
                "popup": f"{map_data['name']}: {line_type}",
            }
        )

    # Points
    nodes_data = map_data.get("nodes", {})
    nodes_list = nodes_data if isinstance(nodes_data, list) else [
        {"id": k, **v} for k, v in nodes_data.items()
    ]
    for n in nodes_list:
        ntype = n.get("type", "")
        style = STYLE_MAP.get(ntype)
        if not style or style.get("type") not in ("point", "icon"):
            continue
        point_feature = {
            "coords": [n["lat"], n["lon"]],
            "color": style.get("color", "black"),
            "popup": f"{map_data.get('name', '')}: {ntype} ({n.get('id', '')})",
        }
        if style["type"] == "icon":
            point_feature["icon"] = style["icon"]
            point_feature["size"] = style.get("size", 6)
        else:
            point_feature["marker"] = style.get("marker", "o")
            point_feature["size"] = style.get("markersize", 6)
        features["points"].append(point_feature)

    return features
```

(The `# Polygons` and `# Lines` blocks are copied verbatim from the current file — unchanged — so the whole function is shown for clarity; only the `features = {...}` initializer and the new `# Points` block actually change.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_render_features.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/features/render_features.py tests/test_render_features.py
git commit -m "fix(render-features): populate points in extract_features_from_json

The Folium satellite HTML view rendered zero point markers for every
type (B_ice, B_snow, and now the new icon types) because this function
only ever built 'lines' and 'polygons', despite render_to_folium
already having point-rendering code waiting for a 'points' key."
```

---

## Task 7: Line decorations in `extract_features_from_json` (satellite view bearing)

**Files:**
- Modify: `cave_sketch/features/render_features.py` (`extract_features_from_json`)
- Test: `tests/test_render_features.py`

**Interfaces:**
- Consumes: `_canonical_segment_order` (Task 5), `STYLE_MAP[line_type].get("line_decoration")` (Task 3).
- Produces: `extract_features_from_json` also returns `"line_decorations"`: a list of `{"coords": [mid_lat, mid_lon], "bearing_deg": float, "icon": str, "color": str, "size": float}`, `bearing_deg` being degrees clockwise from north (usable as-is by both Folium's CSS rotation and KML's `<heading>`, per the spec — see Tasks 11 and 13).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_render_features.py`:

```python
def test_extract_features_from_json_line_decoration_bearing_and_dedup():
    map_data = {
        "name": "Test Map",
        "lines": [
            {"from": {"id": "0P0", "lat": 0.0, "lon": 0.0}, "to": {"id": "0P1", "lat": 1.0, "lon": 0.0}, "type": "L_water-flow"},
            {"from": {"id": "0P1", "lat": 1.0, "lon": 0.0}, "to": {"id": "0P0", "lat": 0.0, "lon": 0.0}, "type": "L_water-flow"},
        ],
        "nodes": {},
        "water_polygons": [],
    }

    features = extract_features_from_json(map_data)

    assert len(features["lines"]) == 2  # both directions still drawn as plain lines
    assert len(features["line_decorations"]) == 1  # deduplicated to one

    dec = features["line_decorations"][0]
    assert dec["bearing_deg"] == pytest.approx(0.0)  # due north
    assert dec["icon"] == "water_flow_chevron"
```

- [ ] **Step 2: Run tests to verify it fails**

Run: `pytest tests/test_render_features.py -v`
Expected: FAIL with `KeyError: 'line_decorations'`

- [ ] **Step 3: Implement the bearing helper and line decorations**

In `cave_sketch/features/render_features.py`, add a bearing helper near `_canonical_segment_order`:

```python
def _bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Planar-approximation compass bearing (degrees clockwise from north)
    from (lat1, lon1) to (lat2, lon2). Adequate for the short distances
    (meters to a few hundred meters) spanned by a single cave survey."""
    d_lat = lat2 - lat1
    d_lon = (lon2 - lon1) * math.cos(math.radians(lat1))
    return math.degrees(math.atan2(d_lon, d_lat)) % 360
```

Add `"line_decorations": []` to the `features` dict initializer (now `{"lines": [], "polygons": [], "points": [], "line_decorations": []}`), and extend the `# Lines` loop to also emit decorations:

```python
    # Lines
    decorated_segments = set()
    for line in map_data.get("lines", []):
        line_type = line["type"]
        style = STYLE_MAP.get(line_type, {"color": "black", "type": "line"})
        color = style.get("color", "black")
        weight = style.get("weight", 1)
        linestyle = style.get("linestyle", "solid")

        dash = None
        if linestyle == (0, (1, 1)):
            dash = [5, 5]
        elif linestyle == (0, (1, 2)):
            dash = [3, 7]

        pt_from = [line["from"]["lat"], line["from"]["lon"]]
        pt_to = [line["to"]["lat"], line["to"]["lon"]]

        features["lines"].append(
            {
                "coords": [pt_from, pt_to],
                "color": color,
                "weight": weight,
                "dash": dash,
                "popup": f"{map_data['name']}: {line_type}",
            }
        )

        decoration_icon = style.get("line_decoration")
        if decoration_icon:
            from_id, to_id = line["from"]["id"], line["to"]["id"]
            seg_key = frozenset({from_id, to_id})
            if seg_key not in decorated_segments:
                decorated_segments.add(seg_key)
                canon_from, _ = _canonical_segment_order(from_id, to_id)
                if canon_from == from_id:
                    flat, flon, tlat, tlon = pt_from[0], pt_from[1], pt_to[0], pt_to[1]
                else:
                    flat, flon, tlat, tlon = pt_to[0], pt_to[1], pt_from[0], pt_from[1]
                features["line_decorations"].append(
                    {
                        "coords": [(flat + tlat) / 2, (flon + tlon) / 2],
                        "bearing_deg": _bearing_deg(flat, flon, tlat, tlon),
                        "icon": decoration_icon,
                        "color": color,
                        "size": style.get("decoration_size", 4),
                    }
                )
```

(This replaces the current `# Lines` loop body, which only appended to `features["lines"]`; the polygon and point blocks are unaffected.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_render_features.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/features/render_features.py tests/test_render_features.py
git commit -m "feat(render-features): add compass-bearing line decorations for satellite view"
```

---

## Task 8: Render icon points in matplotlib (survey plot)

**Files:**
- Modify: `cave_sketch/backend_renders/matplotlib.py`
- Test: `tests/test_matplotlib_backend.py` (new file)

**Interfaces:**
- Consumes: `icon_to_matplotlib_path` (Task 1), `features["points"]` entries with an `"icon"` key (Task 4).
- Produces: `render_to_matplotlib` draws icon points as scatter markers using a custom `MarkerStyle`, grouped by icon name, alongside the existing marker-character grouping (which is untouched).

- [ ] **Step 1: Write the failing test**

Create `tests/test_matplotlib_backend.py`:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cave_sketch.backend_renders.matplotlib import render_to_matplotlib


def test_render_to_matplotlib_icon_points_are_scattered():
    fig, ax = plt.subplots()
    features = {
        "lines": [],
        "polygons": [],
        "points": [
            {"coords": [1.0, 2.0], "icon": "block", "color": "tan", "size": 5, "popup": "B_blocks (x)"},
            {"coords": [3.0, 4.0], "icon": "block", "color": "tan", "size": 5, "popup": "B_blocks (y)"},
        ],
        "line_decorations": [],
    }

    render_to_matplotlib(features, ax)

    assert len(ax.collections) == 1
    assert len(ax.collections[0].get_offsets()) == 2
    plt.close(fig)


def test_render_to_matplotlib_plain_marker_points_unaffected():
    fig, ax = plt.subplots()
    features = {
        "lines": [],
        "polygons": [],
        "points": [
            {"coords": [1.0, 2.0], "marker": ".", "color": "deepskyblue", "size": 2, "popup": "B_ice (x)"},
        ],
        "line_decorations": [],
    }

    render_to_matplotlib(features, ax)

    assert len(ax.collections) == 1
    plt.close(fig)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_matplotlib_backend.py -v`
Expected: `test_render_to_matplotlib_icon_points_are_scattered` FAILS with `KeyError: 'marker'` (the current code always reads `p.get("marker", "o")` and groups by it, so an icon point with no `"marker"` key falls into the `"o"` group but the underlying access pattern for icon rendering doesn't exist yet — confirm the test fails, then proceed)

- [ ] **Step 3: Implement icon-point rendering**

In `cave_sketch/backend_renders/matplotlib.py`, update the imports (current lines 1-5):

```python
from typing import Any, Dict, List, Optional

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Polygon as MplPolygon

from cave_sketch.style_icons import icon_to_matplotlib_path
```

Then replace the `# ---- POINTS (B_ice, BLOCK, etc.) ----` block (current lines 72-103) with:

```python
    # ---- POINTS (B_ice, B_snow: plain markers; B_blocks etc.: icons) ----
    plain_points = [p for p in features.get("points", []) if "icon" not in p]
    icon_points = [p for p in features.get("points", []) if "icon" in p]

    points_by_marker: Dict[str, List[Dict[str, Any]]] = {}
    for p in plain_points:
        marker = p.get("marker", "o")
        points_by_marker.setdefault(marker, []).append(p)

    for marker, plist in points_by_marker.items():
        xs = []
        ys = []
        sizes = []
        colors = []
        zorder = 3
        for p in plist:
            y, x = p["coords"]
            xs.append(x)
            ys.append(y)
            size_pts = p.get("size", 6)
            s_area = size_pts**2 * 0.5
            sizes.append(s_area)
            colors.append(p.get("color", "black"))
            zorder = p.get("zorder", 3)

        ax.scatter(
            xs,
            ys,
            s=sizes,
            c=colors,
            marker=marker,
            edgecolors="none",
            alpha=0.9,
            zorder=zorder,
        )

        if config.get("show_labels", False):
            for p in plist:
                y, x = p["coords"]
                ax.text(
                    x,
                    y,
                    p.get("popup", ""),
                    fontsize=5,
                    ha="left",
                    va="bottom",
                    color=p.get("color", "black"),
                    zorder=4,
                )

    points_by_icon: Dict[str, List[Dict[str, Any]]] = {}
    for p in icon_points:
        points_by_icon.setdefault(p["icon"], []).append(p)

    for icon_name, plist in points_by_icon.items():
        marker_style = MarkerStyle(icon_to_matplotlib_path(icon_name))
        xs = []
        ys = []
        sizes = []
        colors = []
        zorder = 3
        for p in plist:
            y, x = p["coords"]
            xs.append(x)
            ys.append(y)
            size_pts = p.get("size", 6)
            sizes.append(size_pts**2 * 0.5)
            colors.append(p.get("color", "black"))
            zorder = p.get("zorder", 3)

        ax.scatter(
            xs,
            ys,
            s=sizes,
            c=colors,
            marker=marker_style,
            edgecolors="none",
            alpha=0.9,
            zorder=zorder,
        )

        if config.get("show_labels", False):
            for p in plist:
                y, x = p["coords"]
                ax.text(
                    x,
                    y,
                    p.get("popup", ""),
                    fontsize=5,
                    ha="left",
                    va="bottom",
                    color=p.get("color", "black"),
                    zorder=4,
                )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_matplotlib_backend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/backend_renders/matplotlib.py tests/test_matplotlib_backend.py
git commit -m "feat(matplotlib-backend): render icon-style points with custom marker paths"
```

---

## Task 9: Render line decorations in matplotlib (water-flow chevrons on the survey plot)

**Files:**
- Modify: `cave_sketch/backend_renders/matplotlib.py`
- Test: `tests/test_matplotlib_backend.py`

**Interfaces:**
- Consumes: `icon_to_matplotlib_path` (Task 1), `features["line_decorations"]` (Task 5).
- Produces: `render_to_matplotlib` draws one rotated, unfilled `PathPatch` per decoration entry.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_matplotlib_backend.py`:

```python
import math

from matplotlib.patches import PathPatch


def test_render_to_matplotlib_line_decorations_add_path_patches():
    fig, ax = plt.subplots()
    features = {
        "lines": [],
        "polygons": [],
        "points": [],
        "line_decorations": [
            {"coords": [0.0, 0.0], "angle_rad": 0.0, "icon": "water_flow_chevron", "color": "steelblue", "size": 4},
            {"coords": [5.0, 5.0], "angle_rad": math.pi / 2, "icon": "water_flow_chevron", "color": "steelblue", "size": 4},
        ],
    }

    render_to_matplotlib(features, ax)

    chevron_patches = [p for p in ax.patches if isinstance(p, PathPatch)]
    assert len(chevron_patches) == 2
    plt.close(fig)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_matplotlib_backend.py -v`
Expected: FAIL (`assert len(chevron_patches) == 2` — nothing adds patches for `line_decorations` yet)

- [ ] **Step 3: Implement line-decoration rendering**

In `cave_sketch/backend_renders/matplotlib.py`, update the `matplotlib.patches` import line to also bring in `PathPatch`, and add `Affine2D`:

```python
from matplotlib.patches import PathPatch, Polygon as MplPolygon
from matplotlib.transforms import Affine2D
```

Then add a new block at the end of `render_to_matplotlib`, just before the `if layer_name:` line:

```python
    # ---- LINE DECORATIONS (e.g. water-flow chevrons) ----
    for dec in features.get("line_decorations", []):
        base_path = icon_to_matplotlib_path(dec["icon"])
        mid_y, mid_x = dec["coords"]
        size = dec.get("size", 4)
        transform = (
            Affine2D()
            .scale(size)
            .rotate(dec.get("angle_rad", 0.0))
            .translate(mid_x, mid_y)
            + ax.transData
        )
        patch = PathPatch(
            base_path,
            transform=transform,
            facecolor="none",
            edgecolor=dec.get("color", "black"),
            linewidth=1.0,
            zorder=dec.get("zorder", 3),
        )
        ax.add_patch(patch)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_matplotlib_backend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/backend_renders/matplotlib.py tests/test_matplotlib_backend.py
git commit -m "feat(matplotlib-backend): render rotated water-flow chevrons along line segments"
```

---

## Task 10: Render icon points in Folium (satellite HTML view)

**Files:**
- Modify: `cave_sketch/backend_renders/folium.py`
- Test: `tests/test_folium_backend.py` (new file)

**Interfaces:**
- Consumes: `icon_to_svg_path_d` (Task 1), `features["points"]` entries with an `"icon"` key (Task 6).
- Produces: a new private helper `_icon_svg_html(icon_name: str, color: str, size_px: float, rotate_deg: float = 0.0) -> str` (reused by Task 11); `render_to_folium` draws icon-style points as a `folium.DivIcon` instead of `CircleMarker`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_folium_backend.py`:

```python
import folium

from cave_sketch.backend_renders.folium import render_to_folium


def test_render_to_folium_icon_point_uses_div_icon_svg():
    fmap = folium.Map(location=[0, 0], zoom_start=15)
    features = {
        "lines": [],
        "polygons": [],
        "points": [
            {"coords": [1.0, 2.0], "icon": "block", "color": "tan", "size": 5, "popup": "B_blocks (x)"},
        ],
        "line_decorations": [],
    }

    render_to_folium(features, fmap, "Test Layer")
    html = fmap.get_root().render()

    # Folium/Jinja2 JSON-encodes the DivIcon html (escaping `<`/`>`/`"`), so
    # look for substrings that survive that encoding rather than raw tags.
    assert "viewBox" in html
    assert 'stroke=\\"tan\\"' in html


def test_render_to_folium_plain_marker_point_unaffected():
    fmap = folium.Map(location=[0, 0], zoom_start=15)
    features = {
        "lines": [],
        "polygons": [],
        "points": [
            {"coords": [1.0, 2.0], "marker": ".", "color": "deepskyblue", "size": 2, "popup": "B_ice (x)"},
        ],
        "line_decorations": [],
    }

    render_to_folium(features, fmap, "Test Layer")
    html = fmap.get_root().render()

    assert "L.circleMarker(" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_folium_backend.py -v`
Expected: `test_render_to_folium_icon_point_uses_div_icon_svg` FAILS (no `viewBox` in output — the current code always emits a `CircleMarker`)

- [ ] **Step 3: Implement icon-point rendering**

In `cave_sketch/backend_renders/folium.py`, update imports and replace the `# ---- POINTS (B_ice, BLOCK, etc.) ----` block:

```python
from typing import Dict

import folium

from cave_sketch.style_icons import icon_to_svg_path_d


def _icon_svg_html(icon_name: str, color: str, size_px: float, rotate_deg: float = 0.0) -> str:
    """Inline SVG markup for a Folium DivIcon: the named vector icon at
    `size_px`, stroked in `color`, optionally rotated clockwise by
    `rotate_deg` degrees (used for direction-sensitive icons like the
    water-flow chevron — a north-up Leaflet map's clockwise CSS rotation
    matches a clockwise-from-north compass bearing directly, no sign flip)."""
    path_d = icon_to_svg_path_d(icon_name, viewbox_size=size_px)
    return (
        f'<div style="transform: rotate({rotate_deg}deg);">'
        f'<svg width="{size_px}" height="{size_px}" viewBox="0 0 {size_px} {size_px}">'
        f'<path d="{path_d}" stroke="{color}" fill="none" stroke-width="2"/>'
        f"</svg></div>"
    )


def render_to_folium(features: Dict[str, list], folium_map, layer_name: str):
    """Render extracted features onto a Folium map."""
    fg = folium.FeatureGroup(name=layer_name)

    # ---- POLYGONS ----
    for p in features.get("polygons", []):
        folium.Polygon(
            locations=p["coords"],
            color=p.get("edge_color", p.get("fill_color", "blue")),
            weight=0,
            fillColor=p.get("fill_color", "blue"),
            fillOpacity=p.get("fill_opacity", 0.3),
            popup=p.get("popup"),
        ).add_to(fg)

    # ---- LINES ----
    for line in features.get("lines", []):
        kwargs = dict(
            locations=line["coords"],
            color=line.get("color", "black"),
            weight=line.get("weight", 1),
            opacity=0.8,
            popup=line.get("popup", ""),
        )
        if line.get("dash"):
            kwargs["dashArray"] = ",".join(map(str, line["dash"]))
        folium.PolyLine(**kwargs).add_to(fg)

    # ---- POINTS (B_ice, B_snow: plain circle markers; icon types: SVG) ----
    for p in features.get("points", []):
        if "icon" in p:
            size = p.get("size", 6) * 4
            svg = _icon_svg_html(p["icon"], p.get("color", "black"), size)
            folium.Marker(
                location=p["coords"],
                icon=folium.DivIcon(html=svg, icon_size=(size, size), icon_anchor=(size / 2, size / 2)),
                popup=p.get("popup", ""),
            ).add_to(fg)
        else:
            folium.CircleMarker(
                location=p["coords"],
                radius=p.get("size", 6),
                color=p.get("color", "black"),
                fill=True,
                fillColor=p.get("color", "black"),
                fillOpacity=0.9,
                popup=p.get("popup", ""),
            ).add_to(fg)

    fg.add_to(folium_map)
```

(The polygon and line blocks are copied verbatim from the current file — unchanged — so the whole function is shown for clarity; only the points block's body actually changes.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_folium_backend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/backend_renders/folium.py tests/test_folium_backend.py
git commit -m "feat(folium-backend): render icon-style points as inline-SVG DivIcons"
```

---

## Task 11: Render line decorations in Folium (water-flow chevrons on satellite view)

**Files:**
- Modify: `cave_sketch/backend_renders/folium.py`
- Test: `tests/test_folium_backend.py`

**Interfaces:**
- Consumes: `_icon_svg_html` (Task 10), `features["line_decorations"]` (Task 7).
- Produces: `render_to_folium` draws one rotated `DivIcon` per decoration entry.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_folium_backend.py`:

```python
def test_render_to_folium_line_decoration_rotated_div_icon():
    fmap = folium.Map(location=[0, 0], zoom_start=15)
    features = {
        "lines": [],
        "polygons": [],
        "points": [],
        "line_decorations": [
            {"coords": [1.0, 2.0], "bearing_deg": 90.0, "icon": "water_flow_chevron", "color": "steelblue", "size": 4},
        ],
    }

    render_to_folium(features, fmap, "Test Layer")
    html = fmap.get_root().render()

    assert "rotate(90.0deg)" in html
    assert 'stroke=\\"steelblue\\"' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_folium_backend.py -v`
Expected: FAIL (`"rotate(90.0deg)" not in html` — `line_decorations` isn't consumed yet)

- [ ] **Step 3: Implement line-decoration rendering**

In `cave_sketch/backend_renders/folium.py`, add a new block at the end of `render_to_folium`, just before `fg.add_to(folium_map)`:

```python
    # ---- LINE DECORATIONS (e.g. water-flow chevrons) ----
    for dec in features.get("line_decorations", []):
        size = dec.get("size", 4) * 4
        svg = _icon_svg_html(
            dec["icon"], dec.get("color", "black"), size, rotate_deg=dec.get("bearing_deg", 0.0)
        )
        folium.Marker(
            location=dec["coords"],
            icon=folium.DivIcon(html=svg, icon_size=(size, size), icon_anchor=(size / 2, size / 2)),
            popup=dec.get("popup", ""),
        ).add_to(fg)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_folium_backend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/backend_renders/folium.py tests/test_folium_backend.py
git commit -m "feat(folium-backend): render rotated water-flow chevrons on the satellite map"
```

---

## Task 12: Generate and commit icon PNG assets (for KML/KMZ)

**Files:**
- Create: `scripts/generate_icon_assets.py`
- Create (generated, then committed as binary): `cave_sketch/assets/icons/block.png`, `entrance.png`, `continuation.png`, `water_flow_point.png`, `water_flow_chevron.png`
- Test: `tests/test_icon_assets.py` (new file)

**Interfaces:**
- Consumes: `ICONS`, `icon_to_matplotlib_path` (Task 1).
- Produces: one transparent-background PNG per icon under `cave_sketch/assets/icons/`, matching every name in `ICONS`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_icon_assets.py`:

```python
from pathlib import Path

from cave_sketch.style_icons import ICONS

ICONS_DIR = Path(__file__).resolve().parent.parent / "cave_sketch" / "assets" / "icons"


def test_all_icon_pngs_exist_and_are_valid_png():
    for name in ICONS:
        png_path = ICONS_DIR / f"{name}.png"
        assert png_path.exists(), f"missing icon asset: {png_path}"
        with open(png_path, "rb") as f:
            header = f.read(8)
        assert header == b"\x89PNG\r\n\x1a\n"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_icon_assets.py -v`
Expected: FAIL (`AssertionError: missing icon asset: .../cave_sketch/assets/icons/block.png`)

- [ ] **Step 3: Write the generation script**

Create `scripts/generate_icon_assets.py`:

```python
"""One-time dev script: rasterize each vector icon in cave_sketch/style_icons.py
to a small transparent PNG under cave_sketch/assets/icons/, for use by KML/KMZ
exports (cave_sketch/backend_renders/google_earth.py). Not imported at runtime;
re-run and re-commit the output whenever an icon shape changes in style_icons.py.

Usage: python scripts/generate_icon_assets.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch

from cave_sketch.style_icons import ICONS, icon_to_matplotlib_path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "cave_sketch" / "assets" / "icons"


def generate_icon_png(name: str, size_px: int = 64) -> Path:
    path = icon_to_matplotlib_path(name)
    color = ICONS[name].color

    fig = plt.figure(figsize=(size_px / 100, size_px / 100), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.axis("off")

    patch = PathPatch(path, facecolor="none", edgecolor=color, linewidth=2.5)
    ax.add_patch(patch)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{name}.png"
    fig.savefig(output_path, transparent=True)
    plt.close(fig)
    return output_path


def main() -> None:
    for name in ICONS:
        output_path = generate_icon_png(name)
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the script and verify the tests pass**

Run: `python scripts/generate_icon_assets.py`
Expected output: 5 lines, `wrote .../cave_sketch/assets/icons/<name>.png`

Run: `pytest tests/test_icon_assets.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_icon_assets.py cave_sketch/assets/icons/*.png tests/test_icon_assets.py
git commit -m "feat(assets): generate and commit rasterized icon PNGs for KML/KMZ export"
```

---

## Task 13: Use icon PNGs and heading rotation in KML/KMZ export

**Files:**
- Modify: `cave_sketch/backend_renders/google_earth.py`
- Test: `tests/test_kmz_export.py`

**Interfaces:**
- Consumes: `STYLE_MAP[stype]["type"] == "icon"` (Task 3), `features["line_decorations"]` with `"bearing_deg"` (Task 7), the committed PNGs under `cave_sketch/assets/icons/` (Task 12).
- Produces: icon-type `STYLE_MAP` entries get a `<Style id="icon_{stype}">` referencing `icons/{icon}.png`; each node whose style is `"icon"` gets a `styleUrl` matching that new id (existing `"point"`-type nodes are unaffected — same generic `styleUrl` formula, now type-aware); each `line_decorations` entry becomes its own `Placemark` with an inline per-placemark `Style`/`IconStyle`/`heading`; `render_to_kmz` bundles every icon PNG referenced by `STYLE_MAP` under `icons/<name>.png` in the zip.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_kmz_export.py`:

```python
def test_kml_icon_style_uses_png_href():
    map_data = {
        "name": "Test Map",
        "lines": [],
        "nodes": [{"id": "5", "lat": 5.0, "lon": 5.0, "type": "B_blocks"}],
        "water_polygons": [],
    }

    kml_str = render_to_kml([map_data])
    root = ET.fromstring(kml_str.encode("utf-8"))
    ns = {"kml": "http://www.opengis.net/kml/2.2"}

    icon_style = next(s for s in root.findall(".//kml:Style", ns) if s.get("id") == "icon_B_blocks")
    href = icon_style.find(".//kml:Icon/kml:href", ns).text
    assert href == "icons/block.png"

    placemark = root.find(".//kml:Point/..", ns)
    assert placemark.find("kml:styleUrl", ns).text == "#icon_B_blocks"


def test_kml_line_decoration_has_heading_and_icon_href():
    map_data = {
        "name": "Test Map",
        "lines": [
            {"from": {"id": "0P0", "lat": 0.0, "lon": 0.0}, "to": {"id": "0P1", "lat": 1.0, "lon": 0.0}, "type": "L_water-flow"},
        ],
        "nodes": [],
        "water_polygons": [],
    }

    kml_str = render_to_kml([map_data])
    root = ET.fromstring(kml_str.encode("utf-8"))
    ns = {"kml": "http://www.opengis.net/kml/2.2"}

    decoration_placemarks = [
        p for p in root.findall(".//kml:Placemark", ns)
        if p.find(".//kml:IconStyle/kml:heading", ns) is not None
    ]
    assert len(decoration_placemarks) == 1
    heading = decoration_placemarks[0].find(".//kml:IconStyle/kml:heading", ns).text
    assert float(heading) == pytest.approx(0.0)
    href = decoration_placemarks[0].find(".//kml:Icon/kml:href", ns).text
    assert href == "icons/water_flow_chevron.png"


def test_kmz_bundles_icon_pngs(tmp_path):
    map_data = {"name": "Test Map", "lines": [], "nodes": [], "water_polygons": []}
    out_file = str(tmp_path / "test.kmz")
    render_to_kmz([map_data], out_file)

    with zipfile.ZipFile(out_file, "r") as zf:
        names = zf.namelist()
        assert "icons/block.png" in names
        assert "icons/water_flow_chevron.png" in names
```

Add the needed imports at the top of `tests/test_kmz_export.py` (alongside the existing `import xml.etree.ElementTree as ET` / `import zipfile`):

```python
import pytest
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_kmz_export.py -v`
Expected: FAIL — `test_kml_icon_style_uses_png_href` (no `Style id="icon_B_blocks"` exists yet — `B_blocks` isn't even in `STYLE_MAP` under the old code, and today's `styleUrl` is hardcoded to `#point_{ntype}`), `test_kml_line_decoration_has_heading_and_icon_href` (no decoration placemarks emitted), `test_kmz_bundles_icon_pngs` (`icons/block.png` not in the zip)

- [ ] **Step 3: Implement icon styles, decoration placemarks, and KMZ bundling**

In `cave_sketch/backend_renders/google_earth.py`, add `Path` to the imports (top of file):

```python
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List
from xml.dom import minidom

from cave_sketch.features.chaining import chain_segments_by_type
from cave_sketch.features.render_features import extract_features_from_json
from cave_sketch.style import STYLE_MAP

_ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"
```

In the `render_to_kml` Style-generation loop, add an `"icon"` branch before the existing `"point"` branch (the loop currently has `if sdict.get("type") == "area": ... elif sdict.get("type") == "point": ... else: # line`):

```python
        if sdict.get("type") == "area":
            # (unchanged)
            line_style = ET.SubElement(style, "LineStyle")
            ET.SubElement(line_style, "color").text = rgba_to_kml_color(
                str(sdict.get("color", "blue")), 1.0
            )
            ET.SubElement(line_style, "width").text = "1"

            poly_style = ET.SubElement(style, "PolyStyle")
            ET.SubElement(poly_style, "color").text = rgba_to_kml_color(
                str(sdict.get("color", "blue")), float(str(sdict.get("alpha", 0.3)))
            )
            ET.SubElement(poly_style, "fill").text = "1"
            ET.SubElement(poly_style, "outline").text = "1"
        elif sdict.get("type") == "icon":
            icon_style = ET.SubElement(style, "IconStyle")
            icon_el = ET.SubElement(icon_style, "Icon")
            ET.SubElement(icon_el, "href").text = f"icons/{sdict['icon']}.png"
            ET.SubElement(icon_style, "scale").text = str(float(sdict.get("size", 4)) / 4)
        elif sdict.get("type") == "point":
            icon_style = ET.SubElement(style, "IconStyle")
            color_kml = rgba_to_kml_color(str(sdict.get("color", "black")))
            ET.SubElement(icon_style, "color").text = color_kml
            scale_str = str(float(str(sdict.get("markersize", 4))) / 4)
            ET.SubElement(icon_style, "scale").text = scale_str
        else: # line
            line_style = ET.SubElement(style, "LineStyle")
            ET.SubElement(line_style, "color").text = rgba_to_kml_color(
                str(sdict.get("color", "black"))
            )
            ET.SubElement(line_style, "width").text = str(sdict.get("weight", 2))
```

In the `# --- POINTS ---` block (inside the `for map_data in map_list:` loop), change the hardcoded `styleUrl` to be type-aware:

```python
        for n in nodes_list:
            ntype = n.get("type", "")
            style_info = STYLE_MAP.get(ntype)
            if style_info and style_info.get("type") in ("point", "icon"):
                placemark = ET.SubElement(folder, "Placemark")
                ET.SubElement(placemark, "name").text = str(n.get("id", ""))
                ET.SubElement(placemark, "styleUrl").text = f"#{style_info['type']}_{ntype}"
                point = ET.SubElement(placemark, "Point")
                lat, lon = n["lat"], n["lon"]
                ET.SubElement(point, "coordinates").text = f"{lon},{lat},0"
```

Add a `# --- LINE DECORATIONS ---` block right after the `# --- POINTS ---` block, still inside the `for map_data in map_list:` loop:

```python
        # --- LINE DECORATIONS ---
        for dec in features.get("line_decorations", []):
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = dec.get("icon", "")
            dec_style = ET.SubElement(placemark, "Style")
            dec_icon_style = ET.SubElement(dec_style, "IconStyle")
            dec_icon_el = ET.SubElement(dec_icon_style, "Icon")
            ET.SubElement(dec_icon_el, "href").text = f"icons/{dec['icon']}.png"
            ET.SubElement(dec_icon_style, "scale").text = str(float(dec.get("size", 4)) / 4)
            ET.SubElement(dec_icon_style, "heading").text = str(dec.get("bearing_deg", 0.0))
            point = ET.SubElement(placemark, "Point")
            lat, lon = dec["coords"]
            ET.SubElement(point, "coordinates").text = f"{lon},{lat},0"
```

Finally, update `render_to_kmz` to bundle the icon PNGs:

```python
def render_to_kmz(
    map_list: List[Dict[str, Any]], output_path: str, layer_name: str = "All Maps"
) -> str:
    """
    Generate KML and zip it into a KMZ file, bundling any icon PNGs
    referenced by STYLE_MAP's icon-type entries and line decorations.
    """
    kml_str = render_to_kml(map_list, layer_name)
    icon_names = {sdict["icon"] for sdict in STYLE_MAP.values() if sdict.get("type") == "icon"}
    icon_names |= {sdict["line_decoration"] for sdict in STYLE_MAP.values() if sdict.get("line_decoration")}

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_str)
        for icon_name in sorted(icon_names):
            png_path = _ICONS_DIR / f"{icon_name}.png"
            if png_path.exists():
                zf.write(png_path, f"icons/{icon_name}.png")
    return output_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_kmz_export.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/backend_renders/google_earth.py tests/test_kmz_export.py
git commit -m "feat(kml-backend): use rasterized icon PNGs and per-placemark heading rotation"
```

---

## Task 14: Fix the stale `"BLOCK"` placeholder in the existing KMZ test

**Files:**
- Modify: `tests/test_kmz_export.py:18`

**Interfaces:**
- Consumes: `STYLE_MAP["B_blocks"]` (Task 3) replacing the now-removed `STYLE_MAP["BLOCK"]`.
- Produces: no behavior change to production code — a pre-existing test kept passing for the right reason.

- [ ] **Step 1: Run the existing test to confirm it currently fails for the right reason**

Run: `pytest tests/test_kmz_export.py::test_compact_kml_export -v`
Expected (after Task 3's rename lands): FAIL — `assert len(point_placemarks) == 1` fails because type `"BLOCK"` no longer matches any `STYLE_MAP` entry, so the node is silently skipped.

- [ ] **Step 2: Fix the placeholder type**

In `tests/test_kmz_export.py`, line 18, change:

```python
            {"id": "5", "lat": 5.0, "lon": 5.0, "type": "BLOCK"},
```

to:

```python
            {"id": "5", "lat": 5.0, "lon": 5.0, "type": "B_blocks"},
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_kmz_export.py::test_compact_kml_export -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_kmz_export.py
git commit -m "test(kmz): update placeholder point type from removed BLOCK to B_blocks"
```

---

## Task 15: Full test suite, real-fixture smoke test, and Android verification

**Files:** none (verification only)

**Interfaces:**
- Consumes: everything from Tasks 1-14.
- Produces: confidence that the whole feature works end-to-end on real data, on both platforms.

- [ ] **Step 1: Run the full test suite**

Run: `pytest -v`
Expected: PASS, including every test added in Tasks 1-14 and no regressions in the pre-existing suite.

- [ ] **Step 2: Write a throwaway smoke-test script exercising the real fixture DXFs**

Create `/tmp/smoke_test_icons.py` (not committed — scratch verification only):

```python
from pathlib import Path

from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.survey.survey import draw_survey
from cave_sketch.satellite_view import draw_map

for name in ["val_cont_06-0p.dxf", "val_mul_4-1p.dxf", "grotta_mittelbergferner-1p.dxf"]:
    dxf_path = Path(name)
    csv_path = Path(f"/tmp/{dxf_path.stem}.csv")
    parse_dxf(dxf_path, csv_path)

    pdf_path = f"/tmp/{dxf_path.stem}.pdf"
    draw_survey(
        title=dxf_path.stem,
        rule_length=20,
        csv_map_path=str(csv_path),
        output_path=pdf_path,
    )
    print(f"wrote {pdf_path}")

    html_path = f"/tmp/{dxf_path.stem}.html"
    draw_map(
        map_path=str(csv_path),
        gps_points=[{"station": "0", "lat": 46.0, "lon": 11.0}],
        output_path=html_path,
        map_name=dxf_path.stem,
    )
    print(f"wrote {html_path} and its .kmz")
```

Run: `python /tmp/smoke_test_icons.py`
Expected: no exceptions; 3 PDFs and 3 HTML+KMZ pairs written under `/tmp/`. (If a given fixture has no station matching `"0"`, adjust the `gps_points` station id to one that exists in that fixture's CSV — check with `head -5 /tmp/<name>.csv`.)

- [ ] **Step 3: Manually inspect the outputs**

Open each `/tmp/*.pdf` and confirm: `val_cont_06-0p.dxf` shows entrance/continuation icons and water-flow chevrons along its `L_water-flow` segments; `val_mul_4-1p.dxf` and `grotta_mittelbergferner-1p.dxf` show block icons and water-flow point icons where those types appear. Open each `/tmp/*.html` in a browser and confirm the same icons appear on the satellite tiles (this is the view that was previously blank for all point types — Task 6's fix). Open each `/tmp/*.kmz` in Google Earth (or unzip and inspect `doc.kml`) and confirm the icons render there too, with the water-flow chevrons rotated to match segment direction.

- [ ] **Step 4: Android verification (manual, by the maintainer)**

Build and run the Android app (`android/`), load a DXF containing these element types (e.g. copy `val_mul_4-1p.dxf` onto the device or emulator), generate a survey plot and a satellite map, and confirm the icons render identically to the webapp outputs from Step 3. This validates the Global Constraints' asset-bundling assumption (Chaquopy packaging `cave_sketch/assets/icons/*.png` correctly) — it cannot be verified from this session without Android build tooling/an emulator, so it is called out explicitly here rather than skipped silently.

- [ ] **Step 5: Clean up scratch files**

```bash
rm -f /tmp/smoke_test_icons.py /tmp/val_cont_06-0p.* /tmp/val_mul_4-1p.* /tmp/grotta_mittelbergferner-1p.*
```

(No commit — this task produces no repository changes, only verification.)
