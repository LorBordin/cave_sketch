# Plan: DXF Icon Elements — Water-Flow, Continuation, Entrance, Blocks Fix

> Full code for every step lives in
> `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md`. This
> conductor plan mirrors it in phases. Follow the standard task workflow in
> `conductor/workflow.md` (Red → Green → verify → commit → git note → mark
> `[x]`), including the Phase Completion Verification and Checkpointing
> Protocol at the end of each phase below. Phases are ordered so the shared
> icon-shape module lands first, then the parser/style root-cause fixes,
> then the survey-plot data path, then the satellite-view data path, then
> each of the three renderers, then the KML icon assets, then cleanup and
> final verification. Design spec: `./spec.md` (also at
> `docs/superpowers/specs/2026-09-30-dxf-icon-elements-design.md`).

## Global Constraints

- Icon PNG assets must live under `cave_sketch/assets/icons/` (inside the
  package tree), never at the repo root — only `cave_sketch/` is visible
  through the Android Chaquopy symlink
  (`android/app/src/main/python/cave_sketch -> ../../../../../cave_sketch`).
- Any code that locates icon assets must resolve the path via
  `Path(__file__).resolve().parent / "assets" / "icons"` (relative to the
  installed package) — never a repo-root-relative or CWD-relative path,
  since Android ships only the packaged `cave_sketch` subtree.
- `L_water-flow` gets exactly one chevron decoration per DXF polyline
  segment — not a continuously repeating pattern (rejected alternative,
  see spec Decisions table).
- `B_ice` / `B_snow` stay on the existing plain-marker / color-tinted-
  pushpin path — no icon shapes were provided for them; do not touch their
  `STYLE_MAP` entries or rendering branches.
- Icon colors are exactly as given in the spec's Icon Shape Definitions
  table (`tan`, `firebrick`, `mediumpurple`, `steelblue`) — approximated
  from screenshots, not to be re-derived or second-guessed during
  implementation.
- No new runtime dependencies — matplotlib, folium, and ezdxf are already
  present in both the webapp's environment and
  `android/app/build.gradle`'s Chaquopy `pip` block.

---

## Phase 1: Vector Icon Shape Definitions

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 1.

