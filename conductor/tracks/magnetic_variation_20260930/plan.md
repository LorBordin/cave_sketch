# Plan: Magnetic Variation (Declination) Correction

> Full code for every step lives in
> `docs/superpowers/plans/2026-09-30-magnetic-variation.md`. This conductor
> plan mirrors it in phases. Follow the standard task workflow in
> `conductor/workflow.md` (Red → Green → verify → commit → git note → mark
> `[x]`). Phases are ordered so the shared correction utility lands first,
> then each backend call site, then the two webapp pages that surface it.
> Design spec: `./spec.md` (also at
> `docs/superpowers/specs/2026-09-30-magnetic-variation-design.md`).

## Global Constraints

- Default `magnetic_variation_deg = 0.0` on every touched function must be a
  no-op: output byte-identical to omitting the argument entirely.
- Sign convention: positive = East declination, negative = West (true
  bearing = magnetic bearing + variation) — rotate coordinates by
  `-variation_deg` in `rotate_points()`'s CCW-positive convention. Worked
  example: `variation_deg=+10`, point `(0, 10)` about centroid `(0, 0)` →
  `(1.7364817766693033, 9.848077530122081)`.
- The correction applies to the map/plan view only — never the
  section/profile view.
- `cave_sketch/geo/georef.py` (`georeference()` / `GpsRef`) is dead code —
  do not touch it.
- `cave_sketch/geo/declination.py` has no Streamlit import; fully
  type-annotated.
- `uv run ruff check .`, `uv run mypy cave_sketch/`, and `uv run pytest`
  must all pass after every task.
- Test fixtures use non-purely-numeric `Node_Id`/`Links` values (e.g.
  `"st1"`, `"st2"`) — matches existing repo test fixtures and avoids a
  pandas numeric-dtype inference issue elsewhere in the pipeline.
- Android (Kotlin) code is out of scope for this track — see the spec's
  "Handoff to Android Story" section for the follow-up.

---

## Phase 1: Shared Magnetic-Variation Correction Utility [checkpoint: 26fa142]

Full code: `docs/superpowers/plans/2026-09-30-magnetic-variation.md` → Task 1.

- [x] Task: Write the failing tests (Red) [702249d]
    - [x] Create `tests/test_declination.py` covering: zero-variation no-op
      copy, `+10°` East worked example, `-10°` West mirror, and a
      `+7.5°`/`-7.5°` round-trip restoring the original coordinates.
    - [x] Run `uv run pytest tests/test_declination.py -v`; confirm it fails
      with `ModuleNotFoundError: No module named 'cave_sketch.geo.declination'`.
- [x] Task: Implement `apply_magnetic_variation` (Green) [702249d]
    - [x] Create `cave_sketch/geo/declination.py` with
      `apply_magnetic_variation(df: pd.DataFrame, variation_deg: float) -> pd.DataFrame`,
      rotating `X`/`Y` about the DataFrame's own centroid via the existing
      `rotate_points()` helper (`cave_sketch/features/geometry.py`),
      negating `variation_deg` per the sign convention above.
    - [x] Run `uv run pytest tests/test_declination.py -v`; confirm all 4 pass.
- [x] Task: Verify and commit [702249d]
    - [x] Run `uv run ruff check cave_sketch/geo/declination.py tests/test_declination.py && uv run mypy cave_sketch/geo/declination.py`.
    - [x] Commit (`feat(geo): add apply_magnetic_variation coordinate correction`).

## Phase 2: Wire the Correction into `draw_survey()` (Survey Plot Backend) [checkpoint: 3d2023b]

Full code: `docs/superpowers/plans/2026-09-30-magnetic-variation.md` → Task 2.

