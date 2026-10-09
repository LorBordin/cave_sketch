# Plan: Title Block Metadata & Adaptive Placement

> **Read this section before doing anything.**
>
> - **Spec:** `./spec.md` (same as `docs/superpowers/specs/2026-10-09-title-block-metadata-design.md`).
> - **Full code:** every task below points to a numbered Task/Step in
>   `docs/superpowers/plans/2026-10-09-title-block-metadata.md`. That file contains the exact
>   test code, implementation code and commands. **Copy the code from there exactly.** Do not
>   invent different names, signatures, labels or file paths. If something in that file looks
>   wrong, STOP and ask the user instead of improvising.
> - **Workflow:** follow `conductor/workflow.md` for every task (mark `[~]` → Red → Green →
>   quality gates → commit → git note → mark `[x]` with the 7-char SHA → commit the plan).
> - **One phase at a time.** Every phase ends with a *Device Verification & Approval* task.
>   The user tests the result **on the devices** (webapp in a browser and the Android app on a
>   phone/emulator). You **MUST STOP** after presenting the verification steps and wait for the
>   user to answer **"yes"**. Never start the next phase without that explicit approval. If the
>   user reports a problem, fix it inside the same phase, rerun the gates, and ask again.
> - Phases are ordered so that **both apps keep working after every phase**. A phase that has
>   no new visible feature still gets a device check: the user confirms nothing regressed.

## Global Constraints

- PDF labels are Italian, exactly: `Rilevatore`, `Disegnatore`, `Data`, `Comune`,
  `Coordinate`, `Quota slm`, `Declinazione`, `Sviluppo`, `Dislivello`. UI labels (web and
  Android) stay English.
- Row order: Rilevatore, Disegnatore, Data, Comune, Coordinate, Quota slm, Declinazione,
  Sviluppo, Dislivello. Optional rows appear **only when entered**. `Rilevatore` shows `-`
  when empty (existing behaviour).
- Formats: `Coordinate: 45.12345° N, 11.54321° E` (5 decimals, absolute values, N/S, E/W);
  `Quota slm: 1250 m` (rounded integer); `Declinazione: 2.5° E` (1 decimal, E positive /
  W negative, printed only when the variation is not 0). Free-text values longer than 30
  characters are truncated with `…`.
- Validation: latitude in [-90, 90], longitude in [-180, 180], latitude and longitude both set
  or both empty. Zero is a valid value (never use truthiness checks on numbers).
- Placement order: header slot → corners of the map plot (top-right, top-left, bottom-right,
  bottom-left) → corners of the section plot → grow the header. Grid lines never block a corner.
- `cave_sketch/` must not import Streamlit. Full type annotations on public functions.
- matplotlib on Android is **3.8.4**: use only APIs that exist in 3.8.
- No changes to DXF, KML/KMZ or satellite exports.
- Python gates after every task (all must pass):
  `uv run ruff check .` (run `uv run ruff check --fix .` first for import order) ·
  `uv run mypy cave_sketch/` · `uv run pytest -q`
- Android gates for tasks touching `android/` (including the Python bridge):
  `cd android && ./gradlew :app:testDebugUnitTest :app:assembleDebug`

## Device Verification Kit (used by every phase)

- **Webapp:** `uv run streamlit run app/app.py`, open `http://localhost:8501`, go to
  **Survey Plot**, upload `tests/fixtures/sample.dxf` as the cave map (and again as the
  section when a step asks for a dual plot), click **✨ Generate Survey Plot**, then
  **📥 Download PDF** and open the PDF.
- **Android:** connect the phone (USB debugging on) or start an emulator, run
  `cd android && ./gradlew :app:installDebug`, open CaveSketch → **Survey Plot**, pick the
  same `sample.dxf` (copy it to the device's Downloads first:
  `adb push tests/fixtures/sample.dxf /sdcard/Download/`), tap **Generate Survey Plot**, and
  look at the PDF preview (use **Save / Share PDF** to open it full-screen if needed).
- **Baseline for "unchanged":** before Phase 1, generate one PDF on each device with surveyor
  `Test` and keep it as the reference (`before_web.pdf`, `before_android.pdf`).

---

## Phase 1: `TitleBlockInfo` Model [checkpoint: b994803]

Full code: superpowers plan → **Task 1**.

