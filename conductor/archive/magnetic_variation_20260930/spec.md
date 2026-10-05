# Spec: Magnetic Variation (Declination) Correction — Backend & Webapp

## Overview

Cave survey data is captured with a magnetic compass, so the `X`/`Y` coordinates
in the map CSV are referenced to **magnetic** north, not **geographic (true)**
north. Today the app has no concept of this distinction: the north arrow on the
Survey Plot always points along the data's own `+Y` axis, and the Satellite Map
page's georeferencing (`cave_sketch/satellite_view/map.py`) assumes `X`=Easting,
`Y`=Northing with no correction, so any real-world declination shows up as a
systematic rotational error against satellite imagery.

This track adds an optional **magnetic variation** input, entered once per
survey on the Survey Plot page. When set, the map coordinates are rotated so
that `+Y` (and the fixed, upward-pointing north arrow) represent true
geographic north instead of magnetic north. The same corrected orientation
automatically carries over to the Satellite Map page's georeferencing. When
left at its default (`0`), behavior is byte-for-byte unchanged from today.

This track is **backend + webapp only**. The Android app shares the backend
package (`cave_sketch/`) via a Chaquopy symlink and needs no backend change,
but its Kotlin UI still needs new input fields — that is an explicit follow-up
story; see "Handoff to Android story" below.

## Decisions (locked with maintainer)

| Decision | Choice |
|----------|--------|
| Input shape | Single signed number, degrees, **+East / −West** (standard compass-software convention) |
| Relationship to existing "Map rotation (°)" | Independent, new field. Existing field keeps rotating data **and** arrow together (page-layout only); the new field rotates data only, arrow stays fixed pointing up = true north. The two compose. |
| Scope | Map/plan view only. Section (vertical profile) view is never touched — it has no compass-north meaning. |
| Satellite Map page | Auto-applies the survey's magnetic variation underneath the existing manual "Map rotation angle" field, which is unchanged and composes on top. |
| `cave_sketch/geo/georef.py` (`georeference()`/`GpsRef`) | Dead code (only its own test imports it, no UI path uses it) — left untouched, out of scope. |
| Default value | `0.0` — no-op, guarantees existing behavior is preserved when the field is left blank/zero. |

## Functional Requirements

### FR-1: Shared correction utility
- Create `cave_sketch/geo/declination.py` with:
  `apply_magnetic_variation(df: pd.DataFrame, variation_deg: float) -> pd.DataFrame`
- Rotates the `X`/`Y` columns about the DataFrame's own centroid, using the
  existing `rotate_points()` helper from `cave_sketch/features/geometry.py`
  (`mode="cartesian"`, which is CCW-positive).
- **Sign convention (non-obvious, must be preserved):** a positive
  (East) `variation_deg` means the point set must be rotated by **`-variation_deg`**
  in `rotate_points`'s CCW-positive convention. Derivation: a station recorded
  at magnetic-azimuth 0° (on the local `+Y` axis) with `East` declination `D`
  has true-azimuth `D` (magnetic north is `D°` east of true north), which is a
  **clockwise** rotation of `D°`, i.e. `rotate_points(..., angle_deg=-D)`.
  Worked example used as the test oracle: `D=+10°`, point `(0, 10)` → approx.
  `(1.736, 9.848)`.
- Returns an unmodified copy (no-op) when `variation_deg == 0`.
- No Streamlit imports; pure function, fully unit-testable in isolation.

### FR-2: Survey Plot backend — `cave_sketch/survey/survey.py`
- `draw_survey()` gains a new keyword argument `magnetic_variation_deg: float = 0.0`.
- Applied via `apply_magnetic_variation()` to `merged_map` (the **post-merge**
  map DataFrame, so a parent+child merge gets one consistent correction),
  immediately before `_df_to_survey(merged_map, title)`.
- `merged_section` is never passed through the correction.
- This is a data-preprocessing step, not a rendering parameter: it is **not**
  added to `SurveyConfig` (which stays scoped to matplotlib rendering
  options); `render_survey`/`create_survey`/the existing `rotation_deg`
  page-layout rotation are unaffected and continue to operate on the
  already-corrected coordinates exactly as they do today.

### FR-3: Satellite Map backend — `cave_sketch/satellite_view/map.py`
- `draw_map()` gains a new keyword argument `magnetic_variation_deg: float = 0.0`.
- Applied via `apply_magnetic_variation()` to `map_df` immediately after
  `pd.read_csv(map_path)`, **before** the existing `rotation_angle` manual
  rotation block. The two rotations compose (declination correction first,
  then the unchanged manual/cosmetic rotation on top).

