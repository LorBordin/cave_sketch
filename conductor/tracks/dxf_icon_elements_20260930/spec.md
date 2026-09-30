# Spec: DXF Icon Elements — Water-Flow, Continuation, Entrance, Blocks Fix

## Overview

Five DXF element types are missing or broken across both render surfaces
(the Survey Plot / matplotlib PDF, and the Satellite view / Folium HTML +
KMZ): `L_water-flow`, `B_water-flow`, `B_continuation`, `B_entrance` are not
parsed or styled at all, and `B_blocks` is silently dropped due to a
name mismatch. `docs/DXF_ELEMENTS.md` documents the gaps; `icon_samples/`
(provided by the maintainer) contains one screenshot of the real TopoDroid
symbol for each of the five — hand-drawn shapes (a crossed quadrilateral, a
curling hook, a triangle, a wavy line, and a repeating chevron pattern along
a line), not simple round/star/triangle markers.

This track adds real vector icon rendering for these five element types,
shared identically across matplotlib, Folium, and KML/KMZ, plus fixes the
parsing/styling root causes that make them invisible today.

This track is **backend-only, both platforms automatically**: the Android
app has no separate rendering code — `android/app/src/main/python/cave_sketch`
is a **symlink** to the repo-root `cave_sketch/` package (confirmed via
`android/app/src/main/python/survey_bridge.py` and `satellite_bridge.py`,
which call the exact same `draw_survey()` / `draw_map()` entrypoints the
Streamlit webapp calls). Every file this spec touches ships to both
platforms verbatim. See "Android-specific constraints" below for the two
platform details this actually changes.

## Decisions (locked with maintainer)

