# Plan: Reduce Survey PDF Render Latency (Lossless)

> Full code for every step lives in
> `docs/superpowers/plans/2026-06-23-survey-render-latency.md`. This conductor
> plan mirrors it in phases. Follow the standard task workflow in
> `conductor/workflow.md` (Red → Green → verify → commit → git note → mark `[x]`).
> Phases are ordered so the safety net lands first, then each optimization is
> verified against it. Measure on the S22 during the Phase 3 and Phase 4 manual
> verification steps.

## Phase 1: Image-Regression Safety Net

Build the PNG baseline gate FIRST, from the current (unoptimized) code, so every
later phase can prove it did not change the output. The title block embeds
`datetime.date.today()`, so the date must be pinned for deterministic images.

- [ ] Task: Write the image-regression test (Red/characterization)
    - [ ] Create `tests/test_render_regression.py` using `matplotlib.use("Agg")`,
      `matplotlib.testing.compare.compare_images`, and a `fixed_date` fixture
      that monkeypatches `cave_sketch.survey.graphics.title_block.datetime.date`
      to a fixed `date(2026, 1, 1)`.
    - [ ] Parametrize two scenarios over the dense `tests/fixtures/sample.dxf`:
      `plan_only` (`draw_survey(csv_map_path=...)`) and `dual`
      (`draw_survey(csv_map_path=..., csv_section_path=...)`, reusing the same
      parsed CSV for both). Render to PNG at `dpi=100`, compare with `tol=1.0`.
    - [ ] Gate baseline generation behind env var
      `CAVE_SKETCH_GENERATE_BASELINES` (generate + `pytest.skip` when set).
- [ ] Task: Generate baselines from current code
    - [ ] Run `CAVE_SKETCH_GENERATE_BASELINES=1 uv run pytest tests/test_render_regression.py -v`
    - [ ] Confirm `tests/fixtures/render_baselines/plan_only.png` and `dual.png`
      now exist (both scenarios SKIP).
- [ ] Task: Verify the test passes against the fresh baselines (Green)
    - [ ] Run `uv run pytest tests/test_render_regression.py -v`; confirm both
      `[plan_only]` and `[dual]` PASS.
    - [ ] Commit test + committed baseline PNGs
      (`test: add survey render image-regression baseline`).
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Image-Regression Safety Net' (Protocol in workflow.md)

## Phase 2: De-duplicate DXF File Reads in parse_dxf

`parse_dxf` calls `ezdxf.readfile()` four times. Read once, pass the modelspace
to each helper. Output identical — covered by `tests/test_dxf_parser.py` and the
Phase 1 regression test.

- [ ] Task: Confirm safety net is green before refactor
    - [ ] Run `uv run pytest tests/test_dxf_parser.py tests/test_render_regression.py -v`; all PASS.
- [ ] Task: Read the DXF once and thread `msp` through the helpers
    - [ ] In `cave_sketch/dxf/parser.py`, read once in `parse_dxf`
      (`doc = ezdxf.readfile(input_str); msp = doc.modelspace()`) and call
      `_get_stations(msp)`, `_parse_polylines(msp, filter_layers=["SCRAP_0"])`,
      `_get_offset(msp, offset_idx=0)`, `_get_features(msp)`.
    - [ ] Change the four helper signatures from `(input_dxf_file: str, ...)` to
      `(msp, ...)` and delete their `ezdxf.readfile(...)` / `.modelspace()`
      lines. Leave every loop body, filter, and return value unchanged.
- [ ] Task: Verify and commit
    - [ ] Run `uv run pytest tests/test_dxf_parser.py tests/test_render_regression.py -v`; all PASS.
    - [ ] Run `uv run mypy cave_sketch/ && uv run ruff check .`; no errors.
    - [ ] Commit (`perf(dxf): read DXF file once instead of four times in parse_dxf`).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: De-duplicate DXF File Reads' (Protocol in workflow.md)

## Phase 3: Eliminate the O(n²) Neighbour Lookup

Replace the per-node `df[df["Node_Id"] == nbr]` scan with a one-time coordinate
index. Lock the exact output with a feature-equality test (the second
safety-net tier).

