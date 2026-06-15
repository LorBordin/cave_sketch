# CaveSketch Mobile App — Umbrella Spec (Roadmap)

**Status:** Approved (design). Phase specs created just-in-time.
**Date:** 2026-06-15
**Level:** 1 (roadmap). Per-phase specs/plans live under `phases/`.

---

## 1. Goal

Ship an installable Android app (sideloaded `.apk`) that exposes **all** of
CaveSketch's existing functionality and works **offline in the field**, while
the existing Streamlit web app keeps working unchanged.

A caver with no signal must be able to:
- import TopoDroid `.dxf` (or `.csv`) files,
- generate the PDF survey plot (plan + section, with merging),
- georeference the cave and export a **KMZ + JSON** for offline GIS apps (e.g. Locus Map).

The satellite **preview** is the only feature allowed to require internet; it
degrades gracefully when offline (see §6).

## 2. Non-goals

- **No iOS** in this initiative (`.apk` / Android only).
- **No Google Play Store** distribution (sideload only). Play release may come later.
- **No rewrite of the Python logic** into another language.
- **No change to the Streamlit web app's behaviour.**
- **No new survey/drawing features** — parity with today's web app only.

## 3. Background — current state

CaveSketch is a Python project:

- `cave_sketch/` — pure-Python core library. **Zero Streamlit imports.** Does
  DXF parsing (`ezdxf`), survey rendering & PDF (`matplotlib`), georeferencing,
  HTML map (`folium`), KML/KMZ and JSON export. Deps: `ezdxf`, `folium`,
  `matplotlib`, `numpy`, `pandas`.
- `app/` — Streamlit web UI (pages, components, `session.py`). Thin glue: it
  collects inputs and calls `cave_sketch` functions. No business logic.
- `tests/` — pytest over the core.

The core already has a clean, path-in / file-out interface (see §5), which is
what makes a second front-end feasible without touching it.

## 4. Architecture decision