- [x] Task: Write failing tests (Red) [15d117f]
    - [x] Create `tests/test_title_block_info.py` with the tests from Task 1 Step 1.
    - [x] Run `uv run pytest tests/test_title_block_info.py -v`; confirm it fails with
      `ImportError: cannot import name 'TitleBlockInfo'`.
- [x] Task: Implement `TitleBlockInfo` (Green) [a598f76]
    - [x] Add the dataclass to `cave_sketch/survey/config.py` (Task 1 Step 3). Do **not**
      remove `SurveyConfig.surveyor_name` yet (that happens in Phase 5).
    - [x] Run `uv run pytest tests/test_title_block_info.py -v`; all pass.
- [x] Task: Quality gates and commit [a598f76]
    - [x] Run the Python gates. Commit `feat(survey): add validated TitleBlockInfo model`.
- [x] Task: Conductor - Device Verification & Approval 'Phase 1' (Protocol in workflow.md) [b994803]
    - [x] Show the validation working:
      `uv run python -c "from cave_sketch.survey.config import TitleBlockInfo as T; print(T(latitude=0.0, longitude=0.0)); T(latitude=45.0)"`
      → prints the object, then `ValueError: Latitude and longitude must be entered together.`
    - [x] Webapp: generate a PDF (map only, surveyor `Test`); title block identical to
      `before_web.pdf`.
    - [x] Android: `./gradlew :app:installDebug`, generate a PDF; identical to
      `before_android.pdf`.
    - [x] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.

## Phase 2: Title Block Rows [checkpoint: 6a6108b]

Full code: superpowers plan → **Task 2**.

- [x] Task: Write failing tests (Red) [be5fd2a]
    - [x] Create `tests/test_title_block_rows.py` (Task 2 Step 1).
    - [x] Run `uv run pytest tests/test_title_block_rows.py -v`; confirm
      `ImportError: cannot import name 'build_title_rows'`.
- [x] Task: Implement `build_title_rows` (Green) [2f89c5b]
    - [x] Add `MAX_VALUE_CHARS`, `_truncate`, `_format_coordinates`, `build_title_rows` to
      `cave_sketch/survey/graphics/title_block.py` (Task 2 Step 3). Leave the existing
      `draw_title_block` untouched.
    - [x] Run `uv run pytest tests/test_title_block_rows.py tests/test_title_block.py -v`; all pass.
- [x] Task: Quality gates and commit [2f89c5b]
    - [x] Python gates. Commit `feat(survey): build title block rows from TitleBlockInfo`.
- [x] Task: Conductor - Device Verification & Approval 'Phase 2' (Protocol in workflow.md) [6a6108b]
    - [x] Show the rows the PDF will contain:
      ```bash
      uv run python - <<'EOF'
      from cave_sketch.survey.config import TitleBlockInfo
      from cave_sketch.survey.graphics.title_block import build_title_rows
      info = TitleBlockInfo(surveyor_name="Alice", drawer_name="Bob", municipality="Genga",
                            latitude=-33.5, longitude=12.96543, elevation_m=0)
      print("\n".join(build_title_rows(info, -1.25, 154.3, 45.2)))
      EOF
      ```
      Expected: 9 rows in the order of Global Constraints, `Coordinate: 33.50000° S, 12.96543° E`,
      `Quota slm: 0 m`, `Declinazione: 1.2° W`.
    - [x] Webapp and Android: generate a PDF; identical to the Phase 1 references.
    - [x] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.

## Phase 3: Measure the Box; Header Slot and Grow-Header Placement [checkpoint: 1c9ed85]

Full code: superpowers plan → **Task 3**.

- [x] Task: Write failing tests (Red) [9db1a65]
    - [x] Create `tests/test_title_block_layout.py` (Task 3 Step 1).
    - [x] Run `uv run pytest tests/test_title_block_layout.py -v`; confirm
      `ModuleNotFoundError: ... title_block_layout`.
- [x] Task: Implement `title_block_layout.py` (Green) [843fd1e]
    - [x] Create `cave_sketch/survey/graphics/title_block_layout.py` (Task 3 Step 3), including
      the `_find_free_corner` stub that returns `None` (Phase 4 replaces it).
    - [x] Run `uv run pytest tests/test_title_block_layout.py -v`; all pass.
- [x] Task: Quality gates and commit [89f676d]
    - [x] Python gates. Commit
      `feat(survey): measure title block and place it in header or grown header`.
