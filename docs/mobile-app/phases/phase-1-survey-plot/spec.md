# Phase 1 — Survey Plot Screen — Spec

**Initiative:** CaveSketch Mobile App (see `../../umbrella-spec.md`, Level 1)
**Phase:** 1 of 3 · one conductor track
**Status:** Approved (design) — ready for plan
**Date:** 2026-06-19

---

## 1. Purpose

Ship the full **Survey Plot** screen on-device, at feature parity with the web
Survey Plot page (`app/pages/1_survey_plot.py`): file inputs, optional survey
merge, all settings, **Generate** → on-screen PDF preview → **Save / Share** —
built on a clean foundation that Phase 2's Satellite Map screen plugs into.

Phase 0 retired the feasibility risk (the CPython scientific stack runs on a
real phone and produces a correct PDF). Phase 1 turns that throwaway spike into
the first real app code. Its dominant open question is **performance**: the
Phase 0 spike measured a ~70s first render, but never instrumented *where* that
time goes. Phase 1 therefore opens with a measurement step and chooses its
cold-start strategy from hard data — not from the spike's (plausible but
unverified) attribution.

## 2. Findings from Phase 0 that shape this phase

From `../phase-0-spike/review.md` and `android/DEVLOG.md`:

- **Working dependency pins (proven):** `numpy==1.26.2`, `pandas==2.1.3`,
  `matplotlib==3.8.4`, `ezdxf==1.4.1`, `folium==0.19.5`; Chaquopy 17.0,
  Python 3.13, ABIs `arm64-v8a` (phone) + `x86_64` (emulator). APK ~104 MB.
- **~70s cold render is a measured _total_, not a breakdown.** The Phase 0
  timer wrapped the *first* `getModule("spike").callAttr(...)`, which bundles
  (a) the first heavy import (`numpy`/`pandas`/`matplotlib`/`ezdxf`),
  (b) `parse_dxf`, and (c) `draw_survey` (including matplotlib's first-run
  font-cache build + PDF write). `Python.start()` (interpreter boot) happens at
  app launch and is *outside* that window. The split between imports and
  draw-compute was **not** instrumented, and **no warm-render number** was
  recorded. The review's three-way attribution is informed reasoning, not data.
- **Keep the symlink:** `android/app/src/main/python/cave_sketch` →
  `../../../../../cave_sketch` exposes the untouched core to Chaquopy with zero
  duplication and avoids the Gradle input/output overlap error. Keep it.
- **Toolchain:** Gradle/AGP require JVM 17+; build with Android Studio's bundled
  JDK via `JAVA_HOME` (see `android/DEVLOG.md`).
- **`rule_length` divisibility:** `_add_rule` asserts
  `scale_len % segment_len == 0` (`cave_sketch/survey/graphics/rule.py:15`). In
  the real draw path `segment_len = rule_length / 5`
  (`cave_sketch/survey/graphics/survey_plot.py:116`), so the assertion holds
  **iff `rule_length` is a multiple of 5**. The web app guarantees this
  (`step=5, min=5`) and is never exposed; the spike tripped it only by using
  `rule_length=1.0`. Phase 1 keeps the web's input constraints and inherits the
  safety.

## 3. Sub-steps (the measurement step gates the rest)

### Step 1 — Measurement spike (first; ~1 hour)
Instrument timing to break the ~70s total into its parts before choosing a fix.
- Log timestamps around (a) the first heavy import, (b) `parse_dxf`, and
  (c) `draw_survey`, on a **cold** run (fresh process) and a **warm** second run
  (same session).
- Record the breakdown + cold/warm numbers in `android/DEVLOG.md`.
- **Decision output:** the cold-start strategy —
  - imports / font-cache dominate → **pre-warm at launch** (background import +
    matplotlib font-cache warm) so the cost is paid once and warm renders are
    fast;
  - `draw_survey` compute dominates → optimize the draw path and/or set UX
    expectations (pre-warming imports would not help per-render latency);
  - both → do both.
- This step may reuse the Phase 0 spike harness; it is throwaway measurement,
  not foundation code.

### Step 2 — Foundation
Replace the throwaway spike with the first real app structure:
- New app module / package (e.g. `com.cavesketch.app`).
- `SurveyPlotViewModel` (Kotlin) — single source of UI truth; runs Generate on
  a background dispatcher (non-blocking to Compose); owns the pre-warm job whose
  shape comes from Step 1.
- `PythonBridge.kt` — the only Kotlin that touches Python: marshals inputs,
  invokes the Python entrypoint via Chaquopy on a background dispatcher, parses
  the result.