**Native Android shell (Kotlin + Jetpack Compose) embedding a real CPython
runtime via [Chaquopy](https://chaquo.com/chaquopy/), calling the untouched
`cave_sketch` package.**

```
┌─────────────────────────────────────────────┐
│  Android UI (Kotlin + Jetpack Compose)      │  NEW
│  Survey Plot screen · Satellite Map screen  │
└───────────────────┬─────────────────────────┘
                    │ passes file paths, reads back output paths
┌───────────────────▼───────────────────────────┐
│  Bridge layer (thin Kotlin ↔ Python glue)     │  NEW (small)
│  copy picked files in · call core fns · return│
│  output paths (pdf / html / json / kmz)       │
└───────────────────┬───────────────────────────┘
                    │ Chaquopy (embedded CPython + deps in the .apk)
┌───────────────────▼────────────────────────────┐
│  cave_sketch  (UNTOUCHED, shared with web)     │  EXISTING
│  ezdxf · matplotlib · numpy · pandas · folium  │
└────────────────────────────────────────────────┘
```

**Why Python-on-device is the crux (not the UI):** a phone app is a
self-contained `.apk`; it cannot assume Python is installed. Chaquopy bundles a
CPython interpreter + mobile builds of `numpy`/`pandas`/`matplotlib` + the
`cave_sketch` sources *inside* the `.apk`, so the genuine Python code runs
offline. No algorithm is translated. The work is *packaging* + *native UI
wiring*, not porting logic.

**Rejected alternative:** stlite/Pyodide (Streamlit-in-WebAssembly wrapped as a
WebView `.apk`). Lower effort and high code reuse, but a non-native "web app in
a shell". The user explicitly chose the native path for feel/performance.

## 5. Shared core — the interface the app calls

The mobile bridge calls the same functions the web app calls. These define the
contract and **must not change** for the mobile work:

- `parse_dxf(input_path, output_path)` — DXF → CSV.
- `draw_survey(title, rule_length, csv_map_path, csv_section_path, child_*,
  parent_station, child_station, section_protocol, output_path, surveyor_name,
  config)` → matplotlib `Figure` + writes PDF.
- `merge_surveys(...)` — merge parent/child surveys.
- `draw_map(map_path, gps_points, output_path, map_name,
  additional_json_maps, rotation_angle)` → `(html, json_path, kmz_path)`.

If a genuine gap appears (e.g. a function needs a Streamlit-free helper that
today lives in `app/`), it is added **to `cave_sketch`** (keeping it
Streamlit-free) so both front-ends share it — never duplicated in the app.

## 6. Repository structure (target)

```
cave_sketch/   shared core. UNTOUCHED. Used by BOTH web and mobile.
app/           existing Streamlit web UI. Unchanged.
android/       NEW native app (Kotlin/Compose + Chaquopy → ../cave_sketch)
tests/         existing core tests keep passing; bridge gets thin tests.
docs/mobile-app/   this initiative (umbrella + per-phase specs).
```

## 7. Screens (feature parity with the web app)

**Screen 1 — Survey Plot**
- File pickers: Cave Map (`.dxf`/`.csv`), Cave Section (`.dxf`/`.csv`).
- Optional "merge another survey": child map/section + parent station, child
  station, section protocol.
- Text: survey name, surveyor name.
- Settings: rule length, rotation, marker zoom, text zoom, line-width zoom,
  "show station markers" toggle, "show grid" toggle.
- **Generate** → `parse_dxf` then `draw_survey` → on-screen PDF preview →
  **Save / Share PDF**.

**Screen 2 — Satellite Map**
- GPS points editor: add/remove rows of (station, lat, lon).
- Text: survey name; number: rotation angle.
- Optional: import additional JSON maps.
- **Generate** → `draw_map` → HTML map (WebView preview *if online*), JSON, KMZ →
  **Save / Share** each.

Mobile replaces web "download" buttons with **Save to device / Share** (Android
share sheet), so KMZ can go straight to Locus Map, PDF to Files, etc.

## 8. Offline behaviour & file handling

- **Fully on-device (work offline):** DXF parse, survey PDF, KMZ + JSON export.
  No network calls.
- **Online-dependent (degrades gracefully):** the satellite *preview*. folium
  HTML references online tile servers. When offline, the app detects no
  connectivity, shows a clear **"No connection — satellite preview
  unavailable"** banner, skips tile rendering, and **still generates KMZ +
  JSON** to save/share.
- **Files:** picked inputs are copied into app-private storage; outputs written
  there too, surfaced via the Android share sheet / "Save to Files". Per-session
  temp cleanup mirrors the web app's `files_dir` approach. Nothing leaves the
  device unless the user shares it.

## 9. Risks (de-risk early)

1. **Dependency build compatibility (main risk).** Chaquopy ships its own
   `numpy`/`pandas`/`matplotlib` versions, which may differ from the pins in
   `pyproject.toml` (`numpy==2.2.5`, etc.). The mobile build may need relaxed
   pins. `ezdxf`/`folium` are pure Python — low risk.
2. **`matplotlib` on Android.** Works under Chaquopy; PDF generation may be the
   slowest step. Verify performance on a real device in Phase 0.
3. **`.apk` size.** Bundling Python + scientific libs yields a larger `.apk`
   (tens of MB). Acceptable for this tool.

These are resolved **before** investing in polished UI (Phase 0).

## 10. Phased plan

Each phase is built just-in-time with its own `spec.md` + `plan.md` under
`phases/`, after the previous phase's findings are known.

- **Phase 0 — Spike (de-risk).** Bare Android project + Chaquopy. Call
  `parse_dxf` + `draw_survey` on a sample DXF; render the PDF on screen.
  *Exit criteria:* the Python scientific stack runs on a real phone and produces
  a correct PDF; dependency versions + rough render time recorded.
- **Phase 1 — Survey Plot screen.** Full Screen 1: all settings, merge support,
  save/share PDF. *Exit:* feature parity with the web Survey Plot page on device.
- **Phase 2 — Satellite Map screen.** Screen 2: GPS editor, JSON import,
  connectivity handling, save/share HTML/JSON/KMZ. *Exit:* parity with the web
  Satellite Map page, including offline KMZ.
- **Phase 3 — Polish & release.** App icon, error states, session cleanup,
  build a distributable `.apk`. *Exit:* a sideloadable `.apk`.

## 11. Two-level spec process

- **Level 1 (this file):** stable roadmap — architecture, structure, risks,
  phase boundaries. Changes rarely.
- **Level 2 (`phases/<phase>/spec.md` + `plan.md`):** detailed, created right
  before building each phase. Phase N's spec may incorporate findings from
  earlier phases (e.g. the dependency versions discovered in Phase 0). We do
  **not** pre-write all phase specs up front.

Each phase maps to one **conductor track** for `agy` (see `GEMINI.md`).

## 12. Hard constraints (both tools, every phase)

- `cave_sketch/` stays **untouched and Streamlit-free**; shared by web + mobile.
- Streamlit web app behaviour is unchanged.
- Python project managed with **`uv`** (never bare `pip`); commit `uv.lock`.
- Verification gates before "done": `uv run ruff check .`,
  `uv run mypy cave_sketch/`, `uv run pytest` all pass.
- **Two DEVLOGs.** The root `DEVLOG.md` covers the Python project (the
  `cave_sketch` core + the Streamlit web app). Mobile work logs to a separate
  `android/DEVLOG.md` (created in Phase 0). Use the same entry format for both.
