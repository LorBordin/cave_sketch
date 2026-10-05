# Plan: DXF Icon Elements — Water-Flow, Continuation, Entrance, Blocks Fix

> **Revision 2 (2026-10-05). Self-contained: do not look for code anywhere else.**
> Every code block below was implemented and run in a scratch copy of this
> repo before this plan was written. Result: full suite green (131 → 182
> tests) and `ruff check cave_sketch tests` clean. Copy the code
> **verbatim**. Design rationale: `./spec.md`.

## How to execute this plan (read first)

1. Follow `conductor/workflow.md` for every task: mark `[~]`, Red (run the
   tests, see them fail), Green, verify, commit, attach a git note, mark
   `[x]` with the short commit SHA. Run the Phase Completion Verification
   and Checkpointing Protocol at the end of each phase.
2. Run tests with `uv run pytest -q <file>` and the whole suite with
   `uv run pytest -q`. Run lint with `uv run ruff check cave_sketch tests`
   (line length 100; long test lines are allowed only in files that start
   with `# ruff: noqa: E501`, as below).
3. "**Replace** block A **with** block B" means: find block A
   **exactly** (it occurs once), and substitute it. Do not reformat
   surrounding code.
4. Phases must be done **in order**: later phases import what earlier
   phases create.

## Global constraints (never violate)

- **Icons are line geometry in meters.** Never use KML `<IconStyle>`,
  `<Icon>`, `<href>`, PNG files, SVG, Folium `DivIcon`/`Marker`,
  matplotlib `MarkerStyle(Path)`, `scatter` or `PathPatch` for icons.
  Icons are polylines (`LineCollection` / `folium.PolyLine` / KML
  `LineString`), so they scale with zoom exactly like the walls.
- **Icon line width = `L_wall` line width.** Always use
  `ICON_LINE_WEIGHT` from `cave_sketch/style.py`
  (`= STYLE_MAP["L_wall"]["weight"]`), never a literal `3`. In
  matplotlib, icons go through the same `_scaled_linewidth()` as walls.
- **Rotation convention:** degrees, **counter-clockwise**, `0` = the
  icon's "up" points north (+Y). It equals the DXF INSERT rotation and
  `rotate_points()`'s sign.
- **Coordinate order:** feature `coords`/`strokes` are `[y, x]` (meters)
  in the DataFrame path and `[lat, lon]` in the JSON path. Shapes and
  `icon_strokes()` use `(x, y)` / `(u, v)`.
- Old CSVs have **no** `Rotation` column and merged connector rows have
  `NaN`. Treat both as `0.0` and never raise.
- `B_ice` / `B_snow` stay plain markers (`type: "point"`). Do not touch
  their styles or rendering.
- No new dependencies. No Kotlin/Android changes. No files under
  `docs/superpowers/` are touched by this track.
- matplotlib on this repo's Python 3.14 can hit `RecursionError` when
  copying tick/marker styles (seen with `plt.subplots(1, 2)` + custom
  markers). Tests use a single `plt.subplots()` and never custom markers.

## Files touched (overview)

| File | Phase | Change |
|---|---|---|
| `cave_sketch/style_icons.py` | 1 | **new**: shapes + `icon_strokes()` |
| `cave_sketch/dxf/models.py` | 2 | `SurveyPoint.rotation` |
| `cave_sketch/dxf/parser.py` | 2 | block whitelist, `Rotation`, CSV column |
| `cave_sketch/survey/renderer.py` | 2 | `_survey_to_df` gets `Rotation` |
| `cave_sketch/style.py` | 3 | remove `BLOCK`, add 5 entries, `ICON_LINE_WEIGHT` |
| `cave_sketch/geo/georef.py` | 4 | rename helper to public `meters_per_degree_wgs84` |
| `cave_sketch/features/render_features.py` | 4, 5 | `features["icons"]`, helpers, JSON points |
| `cave_sketch/backend_renders/matplotlib.py` | 6 | `_scaled_linewidth`, icon `LineCollection` |
| `cave_sketch/backend_renders/folium.py` | 7 | icon `PolyLine` |
| `cave_sketch/backend_renders/google_earth.py` | 8 | icon styles, placemarks, colors |
| `cave_sketch/survey/graphics/survey_plot.py` | 9 | view rotation → `Rotation` |
| `cave_sketch/satellite_view/map.py` | 9 | view rotation, node `rotation`, drop duplicate WGS84 helper |
| `docs/DXF_ELEMENTS.md` | 10 | mark the 5 elements supported |
| tests | 1–9 | see each phase |

---

## Phase 1: Icon shapes module [checkpoint: d4b52e6]

- [x] Task: Write the failing tests (Red)
    - [x] Create `tests/test_style_icons.py` with exactly this content:

```python
import pytest

from cave_sketch.style_icons import ICON_SHAPES, icon_strokes


@pytest.mark.parametrize("name", list(ICON_SHAPES))
def test_unit_shape_is_centered_with_largest_side_one(name):
    xs = [u for stroke in ICON_SHAPES[name] for u, _ in stroke]
    ys = [v for stroke in ICON_SHAPES[name] for _, v in stroke]
    assert max(max(xs) - min(xs), max(ys) - min(ys)) == pytest.approx(1.0, abs=1e-3)
    assert (max(xs) + min(xs)) / 2 == pytest.approx(0.0, abs=1e-3)
    assert (max(ys) + min(ys)) / 2 == pytest.approx(0.0, abs=1e-3)


@pytest.mark.parametrize("name", list(ICON_SHAPES))
def test_every_stroke_is_a_polyline(name):
    assert all(len(stroke) >= 2 for stroke in ICON_SHAPES[name])


def test_expected_icons_exist():
    assert set(ICON_SHAPES) == {
        "blocks", "entrance", "continuation", "water_flow", "water_flow_chevron"
    }


def test_icon_strokes_scales_and_translates():
    strokes = icon_strokes("entrance", 10.0, 20.0, size_m=2.0)
    apex = strokes[0][0]  # unit (0.0, 0.5)
    assert apex == pytest.approx((10.0, 21.0))


def test_icon_strokes_rotates_counter_clockwise():
    # Rotating 90 deg CCW turns "up" (+Y) into "west" (-X).
    apex = icon_strokes("entrance", 0.0, 0.0, size_m=1.0, rotation_deg=90.0)[0][0]
    assert apex == pytest.approx((-0.5, 0.0), abs=1e-9)


def test_water_flow_arrow_tip_points_up_at_rotation_zero():
    points = [p for stroke in icon_strokes("water_flow", 0.0, 0.0, 1.0) for p in stroke]
    tip = max(points, key=lambda p: p[1])
    assert tip == pytest.approx((0.0, 0.5))


def test_continuation_is_question_mark_with_dot():
    hook, dot = ICON_SHAPES["continuation"]
    assert len(hook) > len(dot) == 2
    assert max(v for _, v in dot) < min(v for _, v in hook)  # dot sits below the hook


def test_unknown_icon_raises_key_error():
    with pytest.raises(KeyError):
        icon_strokes("no_such_icon", 0.0, 0.0, 1.0)
```

    - [x] Run `uv run pytest -q tests/test_style_icons.py`. Expected: collection error
      `ModuleNotFoundError: No module named 'cave_sketch.style_icons'`.
- [x] Task: Implement `cave_sketch/style_icons.py` (Green) [cbc16a6]
    - [x] Create `cave_sketch/style_icons.py` with exactly this content. The vertex lists are
      final: they are TopoDroid's own block geometry (`blocks`, `entrance`, `continuation`)
      normalized to the unit box, plus the maintainer-requested S-arrow and chevron.