- `survey_bridge.py` — one Python entrypoint (see §5), the mobile analogue of
  `1_survey_plot.py`, living under `android/` (**not** in `cave_sketch`).
- `AppNavHost` — a two-destination navigation skeleton: Survey Plot (this phase)
  and a Satellite Map **stub** (Phase 2 fills it in, without restructuring nav).
- Carries over the proven Chaquopy config, the `cave_sketch` symlink, and the
  PdfRenderer→bitmap display approach.
- The Phase 0 spike (`com.cavesketch.spike` `MainActivity`/`spike.py`) stays as a
  reference during development and is **deleted once Phase 1 works**.

### Step 3 — Survey Plot screen
Full Screen 1 (umbrella §7), built from small stateless sub-composables
mirroring the web components:
- **File pickers** (SAF): Cave Map and Cave Section, each `.dxf` or `.csv`;
  optional "merge another survey" with child map / child section.
- **Merge controls** (shown when a child file is present): parent station ID,
  child station ID, section protocol (`simple` / `mirror` / `displacement`);
  with the web's validation (§6).
- **Settings form** at web parity (`app/components/settings_panel.py`): rule
  length (min 5, max 1000, **step 5**), map rotation (−180..180), marker zoom /
  text zoom / line-width zoom (−1..1, step 0.1), show-station-markers toggle,
  show-grid toggle.
- **Text:** survey name, surveyor name.
- **Generate** → async with a **staged progress indicator** (labels driven by
  Step 1's findings) → **static fit-to-width PDF preview** (PdfRenderer → bitmap
  → Compose `Image`). Pinch-zoom is deferred to Phase 3.

### Step 4 — Save / Share
- `FileProvider` + the Android share sheet (`ShareCompat`), plus a "Save to
  device" action. Replaces the web's download button (umbrella §7).
- Per-session temp dir for picked inputs and generated outputs, mirroring the
  web app's `files_dir`; cleaned up per session. Nothing leaves the device
  unless the user shares it.

## 4. Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Compose UI                                                 │
│  AppNavHost ── SurveyPlotScreen   (Phase 1)                │
│             └─ SatelliteScreen (stub)   (Phase 2 fills in) │
│  SurveyPlotScreen = file pickers · merge · settings form · │
│  Generate · progress · static PDF preview · share          │
└───────────────────────┬────────────────────────────────────┘
                        │ observes UiState, sends intents
┌───────────────────────▼────────────────────────────────────┐
│ SurveyPlotViewModel  (Kotlin)                               │
│  • UiState (inputs, settings, merge, phase, result, error)  │
│  • Generate on background dispatcher (non-blocking)         │
│  • owns the pre-warm job (strategy from Step 1)             │
└───────────────────────┬────────────────────────────────────┘
                        │ calls
┌───────────────────────▼────────────────────────────────────┐
│ PythonBridge (Kotlin) ──► survey_bridge.py  (one entrypoint)│
│  copies picked files into app-private dir · calls core ·    │
│  returns output paths (+ structured errors)                 │
└───────────────────────┬────────────────────────────────────┘
                        │ Chaquopy / CPython
