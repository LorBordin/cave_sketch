# Survey Render Latency Reduction — Design Spec

**Status:** Approved (design)
**Date:** 2026-06-23
**Scope:** `cave_sketch/` core (shared by Streamlit web app + Android app)
**Related:** `docs/mobile-app/umbrella-spec.md`, `docs/mobile-app/phases/phase-1-survey-plot/review.md`

---

## 1. Problem

On a physical device (Samsung Galaxy S22, SM-S901B), generating the survey PDF
takes ~65–68 s total even on relatively simple sketches. The measured breakdown
(`phases/phase-1-survey-plot/review.md`, §2):

| Step | Warm timing |
| :--- | :--- |
| Python / library imports | 0 ms (already pre-warmed at app launch) |
| DXF parsing (`parse_dxf`) | ~4.5 s |
| Matplotlib render (`draw_survey`) | ~60.6 s |
| **Total** | **~65 s** |

`draw_survey` is ~90% of runtime and is the primary target. The DXF parse is a
secondary, low-risk win.

## 2. Goal & success criteria

- Cut `draw_survey` from ~60 s toward a few seconds on the S22.
- **Output must be pixel-identical** to the current PDF — no fidelity change.
- Leave the parse/render code **simpler** than we found it.
- `cave_sketch` public signatures (umbrella-spec §5) unchanged; both front-ends
  benefit with zero caller changes.

Success = the lossless optimizations land, the regression safety net proves
identical output, all verification gates pass, and a before/after S22 timing is
recorded.

## 3. Non-goals (explicitly out of scope)

- **No downsampling / vertex simplification** of walls or any feature (would
  change output). Held in reserve only if the lossless work misses target.
- **No rendering-backend swap** (would affect the web app; last resort).
- **No change to `cave_sketch` public function signatures.**
- **No change to Streamlit web app behaviour** (it calls the same functions and
  must render identically).

## 4. Root-cause analysis

Three concrete hotspots, all inside `draw_survey`, plus one in the parser:

1. **O(n²) neighbour lookup** — `cave_sketch/features/render_features.py:96-99`.
   For every node, `extract_features_from_df` does
   `df[df["Node_Id"] == nbr]` (a full DataFrame scan) inside a loop over every
   node. TopoDroid wall scraps (`SCRAP_0` polylines) are exploded into one node
   per vertex (`cave_sketch/dxf/parser.py:48-69`), so dense-looking-but-simple
   sketches have thousands of nodes and this term grows quadratically. Likely
   the single dominant cost.

2. **One matplotlib artist per primitive** —
   `cave_sketch/backend_renders/matplotlib.py`. Each wall segment is its own
   `ax.plot()` (Line2D) and each point its own `ax.scatter()`. Thousands of
   individual artists are slow to build and to serialize to PDF. The per-station
   loop in `cave_sketch/survey/graphics/survey_plot.py:71-83` has the same shape.

3. **Leftover debug prints** — `matplotlib.py:70-72`
   (`print("BLOCK!!")` / `print("ICE")`) fire once per point; per-element stdout
   on Android is expensive.

4. **Redundant DXF reads** — `cave_sketch/dxf/parser.py` calls
   `ezdxf.readfile(...)` four separate times (`_get_stations`,
   `_parse_polylines`, `_get_offset`, `_get_features`), parsing the same file 4×.

## 5. Components

### Component 1 — Regression safety net (built FIRST, from current `main`)

Two tiers so identical output is *enforced*, not assumed:

- **Feature-equality unit test** (`tests/`): assert that
  `extract_features_from_df(...)` returns an identical features dict before and
  after the Component 2 refactor. Deterministic and environment-independent.
- **Image-regression test**: render representative fixtures to PNG at a fixed
  DPI and compare to committed baselines via
  `matplotlib.testing.compare.compare_images` with a small RMS tolerance.
  Fixtures:
  - small: `tests/fixtures/test_survey.csv`
  - denser: parsed `tests/fixtures/sample.dxf` (exercises the polyline-explosion
    hotspot)
  - a dual plan + section render
  Baselines are generated on the pinned matplotlib/freetype stack **before** any
  optimization and committed. Caveat: PNG rasterization is sensitive to
  matplotlib/freetype versions, so the tolerance absorbs sub-pixel noise; this is
  a developer-machine gate, not a cross-machine guarantee.

### Component 2 — Eliminate the O(n²) lookup

In `extract_features_from_df` (`render_features.py`):
- Build a `{Node_Id: (X, Y)}` dict once and replace the per-neighbour
  `df[df["Node_Id"] == nbr]` scan with a dict lookup (missing neighbour → skip,
  matching the current `nbr_row.empty` behaviour).
- Replace `df.iterrows()` with `itertuples` for speed and clarity.
- Output: identical features dict (proven by the Component 1 unit test).
- Net effect: nested DataFrame filtering removed — simpler and O(n).

### Component 3 — Batch matplotlib artists + remove debug prints

In `backend_renders/matplotlib.py`:
- Delete `print("BLOCK!!")` / `print("ICE")`.
- **Lines** → group by dash pattern into one `LineCollection` per group, with
  per-segment color and linewidth arrays. Preserve `zorder` and `alpha` exactly
  (current data sets all lines to the default `zorder=2`).
- **Points** → one `scatter` call per marker type, with size and color arrays
  (preserving the existing `size_pts**2 * 0.5` area mapping and `zorder=3`).
- **Polygons** are few → left as the existing per-polygon loop.

In `survey/graphics/survey_plot.py`:
- **Stations** → collect station coordinates and emit a single batched
  `ax.scatter(...)`. Text labels stay per-label (no batched-text API in
  matplotlib); behaviour and styling unchanged.

Verified against the Component 1 image baseline.

### Component 4 — Parser read-once

In `dxf/parser.py`:
- Read the file once into a `modelspace` (`msp`) and pass it to the four helpers
  (`_get_stations`, `_parse_polylines`, `_get_offset`, `_get_features`),
  changing their signatures to accept the `msp` instead of a path.
- Output identical (covered by existing `tests/test_dxf_parser.py`).
- Simpler, and turns ~4.5 s parse into roughly ~1 s.

## 6. Sequencing — measure between steps

1. Land **Component 1**; commit baselines generated from current `main`.
2. **Component 4** (isolated, simplest). Run full suite.
3. **Component 2**. Run full suite. **Measure `draw_survey` on the S22.**
4. **Component 3**. Run full suite. **Measure `draw_survey` on the S22.**
5. Final verification gates; record before/after timings.

The step-3 measurement reveals whether batching (step 4) is strictly needed to
hit target. Batching stays in the plan regardless, because it serves the
simplify-and-de-risk goal, but the data tells us how much it contributed.

## 7. Edge cases

- Empty survey / single point / no links: dict lookup with skip-on-miss matches
  the current `nbr_row.empty` guard.
- Mixed solid/dashed lines: handled by grouping into separate `LineCollection`s.
- `excluded_nodes` filtering behaviour is preserved exactly.
- Mixed marker types among point features: handled by one `scatter` per marker.

## 8. Verification gates (before "done")

- `uv run ruff check .`
- `uv run mypy cave_sketch/`
- `uv run pytest` (existing suite + new Component 1 tests green)
- On-device S22 re-measurement of `draw_survey`, before/after, recorded in
  `android/DEVLOG.md` (and the root `DEVLOG.md` for the core change).
