# Spec: Map Merge Protocol (Simple / Displacement)

## Overview
When merging a child survey, the **section** already offers a protocol choice (Simple / Mirror /
Displacement). This track adds the equivalent choice for the **map (plan view)**, restricted to
**Simple** and **Displacement**. With Displacement, the child map is placed so that it does not
overlap the main map, and a dotted connector line links the two matching stations. The existing
(section-only) Displacement code is untested and buggy, so it is rewritten as one shared, tested
routine used by both views. Both UIs (Streamlit webapp and Android app) are updated.

**Current Displacement bugs (`cave_sketch/survey/merger.py::_merge_single_view`):**
1. The child matching station is deleted and its ID remapped to the parent station, so displaced
   child shots that ended at that station are drawn as long stray lines back to the parent station.
2. The `CONN_1` connector links to `child_station`, which is then remapped to `parent_station`,
   producing a zero-length (invisible) line.
3. Padding is a fixed 50 units (does not scale with the cave size) and the only placement ever
   tried is "right".
4. There are no tests.

## Functional Requirements
- **FR1 – Library API:** add `MapProtocol(Enum)` with `SIMPLE = "simple"` and
  `DISPLACEMENT = "displacement"` in `cave_sketch/survey/merger.py`. Add
  `map_protocol: MapProtocol = MapProtocol.SIMPLE` to `merge_surveys()` and `draw_survey()`.
  Defaults preserve today's behaviour.
- **FR2 – Shared displacement routine:** one pure helper used by both map
  (`MapProtocol.DISPLACEMENT`) and section (`SectionProtocol.DISPLACEMENT`). It produces ONE
  placement of the child:
  - Start from the Simple alignment (child matching station on top of the parent station).
  - Padding = **10% of the diagonal of the parent bounding box** (relative, no fixed units). A tiny
    floor of 1 m applies only for a degenerate single-point parent.
  - Bounding boxes are computed over **all** rows (stations, walls, details).
  - Candidate directions: every angle from **0° (right) to −90° (below) in 5° steps** (19
    candidates, including intermediate diagonal positions). For each direction, slide the child
    along that direction by the smallest distance that makes its bounding box clear the parent
    bounding box by at least the padding.
  - Choose the graphically best candidate: **smallest area of the combined bounding box** (most
    compact drawing). Tie-break: shorter slide distance, then angle closer to 0°.
  - Guarantee: the child bounding box never comes closer than the padding to the parent bounding
    box; the result is deterministic. This holds after PDF rotation / magnetic variation, since
    both are rigid transforms applied to the whole merged drawing.
- **FR3 – Station handling in Displacement:** do NOT delete the child's matching station. Keep it
  at its displaced position with a remapped ID (same numeric offset as the other child stations),
  so the child's own shots stay attached to it. Add one connector row (`Type = "connector"`, the
  dotted grey style already defined in `cave_sketch/style.py`) from the parent station to the
  displaced child station. The connector gets no station marker or label.
- **FR4 – Metrics:** connector rows are excluded from `compute_total_length` /
  `compute_total_depth` (Sviluppo / Dislivello). Displacement totals equal Simple totals.
- **FR5 – Satellite / KML / KMZ:** always use the true geographic merge (`MapProtocol.SIMPLE`)
  regardless of the chosen map protocol — both the web `merged_map.csv`
  (`app/pages/1_survey_plot.py`) and Android `effective_map_csv`
  (`android/app/src/main/python/survey_bridge.py`).
- **FR6 – Section protocols unchanged:** the section keeps Simple / Mirror / Displacement. Mirror
  is never offered for the map.
- **FR7 – Webapp UI:** in `app/components/merging_controls.py`, add an inline radio group
  "🗺️ Map View Merging Protocol" (Simple / Displacement), shown only when a child map is
  uploaded, next to the existing section selector. Add session key `map_protocol` (default
  `"simple"`) in `app/session.py`; pass it to `draw_survey`.
- **FR8 – Android UI:** in `MergeControls.kt`, add a "Map merge protocol" radio group
  (Simple / Displacement), shown only when `childMapPath != null`. Add
  `SurveyInputs.mapProtocol = "simple"`, serialised as `"map_protocol"` in `toJson()`.
  `survey_bridge.py` parses it (default `"simple"`) and passes it to `draw_survey`.
- **FR9 – Docs:** update `docs/web/survey-merging.md`, `docs/web/survey-merging.it.md`, README
  and the in-app guide (if it describes the protocols).

## Non-Functional Requirements
- `cave_sketch/` keeps zero Streamlit imports; full type annotations; Python gates
  (`uv run ruff check .`, `uv run mypy cave_sketch/`, `uv run pytest`) pass; TDD; >80% coverage of
  new code.
- matplotlib 3.8-compatible (Android).
- DEVLOG entries: root `DEVLOG.md` (Python / web), `android/DEVLOG.md` (Android).

## ⏸ Device Constraint (Android)
The machine where this track was created has no Android Studio / Android SDK. Everything possible
here (library, Python bridge + pytest tests, writing the Kotlin code and its JVM unit tests) is done
here. **Running `./gradlew :app:testDebugUnitTest :app:assembleDebug` and verifying on a
phone/emulator CANNOT be done on this machine.** The plan contains an explicit **PAUSE POINT**
(end of Phase 4): the executor stops there, marks the track `in_progress` with the note
"paused: Phase 5 requires Android device", and completes Phase 5 later on an Android-capable
machine.

## Acceptance Criteria
1. Unit tests: map Displacement → child bbox clears parent bbox by ≥ padding (right, below and
   intermediate-angle cases); a connector row links parent station → displaced child station; no
   child shot links to the parent station; totals equal Simple.
2. Section Displacement passes the same tests; existing Mirror / Simple tests still pass.
3. Webapp: map radio appears only with a child map; the PDF shows the displaced child + dotted
   connector; the Satellite page still shows the cave at its true position.
4. Android: same behaviour on a device (after the pause point).
5. All Python gates green; Android gradle gates green on the Android machine.

## Out of Scope
- Manual / user-dragged placement or user-chosen direction.
- Merging more than one child survey.
- Changes to DXF parsing or the KML/KMZ format.

## Risks
- Track `title_block_metadata_20261009` (status: new) also edits `survey_bridge.py`,
  `SurveyInputs` and `draw_survey`. Whichever track runs second must rebase carefully.