- [x] Task: Write the failing tests (Red) [2dc72c4]
    - [x] Create `tests/test_survey_declination.py` covering: default vs.
      explicit `magnetic_variation_deg=0.0` producing identical, unrotated
      station offsets; and `magnetic_variation_deg=10.0` rotating the map
      subplot's station offsets while leaving the section subplot untouched.
    - [x] Run `uv run pytest tests/test_survey_declination.py -v`; confirm it
      fails with `TypeError: draw_survey() got an unexpected keyword
      argument 'magnetic_variation_deg'`.
- [x] Task: Implement the wiring (Green) [2dc72c4]
    - [x] In `cave_sketch/survey/survey.py`, add the
      `from cave_sketch.geo.declination import apply_magnetic_variation`
      import in alphabetical order (between the `cave_sketch.dxf.models`
      and `cave_sketch.survey.config` imports).
    - [x] Add `magnetic_variation_deg: float = 0.0` to `draw_survey()`'s
      signature, after `surveyor_name` and before `config`.
    - [x] Right after the merge/no-merge branch resolves `merged_map` (and
      before "Compute metrics after merge"), apply
      `merged_map = apply_magnetic_variation(merged_map, magnetic_variation_deg)`
      when `merged_map is not None`. `merged_section` is never touched.
    - [x] Run `uv run pytest tests/test_survey_declination.py -v`; confirm
      both pass.
- [x] Task: Regression-test, verify, and commit [2dc72c4]
    - [x] Run `uv run pytest tests/test_survey_rendering.py tests/test_survey_plot.py tests/test_survey_plot_placement.py tests/test_survey_bridge.py tests/test_survey_metrics.py tests/test_survey_section_scale_bar.py -v`; confirm all pass unchanged.
    - [x] Run `uv run ruff check cave_sketch/survey/survey.py tests/test_survey_declination.py && uv run mypy cave_sketch/survey/survey.py`.
    - [x] Commit (`feat(survey): apply magnetic variation correction in draw_survey`).

## Phase 3: Wire the Correction into `draw_map()` (Satellite Map Backend) [checkpoint: 1e410e0]

Full code: `docs/superpowers/plans/2026-09-30-magnetic-variation.md` → Task 3.

- [x] Task: Write the failing tests (Red) [08d6146]
    - [x] Create `tests/test_map_declination.py` covering: default vs.
      explicit `magnetic_variation_deg=0.0` producing identical
      georeferenced output; `magnetic_variation_deg=10.0` rotating the
      georeferenced lat/lon of a station relative to its GPS anchor by the
      expected amount; and (via mocking
      `cave_sketch.satellite_view.map.apply_magnetic_variation`) that the
      correction runs on the raw CSV data before the existing manual
      `rotation_angle` block, so the two compose instead of one silently
      overriding the other.
    - [x] Run `uv run pytest tests/test_map_declination.py -v`; confirm it
      fails (missing kwarg / missing patch target).
- [x] Task: Implement the wiring (Green) [08d6146]
    - [x] In `cave_sketch/satellite_view/map.py`, add the
      `from cave_sketch.geo.declination import apply_magnetic_variation`
      import in alphabetical order (after the
      `cave_sketch.features.render_features` import).
    - [x] Add `magnetic_variation_deg: float = 0.0` to `draw_map()`'s
      signature, after `rotation_angle`.
    - [x] Apply `map_df = apply_magnetic_variation(map_df, magnetic_variation_deg)`
      immediately after `pd.read_csv(map_path)`, before the existing
      `if rotation_angle != 0:` block (left otherwise unchanged).
    - [x] Run `uv run pytest tests/test_map_declination.py -v`; confirm all pass.
- [x] Task: Regression-test, verify, and commit [08d6146]
    - [x] Run `uv run pytest tests/test_satellite_map.py tests/test_satellite_bridge.py -v`; confirm all pass unchanged.
    - [x] Run `uv run ruff check cave_sketch/satellite_view/map.py tests/test_map_declination.py && uv run mypy cave_sketch/satellite_view/map.py`.
    - [x] Commit (`feat(satellite): apply magnetic variation correction in draw_map`).