```python
"""Vector shapes for DXF point symbols, drawn as plain line strokes.

Every shape lives in a unit box: centered on (0, 0), largest side 1.0, and
the icon's "up" pointing to +Y. Rotation 0 therefore means "up = north",
the same convention as the TopoDroid DXF block definitions, whose INSERT
rotation (degrees, counter-clockwise) can be applied directly.
"""

import math
from typing import Dict, List, Tuple

Point = Tuple[float, float]
Stroke = List[Point]

ICON_SHAPES: Dict[str, List[Stroke]] = {
    # Rock block: outline plus two inner fracture lines (TopoDroid B_blocks).
    "blocks": [
        [(-0.5, -0.267), (0.367, -0.4), (0.5, -0.333), (0.433, 0.333), (-0.367, 0.4),
         (-0.5, 0.267), (-0.5, -0.267), (0.1, 0.067), (0.5, -0.333)],
        [(-0.5, 0.267), (0.1, 0.067), (0.433, 0.333)],
    ],
    # Entrance: closed triangle pointing up (TopoDroid B_entrance).
    "entrance": [
        [(0.0, 0.5), (-0.333, -0.5), (0.333, -0.5), (0.0, 0.5)],
    ],
    # Continuation: a question mark "?" -- hook + stem, then the dot (TopoDroid B_continuation).
    "continuation": [
        [(0.031, -0.192), (0.031, 0.038), (0.031, 0.069), (0.046, 0.1), (0.062, 0.131),
         (0.077, 0.162), (0.108, 0.177), (0.123, 0.208), (0.154, 0.238), (0.185, 0.269),
         (0.2, 0.3), (0.2, 0.331), (0.185, 0.377), (0.169, 0.408), (0.138, 0.454),
         (0.092, 0.469), (0.062, 0.5), (0.031, 0.5), (0.0, 0.485), (-0.031, 0.469),
         (-0.077, 0.438), (-0.108, 0.392), (-0.154, 0.362), (-0.169, 0.331), (-0.2, 0.331),
         (-0.2, 0.346)],
        [(0.031, -0.5), (0.031, -0.346)],
    ],
    # Water flow: S-shaped wiggle with an arrowhead on top; the arrow points
    # downstream (+Y at rotation 0).
    "water_flow": [
        [(0.0, -0.5), (-0.1, -0.438), (-0.173, -0.375), (-0.2, -0.312), (-0.173, -0.25),
         (-0.1, -0.188), (0.0, -0.125), (0.1, -0.062), (0.173, 0.0), (0.2, 0.062),
         (0.173, 0.125), (0.1, 0.188), (0.0, 0.25), (0.0, 0.5)],
        [(-0.2, 0.28), (0.0, 0.5), (0.2, 0.28)],
    ],
    # Chevron placed on each L_water-flow segment, apex pointing downstream.
    "water_flow_chevron": [
        [(-0.5, -0.25), (0.0, 0.25), (0.5, -0.25)],
    ],
}


def icon_strokes(
    name: str, x: float, y: float, size_m: float, rotation_deg: float = 0.0
) -> List[Stroke]:
    """Place icon ``name`` in local metric coordinates (X east, Y north).

    The unit shape is scaled so its largest side is ``size_m`` meters,
    rotated ``rotation_deg`` degrees counter-clockwise, and centered on
    ``(x, y)``. Returns one open polyline per stroke. Raises ``KeyError``
    for an unknown icon name.
    """
    theta = math.radians(rotation_deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    return [
        [
            (x + size_m * (u * cos_t - v * sin_t), y + size_m * (u * sin_t + v * cos_t))
            for u, v in stroke
        ]
        for stroke in ICON_SHAPES[name]
    ]
```

    - [x] Run `uv run pytest -q tests/test_style_icons.py`. Expected: 16 passed.
- [x] Task: Verify and commit [cbc16a6]
    - [x] `uv run pytest -q` (all green) and `uv run ruff check cave_sketch tests`.
    - [x] Commit: `feat(style): add ground-scaled vector icon shapes for DXF symbols`.

## Phase 2: Parse the missing DXF blocks and keep their rotation [checkpoint: b298b4d]

- [x] Task: Write the failing tests (Red)
    - [ ] In `tests/test_dxf_parser.py`, **replace** the imports

```python
import pandas as pd
import pytest

from cave_sketch.dxf.models import CaveSurvey
from cave_sketch.dxf.parser import parse_dxf
```

      **with**

```python
import ezdxf
import pandas as pd
import pytest

from cave_sketch.dxf.models import CaveSurvey
from cave_sketch.dxf.parser import _get_features, parse_dxf
```

    - [ ] In the same file, in `test_parse_writes_csv`, **replace**
      `assert set(df.columns) == {"Node_Id", "Links", "X", "Y", "Type"}` **with**
      `assert set(df.columns) == {"Node_Id", "Links", "X", "Y", "Type", "Rotation"}`.
    - [ ] Append to the end of `tests/test_dxf_parser.py`:

```python
def _doc_with_inserts(names_and_rotations):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for name, rotation in names_and_rotations:
        if name not in doc.blocks:
            doc.blocks.new(name=name)
        msp.add_blockref(name, (1.0, 2.0), dxfattribs={"rotation": rotation})
    return msp


def test_get_features_recognizes_all_supported_blocks():
    names = ["B_ice", "B_snow", "B_blocks", "B_water-flow", "B_continuation", "B_entrance"]
    blocks = _get_features(_doc_with_inserts([(n, 0.0) for n in names]))
    assert sorted(b["Type"] for b in blocks) == sorted(names)


def test_get_features_ignores_unsupported_blocks():
    assert _get_features(_doc_with_inserts([("B_user", 0.0)])) == []


def test_get_features_keeps_insert_rotation_normalized():
    blocks = _get_features(_doc_with_inserts([("B_water-flow", 280.5), ("B_blocks", 360.0)]))
    assert [b["Rotation"] for b in blocks] == [pytest.approx(280.5), pytest.approx(0.0)]


def test_parse_sample_v14_includes_blocks_and_oriented_water_flow():
    survey = parse_dxf(Path("tests/fixtures/sample_v14.dxf"))
    types = {p.point_type for p in survey.points}
    assert {"B_blocks", "B_water-flow"} <= types
    flows = [p for p in survey.points if p.point_type == "B_water-flow"]
    assert any(p.rotation != 0.0 for p in flows)
    assert all(0.0 <= p.rotation < 360.0 for p in survey.points)
```

    - [x] Run `uv run pytest -q tests/test_dxf_parser.py`. Expected failures: the CSV column
      `test_get_features_recognizes_all_supported_blocks` (only B_ice/B_snow found),
      `KeyError: 'Rotation'`, and the sample_v14 test (`B_blocks` missing).
- [x] Task: Implement (Green) [754172e]
    - [x] `cave_sketch/dxf/models.py`: in `SurveyPoint`, **replace**

```python
    point_type: str = "station"
    links: List[str] = field(default_factory=list)
```

      **with**

```python
    point_type: str = "station"
    links: List[str] = field(default_factory=list)
    # DXF INSERT rotation in degrees, counter-clockwise (0 for non-block points).
    rotation: float = 0.0
```

    - [ ] `cave_sketch/dxf/parser.py`, function `_get_features`: **replace**
      `    valid_block_names = {"B_ice", "BLOCK", "B_snow"}` **with**

```python
    valid_block_names = {
        "B_ice", "B_snow", "B_blocks", "B_water-flow", "B_continuation", "B_entrance"
    }
```

      and in the same function **replace**

```python
                    "Type": entity.dxf.name,
                }
```

      **with**

```python
                    "Type": entity.dxf.name,
                    "Rotation": float(entity.dxf.rotation) % 360.0,
                }
```

    - [ ] `cave_sketch/dxf/parser.py`, function `parse_dxf`, block loop (`# Process blocks`):
      **replace**