| Decision | Choice |
|----------|--------|
| Icon fidelity approach | Hand-traced vector shapes (vertex lists), not cropped/rasterized JPEGs — the source screenshots are anti-aliased, grid-overlaid, JPEG-compressed UI captures, not clean assets. One shape definition per icon, rendered three ways (matplotlib `Path`, inline SVG for Folium, rasterized PNG for KML). |
| `L_water-flow` line treatment | One small chevron icon per line **segment** (matching the DXF's own polyline-segment granularity), rotated to the segment's direction — not a continuous repeating pattern. Same technique in all three backends. |
| Icon colors | Best-effort read of the screenshots (tan/wheat block, red/firebrick continuation + entrance, purple water-flow point), **except** the water-flow line chevrons: the source renders white-on-black, which would be invisible on the survey plot's white background — substituted with `steelblue` (ties to the existing `A_water` blue). This is the one deliberate deviation from the source imagery. |
| `B_ice` / `B_snow` | Left untouched — still plain matplotlib markers / color-tinted KML pushpins. Out of scope; no icon shapes were provided for them. |
| Exact TopoDroid hex values | Not pursued — approximated visually. Maintainer did not have exact values on hand. |

## Icon Shape Definitions

All vertices are in a local unit space (roughly `0..1` or `-1..1`), origin
and scale arbitrary — each renderer scales/positions independently using
the existing per-type `size`/`markersize` convention already in `STYLE_MAP`.
Traced by eye from `icon_samples/*.jpg`; not pixel-exact, may be refined
during implementation against the source images.

| Icon name | Sub-paths (vertices) | Closed? | Color |
|---|---|---|---|
| `block` | `(0.05,0.55) (0.55,1.00) (1.00,0.35) (0.60,0.05)` — outline; plus two more sub-paths: `(0.05,0.55)-(1.00,0.35)` and `(0.55,1.00)-(0.60,0.05)` — diagonals | Outline closed; diagonals open | `tan` |
| `entrance` | `(0.0,0.35) (1.0,1.0) (0.55,0.0)` | Closed | `firebrick` |
| `continuation` | Open polyline: `(0.30,1.00) (0.10,0.92) (0.05,0.80) (0.20,0.72) (0.45,0.78) (0.65,0.95) (0.80,1.00) (0.95,0.85) (0.90,0.60) (0.70,0.45) (0.55,0.30) (0.50,0.15) (0.50,0.00)` | Open | `firebrick` |
| `water_flow_point` | Two sub-paths: flag tick `(0.05,0.30) (0.05,0.60) (0.35,0.85)`; wavy body `(0.05,0.60) (0.25,0.55) (0.40,0.65) (0.55,0.55) (0.65,0.40) (0.80,0.30) (0.90,0.15) (1.00,0.05)` | Both open | `mediumpurple` |
| `water_flow_chevron` | `(-0.5,0.6) (0.5,0.0) (-0.5,-0.6)` — points along local `+x` before rotation | Open | `steelblue` |

## Functional Requirements

### FR-1: New module `cave_sketch/style_icons.py`
- `ICONS: Dict[str, IconDef]` holding the five shapes above (`IconDef` =
  list of `(vertices, closed)` sub-paths + `color`).
- `icon_to_matplotlib_path(name: str) -> matplotlib.path.Path` — one
  `Path` per icon, `MOVETO` at the start of each sub-path, `LINETO` for
  each subsequent vertex, `CLOSEPOLY` only for closed sub-paths.
- `icon_to_svg_path_d(name: str) -> str` — the same vertex data as an SVG
  `<path d="...">` string (`M`/`L` commands, `Z` for closed sub-paths),
  normalized to a small `viewBox` (e.g. `0 0 32 32`).
- Pure data + pure functions; no matplotlib `pyplot`/figure state, no I/O.

### FR-2: Root-cause fix — `cave_sketch/dxf/parser.py::_get_features`
- `valid_block_names` currently is `{"B_ice", "BLOCK", "B_snow"}`. The
  literal `"BLOCK"` never matches a real DXF block name — verified via
  `ezdxf` against all 6 fixture files (`sample_v14.dxf`, `sample_v9.dxf`,
  `grotta_mittelbergferner-1p.dxf`, `val_cont_06-0p.dxf`,
  `val_mul_4-1p.dxf`): the real name is always `B_blocks`. This is dead
  code — remove it.
- New set: `{"B_ice", "B_snow", "B_blocks", "B_water-flow", "B_continuation", "B_entrance"}`.
- Without this fix, none of the four target block types are ever added to
  the parsed `CaveSurvey`/DataFrame — they're dropped before styling is
  even reached.

### FR-3: `cave_sketch/style.py` — STYLE_MAP additions
- Remove `"BLOCK"` and replace it with `"B_blocks"` (matches the real DXF
  name; fixes the reported "not correctly rendered" bug), using the new
  `type: "icon"` below instead of the old plain-circle marker, since an
  icon sample was provided for it (`icon_samples/b_block.jpg`).
- New entries, all using a new `type: "icon"` (distinct from the existing
  `type: "point"`, which stays untouched for `B_ice`/`B_snow`):
  ```
  "B_blocks":       {"type": "icon", "icon": "block",             "color": "tan",          "size": 5}
  "B_continuation": {"type": "icon", "icon": "continuation",      "color": "firebrick",    "size": 6}
  "B_entrance":     {"type": "icon", "icon": "entrance",          "color": "firebrick",    "size": 7}
  "B_water-flow":   {"type": "icon", "icon": "water_flow_point",  "color": "mediumpurple", "size": 4}
  ```
- New line entry:
  ```
  "L_water-flow": {"type": "line", "color": "steelblue", "linestyle": "solid", "weight": 1,
                   "line_decoration": "water_flow_chevron"}
  ```
  `line_decoration` is a new optional key on line-type entries, read by
  both feature-extraction functions (FR-4/FR-5) to emit one decoration
  per segment. No other existing line type sets it.

### FR-4: `cave_sketch/features/render_features.py::extract_features_from_df`
(feeds the matplotlib survey plot)
- Points: where `STYLE_MAP[typ]["type"] == "icon"`, emit into a
  `features["points"]` entry carrying `{"icon": ..., "color": ..., "size": ..., "coords": [y, x]}`
  instead of the current `marker`/`markersize` shape — same list, richer
  dict, distinguished by the presence of an `"icon"` key. Existing
  `type: "point"` entries (`B_ice`, `B_snow`) are untouched.
- Line decorations: for line types whose style has `line_decoration` set,
  build a new `features["line_decorations"]` list. **Non-obvious, must be
  preserved:** the existing line-building loop visits each polyline
  segment from *both* endpoints (row *j* draws to neighbor *j+1*, and row
  *j+1* separately draws back to *j*), so segments must be deduplicated
  and given a **canonical direction** before decorating, or two
  opposite-pointing chevrons will overlap at the same spot. Node IDs for
  polyline points follow `f"{i}P{j}"` (segment group `i`, vertex index
  `j`); canonicalize by parsing the trailing `P(\d+)` from both node IDs
  in a pair and always treating the lower `j` as "from" — this preserves
  the DXF's original vertex ordering (the actual drawn flow direction).
  Dedupe by `frozenset({node_id_a, node_id_b})`.
  Each entry: `{"coords": [mid_y, mid_x], "angle_rad": atan2(dy, dx), "icon": ..., "color": ..., "size": ...}`,
  angle computed in local Cartesian survey space (matches the plot's own
  X/Y axes directly — no geographic conversion needed here).

### FR-5: `cave_sketch/features/render_features.py::extract_features_from_json`
(feeds Folium satellite HTML + KMZ)
- **Separate pre-existing bug, required for this task**: this function
  currently builds only `features["lines"]` and `features["polygons"]` —
  never `"points"` — even though `render_to_folium` already has
  point-rendering code waiting for that key. Result: **the Folium
  satellite HTML view renders zero point markers today, for every type**,
  not just the new ones. Add a `"points"` builder reading
  `map_data.get("nodes", ...)`, normalizing the dict-or-list shape the
  same way `google_earth.py`'s existing node loop already does (lines
  124-127 there), filtered to entries whose `STYLE_MAP` type is `"point"`
  or `"icon"`.
