# Spec: DXF Icon Elements — Water-Flow, Continuation, Entrance, Blocks Fix

> **Revision 2 (2026-10-05).** Replaces the first version of this spec.
> The PNG / inline-SVG / pushpin approach was dropped. Every icon is now
> **plain line geometry, drawn in ground meters, stroked as thick as
> `L_wall`**. The design below was prototyped end to end (full test suite
> green, real-fixture render checked) before this spec was written. The
> plan (`./plan.md`) contains the exact code.

## 1. Goal (one paragraph)

Five TopoDroid DXF element types are invisible or broken in every output:
`B_water-flow`, `B_continuation`, `B_entrance` and `L_water-flow` are never
drawn, and `B_blocks` is dropped by the parser because of a name mismatch.
This track makes them all appear, identically, in the three outputs the app
produces:

| Output | Code | Where the user sees it |
|---|---|---|
| Survey plot (PDF / PNG) | `cave_sketch/backend_renders/matplotlib.py` | "Survey Plot" page (webapp + Android) |
| Satellite map (HTML) | `cave_sketch/backend_renders/folium.py` | "Satellite View" page (webapp + Android) |
| Google Earth (KMZ) | `cave_sketch/backend_renders/google_earth.py` | KMZ download |

The Android app has **no separate rendering code**:
`android/app/src/main/python/cave_sketch` is a symlink to the repo-root
`cave_sketch/` package. Every change in this track ships to both platforms
automatically. No Kotlin changes.

## 2. Hard requirements (from the maintainer)

| # | Requirement | How this spec satisfies it |
|---|---|---|
| R1 | Icon strokes have **the same line width as `L_wall`**. | New constant `ICON_LINE_WEIGHT = STYLE_MAP["L_wall"]["weight"]` in `cave_sketch/style.py` (derived, never hard-coded). Every icon feature carries `weight = ICON_LINE_WEIGHT`, and every backend turns that weight into a width **through exactly the same code path it uses for `L_wall` lines** (§6). If `L_wall`'s weight changes, icons follow. |
| R2 | In KMZ (and the HTML map) icons **must not behave like pushpins**. They must stay the same size **relative to the cave survey** at every zoom level. | Icons are **real geometry**: KML `LineString`s (Folium `PolyLine`s) with lat/lon vertices computed from a fixed size **in meters**. Zooming in makes them bigger exactly as it makes walls bigger. **No** KML `<IconStyle>`, `<Icon>`, `<href>`, PNG, SVG or Folium `DivIcon` anywhere. |
| R3 | `B_continuation` icon is a **question mark "?"**. | Shape `continuation` (§4): a hook + stem stroke and a separate dot stroke. Vertices come from TopoDroid's own `B_continuation` DXF block, which *is* a "?". |
| R4 | `B_water-flow` icon is a **wiggly "S" line with an arrowhead on top**, **oriented in the direction of the water flow**. | Shape `water_flow` (§4): an S-shaped sine stroke ending in a short straight shaft, plus an arrowhead stroke. The arrow points along the icon's local +Y. The flow direction comes from the DXF INSERT rotation (§5), which the parser now keeps. |

## 3. Decisions (locked with the maintainer)