```python
                point_type=block["Type"],
                links=[],
            )
```

      **with**

```python
                point_type=block["Type"],
                links=[],
                rotation=block["Rotation"],
            )
```

    - [ ] In **both** `cave_sketch/dxf/parser.py::_export_to_csv` **and**
      `cave_sketch/survey/renderer.py::_survey_to_df`, **replace**
      `        data.append([p.id, links_str, p.x, p.y, p.point_type])` **with**
      `        data.append([p.id, links_str, p.x, p.y, p.point_type, p.rotation])`, and
      **replace** `columns=["Node_Id", "Links", "X", "Y", "Type"])` **with**
      `columns=["Node_Id", "Links", "X", "Y", "Type", "Rotation"])`.
    - [x] Run `uv run pytest -q tests/test_dxf_parser.py tests/test_dxf_compatibility.py`.
      Expected: all pass.
- [x] Task: Verify and commit [754172e]
    - [x] `uv run pytest -q` and `uv run ruff check cave_sketch tests`.
    - [x] Commit: `fix(dxf): parse B_blocks/B_water-flow/B_continuation/B_entrance and keep rotation`.
      Commit body: these four block types were silently dropped by the parser because the
      whitelist contained the non-existent name `BLOCK`. The INSERT rotation is now stored in a
      new `Rotation` CSV column (missing in old CSVs, treated as 0 downstream).

## Phase 3: `STYLE_MAP` entries and `ICON_LINE_WEIGHT` [checkpoint: c231428]

- [x] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_style.py`:

```python
from matplotlib.colors import is_color_like

from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP
from cave_sketch.style_icons import ICON_SHAPES

ICON_TYPES = ["B_blocks", "B_continuation", "B_entrance", "B_water-flow"]


def test_block_placeholder_is_replaced_by_real_dxf_name():
    assert "BLOCK" not in STYLE_MAP
    assert STYLE_MAP["B_blocks"]["type"] == "icon"


def test_icon_types_reference_existing_shapes_with_positive_size():
    expected = {
        "B_blocks": "blocks",
        "B_continuation": "continuation",
        "B_entrance": "entrance",
        "B_water-flow": "water_flow",
    }
    for typ, icon in expected.items():
        style = STYLE_MAP[typ]
        assert style["type"] == "icon"
        assert style["icon"] == icon and icon in ICON_SHAPES
        assert style["size_m"] > 0


def test_water_flow_line_has_chevron_decoration():
    style = STYLE_MAP["L_water-flow"]
    assert style["type"] == "line"
    assert style["line_decoration"] == "water_flow_chevron"
    assert style["line_decoration"] in ICON_SHAPES
    assert style["decoration_size_m"] > 0


def test_icon_line_weight_matches_wall():
    assert ICON_LINE_WEIGHT == STYLE_MAP["L_wall"]["weight"]


def test_ice_and_snow_stay_plain_markers():
    assert STYLE_MAP["B_ice"]["type"] == "point"
    assert STYLE_MAP["B_snow"]["type"] == "point"


def test_every_style_color_is_renderable():
    for style in STYLE_MAP.values():
        assert is_color_like(style["color"]), style["color"]
```

    - [x] Run `uv run pytest -q tests/test_style.py`. Expected: `ImportError: cannot import name
      'ICON_LINE_WEIGHT'`.
- [x] Task: Implement (Green) [e83f86e]
    - [x] `cave_sketch/style.py`: **replace** the whole `"BLOCK"` entry

```python
    "BLOCK": {
        "color": "saddlebrown",
        "marker": "o",  # square marker
        "markersize": 4,
        "type": "point",
    },
```

      **with**

```python
    "L_water-flow": {
        "color": "steelblue",
        "linestyle": "solid",
        "type": "line",
        "weight": 1,
        "line_decoration": "water_flow_chevron",  # one chevron per segment
        "decoration_size_m": 1.0,
    },
    "B_blocks": {"color": "tan", "icon": "blocks", "size_m": 1.5, "type": "icon"},
    "B_continuation": {"color": "firebrick", "icon": "continuation", "size_m": 1.5, "type": "icon"},
    "B_entrance": {"color": "firebrick", "icon": "entrance", "size_m": 1.5, "type": "icon"},
    "B_water-flow": {"color": "mediumpurple", "icon": "water_flow", "size_m": 1.5, "type": "icon"},
```

    - [ ] Append to the end of `cave_sketch/style.py` (after the closing `}` of `STYLE_MAP`):

```python

# Icons are stroked exactly as thick as walls, in every backend.
ICON_LINE_WEIGHT = STYLE_MAP["L_wall"]["weight"]
```

    - [ ] Removing `BLOCK` breaks `tests/test_kmz_export.py::test_compact_kml_export`, which
      uses `BLOCK` as a placeholder *plain point*. In `tests/test_kmz_export.py` **replace**
      `{"id": "5", "lat": 5.0, "lon": 5.0, "type": "BLOCK"},` **with**
      `{"id": "5", "lat": 5.0, "lon": 5.0, "type": "B_ice"},`. Do **not** use `B_blocks`:
      it is now an icon (MultiGeometry), so the test's point/wall counts would be wrong.
    - [x] Run `uv run pytest -q tests/test_style.py tests/test_kmz_export.py`. Expected: all pass.
- [x] Task: Verify and commit [e83f86e]
    - [x] `uv run pytest -q` and `uv run ruff check cave_sketch tests`.
    - [x] Commit: `feat(style): add icon styles for blocks, continuation, entrance, water-flow`.

## Phase 4: Icons and water-flow chevrons from the survey DataFrame (survey plot data) [checkpoint: de14143]

- [x] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_render_icons_df.py`:

