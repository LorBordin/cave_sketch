# Spec: Extended Title Block Metadata & Adaptive Placement — Backend, Webapp, Android

## Overview

The technical title block (cartiglio) of the Survey Plot PDF currently shows
cave name, surveyor, today's date, total length and (when a section exists)
depth. It is a fixed-size box at fixed figure coordinates
(`cave_sketch/survey/graphics/title_block.py`, `fig.add_axes((0.68, 0.88, 0.27, 0.08))`);
overlap with the drawing is avoided only by `fig.subplots_adjust(top=0.86)` in
`cave_sketch/survey/renderer.py`.

This track:

1. Adds five optional fields to the title block — **Comune** (municipality),
   **Disegnatore** (drawer), **Coordinate** (GPS lat/lon of the cave),
   **Quota slm** (elevation) and **Declinazione** (magnetic variation, already
   an input) — each printed **only when entered**.
2. Exposes the new inputs in both the Streamlit webapp and the Android app.
   Android also gains the **magnetic variation** input it currently lacks
   (frontend-only; the backend already supports it).
3. Replaces the fixed-size box with a **measured** box and an **adaptive
   placement** step that puts it in the best free position on the page.

Both apps render through the same Python `draw_survey` (Android via Chaquopy
symlink to `cave_sketch/`), so all rendering changes are made once.

## Decisions (locked with maintainer)

