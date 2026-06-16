# Phase 0 — Spike (De-risk) — Spec

**Initiative:** CaveSketch Mobile App (see `../../umbrella-spec.md`, Level 1)
**Phase:** 0 of 3 · one conductor track
**Status:** Approved (design) — ready for plan
**Date:** 2026-06-16

---

## 1. Purpose

Answer one question with hard evidence before any UI investment:

> **How hard is the CaveSketch mobile app, really?**

Phase 0 retires the dominant risk identified in umbrella-spec §9.1 — running the
CPython scientific stack (`numpy`/`pandas`/`matplotlib`) under
[Chaquopy](https://chaquo.com/chaquopy/) on a real phone — and records the
concrete numbers (working dependency versions, on-device render time, APK size)
that Phase 1's spec will build on.

It is a **throwaway spike**, not foundation code. No reusable Android scaffolding
is a goal here (that decision was made explicitly during brainstorming).

## 2. Feasibility findings that shape this phase

Research against **Chaquopy 17.0** (current release; native wheels served from
its `pypi-13.1` repository) versus this project's pins:

| Package | Project pin (`pyproject.toml`) | Max on Chaquopy 17.0 | Action |
|---|---|---|---|
| numpy | 2.2.5 | **1.26.2** | Relax (2.x → 1.26) |
| pandas | 2.2.3 | **2.1.3** | Relax (minor) |
| matplotlib | 3.10.3 | **3.8.4** (cp313) / 3.8.2 (cp312) | Relax (minor) |
| ezdxf | 1.4.1 | pure-Python (any) | None |
| folium | 0.19.5 | pure-Python (any) | None |

- Native wheels exist only for **arm64-v8a + x86_64** on **Python 3.12 / 3.13**.
  arm64-v8a covers every modern phone; x86_64 covers the emulator.
- Chaquopy 17.0: minSdk 24, Android Gradle Plugin 7.3–9.2.

**Why the downgrade is low-risk** (verified by grepping the core):
- **numpy:** every call in `cave_sketch/` is bedrock-stable
  (`np.sin/cos/mean/sqrt`, `np.column_stack`, `np.atleast_2d`, `np.empty_like`,
  `np.flatnonzero`, `np.nan`). **Zero** numpy-2.x-only or 2.0-removed APIs.
- **matplotlib:** PDF goes through
  `from matplotlib.backends.backend_pdf import PdfPages` → `pdf.savefig(fig)`
  (`cave_sketch/survey/pdf.py`) — the pure-Python, headless PDF backend. No
  GUI/display dependency; behaves identically on 3.8.

**Consequence:** most dependency risk can be retired *on the laptop* before any
Android work. Hence the two-gate structure below.

## 3. Architecture (spike slice only)

The thinnest vertical slice through the umbrella architecture:

```
Compose screen (one button: "Run spike")
        │
Kotlin bridge → Chaquopy → spike.py   (lives in android/, NOT in cave_sketch)
        │                      │ imports the UNTOUCHED cave_sketch package
        │                      └ parse_dxf(sample.dxf) → draw_survey(...) → out.pdf
        ▼
Android PdfRenderer → first page bitmap → Compose Image   (visual correctness proof)
```

- `cave_sketch/` stays **untouched and Streamlit/Android-free** (umbrella §12).
- The only Python authored is a small `spike.py` glue module under `android/`,
  mirroring what the web Survey Plot page does: call `parse_dxf` then
  `draw_survey` to produce a PDF.
- PDF is displayed with Android's built-in `PdfRenderer` → bitmap → Compose
  `Image` (no extra dependencies).

### Core contract used (must not change — umbrella §5)
- `parse_dxf(input_path, output_path=None) -> CaveSurvey` (`cave_sketch/dxf/parser.py`)
- `draw_survey(title, rule_length, csv_map_path, csv_section_path, …, output_path, …) -> Figure`
  (`cave_sketch/survey/survey.py`); PDF written via `export_pdf` / `PdfPages`.

### Spike inputs (already in the repo)
- `tests/fixtures/sample.dxf` and `tests/fixtures/test_survey.csv`. Hardcoded;
  no file picker in this phase.

## 4. Gate A — Desktop relaxed-pin proof (laptop, ~1 hour)

Cheapest risk-retirement first, where debugging is fast.

1. Create a **separate** mobile dependency environment (e.g. a `mobile` extra in
   `pyproject.toml` or a dedicated `pyproject`/lock) pinning:
   `numpy==1.26.2`, `pandas==2.1.3`, `matplotlib==3.8.4`, on **Python 3.13**
   (matches the cp313 wheels: numpy 1.26.2, pandas 2.1.3, matplotlib 3.8.4 all
   ship arm64-v8a + x86_64). `ezdxf==1.4.1`, `folium==0.19.5` unchanged.
2. Run the **existing** test suite against it: `uv run pytest`.
3. Record any code change required to pass (expected: **none**).

**The main `pyproject.toml` / `uv.lock` (numpy 2.2.5 etc., used by the web app)
are NOT modified.** The relaxed pins live only in the mobile environment.

**Gate A exit:** the full existing pytest suite is **green** under the relaxed
pins. If it is not, the failures and any code adaptations are recorded before
proceeding — and if an adaptation would touch `cave_sketch`, it must stay
Streamlit/Android-free and keep the web app green (umbrella §12).

## 5. Gate B — On-device proof (real arm64 phone)

Android Studio is **not yet installed**, so Gate B begins with toolchain setup.

1. **Toolchain:** install Android Studio + SDK + JDK. Create the `android/`
   Gradle project with the Chaquopy 17.0 plugin (AGP 7.3–9.2, minSdk 24,
   Python 3.13, ABIs `arm64-v8a` for the phone — optionally also `x86_64`).
2. **Python packaging:** `pip { install … }` the relaxed pins proven in Gate A;
   bundle the `cave_sketch/` sources and `tests/fixtures/sample.dxf` into the APK.
3. **UI + bridge:** one Compose screen, one "Run spike" button → Kotlin bridge →
   `spike.py` → PDF written to app-private storage.
4. **Display:** render PDF page 1 via Android `PdfRenderer` into a Compose
   `Image`, and eyeball-compare it to the desktop-generated PDF for the same
   `sample.dxf`.
5. **Deploy:** install and run on the **real phone** over USB (not emulator-only;
   GEMINI.md requires real-device verification).

## 6. Exit criteria — "done + difficulty known"

- [ ] **Gate A green:** existing `uv run pytest` passes under the relaxed pins.
- [ ] **APK runs on the real phone** and shows a PDF **visually matching** the
      desktop output for `sample.dxf`.
- [ ] **Numbers recorded** in `android/DEVLOG.md` and this `spec.md` (or a
      `findings` note): final working dependency versions, Python version, ABIs,
      **PDF render time on device**, **APK size**, and any surprises.
- [ ] **Difficulty verdict** for the remaining phases (green / yellow / red),
      written from this real evidence, to inform the Phase 1 spec.
- [ ] `android/DEVLOG.md` created (first mobile-app DEVLOG entry; umbrella §12).

## 7. Non-goals (explicitly out of scope for the spike)

No file picker · no settings (rule length, rotation, zooms, toggles) · no merge
support · no satellite map / KMZ / JSON · no save/share sheet · no app icon · no
error-state polish · no reusable Android scaffolding. Sample input is hardcoded.
All of these belong to Phase 1+.

## 8. Hard constraints (umbrella §12 — apply here too)

- `cave_sketch/` stays untouched and free of UI/Streamlit/Android imports.
- Streamlit web app behaviour unchanged; main `pyproject.toml`/`uv.lock` for the
  web app unchanged.
- Python managed with `uv` (never bare `pip` for the project env). Commit lock
  changes for the mobile env if one is added.
- Mobile-app work logs to **`android/DEVLOG.md`**, not the root `DEVLOG.md`.
- The Android project lives under a new top-level `android/` directory.