```python
# ruff: noqa: E501
import pandas as pd
import pytest

from cave_sketch.features.render_features import extract_features_from_df
from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP
from cave_sketch.style_icons import ICON_SHAPES


def _xy_points(icon):
    """All stroke vertices of a DataFrame-path icon as (x, y); coords are stored [y, x]."""
    return [(px, py) for stroke in icon["strokes"] for py, px in stroke]


def test_df_icon_point_becomes_ground_sized_strokes():
    df = pd.DataFrame([
        {"Node_Id": "B_blocks_0", "X": 10.0, "Y": 20.0, "Links": "-", "Type": "B_blocks", "Rotation": 0.0},
    ])
    features = extract_features_from_df(df)
    assert features["points"] == []
    (icon,) = features["icons"]
    assert icon["type"] == "B_blocks"
    assert icon["color"] == STYLE_MAP["B_blocks"]["color"]
    assert icon["weight"] == ICON_LINE_WEIGHT == STYLE_MAP["L_wall"]["weight"]
    assert len(icon["strokes"]) == len(ICON_SHAPES["blocks"])
    xs = [x for x, _ in _xy_points(icon)]
    ys = [y for _, y in _xy_points(icon)]
    size = STYLE_MAP["B_blocks"]["size_m"]
    assert max(max(xs) - min(xs), max(ys) - min(ys)) == pytest.approx(size, abs=1e-2)
    assert (max(xs) + min(xs)) / 2 == pytest.approx(10.0, abs=1e-2)
    assert (max(ys) + min(ys)) / 2 == pytest.approx(20.0, abs=1e-2)


def test_df_icon_uses_rotation_column():
    # Rotation 270 CCW turns the arrow from north (+Y) to east (+X).
    df = pd.DataFrame([
        {"Node_Id": "B_water-flow_0", "X": 0.0, "Y": 0.0, "Links": "-", "Type": "B_water-flow", "Rotation": 270.0},
    ])
    (icon,) = extract_features_from_df(df)["icons"]
    tip = max(_xy_points(icon), key=lambda p: p[0])
    assert tip == pytest.approx((STYLE_MAP["B_water-flow"]["size_m"] / 2, 0.0), abs=1e-9)


@pytest.mark.parametrize("rotation", [None, float("nan")])
def test_df_icon_missing_or_nan_rotation_means_zero(rotation):
    row = {"Node_Id": "B_entrance_0", "X": 0.0, "Y": 0.0, "Links": "-", "Type": "B_entrance"}
    if rotation is not None:
        row["Rotation"] = rotation
    (icon,) = extract_features_from_df(pd.DataFrame([row]))["icons"]
    tip = max(_xy_points(icon), key=lambda p: p[1])
    assert tip == pytest.approx((0.0, STYLE_MAP["B_entrance"]["size_m"] / 2))


def test_df_plain_marker_points_unchanged():
    df = pd.DataFrame([{"Node_Id": "B_ice_0", "X": 1.0, "Y": 2.0, "Links": "-", "Type": "B_ice"}])
    features = extract_features_from_df(df)
    assert features["icons"] == []
    (point,) = features["points"]
    assert point["marker"] == STYLE_MAP["B_ice"]["marker"]


def _water_flow_df(rows):
    return pd.DataFrame(
        [{"Node_Id": nid, "X": x, "Y": y, "Links": links, "Type": "L_water-flow"} for nid, x, y, links in rows]
    )


def test_df_water_flow_line_gets_one_chevron_per_segment_pointing_downstream():
    df = _water_flow_df([
        ("0P0", 0.0, 0.0, "0P1"),
        ("0P1", 10.0, 0.0, "0P0-0P2"),
        ("0P2", 10.0, 10.0, "0P1"),
    ])
    features = extract_features_from_df(df)
    assert len(features["lines"]) == 4  # unchanged: both directions are still drawn
    chevrons = features["icons"]
    assert len(chevrons) == 2
    # Segment 1 runs east: chevron apex (unit (0, 0.25)) is its easternmost vertex.
    apex1 = chevrons[0]["strokes"][0][1]
    assert apex1 == pytest.approx([0.0, 5.0 + 0.25 * STYLE_MAP["L_water-flow"]["decoration_size_m"]])
    # Segment 2 runs north: apex is its northernmost vertex.
    apex2 = chevrons[1]["strokes"][0][1]
    assert apex2 == pytest.approx([5.0 + 0.25 * STYLE_MAP["L_water-flow"]["decoration_size_m"], 10.0])
    assert all(c["weight"] == ICON_LINE_WEIGHT for c in chevrons)
    assert all(c["color"] == STYLE_MAP["L_water-flow"]["color"] for c in chevrons)


def test_df_single_segment_gets_exactly_one_chevron():
    df = _water_flow_df([("3P0", 0.0, 0.0, "3P1"), ("3P1", 0.0, 5.0, "3P0")])
    assert len(extract_features_from_df(df)["icons"]) == 1


def test_df_two_polylines_do_not_interfere():
    df = _water_flow_df([
        ("0P0", 0.0, 0.0, "0P1"), ("0P1", 1.0, 0.0, "0P0"),
        ("1P0", 0.0, 5.0, "1P1"), ("1P1", 1.0, 5.0, "1P0"),
    ])
    assert len(extract_features_from_df(df)["icons"]) == 2


def test_df_missing_neighbor_is_skipped():
    df = _water_flow_df([("0P0", 0.0, 0.0, "0P1")])
    assert extract_features_from_df(df)["icons"] == []


def test_df_other_lines_get_no_decoration():
    df = pd.DataFrame([
        {"Node_Id": "0P0", "X": 0.0, "Y": 0.0, "Links": "0P1", "Type": "L_wall"},
        {"Node_Id": "0P1", "X": 1.0, "Y": 0.0, "Links": "0P0", "Type": "L_wall"},
    ])
    assert extract_features_from_df(df)["icons"] == []
```

    - [x] Run `uv run pytest -q tests/test_render_icons_df.py`. Expected: failures with
      `KeyError: 'icons'`.
- [x] Task: Make the WGS84 helper public (needed here and in Phase 5) [d6c38a5]
    - [x] `cave_sketch/geo/georef.py`: rename `def _meters_per_degree_wgs84(` to
      `def meters_per_degree_wgs84(` and update its one call site in the same file
      (`= _meters_per_degree_wgs84(` → `= meters_per_degree_wgs84(`). Do **not** touch the
      private copy in `satellite_view/map.py` yet (Phase 9 removes it).
- [x] Task: Implement (Green) in `cave_sketch/features/render_features.py` [d6c38a5]
    - [ ] **Replace** the module header

```python
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from cave_sketch.style import STYLE_MAP
```

      **with** (shared helpers, also used by Phase 5)

```python
import math
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from cave_sketch.geo.georef import meters_per_degree_wgs84
from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP
from cave_sketch.style_icons import icon_strokes

_POLYLINE_NODE_RE = re.compile(r"^(\d+)P(\d+)$")


def _is_forward_segment(from_id: Any, to_id: Any) -> bool:
    """True when ``from_id -> to_id`` is one step along a DXF polyline in drawing
    order (``"{i}P{j}" -> "{i}P{j+1}"``).

    Every polyline segment appears twice in the data (once from each end).
    Keeping only the forward copy gives exactly one decoration per segment,
    oriented the way the line was drawn (TopoDroid draws water-flow lines
    downstream).
    """
    a = _POLYLINE_NODE_RE.match(str(from_id))
    b = _POLYLINE_NODE_RE.match(str(to_id))
    return bool(a and b and a.group(1) == b.group(1) and int(b.group(2)) == int(a.group(2)) + 1)


def _rotation_value(value: Any) -> float:
    """Rotation from a CSV/JSON cell; missing or NaN (old CSVs, merge connectors) means 0."""
    try:
        rotation = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(rotation) else rotation


def _heading_deg(dx: float, dy: float) -> float:
    """Icon rotation (CCW degrees, 0 = icon up along +Y) pointing the icon along (dx, dy)."""
    return math.degrees(math.atan2(dy, dx)) - 90.0


def _icon_strokes_latlon(
    name: str, lat: float, lon: float, size_m: float, rotation_deg: float
) -> List[List[List[float]]]:
    """Icon strokes as ``[lat, lon]`` polylines, sized in meters on the ground."""
    m_per_deg_lat, m_per_deg_lon = meters_per_degree_wgs84(lat)
    return [
        [[lat + dy / m_per_deg_lat, lon + dx / m_per_deg_lon] for dx, dy in stroke]
        for stroke in icon_strokes(name, 0.0, 0.0, size_m, rotation_deg)
    ]


def _icon_feature(strokes: list, typ: str, color: str, popup: str) -> Dict[str, Any]:
    return {
        "type": typ,
        "strokes": strokes,
        "color": color,
        "weight": ICON_LINE_WEIGHT,
        "popup": popup,
    }
```

    - [ ] In `extract_features_from_df`, **replace**
      `    features: Dict[str, list] = {"lines": [], "polygons": [], "points": []}  # <-- added points`
      **with**
      `    features: Dict[str, list] = {"lines": [], "polygons": [], "points": [], "icons": []}`.
    - [ ] In `extract_features_from_df`, **replace**

```python
        # --- New block: handle standalone point features ---
        style_type = STYLE_MAP.get(typ, {}).get("type", "line")
        if style_type == "point":
```

      **with**

```python
        style_type = STYLE_MAP.get(typ, {}).get("type", "line")

        # --- Icon features (B_blocks, B_water-flow, ...), sized in meters ---
        if style_type == "icon":
            style = STYLE_MAP[typ]
            rotation = _rotation_value(getattr(row, "Rotation", 0.0))
            strokes = icon_strokes(style["icon"], x, y, style["size_m"], rotation)
            features["icons"].append(
                _icon_feature(
                    [[[py, px] for px, py in stroke] for stroke in strokes],
                    typ,
                    style["color"],
                    f"{typ} ({nid})",
                )
            )
            continue

        # --- Standalone point features (B_ice, B_snow) ---
        if style_type == "point":
```

    - [ ] In `extract_features_from_df`, inside `if style_type == "line":`, **replace**