| Decision | Choice |
|----------|--------|
| Placement strategy | Hybrid: header slot → free in-plot corner → grow header (fallback) |
| GPS input | Two decimal-degree number fields (Lat, Lon), validated; printed `45.12345° N, 11.54321° E` |
| Magnetic variation in title block | Reuse existing `magnetic_variation_deg`; printed only when `!= 0`, as `2.5° E` / `1.2° W`. A true 0° is not printed (accepted edge case). |
| Elevation | Number in metres, printed as integer `1250 m` |
| PDF label language | Italian, consistent with existing hardcoded labels |
| Android magnetic variation | Added in this track (frontend + bridge pass-through only) |
| Date row | Unchanged (today's date) |

## Functional Requirements

### FR-1: `TitleBlockInfo` model
- Add to `cave_sketch/survey/config.py`:
  ```python
  @dataclass
  class TitleBlockInfo:
      surveyor_name: str = ""
      drawer_name: str = ""
      municipality: str = ""
      latitude: Optional[float] = None
      longitude: Optional[float] = None
      elevation_m: Optional[float] = None
  ```
- `__post_init__` validation (the trust boundary for both apps):
  - `latitude` and `longitude` must be both `None` or both set; otherwise `ValueError`.
  - `-90 <= latitude <= 90`, `-180 <= longitude <= 180`; otherwise `ValueError`.
  - String fields are stripped; whitespace-only counts as empty.
- Remove `surveyor_name` from `SurveyConfig`. `draw_survey(...)` replaces its
  `surveyor_name` kwarg with `title_block: Optional[TitleBlockInfo] = None`
  (defaults to empty `TitleBlockInfo()`). `render_survey(...)` gains
  `title_block` and `magnetic_variation_deg` params. All in-repo callers
  (webapp page, Android bridge, tests) are migrated.
- `magnetic_variation_deg` stays a separate `draw_survey` param (it drives
  geometry rotation); it is forwarded to the renderer for display only.

### FR-2: Row building
- New pure function `build_title_rows(info, magnetic_variation_deg, date, total_length, total_depth) -> list[str]`
  returning rows in this order, omitting optional rows with no value:
  1. `Rilevatore: <name>` — always present, `-` when empty (current behaviour)
  2. `Disegnatore: <name>` — if set
  3. `Data: DD/MM/YYYY` — always
  4. `Comune: <name>` — if set
  5. `Coordinate: 45.12345° N, 11.54321° E` — if lat/lon set (5 decimals, N/S, E/W suffix, absolute values)
  6. `Quota slm: 1250 m` — if elevation set (rounded integer, sign kept)
  7. `Declinazione: 2.5° E` — if variation `!= 0` (1 decimal, E for positive, W for negative)
  8. `Sviluppo: 123.4 m` — always
  9. `Dislivello: 45.6 m` — if `total_depth is not None`
- Free-text values longer than 30 characters are truncated with `…`.

### FR-3: Box measurement
- New module `cave_sketch/survey/graphics/title_block_layout.py`.
- `measure_title_block(fig, rows) -> (width, height)` in figure-fraction units,
  computed from actual text extents via the figure's renderer at the box font
  size (8.5 pt), plus fixed inner padding and line spacing.

### FR-4: Placement
- `render_survey` draws the cave name and all subplots (incl. north arrow and
  scale rule) **before** placing the box, then calls the placement function.
- Candidates are tried in order; the first that fits wins:
  1. **Header slot** — top-right of the header band (right edge at x=0.95,
     top at y=0.96). Fits if its bottom stays above the subplots' top plus a
     gap, and it does not overlap the cave-name text extent.
  2. **In-plot corner** — the four corners of the map axes (order:
     top-right, top-left, bottom-right, bottom-left), then the section axes in
     the same order, inset by a small margin, box fully inside the axes. A
     corner is free if no obstacle intersects the box rectangle (in display
     coordinates, after `fig.canvas.draw()`):
     - survey lines/paths: tested with `Path.intersects_bbox` on the
       transformed path (not the artist bounding box);
     - texts, markers/collections, patches (north arrow, scale rule):
       tested via their window extents.
     - Grid lines (`zorder=0` axvline/axhline from `_add_grid`) are **ignored**;
       the box has an opaque white face and covers them.
  3. **Grow header (fallback)** — lower `fig.subplots_adjust(top=...)` just
     enough to fit the box in the header slot; redraw. Always succeeds.
- The placement function returns the chosen rectangle and a label of which
  strategy was used (for tests).

### FR-5: Box drawing
- `title_block.py` draws the box as an axes at the chosen rectangle (white
  face, visible border, no ticks) with rows top-to-bottom using fixed line
  spacing — no more step heuristics based on row count.
- Cave name rendering (`wrap_text`, left of header) is unchanged.

### FR-6: Webapp
- `app/pages/1_survey_plot.py`: next to the Surveyor input add
  `Drawer name`, `Municipality` (text), `Latitude`, `Longitude`, `Elevation (m a.s.l.)`
  (optional number inputs; empty = not set; lat/lon bounded to valid ranges).
- Persist in `AppState` (`app/session.py`) like `surveyor_name`.
- Build a `TitleBlockInfo`; on `ValueError` (e.g. only one of lat/lon) show
  `st.error` and do not render.

### FR-7: Android
- `SurveyInputs` (`SurveyPlotViewModel.kt`) gains `drawerName`,
  `municipality`, `latitude`, `longitude`, `elevationM`, `magneticVariationDeg`.
- `SurveyPlotScreen.kt` "Survey details" card: text fields for drawer and
  municipality; decimal fields for lat, lon, elevation, with inline error
  when out of range or only one of lat/lon is set (render button disabled).
- `SettingsForm.kt`: magnetic variation decimal field (+E/−W), default 0,
  matching the webapp's settings panel.
- `toJson()` emits `drawer_name`, `municipality`, `latitude`, `longitude`,
  `elevation_m` (JSON `null` when empty) and `magnetic_variation_deg`.
- `android/app/src/main/python/survey_bridge.py` builds `TitleBlockInfo` and
  passes `magnetic_variation_deg` to `draw_survey`; a `ValueError` is returned
  as the bridge's existing error result.

## Non-goals
- DXF, Google Earth and satellite exports are unchanged.
- No i18n framework; PDF labels stay Italian, UI labels stay English.
- No survey-date input (date stays "today").
- No reuse of known georeferencing GPS points as cave coordinates.
- No free-text/DMS/UTM coordinate formats.

## Testing
- `TitleBlockInfo` validation: lat without lon, out-of-range values, whitespace strings.
- `build_title_rows`: only-required fields, all fields, formatting (N/S/E/W, decimals, rounding, truncation), variation 0 omitted.
- Placement (synthetic figures):
  - small box → header slot;
  - large box + sparse data → in-plot corner, no intersection with survey paths/arrow/rule;
  - large box + dense data → grow-header fallback, subplots top lowered, no overlap;
  - grid lines do not block a corner;
  - box never overlaps cave-name text.
- Integration: `draw_survey` with full metadata produces all rows.
- Bridge: `tests/test_survey_bridge.py` passes new fields and variation; invalid lat/lon returns error.
- Android: `SurveyPlotViewModelTest.kt` asserts new JSON keys and nulls.
- Regression: existing baselines (`tests/fixtures/render_baselines/`) must
  remain valid when no new fields are entered (header slot = today's
  position). If the measured box changes pixels, regenerate baselines and
  note it in DEVLOG. Add one new baseline with all fields filled.

## Acceptance
- Entering any subset of the new fields in either app produces a PDF showing
  exactly those rows, in the specified order and format.
- With no new fields entered, the box stays in today's top-right header
  position with today's rows (minor size/spacing differences from measured
  sizing are allowed; baselines regenerated if so).
- With all fields entered, the box never overlaps survey geometry, north
  arrow, scale rule or cave name.
- Android exposes magnetic variation, and it rotates the map exactly as on the webapp.