- Line decorations: same `"line_decorations"` list as FR-4, but computed
  from `map_data["lines"]` entries (which already carry `from`/`to`
  dicts with `id`/`lat`/`lon`), using the same node-ID canonicalization
  and dedup rule. **Angle must be a compass bearing (degrees clockwise
  from north)**, not a raw `atan2` on lat/lon deltas — for these small
  distances a planar approximation is fine:
  `bearing = degrees(atan2(dlon * cos(radians(lat)), dlat)) % 360`.
  This bearing is used as-is by both downstream renderers (FR-7 KML
  `<heading>` is already clockwise-from-north; FR-6 Folium CSS
  `rotate()` is clockwise on an unrotated north-up map, so no sign flip
  needed either place).

### FR-6: `cave_sketch/backend_renders/matplotlib.py`
- Points with an `"icon"` key: group by icon name (not by marker
  character), build one `MarkerStyle(icon_to_matplotlib_path(name))` per
  group, draw via `ax.scatter(...)` exactly like the existing
  marker-character grouping — same code shape, new branch.
- Line decorations: matplotlib scatter cannot rotate individual markers
  independently within one call, and each chevron needs its own angle,
  so draw these as **individual `matplotlib.patches.PathPatch` objects**
  (unfilled, stroke only) via `ax.add_patch(...)`, one per decoration
  entry, each built by applying
  `Affine2D().rotate(angle_rad).translate(mid_x, mid_y)` to the base
  `water_flow_chevron` path scaled by its `size`. Not batched — segment
  counts here are in the tens to low hundreds, trivial for matplotlib.

### FR-7: `cave_sketch/backend_renders/folium.py`
- Points with an `"icon"` key: use `folium.DivIcon(html=<inline SVG>)`
  (built from `icon_to_svg_path_d`) instead of `CircleMarker`, sized via
  the point's `size`. Existing plain-`CircleMarker` behavior for
  `type: "point"` entries is unchanged.
- Line decorations: one small `DivIcon` per entry at `coords`, inline SVG
  of the `water_flow_chevron` shape, rotated via a CSS
  `transform: rotate(<bearing>deg)` on the icon's HTML — no new plugin
  or JS dependency.

### FR-8: `cave_sketch/backend_renders/google_earth.py`
- Pre-rendered PNG assets (see FR-9) replace the current color-tinted
  default pushpin for `type: "icon"` styles: their `<Style>` block gets
  an `<Icon><href>icons/<name>.png</href></Icon>` instead of the current
  bare `<IconStyle><color>`. Existing `type: "point"` styles
  (`B_ice`/`B_snow`) keep the current color-tinted-default-pushpin
  behavior, untouched.