- [ ] Task: Write the feature-equality characterization test (passes on current code)
    - [ ] Create `tests/test_render_features.py` with a small 3-node `L_wall`
      DataFrame (Node_Id/Links as strings, mirroring `renderer._survey_to_df`).
    - [ ] Assert the exact `extract_features_from_df` output: 4 line dicts with
      keys `coords`/`color`/`weight`/`dash`/`popup`, empty `polygons`/`points`.
    - [ ] Add a test that `excluded_nodes=["B"]` removes every segment touching B,
      and a test that a missing neighbour (`Links="Z"`) yields no line.
    - [ ] Run `uv run pytest tests/test_render_features.py -v`; confirm PASS on the
      current (un-refactored) implementation — this is the contract to preserve.
- [ ] Task: Refactor to a coordinate index (O(n))
    - [ ] In `cave_sketch/features/render_features.py`, build `coord_index` once
      via `df.itertuples(index=False)` with **first-occurrence-wins** semantics
      (`if row.Node_Id not in coord_index:`), and replace the inner DataFrame
      scan with `coord_index[nbr]` (skip when `nbr not in coord_index`).
    - [ ] Replace `df.iterrows()` with `df.itertuples(index=False)` in the main
      loop; preserve the `excluded` set, the `A_`/point/line branching, the dash
      logic, and the unchanged `# 2️⃣ Handle area features` polygon block.
    - [ ] Ensure `Any` is imported in the typing import line.
- [ ] Task: Verify and commit
    - [ ] Run `uv run pytest tests/test_render_features.py tests/test_render_regression.py -v`; all PASS.
    - [ ] Run `uv run mypy cave_sketch/ && uv run ruff check .`; no errors.
    - [ ] Commit (`perf(render): replace O(n^2) neighbour scan with coordinate index`).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Eliminate O(n^2) Lookup' (Protocol in workflow.md)
    - [ ] As part of verification, regenerate a survey PDF on the S22 and record
      the warm `draw_survey` time for the before/after comparison.

## Phase 4: Batch Matplotlib Artists & Remove Debug Prints

Replace per-segment `ax.plot` with a single `LineCollection`, per-point
`ax.scatter` with one `scatter` per marker, batch the station scatter, and delete
the leftover `print()` calls. The Phase 1 image-regression test is the gate.

- [ ] Task: Confirm safety net is green before changes
    - [ ] Run `uv run pytest tests/test_render_regression.py tests/test_survey_rendering.py -v`; all PASS.
- [ ] Task: Batch artists in `render_to_matplotlib`
    - [ ] In `cave_sketch/backend_renders/matplotlib.py`: remove
      `print("BLOCK!!")` / `print("ICE")`.
    - [ ] Keep polygons as the existing per-patch loop (few). Collect all lines
      into `segments`/`colors`/`linewidths`/`linestyles` and draw one
      `LineCollection(..., alpha=0.9, zorder=2)` via `ax.add_collection`
      (preserve the `lw = clip(weight * zoom_factor / ref_scale, 0.2, 4)` and
      `(0, tuple(dash))`/`"solid"` logic).
    - [ ] Group points by marker and draw one `ax.scatter` per marker
      (`s = size**2 * 0.5`, `c=colors`, `edgecolors="none"`, `alpha=0.9`,
      `zorder=3`); keep the optional `show_labels` text loop.
- [ ] Task: Batch the station scatter in `create_survey`
    - [ ] In `cave_sketch/survey/graphics/survey_plot.py`, replace the
      per-station `iterrows` loop (lines ~69-83) with a single
      `ax.scatter(stations["X"], stations["Y"], s=marker_size, color="red", zorder=5)`
      over the station-mask rows, keeping the per-station `ax.text` labels.
- [ ] Task: Verify against baseline (and fix viewport if needed)
    - [ ] Run `uv run pytest tests/test_render_regression.py tests/test_survey_rendering.py -v`; all PASS.
    - [ ] If a scenario fails on a shifted/clipped viewport (not a style change),
      add `ax.autoscale_view()` right after `ax.add_collection(lc)` and re-run.
- [ ] Task: Full gates and commit
    - [ ] Run `uv run pytest && uv run mypy cave_sketch/ && uv run ruff check .`; all PASS.
    - [ ] Commit (`perf(render): batch matplotlib artists and drop debug prints`).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Batch Artists & Remove Prints' (Protocol in workflow.md)
    - [ ] Regenerate a survey PDF on the S22, confirm it looks correct, record the
      warm `draw_survey` before/after timing, and append a DEVLOG entry to both
      `DEVLOG.md` (core) and `android/DEVLOG.md` (device impact).