| Topic | Decision |
|---|---|
| Rendering technique | Icons are polylines ("strokes") in local metric coordinates, converted to `[y, x]` (survey plot) or `[lat, lon]` (map/KMZ). One shape definition, one placement function, three thin renderers. |
| Zoom behaviour | Ground-anchored (fixed meters). |
| Icon size | Fixed meters per type: `size_m` in `STYLE_MAP`. **1.5 m** for the four point icons, **1.0 m** for the `L_water-flow` chevron. `size_m` = length of the icon's **largest side**. Accepted trade-off: on the PDF of a very large cave the icons are small, as a real-scale map would show them. |
| Orientation source | DXF `INSERT` rotation (degrees, counter-clockwise), stored as a new `Rotation` column. Applied to **all** icon types: in the fixtures only `B_water-flow` has non-zero values, the others are `0`/`360`. |
| `L_water-flow` | The line itself stays a thin `steelblue` line (weight 1). In addition, **one chevron per DXF polyline segment** sits at the segment midpoint and points in drawing order (TopoDroid draws water-flow lines downstream). The chevron is an icon, so it uses `ICON_LINE_WEIGHT` (R1). |
| Colors | `B_blocks` = `tan`, `B_continuation` = `firebrick`, `B_entrance` = `firebrick`, `B_water-flow` = `mediumpurple`, `L_water-flow` line + chevrons = `steelblue`. Do not re-derive them. |
| `B_ice`, `B_snow` | Unchanged: they stay plain markers (`type: "point"`). |
| Section-view MIRROR merge | Out of scope (see §10). |

## 4. Icon shapes (exact data)

Convention for every shape. Implement it exactly like this, because the
tests check it:

- A shape is a list of **strokes**. A stroke is an **open** polyline: a
  list of `(u, v)` tuples, at least 2 points. A closed outline repeats its
  first point at the end.
- Unit box: the shape's bounding box is **centered on `(0, 0)`** and its
  **largest side is exactly `1.0`** (±0.001).
- The icon's "up" is **+v**. At rotation 0, "up" points **north** (+Y in
  survey coordinates). This is the TopoDroid DXF block convention, so the
  DXF INSERT rotation can be applied directly.

| Name | Used by | Strokes | Looks like |
|---|---|---|---|
| `blocks` | `B_blocks` | 2 | rock outline with two inner fracture lines (traced from the TopoDroid `B_blocks` block) |
| `entrance` | `B_entrance` | 1 | closed triangle, apex up (TopoDroid `B_entrance`) |
| `continuation` | `B_continuation` | 2 | **"?"**: hook + stem (stroke 0), dot (stroke 1, below the hook) (TopoDroid `B_continuation`) |
| `water_flow` | `B_water-flow` | 2 | **S-wiggle** from bottom to `v=0.25`, straight shaft up to the tip `(0, 0.5)` (stroke 0), arrowhead `(-0.2,0.28)→(0,0.5)→(0.2,0.28)` (stroke 1) |
| `water_flow_chevron` | `L_water-flow` decoration | 1 | `^` chevron, apex `(0, 0.25)` up |

The exact vertex lists are in `plan.md`, Phase 1 (`ICON_SHAPES`). Copy
them verbatim.

Placement function (pure math, no I/O):

```
icon_strokes(name, x, y, size_m, rotation_deg=0.0) -> List[List[(x, y)]]
    for each unit vertex (u, v):
        X = x + size_m * (u*cos(t) - v*sin(t))
        Y = y + size_m * (u*sin(t) + v*cos(t))      with t = radians(rotation_deg)
```

The rotation is **counter-clockwise**, the same sign as DXF INSERT rotation
and as `cave_sketch.features.geometry.rotate_points`. An unknown `name`
raises `KeyError`.

## 5. Data flow (what changes, layer by layer)

```
DXF INSERT (name, insert x/y, rotation)
  └─ dxf/parser.py::_get_features        + 4 block names, + "Rotation"
      └─ SurveyPoint.rotation             new field, default 0.0
          └─ CSV / DataFrame column "Rotation"   (parser._export_to_csv, survey/renderer._survey_to_df)
              ├─ survey_plot.create_survey: view rotation_deg is added to "Rotation"
              │    └─ extract_features_from_df  → features["icons"]  coords [y, x] meters
              │         └─ render_to_matplotlib  (LineCollection, same width formula as walls)
              └─ satellite_view/map.py: draw_map adds rotation_angle; export_map_data writes node "rotation"
                   └─ map JSON  nodes[id] = {lat, lon, type, rotation}
                        └─ extract_features_from_json → features["icons"]  coords [lat, lon]
                             ├─ render_to_folium  (PolyLine, weight = ICON_LINE_WEIGHT)
                             └─ render_to_kml     (Placemark + MultiGeometry/LineString, style icon_<type>)
```

