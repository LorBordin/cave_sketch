# Spec: Reduce Survey PDF Render Latency (Lossless)

## Overview

Generating the survey PDF in the mobile app's "Survey" section takes ~65–68 s
even for relatively simple sketches. An on-device measurement spike (Samsung
Galaxy S22, SM-S901B; see `docs/mobile-app/phases/phase-1-survey-plot/review.md`
§2) isolated the cost:

| Step | Warm timing |
| :--- | :--- |
| Python / library imports | 0 ms (already pre-warmed at app launch) |
| DXF parsing (`parse_dxf`) | ~4.5 s |
| Matplotlib render (`draw_survey`) | ~60.6 s |
| **Total** | **~65 s** |

`draw_survey` is ~90% of runtime and is the primary target. This track removes
that latency with **lossless** changes only — the generated PDF must remain
pixel-identical. All work lives in the shared `cave_sketch/` core, so both the
Streamlit web app and the Android app benefit with no caller changes.

## Read First

- `docs/superpowers/specs/2026-06-23-survey-render-latency-design.md` — design.
- `docs/superpowers/plans/2026-06-23-survey-render-latency.md` — detailed
  step-by-step plan with full code for every change (this conductor plan mirrors
  it in phases).
- `docs/mobile-app/phases/phase-1-survey-plot/review.md` §2 — the latency
  measurements this track is based on.
- Source: `cave_sketch/features/render_features.py`,
  `cave_sketch/backend_renders/matplotlib.py`,
  `cave_sketch/survey/graphics/survey_plot.py`, `cave_sketch/dxf/parser.py`,
  `cave_sketch/survey/graphics/title_block.py`.

## Problem

Four concrete hotspots, all lossless to fix:

1. **O(n²) neighbour lookup** — `cave_sketch/features/render_features.py:96-99`.
   `extract_features_from_df` runs `df[df["Node_Id"] == nbr]` (a full DataFrame
   scan) inside a loop over every node. TopoDroid wall scraps (`SCRAP_0`
   polylines) explode into one node per vertex (`dxf/parser.py:48-69`), so
   "simple-looking" dense sketches carry thousands of nodes and this term grows
   quadratically. Likely the single dominant cost.
2. **One matplotlib artist per primitive** —
   `cave_sketch/backend_renders/matplotlib.py`. Each wall segment is its own
   `ax.plot()` and each point its own `ax.scatter()`; the per-station loop in
   `survey/graphics/survey_plot.py:71-83` is the same shape. Thousands of
   individual artists are slow to build and to serialize into the PDF.
3. **Leftover debug prints** — `backend_renders/matplotlib.py:70-72`
   (`print("BLOCK!!")` / `print("ICE")`) fire once per point; per-element stdout
   on Android is expensive.
4. **Redundant DXF reads** — `cave_sketch/dxf/parser.py` calls
   `ezdxf.readfile(...)` four separate times, parsing the same file 4×.

## Functional Requirements

1. **Pixel-identical output.** The PDF/PNG produced by `draw_survey` after these
   changes must match the current output. A PNG image-regression test
   (rasterized at fixed DPI, with the title-block date pinned) enforces this.
2. **O(1) neighbour resolution.** `extract_features_from_df` builds a one-time
   `{Node_Id: (X, Y)}` index (first occurrence wins, matching the current
   `.iloc[0]` behaviour) and returns a features dict identical to today's.
3. **Batched artists.** `render_to_matplotlib` draws all lines via a single
   `LineCollection` (per-segment color/linewidth/linestyle) and one `scatter`
   per marker type; `create_survey` draws stations with one batched `scatter`
   (text labels stay per-label). The debug `print()` calls are removed.
4. **Single DXF read.** `parse_dxf` reads the file once and passes the
   `modelspace` to its four helpers.
5. **Stable public interface.** Signatures of `parse_dxf`, `draw_survey`,
   `merge_surveys`, `draw_map` are unchanged.

## Non-Functional Requirements

- `cave_sketch/` stays **Streamlit-free**; shared by web + mobile.
- Python 3.11+, full type annotations on public functions.
- Mandatory gates pass: `uv run ruff check .`, `uv run mypy cave_sketch/`,
  `uv run pytest`.
- Project managed with `uv` (never bare `pip`).

## Acceptance Criteria

1. The image-regression test (`tests/test_render_regression.py`) passes for both
   a plan-only and a dual plan+section render of the dense `sample.dxf` fixture.
2. A feature-equality test (`tests/test_render_features.py`) asserts the exact
   `extract_features_from_df` output and continues to pass after the O(n²) fix.
3. The existing suite (`tests/test_dxf_parser.py`, `tests/test_survey_rendering.py`,
   and all others) continues to pass.
4. `parse_dxf` performs exactly one `ezdxf.readfile`.
5. `render_to_matplotlib` contains no `print()` statements; lines are drawn via
   `LineCollection` and points via one `scatter` per marker.
6. On-device (S22) warm `draw_survey` time is measured before/after and recorded
   in `DEVLOG.md` and `android/DEVLOG.md`, referencing the ~60 s baseline.
7. All mandatory verification gates pass.

## Out of Scope

- **Downsampling / vertex simplification** of walls or any feature (changes
  output). Held in reserve only if the lossless work misses target.
- **Rendering-backend swap** (would affect the web app; last resort).
- Any change to `cave_sketch` public function signatures.
- Any change to Streamlit web app behaviour (it renders via the same functions
  and must stay identical).
- New survey/drawing features or UI changes.