```python
                            "popup": f"{typ} ({nid}-{nbr})",
                        }
                    )
```

      **with**

```python
                            "popup": f"{typ} ({nid}-{nbr})",
                        }
                    )

                    decoration = style.get("line_decoration")
                    if decoration and _is_forward_segment(nid, nbr):
                        strokes = icon_strokes(
                            decoration,
                            (x + x2) / 2,
                            (y + y2) / 2,
                            style["decoration_size_m"],
                            _heading_deg(x2 - x, y2 - y),
                        )
                        features["icons"].append(
                            _icon_feature(
                                [[[py, px] for px, py in stroke] for stroke in strokes],
                                typ,
                                style["color"],
                                f"{typ} ({nid}-{nbr})",
                            )
                        )
```

    - [x] Run `uv run pytest -q tests/test_render_icons_df.py tests/test_render_features.py`.
      Expected: all pass (the old tests still see 4 wall lines and no points).
- [x] Task: Verify and commit [d6c38a5]
    - [x] `uv run pytest -q` and `uv run ruff check cave_sketch tests`.
    - [x] Commit: `feat(render-features): emit meter-sized icons and water-flow chevrons from survey data`.

## Phase 5: Points, icons and chevrons from the map JSON (satellite HTML + KMZ data) [checkpoint: 58b872f]

Also fixes a pre-existing bug: `extract_features_from_json` never returned
`"points"`, so the Folium map showed **no** B_ice/B_snow markers at all.

- [x] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_render_icons_json.py`:

```python
# ruff: noqa: E501
import math

import pytest

from cave_sketch.features.render_features import extract_features_from_json
from cave_sketch.geo.georef import meters_per_degree_wgs84
from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP

LAT, LON = 46.5, 11.3


def _ground_extent_m(icon):
    m_lat, m_lon = meters_per_degree_wgs84(LAT)
    lats = [lat for stroke in icon["strokes"] for lat, _ in stroke]
    lons = [lon for stroke in icon["strokes"] for _, lon in stroke]
    return (max(lons) - min(lons)) * m_lon, (max(lats) - min(lats)) * m_lat


def test_json_dict_nodes_produce_icons_and_points():
    map_data = {
        "name": "M",
        "lines": [],
        "nodes": {
            "B_blocks_0": {"lat": LAT, "lon": LON, "type": "B_blocks", "rotation": 0.0},
            "B_ice_0": {"lat": LAT, "lon": LON, "type": "B_ice"},
            "0P0": {"lat": LAT, "lon": LON, "type": "L_wall"},
        },
    }
    features = extract_features_from_json(map_data)
    (icon,) = features["icons"]
    assert icon["type"] == "B_blocks" and icon["weight"] == ICON_LINE_WEIGHT
    width_m, height_m = _ground_extent_m(icon)
    assert max(width_m, height_m) == pytest.approx(STYLE_MAP["B_blocks"]["size_m"], abs=1e-2)
    (point,) = features["points"]
    assert point["coords"] == [LAT, LON]


def test_json_list_nodes_and_rotation():
    map_data = {
        "name": "M",
        "lines": [],
        "nodes": [{"id": "w", "lat": LAT, "lon": LON, "type": "B_water-flow", "rotation": 270.0}],
    }
    (icon,) = extract_features_from_json(map_data)["icons"]
    tip = max((p for stroke in icon["strokes"] for p in stroke), key=lambda p: p[1])  # easternmost
    assert tip[0] == pytest.approx(LAT, abs=1e-9)
    assert tip[1] > LON


def test_json_without_nodes_key():
    features = extract_features_from_json({"name": "M", "lines": []})
    assert features["points"] == [] and features["icons"] == []


def test_json_water_flow_both_directions_give_one_northward_chevron():
    a = {"id": "0P0", "lat": LAT, "lon": LON}
    b = {"id": "0P1", "lat": LAT + 0.0001, "lon": LON}
    map_data = {
        "name": "M",
        "lines": [
            {"from": a, "to": b, "type": "L_water-flow"},
            {"from": b, "to": a, "type": "L_water-flow"},
        ],
        "nodes": {},
    }
    (chevron,) = extract_features_from_json(map_data)["icons"]
    apex = chevron["strokes"][0][1]
    assert apex[1] == pytest.approx(LON, abs=1e-12)
    assert apex[0] > LAT + 0.00005  # north of the segment midpoint
    assert math.isclose(max(_ground_extent_m(chevron)), STYLE_MAP["L_water-flow"]["decoration_size_m"], abs_tol=1e-2)
```

    - [x] Run `uv run pytest -q tests/test_render_icons_json.py`. Expected: `KeyError: 'icons'`.
- [x] Task: Implement (Green) in `cave_sketch/features/render_features.py` [a08f8c6]
    - [x] In `extract_features_from_json`, **replace**

```python
    Extract abstract features (lines, polygons) with styles,
    independent of rendering backend.
    """
    features: Dict[str, List[Dict[str, Any]]] = {"lines": [], "polygons": []}
```

      **with**

```python
    Extract abstract features (lines, polygons, points, icons) with styles,
    independent of rendering backend. Coordinates are ``[lat, lon]``.
    """
    features: Dict[str, List[Dict[str, Any]]] = {
        "lines": [],
        "polygons": [],
        "points": [],
        "icons": [],
    }
```

    - [ ] At the end of `extract_features_from_json`, **replace**

```python
                "popup": f"{map_data['name']}: {line_type}",
            }
        )

    return features
```

      **with**

```python
                "popup": f"{map_data['name']}: {line_type}",
            }
        )

        decoration = style.get("line_decoration")
        if decoration and _is_forward_segment(line["from"].get("id"), line["to"].get("id")):
            mid_lat = (pt_from[0] + pt_to[0]) / 2
            mid_lon = (pt_from[1] + pt_to[1]) / 2
            m_per_deg_lat, m_per_deg_lon = meters_per_degree_wgs84(mid_lat)
            heading = _heading_deg(
                (pt_to[1] - pt_from[1]) * m_per_deg_lon, (pt_to[0] - pt_from[0]) * m_per_deg_lat
            )
            strokes = _icon_strokes_latlon(
                decoration, mid_lat, mid_lon, style["decoration_size_m"], heading
            )
            features["icons"].append(
                _icon_feature(strokes, line_type, color, f"{map_data['name']}: {line_type}")
            )

    # Points and icons (B_* blocks)
    nodes = map_data.get("nodes", {})
    node_list = nodes if isinstance(nodes, list) else [{"id": k, **v} for k, v in nodes.items()]
    for node in node_list:
        node_type = node.get("type", "")
        style = STYLE_MAP.get(node_type, {})
        popup = f"{map_data.get('name', '')}: {node_type} ({node.get('id', '')})"
        if style.get("type") == "point":
            features["points"].append(
                {
                    "coords": [node["lat"], node["lon"]],
                    "color": style["color"],
                    "marker": style.get("marker", "o"),
                    "size": style.get("markersize", 6),
                    "popup": popup,
                }
            )
        elif style.get("type") == "icon":
            strokes = _icon_strokes_latlon(
                style["icon"],
                node["lat"],
                node["lon"],
                style["size_m"],
                _rotation_value(node.get("rotation", 0.0)),
            )
            features["icons"].append(_icon_feature(strokes, node_type, style["color"], popup))

    return features