### 5.1 New feature kind: `features["icons"]`

Both `extract_features_from_df` and `extract_features_from_json` return a
new key `"icons"` (always present, possibly empty). Each entry is:

```python
{
    "type":    "B_blocks",        # STYLE_MAP key; for chevrons: "L_water-flow"
    "strokes": [[[a, b], ...], ...],  # list of open polylines
    "color":   "tan",
    "weight":  ICON_LINE_WEIGHT,  # == STYLE_MAP["L_wall"]["weight"]
    "popup":   "B_blocks (B_blocks_0)",
}
```

Coordinate order follows the existing `"coords"` convention of each path:
**`[y, x]` (meters) in the DataFrame path, `[lat, lon]` in the JSON path.**

### 5.2 Rotation plumbing

- `parser._get_features` stores `"Rotation": float(entity.dxf.rotation) % 360.0`.
  `360.0` becomes `0.0`, and ezdxf returns `0` when the attribute is absent.
- `SurveyPoint.rotation: float = 0.0`. Stations and polyline vertices keep `0.0`.
- Both DataFrame builders gain a 6th column, `"Rotation"`
  (`["Node_Id", "Links", "X", "Y", "Type", "Rotation"]`).
- **Backward compatibility:** CSVs saved before this change have no
  `Rotation` column, and merge connector rows have `NaN`. Readers must treat
  a missing or NaN value as `0.0` (`_rotation_value` helper,
  `getattr(row, "Rotation", 0.0)`). Never `KeyError` on old CSVs.
- **View rotation:** `create_survey(rotation_deg=…)` and
  `draw_map(rotation_angle=…)` rotate X/Y with `rotate_points`, which is
  CCW. They must add the same angle to `Rotation`, or rotated plots would
  show water-flow arrows pointing the wrong way.
- `export_map_data` writes `"rotation"` on every node (`0.0` if absent/NaN).
- The merger already uses `pd.concat`, so the extra column passes through
  unchanged.

### 5.3 `L_water-flow` chevrons: dedup + direction

The data lists every polyline segment **twice**: row `iPj` links to both
`iP(j-1)` and `iP(j+1)`, and `export_map_data` emits a line per link
direction. Emit a chevron **only** for the forward copy
`"{i}P{j}" → "{i}P{j+1}"` (same group `i`, index +1). Helper:
`_is_forward_segment(from_id, to_id)`. This yields exactly one chevron per
segment, pointing in DXF drawing order. Node IDs that don't match
`^\d+P\d+$` never get chevrons.

Chevron heading: `_heading_deg(dx, dy) = degrees(atan2(dy, dx)) - 90`
(converts a direction vector into the "0 = up" icon rotation). In the JSON
path, `dx`/`dy` are converted to meters first with `meters_per_degree_wgs84`,
so headings are correct away from the equator.

### 5.4 Meters → lat/lon

`cave_sketch/geo/georef.py` already has a WGS84 `_meters_per_degree_wgs84(lat)`,
and `satellite_view/map.py` has an identical private copy. Rename the georef
one to public `meters_per_degree_wgs84`, use it in `render_features.py` and
`map.py`, and delete the duplicate in `map.py`. Icons then use the **same**
meters→degrees conversion as the survey itself. Importing
`satellite_view.map` from `render_features` would be circular, which is why
the helper lives in `geo/georef.py`.

## 6. Per-backend rendering rules

### 6.1 matplotlib (`render_to_matplotlib`)
- Extract the existing wall-width formula into
  `_scaled_linewidth(weight, zoom_factor, ref_scale) = clip(weight * zoom_factor / ref_scale, 0.2, 4)`.
  Lines **and** icons call it, so an icon is always exactly as thick as an
  `L_wall` line in the same plot (R1).