- `rgba_to_kml_color`'s `color_map` needs no new entries for icon styles
  (icon color now comes from the PNG's own pixels, not a KML tint) —
  only used by non-icon line/area/point styles as today.
- Line decorations: one small `Placemark`/`Point` per entry, referencing
  the `water_flow_chevron` icon style, with
  `<IconStyle><heading>{bearing}</heading></IconStyle>` for rotation
  (Google Earth natively supports per-placemark icon heading).
- `render_to_kmz` must also write each referenced icon PNG into the zip
  under `icons/<name>.png` alongside `doc.kml`.

### FR-9: Icon asset generation (one-time, dev-time only)
- A small standalone script — **outside** the `cave_sketch` package (e.g.
  `scripts/generate_icon_assets.py` at repo root) — uses
  `icon_to_matplotlib_path` to rasterize each of the 5 icons to a small
  transparent-background PNG, run once by the implementer, with output
  committed to `cave_sketch/assets/icons/<name>.png`. This script is dev
  tooling, not shipped/imported at runtime, and is not part of this
  spec's runtime behavior — it only needs to produce the checked-in PNGs.

### FR-10: `tests/test_kmz_export.py`
- The one test using placeholder point type `"BLOCK"` must be updated to
  `"B_blocks"` to match the renamed `STYLE_MAP` key, or it silently stops
  matching any style and its point-placemark assertion breaks.

## Android-specific constraints

1. **Asset placement**: the PNGs from FR-9 must live *inside* the
   `cave_sketch/` package tree (`cave_sketch/assets/icons/`), not at the
   repo root — only `cave_sketch/` is visible through the Android
   symlink (`android/app/src/main/python/cave_sketch -> ../../../../../cave_sketch`).
   This is a new pattern for this package (today `cave_sketch/` contains
   only `.py` files); pip-installed dependencies already ship binary data
   this way under Chaquopy (matplotlib's own font/data files), so it's
   expected to work, but building and running the Android app after this
   change to confirm the PNGs are actually bundled is a required
   verification step, not an assumption to skip.
2. **Path resolution**: `google_earth.py` must locate the icon PNGs via
   `Path(__file__).resolve().parent / "assets" / "icons"` (relative to
   the installed package), never a repo-root-relative or CWD-relative
   path — on Android there is no repo checkout, only the packaged
   `cave_sketch` subtree.

Everything else in this spec (matplotlib custom `Path` markers, Folium
`DivIcon`/inline-SVG output) is pure Python producing plain data
structures/strings, with no OS-specific behavior — identical on both
platforms with no extra work.

## Testing

- Unit tests for `style_icons.py` (`icon_to_matplotlib_path` /
  `icon_to_svg_path_d` produce valid, non-empty output for all 5 icons).
- Unit test for the `dxf/parser.py` whitelist fix (parsing
  `val_cont_06-0p.dxf` yields `B_continuation`/`B_entrance` points;
  parsing `val_mul_4-1p.dxf` yields `B_blocks`/`B_water-flow` points).
- Unit test for the `extract_features_from_json` points gap (FR-5): a
  `map_data` with a node of a known `type: "point"`/`"icon"` style
  produces a non-empty `features["points"]`.
- Unit test for line-decoration canonicalization/dedup (FR-4/FR-5): a
  synthetic 3-point `L_water-flow` polyline produces exactly 2 decoration
  entries (not 4), each pointing in the direction of increasing vertex
  index.
- Updated `tests/test_kmz_export.py` (FR-10).
- Manual verification: render `val_cont_06-0p.dxf`, `val_mul_4-1p.dxf`,
  and `grotta_mittelbergferner-1p.dxf` (already at the repo root) through
  both `draw_survey` (matplotlib PDF) and `draw_map` (Folium HTML +
  KMZ/Google Earth) and visually confirm all 5 icons appear, correctly
  colored/shaped/rotated, in both outputs.
- Android: build and run the app, generate a survey plot and satellite
  map from a DXF containing these element types, and confirm the icons
  render identically to the webapp (validates the FR-9/Android-specific
  asset-bundling constraint above).

## Out of Scope

- Upgrading `B_ice`/`B_snow` from plain markers to icons (no icon sample
  provided for them).
- Exact TopoDroid hex-color matching (no source-of-truth values
  available; approximated visually).
- A continuously-repeating chevron pattern along the full length of
  `L_water-flow` lines (decided: one chevron per DXF polyline segment
  instead — see Decisions table).
- Any Kotlin/Android UI changes — this track is entirely within the
  shared `cave_sketch/` backend package.