```

    - [x] Run `uv run pytest -q tests/test_render_icons_json.py tests/test_kmz_export.py`.
      Expected: all pass.
- [x] Task: Verify and commit [a08f8c6]
    - [x] `uv run pytest -q` and `uv run ruff check cave_sketch tests`.
    - [x] Commit: `feat(render-features): build points, icons and chevrons from map JSON`.
      Commit body: also fixes the Folium satellite view showing zero point markers, because
      this function never built a `points` list.

## Phase 6: Render icons in matplotlib (survey plot) [checkpoint: e4426d1]

- [x] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_icons_matplotlib.py`:

```python
# ruff: noqa: E501
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.collections import LineCollection

from cave_sketch.backend_renders import render_to_matplotlib
from cave_sketch.features.render_features import extract_features_from_df
from cave_sketch.style import STYLE_MAP
from cave_sketch.style_icons import ICON_SHAPES


def _df_wall_and_block():
    return pd.DataFrame([
        {"Node_Id": "0P0", "X": 0.0, "Y": 0.0, "Links": "0P1", "Type": "L_wall", "Rotation": 0.0},
        {"Node_Id": "0P1", "X": 10.0, "Y": 0.0, "Links": "0P0", "Type": "L_wall", "Rotation": 0.0},
        {"Node_Id": "B_blocks_0", "X": 5.0, "Y": 5.0, "Links": "-", "Type": "B_blocks", "Rotation": 0.0},
    ])


@pytest.mark.parametrize("config", [None, {"line_width_zoom": 10, "ref_scale": 2.0}])
def test_matplotlib_icon_linewidth_equals_wall_linewidth(config):
    fig, ax = plt.subplots()
    render_to_matplotlib(extract_features_from_df(_df_wall_and_block()), ax, config=config)
    walls, icons = [c for c in ax.collections if isinstance(c, LineCollection)]
    assert len(icons.get_segments()) == len(ICON_SHAPES["blocks"])
    assert set(icons.get_linewidths()) == {walls.get_linewidths()[0]}
    assert icons.get_zorder() > walls.get_zorder()
    plt.close(fig)


def test_matplotlib_icon_strokes_are_in_data_coordinates():
    fig, ax = plt.subplots()
    render_to_matplotlib(extract_features_from_df(_df_wall_and_block()), ax)
    icons = [c for c in ax.collections if isinstance(c, LineCollection)][1]
    xs = [x for seg in icons.get_segments() for x, _ in seg]
    assert min(xs) == pytest.approx(5.0 - STYLE_MAP["B_blocks"]["size_m"] / 2, abs=1e-2)
    plt.close(fig)
```

    - [x] Run `uv run pytest -q tests/test_icons_matplotlib.py`. Expected: `ValueError: not
      enough values to unpack` (only the wall `LineCollection` exists).
- [x] Task: Implement (Green) in `cave_sketch/backend_renders/matplotlib.py` [7d03358]
    - [x] **Replace**

```python
from matplotlib.patches import Polygon as MplPolygon

```

      **with**

```python
from matplotlib.patches import Polygon as MplPolygon


def _scaled_linewidth(weight: float, zoom_factor: float, ref_scale: float) -> float:
    """Line width in points, shared by lines and icons so icons match walls."""
    return float(np.clip(weight * zoom_factor / ref_scale, 0.2, 4))

```

    - [ ] **Replace**

```python
        base_weight = line.get("weight", 1)
        lw = base_weight * zoom_factor / ref_scale
        lw = np.clip(lw, 0.2, 4)
        linewidths.append(lw)
```

      **with**

```python
        linewidths.append(_scaled_linewidth(line.get("weight", 1), zoom_factor, ref_scale))
```

    - [ ] **Replace**

```python
        ax.add_collection(lc)
        ax.autoscale_view()

    # ---- POINTS (B_ice, BLOCK, etc.) ----
```

      **with**

```python
        ax.add_collection(lc)
        ax.autoscale_view()

    # ---- ICONS (B_blocks, B_water-flow, ..., L_water-flow chevrons) ----
    # Drawn in data units (meters), stroked exactly like walls.
    icon_segments = []
    icon_colors = []
    icon_linewidths = []
    for icon in features.get("icons", []):
        lw = _scaled_linewidth(icon["weight"], zoom_factor, ref_scale)
        for stroke in icon["strokes"]:
            icon_segments.append([(px, py) for py, px in stroke])  # [y, x] -> (x, y)
            icon_colors.append(icon["color"])
            icon_linewidths.append(lw)

    if icon_segments:
        ax.add_collection(
            LineCollection(
                icon_segments,
                colors=icon_colors,
                linewidths=icon_linewidths,
                capstyle="round",
                joinstyle="round",
                alpha=0.9,
                zorder=3,
            )
        )
        ax.autoscale_view()

    # ---- POINTS (B_ice, B_snow) ----
```

    - [x] Run `uv run pytest -q tests/test_icons_matplotlib.py tests/test_render_regression.py`.
      Expected: all pass (the regression fixture `sample.dxf` has no blocks, so the baselines are
      unchanged).
- [x] Task: Verify and commit [7d03358]
    - [x] `uv run pytest -q` and `uv run ruff check cave_sketch tests`.
    - [x] Commit: `feat(matplotlib-backend): draw icons as meter-sized strokes with wall line width`.

## Phase 7: Render icons in Folium (satellite HTML) [checkpoint: 1e998f1]

- [x] Task: Write the failing test (Red)
    - [ ] Create `tests/test_icons_folium.py`:

```python
import folium

from cave_sketch.backend_renders import render_to_folium
from cave_sketch.style import ICON_LINE_WEIGHT

LAT, LON = 46.5, 11.3


def test_folium_icon_is_polyline_with_wall_weight():
    features = {
        "icons": [{
            "type": "B_entrance",
            "strokes": [[[LAT, LON], [LAT + 1e-5, LON]], [[LAT, LON], [LAT, LON + 1e-5]]],
            "color": "firebrick",
            "weight": ICON_LINE_WEIGHT,
            "popup": "M: B_entrance (e)",
        }],
        "points": [{"coords": [LAT, LON], "color": "deepskyblue", "size": 2, "popup": "ice"}],
    }
    fmap = folium.Map(location=[LAT, LON])
    render_to_folium(features, fmap, "Test")
    html = fmap.get_root().render()
    assert html.count("L.polyline(") == 1
    assert '"color": "firebrick"' in html
    assert f'"weight": {ICON_LINE_WEIGHT}' in html
    assert "L.circleMarker(" in html  # plain points unchanged
```

    - [x] Run `uv run pytest -q tests/test_icons_folium.py`. Expected: assertion fails on
      `html.count("L.polyline(") == 1` (it is 0).
- [x] Task: Implement (Green) in `cave_sketch/backend_renders/folium.py` [5c93d23]
    - [x] **Replace** `    # ---- POINTS (B_ice, BLOCK, etc.) ----` **with**

```python
    # ---- ICONS (B_blocks, B_water-flow, ..., L_water-flow chevrons) ----
    # Ground-anchored polylines: they scale with zoom exactly like the walls.
    for icon in features.get("icons", []):
        folium.PolyLine(
            locations=icon["strokes"],
            color=icon["color"],
            weight=icon["weight"],
            opacity=0.8,
            popup=icon.get("popup", ""),
        ).add_to(fg)

    # ---- POINTS (B_ice, B_snow) ----
```

    - [x] Run `uv run pytest -q tests/test_icons_folium.py`. Expected: pass.
- [x] Task: Verify and commit [5c93d23]
    - [x] `uv run pytest -q` and `uv run ruff check cave_sketch tests`.
    - [x] Commit: `feat(folium-backend): draw icons as ground-anchored polylines`.

## Phase 8: Render icons in KML/KMZ (Google Earth)