- Draw all icon strokes in **one** `LineCollection` in data coordinates
  (meters), `capstyle="round"`, `joinstyle="round"`, `alpha=0.9`, `zorder=3`
  (walls use 2, stations 5). Convert `[y, x]` to `(x, y)`.
- **Do not** use `MarkerStyle(Path)`, `scatter` or `PathPatch` for icons.
  Markers are screen-sized, not meter-sized. Also, deep-copying a custom
  `Path` marker hits a `RecursionError` with this repo's matplotlib on
  Python 3.14 (observed while prototyping).

### 6.2 Folium (`render_to_folium`)
- One `folium.PolyLine(locations=icon["strokes"], color, weight=icon["weight"], opacity=0.8, popup)`
  per icon. Folium accepts a list of polylines (multi-polyline) in a single
  `PolyLine`. `opacity=0.8` and `weight` in pixels match how walls are drawn.
- No `DivIcon`, no `Marker`, no SVG.

### 6.3 KML / KMZ (`render_to_kml`)
- Shared style per icon type: `<Style id="icon_<TYPE>"><LineStyle><color/><width>ICON_LINE_WEIGHT</width></LineStyle></Style>`.
  Emit it for every `STYLE_MAP` entry with `type == "icon"` **instead of**
  the generic style, and **in addition** for every line style that has
  `line_decoration` (→ `icon_L_water-flow`).
- One `Placemark` per icon: `<name>TYPE</name>`, `<styleUrl>#icon_TYPE</styleUrl>`,
  then `<MultiGeometry>` with one `<LineString><tessellate>1</tessellate><coordinates>lon,lat,0 …</coordinates></LineString>`
  per stroke. This is the same structure as the existing wall placemarks.
- `rgba_to_kml_color`'s `color_map` falls back to **white** for unknown
  names. Add `tan ff8cb4d2`, `firebrick ff2222b2`, `mediumpurple ffdb7093`,
  `steelblue ffb48246` (KML is `aabbggrr`). A test asserts that every
  `STYLE_MAP` color is mapped.
- The KML **points** loop stays as is: it only handles `type == "point"`
  (B_ice/B_snow), so icon nodes are drawn once, by the icons loop.
- `render_to_kmz` is unchanged: there are no assets to bundle.

## 7. `STYLE_MAP` changes (`cave_sketch/style.py`)

- **Remove** `"BLOCK"`. That name never occurs in a real DXF; the real
  block is `B_blocks`.
- **Add**:

```python
"L_water-flow": {"color": "steelblue", "linestyle": "solid", "type": "line", "weight": 1,
                 "line_decoration": "water_flow_chevron", "decoration_size_m": 1.0},
"B_blocks":       {"color": "tan",          "icon": "blocks",       "size_m": 1.5, "type": "icon"},
"B_continuation": {"color": "firebrick",    "icon": "continuation", "size_m": 1.5, "type": "icon"},
"B_entrance":     {"color": "firebrick",    "icon": "entrance",     "size_m": 1.5, "type": "icon"},
"B_water-flow":   {"color": "mediumpurple", "icon": "water_flow",   "size_m": 1.5, "type": "icon"},
```

- **Add** after the dict: `ICON_LINE_WEIGHT = STYLE_MAP["L_wall"]["weight"]`.
- `type: "icon"` is a new style type. Only the code in this spec reads it.
  `line_decoration` / `decoration_size_m` are new optional keys on line
  styles.

## 8. Parser fix (`cave_sketch/dxf/parser.py::_get_features`)

`valid_block_names` becomes
`{"B_ice", "B_snow", "B_blocks", "B_water-flow", "B_continuation", "B_entrance"}`.
The literal `"BLOCK"` is dead code: `ezdxf` shows the real name is always
`B_blocks` in `tests/fixtures/sample_v14.dxf` / `sample_v9.dxf`. Without
this, the four block types are discarded before styling.