### FR-4: Webapp — Survey Plot page
- `app/components/settings_panel.py`: add
  `st.number_input("🧭 Magnetic variation (°, +E/−W)", value=0.0, step=0.1)`,
  returned in the settings dict as `magnetic_variation_deg`.
- `app/session.py`: add session default `"magnetic_variation_deg": 0.0`.
- `app/pages/1_survey_plot.py`: pop `magnetic_variation_deg` from `settings`
  and pass it to `draw_survey(...)`; also write it to
  `st.session_state.magnetic_variation_deg` so the Satellite Map page can read
  the same value.

### FR-5: Webapp — Satellite Map page
- `app/pages/2_satellite_map.py`: pass
  `st.session_state.magnetic_variation_deg` into `draw_map(...)`.
- When the value is non-zero, show an informational caption near the existing
  "Map rotation angle" input, e.g.:
  `🧭 Magnetic variation correction: +3.5° applied automatically from Survey Plot`,
  so the (otherwise invisible) automatic correction is visible to the user.

## Non-Functional Requirements

- `apply_magnetic_variation()` fully type-annotated, no Streamlit dependency.
- `uv run ruff check .`, `uv run mypy cave_sketch/`, and `uv run pytest` must
  all pass.
- Backward compatibility: with `magnetic_variation_deg` omitted or `0.0`,
  `draw_survey()` and `draw_map()` output must be identical to current
  behavior (existing tests must continue to pass unmodified).

## Testing Plan

- `apply_magnetic_variation()` unit tests: zero-variation no-op (returns
  equal values), the `+10°` worked example above, a West/negative case, and a
  centroid round-trip check (rotating and rotating back by `-variation_deg`
  restores original coordinates within floating-point tolerance).
- `draw_survey()`: a test asserting output is unchanged when
  `magnetic_variation_deg=0` (or omitted) vs. today's baseline; a test
  asserting the map subplot's station coordinates reflect the corrected
  values when non-zero, while the section subplot's coordinates do not.
- `draw_map()`: a test asserting `magnetic_variation_deg` and `rotation_angle`
  compose (i.e. applying both equals applying declination then rotation in
  sequence).

## Handoff to Android Story (do not implement now)

The Android app has **no independent reimplementation** of survey rendering
or georeferencing — it embeds the real `cave_sketch` package via Chaquopy
through a relative symlink (`android/app/src/main/python/cave_sketch` →
repo-root `cave_sketch/`), documented in `docs/android/architecture.md`.
Once this track ships, Android automatically gains the new
`magnetic_variation_deg` kwargs on `draw_survey`/`draw_map` for free — no
Python-side Android work is needed.

A follow-up story should cover only the Kotlin UI wiring:
1. Add `magneticVariationDeg` to the `SurveyInputs` data class in
   `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt`,
   and include it in `toJson()`'s `settings` object as
   `magnetic_variation_deg` (must match the key name this track uses).
2. Add a `StepperControl` for it in
   `android/app/src/main/java/com/cavesketch/app/ui/components/SettingsForm.kt`,
   alongside the existing "Map rotation (°)" control.
3. Add the equivalent field/state to
   `android/app/src/main/java/com/cavesketch/app/ui/SatelliteViewModel.kt`
   and include it in `buildJson()` so `satellite_bridge.generate_satellite_map`
   receives it.
4. Update `docs/android/architecture.md` (+ `.it.md`) and add/extend Kotlin
   unit tests (`SurveyPlotViewModelTest.kt`, `SatelliteViewModelTest.kt`,
   `SettingsFormTest.kt`) for the new control.
5. No changes needed to the on-device pip/Chaquopy dependency stack — the
   feature lives entirely in already-vendored `cave_sketch` code.

## Out of Scope

- Any Android (Kotlin) implementation — see handoff notes above.
- `cave_sketch/geo/georef.py` / `GpsRef` / `georeference()` — dead code, no
  live UI path uses it.
- Automatic declination lookup (e.g. from a magnetic model given GPS + date).
  Purely a manual numeric input in this track.
- Per-child-survey distinct declination values — one value applies to the
  whole rendered/merged result.
- Any change to the existing "Map rotation (°)" / `rotation_angle` fields'
  behavior — both remain exactly as they are today.