- [x] Task: Write the failing tests (Red)
    - [x] Create `tests/test_icons_kml.py`:

```python
# ruff: noqa: E501
import xml.etree.ElementTree as ET

from cave_sketch.backend_renders.google_earth import render_to_kml, rgba_to_kml_color
from cave_sketch.style import STYLE_MAP
from cave_sketch.style_icons import ICON_SHAPES

NS = {"kml": "http://www.opengis.net/kml/2.2"}
LAT, LON = 46.5, 11.3


def _kml_root(map_data):
    return ET.fromstring(render_to_kml([map_data]).encode("utf-8"))


def test_kml_icon_style_uses_wall_width_and_icon_color():
    root = _kml_root({"name": "M", "lines": [], "nodes": []})
    styles = {s.get("id"): s for s in root.findall(".//kml:Style", NS)}
    for typ in ["B_blocks", "B_continuation", "B_entrance", "B_water-flow", "L_water-flow"]:
        line_style = styles[f"icon_{typ}"].find("kml:LineStyle", NS)
        assert line_style.find("kml:width", NS).text == str(STYLE_MAP["L_wall"]["weight"])
        assert line_style.find("kml:color", NS).text == rgba_to_kml_color(STYLE_MAP[typ]["color"])
        assert styles[f"icon_{typ}"].find("kml:IconStyle", NS) is None


def test_kml_icon_is_ground_geometry_not_pushpin():
    map_data = {
        "name": "M",
        "lines": [],
        "nodes": {"c": {"lat": LAT, "lon": LON, "type": "B_continuation", "rotation": 0.0}},
    }
    root = _kml_root(map_data)
    (placemark,) = [p for p in root.findall(".//kml:Placemark", NS)
                    if p.find("kml:styleUrl", NS).text == "#icon_B_continuation"]
    assert placemark.find(".//kml:Point", NS) is None
    strings = placemark.findall("kml:MultiGeometry/kml:LineString", NS)
    assert len(strings) == len(ICON_SHAPES["continuation"])
    assert root.find(".//kml:Icon", NS) is None  # no pushpin / PNG anywhere


def test_kml_water_flow_line_gets_chevron_placemark():
    a = {"id": "0P0", "lat": LAT, "lon": LON}
    b = {"id": "0P1", "lat": LAT + 0.0001, "lon": LON}
    map_data = {
        "name": "M",
        "lines": [{"from": a, "to": b, "type": "L_water-flow"}, {"from": b, "to": a, "type": "L_water-flow"}],
        "nodes": [],
    }
    urls = [p.find("kml:styleUrl", NS).text for p in _kml_root(map_data).findall(".//kml:Placemark", NS)]
    assert urls.count("#line_L_water-flow") == 1
    assert urls.count("#icon_L_water-flow") == 1


def test_kml_color_map_covers_every_style_color():
    for style in STYLE_MAP.values():
        assert rgba_to_kml_color(style["color"]) != "ffffffff" or style["color"] == "white", style["color"]
```

    - [x] Run `uv run pytest -q tests/test_icons_kml.py`. Expected: `KeyError: 'icon_B_blocks'`
      and the color-map test failing on `tan`.
- [x] Task: Implement (Green) in `cave_sketch/backend_renders/google_earth.py`
    - [x] **Replace** `from cave_sketch.style import STYLE_MAP` **with**
      `from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP`.
    - [x] In `rgba_to_kml_color`, **replace**

```python
        "saddlebrown": "ff13458b",
    }
```

      **with** (KML colors are `aabbggrr`)

```python
        "saddlebrown": "ff13458b",
        "tan": "ff8cb4d2",
        "firebrick": "ff2222b2",
        "mediumpurple": "ffdb7093",
        "steelblue": "ffb48246",
    }
```

    - [x] **Replace** `def render_to_kml(` **with**

```python
def _add_icon_style(doc: ET.Element, stype: str, color: str) -> None:
    """Shared style ``icon_<stype>``: icons are LineStrings stroked like walls."""
    style = ET.SubElement(doc, "Style", id=f"icon_{stype}")
    line_style = ET.SubElement(style, "LineStyle")
    ET.SubElement(line_style, "color").text = rgba_to_kml_color(color)
    ET.SubElement(line_style, "width").text = str(ICON_LINE_WEIGHT)


def render_to_kml(
```

    - [x] **Replace**

```python
    for stype, sdict in STYLE_MAP.items():
        style_id = str(sdict.get("type", "line")) + "_" + stype
```

      **with**

```python
    for stype, sdict in STYLE_MAP.items():
        if sdict.get("type") == "icon":
            _add_icon_style(doc, stype, str(sdict["color"]))
            continue
        if "line_decoration" in sdict:
            _add_icon_style(doc, stype, str(sdict["color"]))

        style_id = str(sdict.get("type", "line")) + "_" + stype
```

    - [x] **Replace** `        # --- POINTS ---` **with**

```python
        # --- ICONS (B_blocks, B_water-flow, ..., L_water-flow chevrons) ---
        # Real ground geometry, not pushpins: they scale with zoom like the survey.
        for icon in features.get("icons", []):
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = icon["type"]
            ET.SubElement(placemark, "styleUrl").text = f"#icon_{icon['type']}"
            multi_geo = ET.SubElement(placemark, "MultiGeometry")
            for stroke in icon["strokes"]:
                ls = ET.SubElement(multi_geo, "LineString")
                ET.SubElement(ls, "tessellate").text = "1"
                coord_str = " ".join([f"{lon},{lat},0" for lat, lon in stroke])
                ET.SubElement(ls, "coordinates").text = coord_str

        # --- POINTS ---
```

      Leave the existing `# --- POINTS ---` loop as it is: it only handles `type == "point"`.
      `render_to_kmz` needs **no** change (there are no assets).
    - [x] Run `uv run pytest -q tests/test_icons_kml.py tests/test_kmz_export.py`. Expected: all pass.
- [x] Task: Verify and commit [a0445ac]
    - [x] `uv run pytest -q` and `uv run ruff check cave_sketch tests`.
    - [x] Commit: `feat(kml-backend): export icons as ground LineStrings with wall line width`.

## Phase 9: Carry rotation through view rotation and the map JSON

Without this phase, `B_water-flow` arrows point the wrong way on rotated
plots and are never oriented on the satellite map/KMZ (the JSON has no
rotation).

- [~] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_icon_rotation_plumbing.py`:

```python
# ruff: noqa: E501
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import cave_sketch.survey.graphics.survey_plot as survey_plot
from cave_sketch.satellite_view.map import export_map_data
from cave_sketch.survey.graphics.survey_plot import create_survey

LAT, LON = 46.5, 11.3


def test_export_map_data_writes_node_rotation(tmp_path):
    df = pd.DataFrame([
        {"Node_Id": "B_water-flow_0", "Links": "-", "X": 0.0, "Y": 0.0, "Type": "B_water-flow",
         "Rotation": 280.0, "Latitude": LAT, "Longitude": LON},
        {"Node_Id": "1", "Links": "-", "X": 1.0, "Y": 1.0, "Type": "station",
         "Rotation": float("nan"), "Latitude": LAT, "Longitude": LON},
    ])
    out = tmp_path / "m.json"
    export_map_data(df, "M", str(out))
    nodes = json.loads(out.read_text())["nodes"]
    assert nodes["B_water-flow_0"]["rotation"] == 280.0
    assert nodes["1"]["rotation"] == 0.0


def test_export_map_data_without_rotation_column(tmp_path):
    df = pd.DataFrame([{"Node_Id": "1", "Links": "-", "X": 0.0, "Y": 0.0, "Type": "station",
                        "Latitude": LAT, "Longitude": LON}])
    out = tmp_path / "m.json"
    export_map_data(df, "M", str(out))
    assert json.loads(out.read_text())["nodes"]["1"]["rotation"] == 0.0