- [x] Task: Conductor - Device Verification & Approval 'Phase 3' (Protocol in workflow.md) [1c9ed85]
    - [x] Render the placement demo and show the user the three images:
      ```bash
      mkdir -p /tmp/title_block_demo && uv run python - <<'EOF'
      import matplotlib
      matplotlib.use("Agg")
      import matplotlib.pyplot as plt
      from matplotlib.patches import Rectangle
      from cave_sketch.survey.graphics.title_block_layout import (
          measure_title_block, place_title_block)
      small = ["Rilevatore: Alice", "Data: 09/10/2026", "Sviluppo: 154.3 m", "Dislivello: 45.2 m"]
      large = ["Rilevatore: Alice", "Disegnatore: Bob", "Data: 09/10/2026", "Comune: Genga",
               "Coordinate: 43.40123° N, 12.96543° E", "Quota slm: 320 m",
               "Declinazione: 2.5° E", "Sviluppo: 154.3 m", "Dislivello: 45.2 m"]
      for label, rows, dense in [("1_small", small, False), ("2_large_sparse", large, False),
                                 ("3_large_dense", large, True)]:
          fig = plt.figure(figsize=(8.27, 11.69))
          fig.subplots_adjust(top=0.86)
          name = fig.text(0.05, 0.92, "Grotta Demo", fontsize=15, weight="bold", va="center")
          ax = fig.add_subplot(1, 1, 1)
          ax.set_xlim(0, 10)
          ax.set_ylim(0, 10)
          ax.plot([0, 10], [0, 10], color="black")
          if dense:
              ax.add_patch(Rectangle((0, 0), 10, 10, alpha=0.3))
          p = place_title_block(fig, measure_title_block(fig, rows), name, [ax])
          box = fig.add_axes(p.rect)
          box.set_xticks([])
          box.set_yticks([])
          box.text(0.05, 0.5, "\n".join(rows), va="center", fontsize=8.5, linespacing=1.5)
          fig.savefig(f"/tmp/title_block_demo/{label}.png", dpi=60)
          print(label, "->", p.strategy)
          plt.close(fig)
      EOF
      open /tmp/title_block_demo
      ```
      Expected printout: `1_small -> header`, `2_large_sparse -> grow-header` (corners arrive
      in Phase 4), `3_large_dense -> grow-header`. In every image the box does not touch the
      cave name and the plot starts below the box.
    - [x] Webapp and Android: generate a PDF; identical to the Phase 1 references (the new
      module is not wired in yet).
    - [x] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.

## Phase 4: Free In-Plot Corner Search

Full code: superpowers plan → **Task 4**.

- [x] Task: Write failing tests (Red) [5e15f12]
    - [x] Add the imports to the **top** of `tests/test_title_block_layout.py` and append the
      five tests (Task 4 Step 1).
    - [x] Run `uv run pytest tests/test_title_block_layout.py -v`; the five new tests fail with
      `strategy == "grow-header"`, Phase 3 tests still pass.
- [x] Task: Implement corner search (Green) [3d10f31]
    - [x] Add `gid="grid"` to both lines in `cave_sketch/survey/graphics/grid.py`.
    - [x] Replace the `_find_free_corner` stub and add `_corner_rects`, `_ignored`, `_hits`,
      `CORNER_INSET`, `MARKER_MARGIN_PX` (Task 4 Step 3).
    - [x] Run `uv run pytest tests/test_title_block_layout.py tests/test_grid.py -v`; all pass.
- [~] Task: Quality gates and commit
    - [ ] Python gates. Commit
      `feat(survey): place title block in a free plot corner when header is too small`.
- [ ] Task: Conductor - Device Verification & Approval 'Phase 4' (Protocol in workflow.md)
    - [ ] Rerun the Phase 3 demo command. Expected: `2_large_sparse -> corner` (box in the
      top-left, not crossing the diagonal line); the other two unchanged.
    - [ ] Webapp and Android: generate a PDF **with grid on**; identical to the Phase 1
      references (grid lines look the same; the new `gid` is invisible).
    - [ ] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.

## Phase 5: Wire the Title Block into Rendering

Full code: superpowers plan → **Task 5**. This phase changes `draw_survey`'s signature, so it
also migrates both apps' call sites (Step 5b) to keep them working.

