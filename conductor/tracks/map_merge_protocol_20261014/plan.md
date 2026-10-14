# Plan: Map Merge Protocol (Simple / Displacement)

> - **Spec:** `./spec.md`.
> - **Workflow:** follow `conductor/workflow.md` for every task: `[~]` → Red → Green → gates
>   (`uv run ruff check .`, `uv run mypy cave_sketch/`, `uv run pytest`) → commit → git note →
>   `[x]` + 7-char SHA → commit plan. Append a DEVLOG entry after each meaningful change.
> - **⏸ PAUSE POINT at the end of Phase 4:** the creating machine has no Android Studio / SDK.
>   Stop there and resume Phase 5 on an Android-capable machine.

## Phase 1: Shared Displacement Routine (library) [checkpoint: 2d48192]
- [x] Task: Write failing tests for the placement helper (`tests/test_merge_displacement.py`) (da889a3)
    - [x] Padding = 10% of the parent bbox diagonal (1 m floor for a degenerate parent)
    - [x] Wide/flat parent → below-ish placement; tall/narrow parent → right-ish; a case where an
      intermediate angle wins
    - [x] Child bbox always clears parent bbox by ≥ padding; deterministic tie-break
- [x] Task: Implement `_compute_displacement(parent_df, child_df, anchor_dx, anchor_dy) -> (dx, dy)`
  in `cave_sketch/survey/merger.py` (angles 0°…−90° in 5° steps, min combined-bbox area,
  tie-break shorter slide then angle closer to 0°) (3c6d7dc)
- [x] Task: Write failing tests for Displacement station handling (section) (df634cd)
    - [x] Child matching station kept (remapped ID) at its displaced position
    - [x] One `connector` row links parent station → displaced child station
    - [x] No child row links to the parent station; existing Simple / Mirror tests still pass
- [x] Task: Refactor `_merge_single_view` to use the helper and the new station/connector handling (9f7d2dd)
- [x] Task: Write failing tests + implement: `compute_total_length` / `compute_total_depth` ignore
  connector rows (Displacement totals == Simple totals) (dac5e24)
- [x] Task: Write failing test + fix if needed: renderer draws connector rows as a dotted line, with
  no station marker/label (b311c38)
- [x] Task: Gates + root `DEVLOG.md` entry (29a3611)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Shared Displacement Routine' (Protocol in workflow.md) (2d48192)

## Phase 2: Map Protocol API [checkpoint: 2ab6c19]
- [x] Task: Write failing tests: `MapProtocol` enum; `merge_surveys(map_protocol=DISPLACEMENT)`
  displaces the map; default stays Simple (existing outputs unchanged); `draw_survey(map_protocol=...)`
  forwards it (484fcd4)
- [x] Task: Implement `MapProtocol` + `map_protocol` param in `merge_surveys` and `draw_survey` (7071bb3)
- [x] Task: Gates + root `DEVLOG.md` entry (ebb85e5)
- [x] Task: Conductor - User Manual Verification 'Phase 2: Map Protocol API' (Protocol in workflow.md) (2ab6c19)

## Phase 3: Webapp UI
- [x] 9025258 Task: Write failing tests (follow existing app test style, e.g. `tests/test_settings_panel.py`,
  `tests/test_satellite_map.py`): session default `map_protocol="simple"`; radio shown only when a
  child map is uploaded; satellite `merged_map.csv` always uses Simple
- [~] Task: Implement: `app/session.py` key; radio in `app/components/merging_controls.py`;
  `app/pages/1_survey_plot.py` passes `map_protocol` to `draw_survey` and forces
  `MapProtocol.SIMPLE` for `merged_map.csv`
- [ ] Task: Update docs (`docs/web/survey-merging.md`, `docs/web/survey-merging.it.md`, README,
  in-app guide if it describes the protocols)
- [ ] Task: Gates + root `DEVLOG.md` entry
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Webapp UI' (Protocol in workflow.md)
    - [ ] `uv run streamlit run app/app.py`: merge `tests/fixtures/sample.dxf` with itself
      (e.g. stations 1/1), Map = Displacement → PDF shows the child clear of the parent + dotted
      connector; Satellite page shows the true position

## Phase 4: Android – code (doable without Android Studio)
- [ ] Task: Write failing tests in `tests/test_survey_bridge.py`: `map_protocol` parsed (default
  `simple`) and forwarded to `draw_survey`; `effective_map_csv` always merges with Simple
- [ ] Task: Implement `android/app/src/main/python/survey_bridge.py` changes
- [ ] Task: Kotlin: `SurveyInputs.mapProtocol = "simple"` + `"map_protocol"` in `toJson()`
  (`SurveyPlotViewModel.kt`); "Map merge protocol" radio (Simple / Displacement) in
  `MergeControls.kt`, shown only when `childMapPath != null`; write/extend a JVM unit test for
  `toJson()` under `android/app/src/test/java/com/cavesketch/app/` (written, NOT run here)
- [ ] Task: Python gates + `android/DEVLOG.md` entry noting the pending Android verification
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Android – code' (Protocol in workflow.md) – Python side only
- [ ] Task: ⏸ PAUSE POINT – requires an Android Studio / SDK machine
    - [ ] Set `metadata.json` status to `in_progress` and add the note
      "paused: Phase 5 requires Android device"; commit; STOP and inform the user.

## Phase 5: Android – build & device verification (REQUIRES Android machine)
- [ ] Task: `cd android && ./gradlew :app:testDebugUnitTest :app:assembleDebug`; fix any
  compile/test failures
- [ ] Task: `./gradlew :app:installDebug`; on a device merge `sample.dxf` with itself,
  Map = Displacement → PDF preview shows the displaced child + connector; Satellite map shows the
  true position; the map radio is hidden without a child map
- [ ] Task: `android/DEVLOG.md` entry; set track status to completed
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Android – build & device verification' (Protocol in workflow.md)
