# Phase 2 — Satellite Map — Spec

**Initiative:** CaveSketch Mobile App
**Phase:** 2 · Satellite Map Screen
**Status:** Approved (design)
**Date:** 2026-06-19
**Level:** 2 (per-phase). See `../../umbrella-spec.md` for the roadmap.

---

## 1. Goal

Build Screen 2 of the Android app — the **Satellite Map** screen — with full
feature parity to the web page `app/pages/2_satellite_map.py`. The user
georeferences the cave by entering known GPS points and gets a **KMZ + JSON**
export (for offline GIS apps such as Locus Map) plus an interactive HTML map
preview. KMZ and JSON generation work fully offline; only the map *preview*
requires internet and degrades gracefully when offline.

This phase replaces the Phase 1 `SatelliteStubScreen` with the real screen,
leaving the existing `AppNavHost` bottom-bar navigation unchanged.

## 2. Parity scope (mirror the web page)

- **GPS points editor** — add/remove rows of `(station, lat, lon)`; coordinates
  parsed via the core `cave_sketch.geo.coordinates.parse_coordinate` (decimal,
  accepting `.` or `,` as the separator). Per-field inline error when a
  coordinate cannot be parsed.
- **Survey name** — text field, prefilled from the shared store (see §4).
- **Map rotation angle** — numeric input (°), default from the shared store / 0.
- **Additional JSON maps** — multi-select `.json` file picker; imported maps are
  combined into the export by `draw_map`.
- **Generate** → `draw_map` → outputs **HTML, JSON, KMZ** → **Save/Share** each
  via the Android share sheet.
- **Preview** — render the generated HTML in a `WebView` when online; degrade
  gracefully when offline (§6).

## 3. Non-goals

- No offline satellite-tile bundling/caching (possible future phase).
- No new map/GIS features beyond web parity.
- No changes to `cave_sketch/` (stays untouched and Streamlit-free) and no
  changes to the Streamlit web app.
- The deferred ~60s `draw_survey` rendering optimization is a **separate track**,
  not part of this phase.

## 4. Architecture & components

Mirrors the Phase 1 layering (UI → bridge → core). New/changed pieces:

### 4.1 Shared store (cross-screen hand-off — Option A)

The Satellite screen needs the parsed cave-map CSV that the Survey Plot screen
produces. We surface it through an app-scoped reactive store rather than nav
arguments or implicit files.

- **`SurveyResultStore`** — held by `CaveSketchApplication`, exposes
  `StateFlow<SurveyResult?>` where
  `SurveyResult = { mapCsvPath: String, surveyName: String }`.
- Written by `SurveyPlotViewModel` on a successful Survey Plot generation.
- Observed by `SatelliteViewModel` to drive the gating empty-state and to pass
  `mapCsvPath` into the satellite bridge.
- This is the faithful, reactive analog of the web's `map_csv` / `merged_map_csv`
  / `map_loaded` session keys.

### 4.2 Phase 1 additive change — surface the effective map CSV

`survey_bridge.generate_survey_plot` currently returns only `{ "pdf_path" }`. It
merges internally inside `draw_survey` but never surfaces the CSV. Extend it to
also return the **effective map CSV path**:

- No merge → the parsed `map.csv` (already written by `resolve_input`).
- Merge present (child map + parent/child stations) → replicate the web glue
  from `app/pages/1_survey_plot.py`: call core `merge_surveys`, write
  `merged_map.csv` into `work_dir`, and return that path.
- Return shape becomes `{ "pdf_path", "map_csv_path" }` (the latter omitted /
  null when only a section was generated, i.e. no map).

`SurveyPlotViewModel` writes `SurveyResult(mapCsvPath, surveyName)` into the
store when `map_csv_path` is present. Core stays untouched; web stays unchanged;
the merged-CSV writing is bridge glue (the algorithm `merge_surveys` lives in
core and is reused, not duplicated).

### 4.3 New mobile pieces

- **`satellite_bridge.py`** (under `android/app/src/main/python/`) — single
  entrypoint `generate_satellite_map(inputs_json, work_dir)`. Validates GPS
  points, calls `cave_sketch.satellite_view.draw_map`, returns
  `{ "html_path", "json_path", "kmz_path" }` or `{ "error", "detail" }`. Same
  structured-error pattern as `survey_bridge.py`. Never imported by `cave_sketch`.