def test_create_survey_view_rotation_also_rotates_icons(monkeypatch):
    captured = {}
    real_extract = survey_plot.extract_features_from_df

    def spy(df, *args, **kwargs):
        captured["df"] = df
        return real_extract(df, *args, **kwargs)

    monkeypatch.setattr(survey_plot, "extract_features_from_df", spy)
    df = pd.DataFrame([
        {"Node_Id": "0", "Links": "-", "X": 0.0, "Y": 0.0, "Type": "station", "Rotation": 0.0},
        {"Node_Id": "B_water-flow_0", "Links": "-", "X": 10.0, "Y": 10.0, "Type": "B_water-flow", "Rotation": 280.0},
    ])
    fig, ax = plt.subplots()
    create_survey(df, rule_flag=False, north_flag=False, config={}, rotation_deg=30.0, ax=ax)
    assert captured["df"]["Rotation"].tolist() == [30.0, 310.0]
    assert df["Rotation"].tolist() == [0.0, 280.0]  # caller's frame untouched
    plt.close(fig)
```

    - [ ] Run `uv run pytest -q tests/test_icon_rotation_plumbing.py`. Expected: `KeyError:
      'rotation'` (2 tests) and `[0.0, 280.0] != [30.0, 310.0]`.
- [ ] Task: Implement (Green)
    - [ ] `cave_sketch/survey/graphics/survey_plot.py`, in `create_survey`: **replace**

```python
        df[["X", "Y"]] = rotate_points(points, center, rotation_deg)
```

      **with**

```python
        df[["X", "Y"]] = rotate_points(points, center, rotation_deg)
        if "Rotation" in df.columns:
            df["Rotation"] = df["Rotation"].fillna(0.0) + rotation_deg
```

      (`df` is already a copy at that point, so the caller's DataFrame is not mutated.)
    - [ ] `cave_sketch/satellite_view/map.py`, in `draw_map`: **replace**

```python
        map_df[["X", "Y"]] = rotate_points(map_df[["X", "Y"]].values, center, rotation_angle)
```

      **with**

```python
        map_df[["X", "Y"]] = rotate_points(map_df[["X", "Y"]].values, center, rotation_angle)
        if "Rotation" in map_df.columns:
            map_df["Rotation"] = map_df["Rotation"].fillna(0.0) + rotation_angle
```

    - [ ] `cave_sketch/satellite_view/map.py`, in `export_map_data`: **replace**

```python
    # Store nodes
    for _, row in df.iterrows():
        map_data["nodes"][row["Node_Id"]] = {
            "lat": row["Latitude"],
            "lon": row["Longitude"],
            "type": row["Type"],
        }
```

      **with**

```python
    # Store nodes
    has_rotation = "Rotation" in df.columns
    for _, row in df.iterrows():
        map_data["nodes"][row["Node_Id"]] = {
            "lat": row["Latitude"],
            "lon": row["Longitude"],
            "type": row["Type"],
            "rotation": (
                float(row["Rotation"]) if has_rotation and pd.notna(row["Rotation"]) else 0.0
            ),
        }
```

    - [ ] Consolidate the duplicated WGS84 helper in `cave_sketch/satellite_view/map.py`, so
      icons and survey use one meters→degrees conversion:
        - delete the `# WGS84 constants` block (`_A`, `_F`, `_E2`, `_DEG2RAD`, 5 lines);
        - delete the whole `def _meters_per_degree_wgs84(lat_deg: float):` function;
        - in `cartesian_to_latlon` change `_meters_per_degree_wgs84(lat_0)` to
          `meters_per_degree_wgs84(lat_0)`;
        - add `from cave_sketch.geo.georef import meters_per_degree_wgs84` right after
          `from cave_sketch.features.render_features import extract_features_from_json`.
        - `numpy` is still used elsewhere in the file: keep `import numpy as np`.
    - [ ] Run `uv run pytest -q tests/test_icon_rotation_plumbing.py tests/test_satellite_map.py
      tests/test_satellite_bridge.py tests/test_georef.py`. Expected: all pass.
- [ ] Task: Verify and commit
    - [ ] `uv run pytest -q` and `uv run ruff check cave_sketch tests`.
    - [ ] Commit: `feat(rotation): propagate DXF symbol rotation through view rotation and map JSON`.

## Phase 10: Docs, full verification, manual and Android checks

- [ ] Task: Update `docs/DXF_ELEMENTS.md`
    - [ ] In the per-element sections and the summary table, mark `L_water-flow`, `B_water-flow`,
      `B_continuation`, `B_entrance` and `B_blocks` as **supported**. Remove the note
      `DXF uses "B_blocks" but style.py defines it as "BLOCK"`. State that these are drawn as
      ground-scaled vector icons (size in meters, stroke width = `L_wall`) in the survey plot,
      satellite map and KMZ, and that `B_water-flow` is oriented by the DXF INSERT rotation.
    - [ ] Commit: `docs(dxf): document icon rendering for water-flow, continuation, entrance, blocks`.
- [ ] Task: Full automated suite
    - [ ] `uv run pytest -q`. Expected: **182 passed**, 0 failed (131 before the track + 51 new).
    - [ ] `uv run ruff check cave_sketch tests`. Expected: `All checks passed!`.
- [ ] Task: Real-fixture smoke test (throwaway script, **not committed**; write outputs to a temp
      dir)
    - [ ] Run:

```python
import matplotlib; matplotlib.use("Agg")
import tempfile, zipfile
from pathlib import Path
import pandas as pd
from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.survey import draw_survey
from cave_sketch.satellite_view.map import draw_map

out = Path(tempfile.mkdtemp())
csv = out / "v14.csv"
parse_dxf(Path("tests/fixtures/sample_v14.dxf"), output_path=csv)
print(pd.read_csv(csv).groupby("Type")["Rotation"].agg(["count", "min", "max"]))
draw_survey(title="t", rule_length=20.0, csv_map_path=str(csv), csv_section_path=None,
            surveyor_name="x").savefig(out / "v14.png", dpi=110)
_, _, kmz = draw_map(str(csv), [{"station": "0", "lat": 46.5, "lon": 11.3}],
                     str(out / "v14.html"), map_name="v14")
kml = zipfile.ZipFile(kmz).read("doc.kml").decode()
print(out, "icon placemarks:", kml.count("#icon_B_"), "<Icon> tags:", kml.count("<Icon>"))
```

    - [ ] Expected: `B_blocks` count 90 and `B_water-flow` count 21 with rotation min ≈ 5.63 and
      max ≈ 305.39; `icon placemarks: 111`, `<Icon> tags: 0`; no exceptions.
- [ ] Task: Manual visual verification
    - [ ] PNG/PDF: zoom into the right-hand end of the cave. You should see tan block outlines
      with the same stroke width as the red walls, and purple S-arrows pointing along the
      passage. On the full page the icons are small (1.5 m in a ~300 m cave): this is expected.
    - [ ] HTML: open `v14.html`. Blocks and water-flow icons sit on the satellite tiles, and
      `B_ice`/`B_snow` circle markers now appear too (Phase 5 fix). Zooming in grows the icons
      together with the walls.
    - [ ] KMZ: open in Google Earth. Zoom in and out: icons scale with the survey and are
      **not** constant-size pushpins. Water-flow arrows follow the passage.
- [ ] Task: Android verification (manual, by the maintainer; call it out, do not skip silently)
    - [ ] Build and run the Android app, load a DXF containing these elements, and generate the
      survey plot and satellite map. Icons must look like the webapp's. There are no asset files
      any more, so this is a plain regression check of the shared `cave_sketch/` package.