- [ ] Task: Write failing tests (Red)
    - [ ] Rewrite the title block tests in `tests/test_title_block.py`, migrate
      `tests/test_title_block_integration.py` (sed command + two new tests) and
      `tests/test_render_regression.py` (new `full_metadata` scenario) — Task 5 Step 1.
    - [ ] Run `uv run pytest tests/test_title_block.py tests/test_title_block_integration.py -v`;
      confirm `ImportError: cannot import name 'draw_cave_name'` / unexpected keyword
      `title_block`.
- [ ] Task: Implement rendering changes (Green)
    - [ ] `title_block.py`: replace old `draw_title_block` with `draw_cave_name`,
      `draw_title_block`, `_draw_box` (Step 3).
    - [ ] `renderer.py`: name first, plots, then rows + `draw_title_block` (Step 4).
    - [ ] `survey.py` / `config.py`: `title_block` parameter, remove
      `SurveyConfig.surveyor_name`, forward variation only when a map exists (Step 5).
    - [ ] Migrate `app/pages/1_survey_plot.py` and `android/app/src/main/python/survey_bridge.py`
      to `title_block=TitleBlockInfo(surveyor_name=...)` (Step 5b).
    - [ ] Run the tests listed in Step 6; all pass.
- [ ] Task: Regenerate render baselines
    - [ ] `CAVE_SKETCH_GENERATE_BASELINES=1 uv run pytest tests/test_render_regression.py -v`
      (3 skipped), then open the three PNGs in `tests/fixtures/render_baselines/` and check
      them as described in Step 7. Then `uv run pytest tests/test_render_regression.py -v`
      (3 pass).
- [ ] Task: Quality gates and commit
    - [ ] Python gates **and** Android gates (the bridge changed). Commit
      `feat(survey): render extended title block with adaptive placement`.
- [ ] Task: Conductor - Device Verification & Approval 'Phase 5' (Protocol in workflow.md)
    - [ ] Show the user `tests/fixtures/render_baselines/full_metadata.png`: 9 rows, no overlap
      with cave walls, stations, north arrow, scale bar or cave name.
    - [ ] Webapp: map only and map + section with surveyor `Test`: box top-right in the header
      as in `before_web.pdf` (row spacing may differ slightly), rows Rilevatore/Data/Sviluppo
      (+ Dislivello with section). Set magnetic variation `2.5` → an extra
      `Declinazione: 2.5° E` row appears.
    - [ ] Android: `./gradlew :app:installDebug`, generate a PDF with surveyor `Test`: same
      result as the webapp; the app does not show an error.
    - [ ] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.

## Phase 6: Webapp Inputs

Full code: superpowers plan → **Task 6**.

- [ ] Task: Write failing tests (Red)
    - [ ] Create `tests/test_title_block_inputs.py` (Task 6 Step 1); confirm
      `ModuleNotFoundError: No module named 'app.components.title_block_inputs'`.
- [ ] Task: Implement (Green)
    - [ ] Create `app/components/title_block_inputs.py` (Step 3).
    - [ ] Update `app/session.py` and `app/pages/1_survey_plot.py` (Step 4).
    - [ ] Run `uv run pytest tests/test_title_block_inputs.py tests/test_settings_panel.py -v`.
- [ ] Task: Quality gates and commit
    - [ ] Python gates. Commit `feat(app): add title block metadata inputs to survey plot page`.
- [ ] Task: Conductor - Device Verification & Approval 'Phase 6' (Protocol in workflow.md)
    - [ ] Webapp on desktop browser **and** on a phone browser (same Wi-Fi, use the
      "Network URL" Streamlit prints):
        1. The "👤 Title block" section shows Surveyor, Drawer, Municipality, Latitude,
           Longitude, Elevation.
        2. Fill all of them (e.g. Alice / Bob / Genga / 43.40123 / 12.96543 / 320) plus magnetic
           variation 2.5, map + section → PDF shows all 9 rows in order, box placed without
           overlapping the drawing.
        3. Clear everything except Surveyor → only Rilevatore/Data/Sviluppo/Dislivello.
        4. Enter only Latitude → red error "Latitude and longitude must be entered together.";
           clicking Generate shows "Please fix the title block fields…" and no PDF is made.
        5. Switch to another page in the sidebar and back → values are kept.
    - [ ] Android: generate a PDF; unchanged from Phase 5.
    - [ ] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.

## Phase 7: Android Bridge and `SurveyInputs` Model

Full code: superpowers plan → **Task 7**.