- **`SatelliteBridge.kt`** — thin Kotlin↔Python wrapper (mirrors `SurveyBridge.kt`).
- **`SatelliteViewModel.kt`** — `StateFlow<SatelliteState>`; holds the GPS-rows
  list, rotation, imported JSON paths; observes `SurveyResultStore`.
- **`SatelliteScreen.kt`** — replaces `SatelliteStubScreen` (no `AppNavHost`
  rename/restructure). Small composables: `GpsPointsEditor`, `MapWebView`; reuse
  the existing `FilePickerRow`.
- **`Share.kt`** — generalize `sharePdf` → `shareFile(path, mimeType)` so HTML,
  JSON, and KMZ all share through the existing `FileProvider` setup.

### 4.4 Inputs JSON contract (Kotlin → `satellite_bridge`)

```json
{
  "map_path": "<effective map CSV from the shared store>",
  "gps_points": [{"station": "13", "lat": 45.1234, "lon": 7.5678}, ...],
  "survey_name": "MySurvey",
  "rotation_angle": 0.0,
  "additional_json_maps": ["<path>", ...]
}
```

The bridge maps these onto
`draw_map(map_path, gps_points, output_path, map_name, additional_json_maps, rotation_angle)`,
with `output_path = work_dir/survey.html` (JSON/KMZ paths derived by `draw_map`).

## 5. State machine (`SatelliteViewModel`)

`SatelliteState`:

- **Idle** — initial.
- **NoMap** — `SurveyResultStore` is empty; show empty-state:
  *"Generate a survey plot first."* Generate is unavailable.
- **Generating** — bridge call in flight (staged message).
- **Success(htmlPath, jsonPath, kmzPath, online)** — outputs ready; preview shown
  if `online`, otherwise the offline banner; Save/Share enabled for all three.
- **Error(message)** — structured error detail surfaced.

## 6. Offline behavior (umbrella §6 — graceful degrade only)

- `draw_map` runs fully on-device; **JSON + KMZ are always produced and
  savable/shareable**, online or offline.
- Connectivity is checked (`ConnectivityManager`) before showing the preview.
- **Online:** load `survey.html` into the `WebView` (`file://` from `filesDir`,
  JavaScript enabled, external navigation blocked).
- **Offline:** skip the `WebView`; show a banner —
  *"No connection — satellite preview unavailable. KMZ & JSON are ready to
  save/share."* The Save/Share actions remain fully functional.
- No tile bundling/caching.

## 7. Error handling

The bridge converts every failure into `{ "error", "detail" }`, surfaced as
`SatelliteState.Error`. Cases:

- **No GPS points / empty fields** — mirror web `validate_known_points`: every
  row needs a non-empty station and parseable lat/lon. Generate disabled until
  valid.
- **Invalid coordinate** — `parse_coordinate` returns `None` → inline per-field
  error in the editor.
- **No anchor matched** — `draw_map` warns and skips a missing anchor station.
  If **no** anchor matches any `Node_Id` (all coords would be NaN), the bridge
  returns a clear error rather than handing back a broken map. (Additive guard in
  the bridge, not core.)
- **No map in store** — unreachable Generate (NoMap state).
- **Render failure** — caught and shown as Error with detail.

## 8. Testing

- **Bridge (Python):** `generate_satellite_map` with a sample map CSV + GPS
  points → asserts HTML/JSON/KMZ written and JSON structure sane; invalid-input
  and no-anchor-match error paths. (`draw_map` itself already has core coverage;
  bridge tests stay thin.)
- **Survey-bridge change:** extend the existing survey bridge / ViewModel test to
  assert the effective map CSV path is returned for both the no-merge and merge
  cases.
- **`SatelliteViewModel` (Kotlin JVM unit test, like `SurveyPlotViewModelTest`):**
  Idle→NoMap, NoMap→ready on store update, Generating→Success/Error, GPS row
  add/remove/edit, online vs offline flag (connectivity injected).
- **Manual device verification (mirrors Phase 1):** generate on a real device,
  confirm KMZ opens in Locus Map, preview online, and the graceful banner appears
  with airplane mode on.

## 9. Verification gates (before "done")

- `uv run ruff check .`
- `uv run mypy cave_sketch/` (unaffected, must stay green)
- `uv run pytest`
- Kotlin unit tests pass.
- Log the phase to `android/DEVLOG.md` (Phase 1 entry format).

## 10. Exit criteria

Feature parity with the web Satellite Map page on a real device, including:
GPS-point georeferencing, JSON-map combination, HTML preview when online, the
graceful offline banner, and **offline KMZ + JSON** save/share.