## Phase 4: Survey Plot Page — Magnetic Variation Input

Full code: `docs/superpowers/plans/2026-09-30-magnetic-variation.md` → Task 4.

- [x] Task: Update the failing tests (Red) [8db0523]
    - [x] In `tests/test_settings_panel.py`, extend both `number_input`
      `side_effect` lists from 5 to 6 values (inserting the new field's
      value right after "Map rotation"), and assert
      `res["magnetic_variation_deg"] == 0.0` in both tests.
    - [x] Run `uv run pytest tests/test_settings_panel.py -v`; confirm it
      fails with `KeyError: 'magnetic_variation_deg'`.
- [x] Task: Implement the wiring (Green) [8db0523]
    - [x] In `app/components/settings_panel.py`, add a `number_input` for
      "🧭 Magnetic variation (°, +E/-W)" right after the existing "Map
      rotation" input, persist it to
      `st.session_state.magnetic_variation_deg` (mirroring the existing
      `show_centerline`/`show_details`/`show_grid` pattern), and add it to
      the returned settings dict.
    - [x] In `app/session.py`, add `magnetic_variation_deg: float` to the
      `AppState` TypedDict and `"magnetic_variation_deg": 0.0` to
      `init_session()`'s defaults, next to `rotation_angle`.
    - [x] In `app/pages/1_survey_plot.py`, add
      `magnetic_variation_deg=settings.pop("magnetic_variation_deg", 0.0),`
      to the `draw_survey(...)` call, alongside the existing
      `rule_length=settings.pop("rule_length")`.
    - [x] Run `uv run pytest tests/test_settings_panel.py -v`; confirm both pass.
- [x] Task: Verify and commit [8db0523]
    - [x] Run `uv run ruff check app/ tests/test_settings_panel.py && uv run mypy cave_sketch/`.
    - [x] Commit (`feat(webapp): add magnetic variation input to Survey Plot settings`).

## Phase 5: Satellite Map Page — Auto-Apply the Survey's Magnetic Variation

Full code: `docs/superpowers/plans/2026-09-30-magnetic-variation.md` → Task 5.

- [ ] Task: Implement the wiring
    - [ ] In `app/pages/2_satellite_map.py`, read
      `st.session_state.magnetic_variation_deg`, show a caption
      (`🧭 Magnetic variation correction: {value:+g}° applied automatically
      from Survey Plot`) when it is non-zero, and pass it to the
      `draw_map(...)` call alongside `rotation_angle`.
- [ ] Task: Regression-test, verify, and commit
    - [ ] Run `uv run pytest`; confirm the full suite passes.
    - [ ] Run `uv run ruff check app/pages/2_satellite_map.py && uv run mypy cave_sketch/`.
    - [ ] Commit (`feat(webapp): auto-apply survey magnetic variation on Satellite Map page`).
- [ ] Task: Manual verification
    - [ ] Run `uv run streamlit run app/app.py`.
    - [ ] On the Cave Survey Plot page, upload `tests/fixtures/test_survey.csv`
      as the map file, set "Magnetic variation" to `10`, generate the plot.
      Confirm the plotted stations visibly rotate compared to `0`, while the
      north arrow stays fixed pointing straight up.
    - [ ] Navigate to the Satellite Map page without changing anything.
      Confirm the caption `🧭 Magnetic variation correction: +10° applied
      automatically from Survey Plot` is shown.
    - [ ] Fill in a station/lat/lon GPS point matching a station from the
      uploaded CSV, generate the HTML map. Confirm it renders without error.
    - [ ] Reset "Magnetic variation" to `0` on Survey Plot, regenerate,
      return to Satellite Map: confirm the caption disappears and the map
      regenerates without error.
    - [ ] Restart with a fresh session and open the Satellite Map page
      first, before ever visiting Survey Plot. Confirm no `AttributeError`
      is raised (the page loads normally, field defaults to `0`).