- [ ] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_style_icons.py` covering: every icon's
      matplotlib `Path` is centered at the origin and bounded to `±0.51`;
      `MOVETO`/`CLOSEPOLY` counts match each icon's sub-path structure;
      the SVG `d` string has one `M` per sub-path and one `Z` per closed
      sub-path; an unknown icon name raises `KeyError` from both
      `icon_to_matplotlib_path` and `icon_to_svg_path_d`.
    - [ ] Run `pytest tests/test_style_icons.py -v`; confirm it fails with
      `ModuleNotFoundError: No module named 'cave_sketch.style_icons'`.
- [ ] Task: Implement `cave_sketch/style_icons.py` (Green)
    - [ ] Define `SubPath`, `IconDef`, and `ICONS: Dict[str, IconDef]` for
      the five icons (`block`, `entrance`, `continuation`,
      `water_flow_point`, `water_flow_chevron`), vertices traced from
      `icon_samples/*.jpg` per the spec's Icon Shape Definitions table.
    - [ ] Implement `_normalized_subpaths` (centers at origin, scales the
      larger bounding-box dimension to `1.0`), `icon_to_matplotlib_path`,
      and `icon_to_svg_path_d`.
    - [ ] Run `pytest tests/test_style_icons.py -v`; confirm all
      parametrized cases pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(style): add vector icon shape definitions for TopoDroid symbols`).

## Phase 2: Fix DXF Block-Name Whitelist (Root Cause of the `B_blocks` Bug)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 2.

- [ ] Task: Write the failing tests (Red)
    - [ ] Add `import ezdxf` and `from cave_sketch.dxf.parser import
      _get_features` to `tests/test_dxf_parser.py`, then add tests
      covering: all six target block names (`B_ice`, `B_snow`,
      `B_blocks`, `B_water-flow`, `B_continuation`, `B_entrance`) are
      recognized by `_get_features` on a synthetic in-memory `ezdxf`
      document; an unrelated block name is silently ignored; parsing
      `tests/fixtures/sample_v14.dxf` (a real, already-committed fixture)
      now includes `B_blocks` and `B_water-flow` in the resulting point
      types.
    - [ ] Run `pytest tests/test_dxf_parser.py -v`; confirm the new tests
      fail (only `B_ice`/`B_snow` recognized today; `B_blocks`/
      `B_water-flow` missing from `sample_v14.dxf`'s parsed points).
- [ ] Task: Fix the whitelist (Green)
    - [ ] In `cave_sketch/dxf/parser.py:170`, change `valid_block_names`
      from `{"B_ice", "BLOCK", "B_snow"}` (the literal `"BLOCK"` never
      matches a real DXF block name — verified via `ezdxf` against all 6
      fixture files) to
      `{"B_ice", "B_snow", "B_blocks", "B_water-flow", "B_continuation", "B_entrance"}`.
    - [ ] Run `pytest tests/test_dxf_parser.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`fix(dxf): parse B_blocks, B_water-flow, B_continuation, B_entrance blocks`)
      — note in the commit body that these four block types were silently
      dropped before parsing even finished.

## Phase 3: `STYLE_MAP` Entries for the New/Fixed Elements

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 3.

- [ ] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_style.py` covering: `"BLOCK"` no longer
      exists in `STYLE_MAP` and `"B_blocks"` is an `"icon"` type
      referencing icon `"block"`; `B_continuation`/`B_entrance`/
      `B_water-flow` are all `"icon"` types referencing a valid name in
      `style_icons.ICONS`; `L_water-flow` is a `"line"` type with
      `line_decoration == "water_flow_chevron"` and a positive
      `decoration_size`; every color referenced by `STYLE_MAP` or
      `style_icons.ICONS` is a real, renderable color name
      (`matplotlib.colors.is_color_like`).
    - [ ] Run `pytest tests/test_style.py -v`; confirm it fails
      (`KeyError: 'B_blocks'`, etc.).
- [ ] Task: Update `cave_sketch/style.py` (Green)
    - [ ] Replace the `"BLOCK"` entry with `"B_blocks"`, `"B_continuation"`,
      `"B_entrance"`, `"B_water-flow"` (all `type: "icon"`, per the spec's
      STYLE_MAP additions table) and a new `"L_water-flow"` line entry
      (`color: "steelblue"`, `line_decoration: "water_flow_chevron"`,
      `decoration_size: 4`). Leave every other entry untouched.
    - [ ] Run `pytest tests/test_style.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(style): add STYLE_MAP entries for water-flow, continuation, entrance, blocks`).

## Phase 4: Icon Points in `extract_features_from_df` (Survey Plot Data Path)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 4.

- [ ] Task: Write the failing tests (Red)
    - [ ] In `tests/test_render_features.py`, add tests covering: an
      icon-type point (`B_blocks`) produces a `features["points"]` entry
      with `"icon"`/`"color"` and no `"marker"` key; a plain-marker point
      (`B_ice`) is unaffected (still has `"marker"`, no `"icon"`).
    - [ ] Run `pytest tests/test_render_features.py -v`; confirm the new
      icon-point test fails with `KeyError: 'icon'`.
- [ ] Task: Update `extract_features_from_df` (Green)
    - [ ] In `cave_sketch/features/render_features.py`, extend the
      point-handling block to branch on `style_type in ("point", "icon")`,
      building `"icon"`/`"size"` for icon types and keeping
      `"marker"`/`"size"` for plain-marker types.
    - [ ] Run `pytest tests/test_render_features.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(render-features): emit icon-style points from survey DataFrame`).

## Phase 5: Line Decorations in `extract_features_from_df` (Water-Flow Chevrons, Survey Plot)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 5.

- [ ] Task: Write the failing tests (Red)
    - [ ] In `tests/test_render_features.py`, add tests covering: a
      3-point `L_water-flow` polyline produces exactly 2 deduplicated,
      correctly-directed decorations (not 4); a single-segment (2-point)
      polyline produces exactly 1 decoration; a segment with a missing
      neighbor node produces no decoration and no crash; two independent
      `L_water-flow` polylines each get their own decoration without
      cross-contaminating through the shared dedup set.
    - [ ] Run `pytest tests/test_render_features.py -v`; confirm it fails
      with `KeyError: 'line_decorations'`.
- [ ] Task: Implement canonicalization + line decorations (Green)
    - [ ] Add `import math` to `cave_sketch/features/render_features.py`
      and a `_POLYLINE_NODE_RE`-backed `_canonical_segment_order(node_a,
      node_b)` helper that orders two `"{i}P{j}"`-style node IDs by
      ascending vertex index (preserving the DXF's original drawn
      direction).
    - [ ] Initialize `features["line_decorations"] = []` and a
      `decorated_segments` dedup set in `extract_features_from_df`, and
      extend the `style_type == "line"` branch to emit one decoration per
      unique segment (via `frozenset({nid, nbr})` dedup and the
      canonicalization helper) whose style has `line_decoration` set.
    - [ ] Run `pytest tests/test_render_features.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(render-features): add direction-canonicalized water-flow line decorations`).

## Phase 6: Fix Missing Points in `extract_features_from_json` (Folium Satellite View Bug)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 6.

- [ ] Task: Write the failing tests (Red)
    - [ ] In `tests/test_render_features.py`, add tests covering:
      dict-shaped `map_data["nodes"]` produces the expected icon point;
      list-shaped `map_data["nodes"]` produces the expected plain-marker
      point; a non-point/icon type (e.g. `L_wall`) in `nodes` is skipped;
      a `map_data` with no `"nodes"` key at all returns an empty points
      list without raising.
    - [ ] Run `pytest tests/test_render_features.py -v`; confirm it fails
      (`features["points"]` is always `[]` today).
- [ ] Task: Implement the points builder (Green)
    - [ ] In `extract_features_from_json`, add `"points": []` to the
      returned dict and a new `# Points` block (after the existing
      `# Lines` loop) that normalizes `map_data.get("nodes", {})`
      (dict-of-dicts or list-of-dicts) and builds point features for
      `STYLE_MAP` types `"point"`/`"icon"`, mirroring Phase 4's shape.
    - [ ] Run `pytest tests/test_render_features.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`fix(render-features): populate points in extract_features_from_json`)
      — note in the commit body that the Folium satellite HTML view
      rendered zero point markers for every type (not just the new ones)
      because this function never built a `"points"` list, despite
      `render_to_folium` already having point-rendering code waiting for
      one.

## Phase 7: Line Decorations in `extract_features_from_json` (Satellite View Bearing)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 7.

- [ ] Task: Write the failing test (Red)
    - [ ] In `tests/test_render_features.py`, add a test covering: two
      opposite-direction line entries for the same `L_water-flow` segment
      produce exactly 1 deduplicated decoration with `bearing_deg == 0.0`
      (due north).
    - [ ] Run `pytest tests/test_render_features.py -v`; confirm it fails
      with `KeyError: 'line_decorations'`.
- [ ] Task: Implement the bearing helper + line decorations (Green)
    - [ ] Add a `_bearing_deg(lat1, lon1, lat2, lon2)` planar-approximation
      compass-bearing helper near `_canonical_segment_order`.
    - [ ] Add `"line_decorations": []` to the returned dict and extend the
      `# Lines` loop in `extract_features_from_json` to emit one
      decoration per unique segment (same dedup/canonicalization rule as
      Phase 5, applied to `line["from"]["id"]`/`line["to"]["id"]`),
      computing `bearing_deg` via the new helper.
    - [ ] Run `pytest tests/test_render_features.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(render-features): add compass-bearing line decorations for satellite view`).

## Phase 8: Render Icon Points in Matplotlib (Survey Plot)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 8.

- [ ] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_matplotlib_backend.py` covering: two
      icon-type points render as a single scatter collection with 2
      offsets; a plain-marker point is unaffected (still renders as a
      scatter collection).
    - [ ] Run `pytest tests/test_matplotlib_backend.py -v`; confirm the
      icon-point test fails.
- [ ] Task: Implement icon-point rendering (Green)
    - [ ] In `cave_sketch/backend_renders/matplotlib.py`, import
      `MarkerStyle` and `icon_to_matplotlib_path`. Split
      `features["points"]` into plain vs. icon points; keep the existing
      marker-character grouping for plain points unchanged, and add a
      parallel grouping-by-icon-name loop that builds one
      `MarkerStyle(icon_to_matplotlib_path(name))` per group and scatters
      it the same way.
    - [ ] Run `pytest tests/test_matplotlib_backend.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(matplotlib-backend): render icon-style points with custom marker paths`).

## Phase 9: Render Line Decorations in Matplotlib (Water-Flow Chevrons on the Survey Plot)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 9.

- [ ] Task: Write the failing test (Red)
    - [ ] In `tests/test_matplotlib_backend.py`, add a test covering: two
      `line_decorations` entries at different angles each produce a
      `PathPatch` in `ax.patches`.
    - [ ] Run `pytest tests/test_matplotlib_backend.py -v`; confirm it
      fails (`assert len(chevron_patches) == 2`).
- [ ] Task: Implement line-decoration rendering (Green)
    - [ ] Import `PathPatch` (alongside the existing `Polygon as
      MplPolygon` import) and `Affine2D`. Add a new block at the end of
      `render_to_matplotlib` that, for each `line_decorations` entry,
      builds a rotated/translated/scaled `PathPatch` (unfilled, stroke
      only) via `Affine2D().scale(size).rotate(angle_rad).translate(mid_x,
      mid_y) + ax.transData` and adds it via `ax.add_patch`.
    - [ ] Run `pytest tests/test_matplotlib_backend.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(matplotlib-backend): render rotated water-flow chevrons along line segments`).

## Phase 10: Render Icon Points in Folium (Satellite HTML View)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 10.

- [ ] Task: Write the failing tests (Red)
    - [ ] Create `tests/test_folium_backend.py` covering: an icon-type
      point produces `viewBox` and (JSON-escaped) `stroke=\"tan\"` in the
      rendered map HTML; a plain-marker point still produces
      `L.circleMarker(` (note: Folium/Jinja2 JSON-escapes the DivIcon
      HTML — `<`/`>` become `<`/`>` and `"` becomes `\"` — so
      assertions must target substrings that survive that encoding, not
      raw `<svg>` tags).
    - [ ] Run `pytest tests/test_folium_backend.py -v`; confirm the
      icon-point test fails (no `viewBox` in output — a `CircleMarker` is
      always emitted today).
- [ ] Task: Implement icon-point rendering (Green)
    - [ ] In `cave_sketch/backend_renders/folium.py`, import
      `icon_to_svg_path_d` and add an `_icon_svg_html(icon_name, color,
      size_px, rotate_deg=0.0)` helper building an inline `<svg>` inside a
      rotatable `<div>`. In the points loop, branch on `"icon" in p`: use
      `folium.Marker(icon=folium.DivIcon(html=_icon_svg_html(...)))`
      instead of `CircleMarker` for icon points; keep `CircleMarker`
      unchanged otherwise.
    - [ ] Run `pytest tests/test_folium_backend.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(folium-backend): render icon-style points as inline-SVG DivIcons`).

## Phase 11: Render Line Decorations in Folium (Water-Flow Chevrons on Satellite View)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 11.

- [ ] Task: Write the failing test (Red)
    - [ ] In `tests/test_folium_backend.py`, add a test covering: a
      `line_decorations` entry with `bearing_deg: 90.0` produces
      `rotate(90.0deg)` and (JSON-escaped) `stroke=\"steelblue\"` in the
      rendered HTML.
    - [ ] Run `pytest tests/test_folium_backend.py -v`; confirm it fails.
- [ ] Task: Implement line-decoration rendering (Green)
    - [ ] Add a new block at the end of `render_to_folium` that, for each
      `line_decorations` entry, builds a rotated `DivIcon` via
      `_icon_svg_html(..., rotate_deg=dec["bearing_deg"])` and adds it as
      a `folium.Marker`.
    - [ ] Run `pytest tests/test_folium_backend.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(folium-backend): render rotated water-flow chevrons on the satellite map`).

## Phase 12: Generate and Commit Icon PNG Assets (for KML/KMZ)

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 12.

- [ ] Task: Write the failing test (Red)
    - [ ] Create `tests/test_icon_assets.py` asserting every icon in
      `style_icons.ICONS` has a valid PNG (correct magic bytes) under
      `cave_sketch/assets/icons/<name>.png`.
    - [ ] Run `pytest tests/test_icon_assets.py -v`; confirm it fails
      (missing asset files).
- [ ] Task: Write and run the generation script (Green)
    - [ ] Create `scripts/generate_icon_assets.py` (dev tooling, not
      imported at runtime) that rasterizes each `ICONS` entry via
      `icon_to_matplotlib_path` to a small transparent PNG under
      `cave_sketch/assets/icons/`.
    - [ ] Run `python scripts/generate_icon_assets.py`; confirm 5 PNGs are
      written.
    - [ ] Run `pytest tests/test_icon_assets.py -v`; confirm it passes.
- [ ] Task: Verify and commit
    - [ ] Commit the script, the 5 generated PNGs (as binary files), and
      the test (`feat(assets): generate and commit rasterized icon PNGs for KML/KMZ export`).

## Phase 13: Use Icon PNGs and Heading Rotation in KML/KMZ Export

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 13.

- [ ] Task: Write the failing tests (Red)
    - [ ] In `tests/test_kmz_export.py` (add `import pytest`), add tests
      covering: an icon-type point's `<Style id="icon_B_blocks">`
      references `icons/block.png` and its placemark's `styleUrl` matches;
      an `L_water-flow` line produces one decoration placemark with
      `<IconStyle><heading>0.0</heading></IconStyle>` and an
      `icons/water_flow_chevron.png` href; `render_to_kmz`'s zip contains
      `icons/block.png` and `icons/water_flow_chevron.png`.
    - [ ] Run `pytest tests/test_kmz_export.py -v`; confirm the new tests
      fail.
- [ ] Task: Implement icon styles, decoration placemarks, and KMZ bundling (Green)
    - [ ] In `cave_sketch/backend_renders/google_earth.py`, add `from
      pathlib import Path` and `_ICONS_DIR = Path(__file__).resolve()
      .parent.parent / "assets" / "icons"`.
    - [ ] In the `render_to_kml` Style-generation loop, add an `"icon"`
      branch (before `"point"`) that writes `<IconStyle><Icon><href>
      icons/{icon}.png</href></Icon><scale>...</scale></IconStyle>`.
    - [ ] In the `# --- POINTS ---` block, change the hardcoded
      `f"#point_{ntype}"` `styleUrl` to the type-aware
      `f"#{style_info['type']}_{ntype}"`.
    - [ ] Add a `# --- LINE DECORATIONS ---` block emitting one
      `Placemark` per `features["line_decorations"]` entry, with an
      inline per-placemark `<Style>`/`<IconStyle>` carrying `<Icon><href>`,
      `<scale>`, and `<heading>{bearing_deg}</heading>`.
    - [ ] Update `render_to_kmz` to collect every icon name referenced by
      an `"icon"`-type `STYLE_MAP` entry or a `line_decoration`, and
      `zf.write` each existing PNG into the zip under `icons/<name>.png`.
    - [ ] Run `pytest tests/test_kmz_export.py -v`; confirm all pass.
- [ ] Task: Verify and commit
    - [ ] Commit (`feat(kml-backend): use rasterized icon PNGs and per-placemark heading rotation`).

## Phase 14: Fix the Stale `"BLOCK"` Placeholder in the Existing KMZ Test

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 14.

- [ ] Task: Confirm the pre-existing test now fails for the right reason
    - [ ] Run `pytest tests/test_kmz_export.py::test_compact_kml_export -v`;
      confirm it fails (`type: "BLOCK"` no longer matches any `STYLE_MAP`
      entry after Phase 3's rename, so the node is silently skipped).
- [ ] Task: Fix the placeholder type
    - [ ] In `tests/test_kmz_export.py:18`, change
      `{"id": "5", "lat": 5.0, "lon": 5.0, "type": "BLOCK"}` to
      `{"id": "5", "lat": 5.0, "lon": 5.0, "type": "B_blocks"}`.
    - [ ] Run `pytest tests/test_kmz_export.py::test_compact_kml_export -v`;
      confirm it passes.
- [ ] Task: Verify and commit
    - [ ] Commit (`test(kmz): update placeholder point type from removed BLOCK to B_blocks`).

## Phase 15: Full-Suite Verification, Real-Fixture Smoke Test, and Android Check

Full code: `docs/superpowers/plans/2026-09-30-dxf-icon-elements-plan.md` → Task 15.

- [ ] Task: Full automated suite
    - [ ] Run `pytest -v`; confirm every test from Phases 1-14 passes with
      no regressions in the pre-existing suite.
- [ ] Task: Real-fixture smoke test
    - [ ] Using a throwaway script (not committed), run `parse_dxf` +
      `draw_survey` + `draw_map` against `val_cont_06-0p.dxf`,
      `val_mul_4-1p.dxf`, and `grotta_mittelbergferner-1p.dxf` (already at
      the repo root) and confirm no exceptions, producing a PDF and an
      HTML+KMZ pair for each.
- [ ] Task: Manual visual verification
    - [ ] Open each generated PDF and confirm the entrance/continuation/
      block/water-flow-point icons and the water-flow line chevrons all
      appear, correctly colored and shaped.
    - [ ] Open each generated HTML in a browser and confirm the same
      icons appear on the satellite tiles — this is the view that was
      previously blank for every point type (Phase 6's fix).
    - [ ] Open each generated KMZ in Google Earth (or inspect `doc.kml`)
      and confirm the icons render there too, with water-flow chevrons
      rotated to match segment direction.
- [ ] Task: Android verification (manual, by the maintainer)
    - [ ] Build and run the Android app, load a DXF containing these
      element types, generate a survey plot and a satellite map, and
      confirm the icons render identically to the webapp. This validates
      the Global Constraints' asset-bundling assumption (Chaquopy
      packaging `cave_sketch/assets/icons/*.png` correctly) and cannot be
      verified without Android build tooling/an emulator — call it out
      explicitly rather than skipping it silently.