- [ ] Task: Bridge — failing tests (Red), implementation (Green)
    - [ ] Append the three bridge tests to `tests/test_survey_bridge.py` (Step 1); confirm they
      fail.
    - [ ] Implement `_optional_float`, the `TitleBlockInfo` construction with the
      `invalid_title_block` error, and the `magnetic_variation_deg` argument (Step 3).
    - [ ] Run `uv run pytest tests/test_survey_bridge.py -v && uv run pytest -q`.
- [ ] Task: Kotlin model — failing tests (Red), implementation (Green)
    - [ ] Append the three tests to `SurveyPlotViewModelTest.kt` (Step 5); confirm compile
      failure.
    - [ ] Add `parseDecimalOrNull`, the new `SurveyInputs` fields, `titleBlockError()` and the
      new JSON keys; make `parsesAsCoordinate` reuse `parseDecimalOrNull` (Step 7).
    - [ ] Run the Android gates.
- [ ] Task: Quality gates and commit
    - [ ] Python + Android gates. Commit
      `feat(android): send title block metadata and magnetic variation to the bridge`.
- [ ] Task: Conductor - Device Verification & Approval 'Phase 7' (Protocol in workflow.md)
    - [ ] Android: `./gradlew :app:installDebug`; generate a PDF with surveyor `Test` → same
      as Phase 5 (no new fields on screen yet; this phase only changes data plumbing). The GPS
      points editor on the Satellite screen still accepts `45,5` without a red error.
    - [ ] Webapp: unchanged from Phase 6.
    - [ ] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.

## Phase 8: Android UI Fields

Full code: superpowers plan → **Task 8**.

- [ ] Task: Write failing UI tests (Red)
    - [ ] Create `TitleBlockFieldsTest.kt` and append the magnetic variation test to
      `SettingsFormTest.kt` (Step 1); confirm compile failure.
- [ ] Task: Implement (Green)
    - [ ] Create `ui/components/TitleBlockFields.kt` (Step 3).
    - [ ] Add the magnetic variation field to `SettingsForm.kt` (Step 4).
    - [ ] Use `TitleBlockFields` in `SurveyPlotScreen.kt` and gate `canGenerate` on
      `titleBlockError() == null` (Step 5).
    - [ ] Run the Android gates.
- [ ] Task: Quality gates and commit
    - [ ] Android gates + `uv run pytest -q`. Commit
      `feat(android): add title block fields and magnetic variation input`.
- [ ] Task: Conductor - Device Verification & Approval 'Phase 8' (Protocol in workflow.md)
    - [ ] On the **physical phone** (and emulator if available), `./gradlew :app:installDebug`:
        1. "Survey details" shows Survey name, Surveyor, Drawer, Municipality, Latitude,
           Longitude, Elevation; Settings shows "Magnetic variation (°, +E/-W)".
        2. Latitude/Longitude/Elevation/Variation open a numeric keyboard.
        3. Fill everything using **commas** (`43,40123`, `12,96543`, `320`, variation `2,5`),
           pick map + section, Generate → PDF shows all 9 rows, box placed without overlap.
        4. Compare with the webapp PDF for the same file and values: same rows, same map
           rotation from the variation.
        5. Enter only Latitude → red error text under the fields, Generate disabled.
        6. Enter Latitude `91` → error; fix it → Generate enabled again.
        7. Rotate the phone / leave and return to the screen → nothing crashes.
    - [ ] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.

## Phase 9: Documentation and DEVLOG

Full code: superpowers plan → **Task 9**.

- [ ] Task: Update user docs
    - [ ] `android/app/src/main/assets/guide/guide_en.md` and `guide_it.md`,
      `docs/android/README.md` and `README.it.md` (Step 1).
- [ ] Task: DEVLOG entries
    - [ ] `DEVLOG.md` and `android/DEVLOG.md` in the existing format (Step 2).
- [ ] Task: Final verification and commit
    - [ ] Python gates + Android gates. Commit
      `docs: document title block metadata fields and Android magnetic variation`.
- [ ] Task: Conductor - Device Verification & Approval 'Phase 9' (Protocol in workflow.md)
    - [ ] Android: `./gradlew :app:installDebug`, open the in-app guide in English and Italian
      → the new fields and magnetic variation are described.
    - [ ] Final end-to-end run on both devices with all fields filled (same values as Phase 8):
      PDFs match each other.
    - [ ] **Does this meet your expectations? Please confirm with yes or provide feedback on
      what needs to be changed.** — STOP and wait.