Fixture facts (verified): `sample_v14.dxf` contains 90 `B_blocks`, 21
`B_water-flow` (rotations 5.6°–305.4°), 106 `B_ice` and 147 `B_snow`.
**No committed fixture contains `B_continuation`, `B_entrance` or
`L_water-flow`.** Those are covered by synthetic tests (in-memory `ezdxf`
docs, hand-built DataFrames/JSON). `tests/fixtures/sample.dxf` has no
INSERTs, so the render-regression baselines are unaffected.

## 9. Testing (acceptance criteria)

New/changed tests, with exact code in the plan:

| File | Proves |
|---|---|
| `tests/test_style_icons.py` (new) | unit-box normalization of every shape; scaling/translation; CCW rotation; water-flow tip at +Y; "?" = hook + dot below; `KeyError` on unknown name |
| `tests/test_dxf_parser.py` (extend) | all 6 block names recognized, others ignored; rotation kept and normalized (`360 → 0`); `sample_v14.dxf` yields `B_blocks` + oriented `B_water-flow`; CSV columns now include `Rotation` |
| `tests/test_style.py` (new) | `BLOCK` gone; icon entries valid; chevron decoration; `ICON_LINE_WEIGHT == L_wall weight`; B_ice/B_snow unchanged; all colors valid |
| `tests/test_kmz_export.py` (edit) | placeholder node type `"BLOCK"` → `"B_ice"` (still a plain point) |
| `tests/test_render_icons_df.py` (new) | DataFrame path: icon size/position in meters, rotation column honored, missing/NaN rotation → 0, plain markers unchanged, one downstream chevron per segment, no cross-talk between polylines, dangling link safe, walls not decorated |
| `tests/test_render_icons_json.py` (new) | JSON path: dict- and list-shaped nodes, B_ice → points, ground size in meters, rotation honored, no `nodes` key safe, two-direction segment → one northward chevron of 1.0 m |
| `tests/test_icons_matplotlib.py` (new) | icon `LineCollection` linewidth **equals** the wall linewidth (two zoom configs); strokes in data meters; drawn above walls |
| `tests/test_icons_folium.py` (new) | icon → one `L.polyline` with icon color and `weight == ICON_LINE_WEIGHT`; plain points still `L.circleMarker` |
| `tests/test_icons_kml.py` (new) | `icon_<TYPE>` styles have `<width>` = L_wall weight and the right color, no `IconStyle`; icon placemark = MultiGeometry/LineStrings, no `<Point>`, **no `<Icon>` anywhere**; one chevron placemark per water-flow segment; color map covers every style color |
| `tests/test_icon_rotation_plumbing.py` (new) | `export_map_data` writes `rotation` (NaN/missing → 0); `create_survey(rotation_deg=30)` adds 30 to `Rotation` without mutating the caller's DataFrame |

Full suite: currently **131 passed**. After the track: **all green** (the
prototype reached 182), and `ruff check cave_sketch tests` passes.

Manual:
- Render `tests/fixtures/sample_v14.dxf` through `draw_survey` and
  `draw_map`. The KMZ's `doc.kml` contains 111 `#icon_B_` placemarks (90
  blocks + 21 water-flow) and **0** `<Icon>` tags. Zoomed in, the PDF shows
  tan block outlines and purple S-arrows pointing along the passage, with
  the same stroke width as the red walls.
- Open the KMZ in Google Earth. Zoom in and out: icons grow and shrink
  together with the walls (they are not fixed-size pushpins).
- Android (maintainer): build, load a DXF with these elements, and check
  that the survey plot and satellite map show the same icons. No asset
  bundling is involved any more, so this is a pure regression check.

## 10. Out of scope

- Turning `B_ice` / `B_snow` into icons.
- Other TopoDroid blocks present in DXFs (`B_stalactite`, `B_air-draught`, …).
- Using each INSERT's DXF scale (`xscale`). The size is fixed per type (§3).
- Flipping icon rotation when a **section** child is merged with
  `SectionProtocol.MIRROR`.
- Exact TopoDroid colors.
- Any Kotlin / Android UI change.