┌───────────────────────▼────────────────────────────────────┐
│ cave_sketch  (UNTOUCHED, via symlink)                       │
│  parse_dxf · draw_survey · merge_surveys                    │
└──────────────────────────────────────────────────────────────┘
```

Rationale: keep the Kotlin↔Python seam as thin as Phase 0 proved works — one
Python entrypoint, one Kotlin wrapper. UI truth lives in one ViewModel so the
async Generate never blocks Compose. Navigation is a skeleton from day one so
Phase 2 adds a screen rather than reshaping the app.

## 5. Shared core contract used (must not change — umbrella §5)

`survey_bridge.py` calls the same functions the web page calls:

- `parse_dxf(input_path, output_path) -> CaveSurvey` — per `.dxf` input;
  `.csv` inputs pass through unchanged.
- `merge_surveys(parent_map, parent_section, child_map, child_section,
  parent_station, child_station, section_protocol)` — optional merge path.
- `draw_survey(title, rule_length, csv_map_path, csv_section_path, child_*,
  parent_station, child_station, section_protocol, output_path, surveyor_name,
  config)` → matplotlib `Figure`; PDF written via the headless `PdfPages`
  backend.

**Proposed single entrypoint:**
`generate_survey_plot(inputs_json, work_dir) -> result_json`, where
`inputs_json` carries the input file paths, names, settings, and merge fields,
and `result_json` is `{ "pdf_path": ... }` on success or
`{ "error": <type>, "detail": <message> }` on failure. The exact JSON shape is a
plan-level detail; the contract is "one call in, paths-or-structured-error out".

If a genuine gap appears (e.g. a Streamlit-free helper that today lives in
`app/`), it is added **to `cave_sketch`** (kept Streamlit/Android-free) so both
front-ends share it — never duplicated in the app (umbrella §5).

## 6. Error handling

Every failure becomes a typed `UiState.Error` with a human-readable message —
never a crash or a silent freeze:

- **No input:** Generate disabled until at least one of map/section is selected
  (mirrors the web "upload at least one file" guard).
- **Merge validation** (replicates `app/components/merging_controls.py`): station
  IDs must be purely numeric, and the referenced station must exist in the
  parent/child survey CSV. Invalid → block Generate with an inline message. The
  check runs against the parsed CSV with the same logic as the web.
- **DXF parse / draw failure:** `survey_bridge.py` catches the Python exception
  and returns a structured `{error, detail}`; the ViewModel surfaces a friendly
  message (e.g. "Couldn't read that DXF" / "Couldn't render the plot"). The
  known `rule.py:15` assertion is pre-empted by the multiple-of-5 rule-length
  constraint.
- **Cancellation:** leaving the screen or starting a new Generate cancels the
  running coroutine cleanly.

## 7. Offline behaviour

The Survey Plot pipeline is **fully on-device** — DXF parse, merge, and PDF
render make **no network calls** (umbrella §8). Nothing in Phase 1 depends on
connectivity. (The online-only satellite preview belongs to Phase 2.)

## 8. Testing & verification

Umbrella §12 gates still apply and `cave_sketch/` stays untouched:

- **Python bridge:** thin pytest coverage of `survey_bridge.py`, run on the
  laptop under the relaxed mobile pins (numpy 1.26.2 / pandas 2.1.3 /
  matplotlib 3.8.4). Given fixture DXF/CSV inputs + a settings dict, it produces
  a PDF and returns the expected paths; the merge path and the
  validation/error paths return structured errors. Uses existing
  `tests/fixtures/` (`sample.dxf`, `test_survey.csv`).
- **Kotlin:** light unit tests on `SurveyPlotViewModel` state transitions
  (idle → running → success / error) against a faked bridge; JSON marshalling
  round-trip. Full instrumented UI tests are not a Phase 1 goal.
- **Manual on-device verification** (GEMINI.md requires real-device): generate a
  plot from a real TopoDroid DXF and confirm it matches the web output; exercise
  the merge path; share the PDF to another app. Recorded in `android/DEVLOG.md`.
- **Gates before "done":** `uv run ruff check .`, `uv run mypy cave_sketch/`,
  `uv run pytest` all green; the web app and its `pyproject.toml`/`uv.lock`
  unchanged.

## 9. Exit criteria

- [ ] **Measurement recorded:** the ~70s total is broken into import / parse /
      draw, with cold *and* warm numbers, in `android/DEVLOG.md`; the chosen
      cold-start strategy is stated.
- [ ] **Feature parity on a real phone** with the web Survey Plot page: file
      inputs (`.dxf`/`.csv`, main + child), merge with validation, all settings,
      Generate, on-screen PDF preview, Save/Share.
- [ ] **Cold-start strategy implemented** per the measurement; final cold/warm
      render numbers logged.
- [ ] **Foundation in place:** real app package, `SurveyPlotViewModel`,
      `PythonBridge` + `survey_bridge.py`, `AppNavHost` with a Satellite stub;
      Phase 0 spike code deleted.
- [ ] **Verification gates green**; `cave_sketch/` untouched; web app unchanged.
- [ ] `android/DEVLOG.md` updated with the Phase 1 entry.

## 10. Non-goals (out of scope for Phase 1)

- No satellite map / KMZ / JSON / connectivity handling (Phase 2).
- No app icon, no error-state visual polish, no pinch-zoom preview, no
  distributable release build (Phase 3).
- No changes to `cave_sketch/` (stays Streamlit/Android-free) and no changes to
  the Streamlit web app or its `pyproject.toml`/`uv.lock`.
- No new survey/drawing features — parity with today's web Survey Plot page only.

## 11. Hard constraints (umbrella §12 — apply here too)

- `cave_sketch/` stays untouched and free of UI/Streamlit/Android imports;
  shared by web + mobile via the symlink.
- Streamlit web app behaviour unchanged; web `pyproject.toml`/`uv.lock`
  unchanged. Relaxed mobile pins live only in the mobile environment.
- Python managed with `uv` (never bare `pip` for the project env).
- Mobile-app work logs to `android/DEVLOG.md`, not the root `DEVLOG.md`.
- The Android project lives under the existing top-level `android/` directory.
