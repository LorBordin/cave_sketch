# Survey Render Latency Reduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut `draw_survey` render time on Android from ~60 s toward a few seconds, with pixel-identical PDF output, by removing an O(n²) lookup, batching matplotlib artists, deleting debug prints, and de-duplicating DXF file reads.

**Architecture:** All work is inside the shared `cave_sketch/` core (used by both the Streamlit web app and the Android app). Public function signatures are unchanged. A two-tier regression safety net (feature-dict equality + PNG image comparison) is built first to enforce identical output, then four lossless optimizations land behind it.

**Tech Stack:** Python 3, `pandas`, `numpy`, `matplotlib` (Agg/PDF backends), `ezdxf`, `pytest`, `uv`.

## Global Constraints

- `cave_sketch/` stays **Streamlit-free**; it is shared by web + mobile — copied verbatim from spec.
- **No change to `cave_sketch` public function signatures** (`parse_dxf`, `draw_survey`, `merge_surveys`, `draw_map`).
- **Output must be pixel-identical** to current PDFs — no downsampling, no fidelity change.
- **No rendering-backend swap.**
- Python project managed with **`uv`** (never bare `pip`); commit `uv.lock` if it changes.
- Verification gates before "done": `uv run ruff check .`, `uv run mypy cave_sketch/`, `uv run pytest` all pass.

---

### Task 1: Image-regression safety net

Build the PNG baseline gate FIRST, from the current (unoptimized) code, so every later task can prove it did not change the output. The title block embeds `datetime.date.today()`, so the date must be pinned for deterministic images.

**Files:**
- Create: `tests/test_render_regression.py`
- Create (generated): `tests/fixtures/render_baselines/plan_only.png`, `tests/fixtures/render_baselines/dual.png`
- Uses: `tests/fixtures/sample.dxf` (existing)

**Interfaces:**
- Consumes: `cave_sketch.dxf.parser.parse_dxf(input_path: Path, output_path: Optional[Path]) -> CaveSurvey`; `cave_sketch.survey.draw_survey(title, rule_length, csv_map_path=None, csv_section_path=None, ...) -> matplotlib.figure.Figure`.
- Produces: committed baseline PNGs + a regression test later tasks must keep green.

- [ ] **Step 1: Write the regression test**

Create `tests/test_render_regression.py`:

```python
import datetime
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.testing.compare import compare_images

from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.survey import draw_survey

BASELINE_DIR = Path(__file__).parent / "fixtures" / "render_baselines"
SAMPLE_DXF = Path(__file__).parent / "fixtures" / "sample.dxf"
SCENARIOS = ["plan_only", "dual"]
TOL = 1.0  # RMS; same machine + pinned mpl/freetype yields ~0, tol absorbs sub-pixel noise


class _FixedDate(datetime.date):
    @classmethod
    def today(cls):
        return cls(2026, 1, 1)


@pytest.fixture
def fixed_date(monkeypatch):
    monkeypatch.setattr(
        "cave_sketch.survey.graphics.title_block.datetime.date", _FixedDate
    )


def _render(scenario: str, csv_path: Path, out_png: Path) -> None:
    if scenario == "plan_only":
        fig = draw_survey(title="Regression", rule_length=20, csv_map_path=str(csv_path))
    else:  # dual: reuse the same survey as both plan and section
        fig = draw_survey(
            title="Regression",
            rule_length=20,
            csv_map_path=str(csv_path),
            csv_section_path=str(csv_path),
        )
    fig.savefig(out_png, dpi=100)
    plt.close(fig)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_render_matches_baseline(scenario, tmp_path, fixed_date):
    csv_path = tmp_path / "parsed.csv"
    parse_dxf(SAMPLE_DXF, csv_path)

    if os.environ.get("CAVE_SKETCH_GENERATE_BASELINES"):
        BASELINE_DIR.mkdir(parents=True, exist_ok=True)
        _render(scenario, csv_path, BASELINE_DIR / f"{scenario}.png")
        pytest.skip(f"Generated baseline for {scenario}")

    baseline = BASELINE_DIR / f"{scenario}.png"
    actual = tmp_path / f"{scenario}.png"
    _render(scenario, csv_path, actual)
    result = compare_images(str(baseline), str(actual), tol=TOL)
    assert result is None, result
```

- [ ] **Step 2: Generate the baselines from current code**

Run: `CAVE_SKETCH_GENERATE_BASELINES=1 uv run pytest tests/test_render_regression.py -v`
Expected: both scenarios SKIP with "Generated baseline ..."; `tests/fixtures/render_baselines/plan_only.png` and `dual.png` now exist.

- [ ] **Step 3: Verify the test passes against the fresh baselines**

Run: `uv run pytest tests/test_render_regression.py -v`
Expected: both `test_render_matches_baseline[plan_only]` and `[dual]` PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_render_regression.py tests/fixtures/render_baselines/
git commit -m "test: add survey render image-regression baseline"
```

---

### Task 2: De-duplicate DXF file reads in parse_dxf

`parse_dxf` calls `ezdxf.readfile()` four times (in `_get_stations`, `_parse_polylines`, `_get_offset`, `_get_features`). Read once, pass the modelspace to each helper. Output is identical — covered by `tests/test_dxf_parser.py` and the Task 1 regression test.

**Files:**
- Modify: `cave_sketch/dxf/parser.py`
- Test: `tests/test_dxf_parser.py` (existing), `tests/test_render_regression.py` (Task 1)

**Interfaces:**
- Consumes: `ezdxf.readfile(...).modelspace()`.
- Produces: unchanged `parse_dxf(...) -> CaveSurvey` behaviour. Helper signatures change from `(input_dxf_file: str, ...)` to `(msp, ...)`.

- [ ] **Step 1: Confirm the existing safety net is green first**

Run: `uv run pytest tests/test_dxf_parser.py tests/test_render_regression.py -v`
Expected: all PASS (baseline established before refactor).

- [ ] **Step 2: Read the file once in `parse_dxf`**

In `cave_sketch/dxf/parser.py`, replace the body of `parse_dxf` that calls the helpers (currently lines ~21-27) with a single read:

```python
    input_str = str(input_path)

    doc = ezdxf.readfile(input_str)
    msp = doc.modelspace()

    stations = _get_stations(msp)
    all_polylines = _parse_polylines(msp, filter_layers=["SCRAP_0"])
    offset_x, offset_y = _get_offset(msp, offset_idx=0)
    blocks = _get_features(msp)
```

- [ ] **Step 3: Change the four helpers to accept `msp` instead of reading the file**

Update each helper signature and delete its `doc = ezdxf.readfile(...)` / `msp = doc.modelspace()` lines:

```python
def _get_stations(msp) -> Dict:
    idxs, coords, legs = [], [], []
    for entity in msp:
        # ... body unchanged ...
```

```python
def _parse_polylines(msp, filter_layers: Optional[List[str]] = None) -> List[Dict]:
    result = []
    for entity in msp.query("POLYLINE"):
        # ... body unchanged ...
```

```python
def _get_offset(msp, offset_idx: int) -> Tuple[float, float]:
    offset_flag = False
    for entity in msp:
        # ... body unchanged ...
```

```python
def _get_features(msp) -> List[Dict]:
    valid_block_names = {"B_ice", "BLOCK", "B_snow"}
    blocks: List[Dict] = []
    for entity in msp.query("INSERT"):
        # ... body unchanged ...
```

Leave every loop body, filter, and return value exactly as it was — only the file-read lines and the signature change.

- [ ] **Step 4: Run parser + regression tests**

Run: `uv run pytest tests/test_dxf_parser.py tests/test_render_regression.py -v`
Expected: all PASS (identical parse output → identical render).

- [ ] **Step 5: Type-check and lint**

Run: `uv run mypy cave_sketch/ && uv run ruff check .`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add cave_sketch/dxf/parser.py
git commit -m "perf(dxf): read DXF file once instead of four times in parse_dxf"
```

---

### Task 3: Eliminate the O(n²) neighbour lookup

In `extract_features_from_df`, every node currently triggers a full `df[df["Node_Id"] == nbr]` scan. Replace with a one-time coordinate index built so the **first** occurrence of a Node_Id wins (matching the current `.iloc[0]` semantics). Add a feature-equality unit test (the second safety-net tier) that locks the exact output.

**Files:**
- Modify: `cave_sketch/features/render_features.py` (function `extract_features_from_df`, lines ~59-111; the `A_` area block stays unchanged)
- Create: `tests/test_render_features.py`

**Interfaces:**
- Consumes: `cave_sketch.features.render_features.extract_features_from_df(df: pd.DataFrame, excluded_nodes: Optional[List[str]] = None) -> Dict[str, list]`.
- Produces: identical features dict — keys `"lines"`, `"polygons"`, `"points"`; each line dict has keys `coords`, `color`, `weight`, `dash`, `popup`.

- [ ] **Step 1: Write the feature-equality characterization test**

Create `tests/test_render_features.py`:

```python
import pandas as pd

from cave_sketch.features.render_features import extract_features_from_df


def _wall_df():
    # Node_Id and Links as strings, mirroring how renderer._survey_to_df builds the df.
    return pd.DataFrame(
        [
            ["A", "B", 0.0, 0.0, "L_wall"],
            ["B", "A-C", 1.0, 0.0, "L_wall"],
            ["C", "B", 2.0, 0.0, "L_wall"],
        ],
        columns=["Node_Id", "Links", "X", "Y", "Type"],
    )


def test_extract_features_lines_exact():
    features = extract_features_from_df(_wall_df())

    assert features["polygons"] == []
    assert features["points"] == []
    assert features["lines"] == [
        {"coords": [[0.0, 0.0], [0.0, 1.0]], "color": "red", "weight": 2, "dash": None, "popup": "L_wall (A-B)"},
        {"coords": [[0.0, 1.0], [0.0, 0.0]], "color": "red", "weight": 2, "dash": None, "popup": "L_wall (B-A)"},
        {"coords": [[0.0, 1.0], [0.0, 2.0]], "color": "red", "weight": 2, "dash": None, "popup": "L_wall (B-C)"},
        {"coords": [[0.0, 2.0], [0.0, 1.0]], "color": "red", "weight": 2, "dash": None, "popup": "L_wall (C-B)"},
    ]


def test_extract_features_excludes_nodes():
    # Excluding B removes every segment that references it.
    features = extract_features_from_df(_wall_df(), excluded_nodes=["B"])
    assert features["lines"] == []


def test_extract_features_skips_missing_neighbour():
    df = pd.DataFrame(
        [["A", "Z", 0.0, 0.0, "L_wall"]],  # Z does not exist
        columns=["Node_Id", "Links", "X", "Y", "Type"],
    )
    assert extract_features_from_df(df)["lines"] == []
```

- [ ] **Step 2: Run the test against current code to confirm it PASSES (locks behaviour)**

Run: `uv run pytest tests/test_render_features.py -v`
Expected: all three tests PASS on the current (un-refactored) implementation. This characterization test is the contract the refactor must preserve.

- [ ] **Step 3: Refactor the line-building loop to use a coordinate index**

In `cave_sketch/features/render_features.py`, replace the body of `extract_features_from_df` from the `if excluded_nodes is None:` line through the end of the line-handling loop (i.e. everything **before** the `# --- 2️⃣ Handle area features` block) with:

```python
    if excluded_nodes is None:
        excluded_nodes = []
    excluded = set(excluded_nodes)

    features: Dict[str, list] = {"lines": [], "polygons": [], "points": []}

    # One-time coordinate index for O(1) neighbour lookups (first occurrence wins,
    # matching the previous df[...].iloc[0] behaviour).
    coord_index: Dict[Any, tuple] = {}
    for row in df.itertuples(index=False):
        if row.Node_Id not in coord_index:
            coord_index[row.Node_Id] = (row.X, row.Y)

    # --- 1️⃣ Handle standard line features (walls, shots, etc.) ---
    for row in df.itertuples(index=False):
        nid, x, y, links, typ = row.Node_Id, row.X, row.Y, row.Links, row.Type

        if nid in excluded or typ.startswith("A_"):
            continue

        # --- standalone point features ---
        style_type = STYLE_MAP.get(typ, {}).get("type", "line")
        if style_type == "point":
            style = STYLE_MAP.get(typ, {"color": "black", "marker": "o", "markersize": 6})
            features["points"].append(
                {
                    "coords": [y, x],  # lat/lon-like
                    "color": style.get("color", "black"),
                    "marker": style.get("marker", "o"),
                    "size": style.get("markersize", 6),
                    "popup": f"{typ} ({nid})",
                }
            )
            continue

        # --- line logic ---
        if pd.notna(links) and links != "-":
            neighbors = [
                nbr.strip() for nbr in links.split("-") if nbr.strip() and nbr not in excluded
            ]
            for nbr in neighbors:
                if nbr not in coord_index:
                    continue
                x2, y2 = coord_index[nbr]

                if style_type == "line":
                    style = STYLE_MAP.get(typ, STYLE_MAP["L_wall"])
                    features["lines"].append(
                        {
                            "coords": [[y, x], [y2, x2]],
                            "color": style.get("color", "black"),
                            "weight": style.get("weight", 1),
                            "dash": None if style.get("linestyle", "solid") == "solid" else [3, 7],
                            "popup": f"{typ} ({nid}-{nbr})",
                        }
                    )
```

Add `Any` to the typing import at the top of the file (change `from typing import Any, Dict, List, Optional` — `Any` is likely already imported; confirm and add if missing). Leave the `# --- 2️⃣ Handle area features` block and the final `return features` unchanged.

- [ ] **Step 4: Run the feature test + image regression + full suite**

Run: `uv run pytest tests/test_render_features.py tests/test_render_regression.py -v`
Expected: all PASS (identical features → identical image).

- [ ] **Step 5: Type-check and lint**

Run: `uv run mypy cave_sketch/ && uv run ruff check .`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add cave_sketch/features/render_features.py tests/test_render_features.py
git commit -m "perf(render): replace O(n^2) neighbour scan with coordinate index"
```

- [ ] **Step 7 (manual, non-blocking): Measure on device**

On the Samsung Galaxy S22, regenerate a survey PDF and record the warm `draw_survey` time. Note it for the Task 4 / DEVLOG comparison. This step does not gate the commit.

---

### Task 4: Batch matplotlib artists and remove debug prints

Replace per-segment `ax.plot` with a single `LineCollection`, per-point `ax.scatter` with one `scatter` per marker, batch the station scatter, and delete the leftover `print()` calls. The Task 1 image-regression test is the correctness gate — if the viewport shifts, see the note in Step 5.

**Files:**
- Modify: `cave_sketch/backend_renders/matplotlib.py` (function `render_to_matplotlib`)
- Modify: `cave_sketch/survey/graphics/survey_plot.py` (station-drawing block, lines ~69-83)
- Test: `tests/test_render_regression.py`, `tests/test_survey_rendering.py`

**Interfaces:**
- Consumes: features dict from `extract_features_from_df` (lines: `coords`, `color`, `weight`, `dash`; points: `coords` `[y, x]`, `color`, `marker`, `size`); `config` with `line_width_zoom`, `ref_scale`, optional `show_labels`.
- Produces: unchanged `render_to_matplotlib(features, ax, layer_name="", config=None) -> None`.

- [ ] **Step 1: Confirm safety net is green before changes**

Run: `uv run pytest tests/test_render_regression.py tests/test_survey_rendering.py -v`
Expected: all PASS.

- [ ] **Step 2: Rewrite `render_to_matplotlib` with batched artists**

Replace the entire contents of `cave_sketch/backend_renders/matplotlib.py` with:

```python
from collections import defaultdict
from typing import Dict, Optional

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon as MplPolygon


def render_to_matplotlib(
    features: Dict[str, list], ax, layer_name: str = "", config: Optional[Dict] = None
):
    """
    Render extracted features onto a Matplotlib Axes with stable line scaling.

    Artists are batched (one LineCollection for all lines, one scatter per marker)
    to keep rendering fast on large surveys; output is identical to per-artist drawing.
    """
    if config is None:
        config = {}

    lz = config.get("line_width_zoom", 10)
    ref_scale = config.get("ref_scale", 1.0)
    zoom_factor = 10 ** (lz - 10)

    # ---- POLYGONS (few; drawn individually) ----
    for p in features.get("polygons", []):
        coords = np.array(p["coords"], dtype=float)
        xy = np.column_stack((coords[:, 1], coords[:, 0]))
        poly = MplPolygon(
            xy,
            closed=True,
            facecolor=p.get("fill_color", "blue"),
            edgecolor=p.get("edge_color", p.get("fill_color", "blue")),
            alpha=p.get("fill_opacity", 0.3),
            linewidth=0.5,
            zorder=p.get("zorder", 1),
        )
        ax.add_patch(poly)

    # ---- LINES (batched into one LineCollection) ----
    segments = []
    colors = []
    linewidths = []
    linestyles = []
    for line in features.get("lines", []):
        coords = np.array(line["coords"], dtype=float)
        xs = coords[:, 1]
        ys = coords[:, 0]

        base_weight = line.get("weight", 1)
        lw = base_weight * zoom_factor / ref_scale
        lw = float(np.clip(lw, 0.2, 4))

        dash = line.get("dash")
        linestyle = (0, tuple(dash)) if dash else "solid"

        segments.append(np.column_stack((xs, ys)))
        colors.append(line.get("color", "black"))
        linewidths.append(lw)
        linestyles.append(linestyle)

    if segments:
        lc = LineCollection(
            segments,
            colors=colors,
            linewidths=linewidths,
            linestyles=linestyles,
            alpha=0.9,
            zorder=2,
        )
        ax.add_collection(lc)

    # ---- POINTS (batched, one scatter per marker type) ----
    by_marker: Dict[str, Dict[str, list]] = defaultdict(
        lambda: {"x": [], "y": [], "s": [], "c": []}
    )
    for p in features.get("points", []):
        y, x = p["coords"]
        size_pts = p.get("size", 6)
        s_area = size_pts**2 * 0.5  # dampen to avoid huge circles
        marker = p.get("marker", "o")
        g = by_marker[marker]
        g["x"].append(x)
        g["y"].append(y)
        g["s"].append(s_area)
        g["c"].append(p.get("color", "black"))

    for marker, g in by_marker.items():
        ax.scatter(
            g["x"],
            g["y"],
            s=g["s"],
            c=g["c"],
            marker=marker,
            edgecolors="none",
            alpha=0.9,
            zorder=3,
        )

    # Optional text labels (rarely used; preserved for parity)
    if config.get("show_labels", False):
        for p in features.get("points", []):
            y, x = p["coords"]
            ax.text(
                x, y, p.get("popup", ""), fontsize=5, ha="left", va="bottom",
                color=p.get("color", "black"), zorder=4,
            )

    if layer_name:
        ax.set_title(layer_name, fontsize=10)

    ax.set_aspect("equal", "datalim")
```

- [ ] **Step 3: Batch the station scatter in `survey_plot.py`**

In `cave_sketch/survey/graphics/survey_plot.py`, replace the station block (the `if config.get("show_details", True):` loop, lines ~69-83) with:

```python
    # --- Stations (batched scatter; labels stay per-point) ---
    if config.get("show_details", True):
        offset = ref_scale * 0.005 if ref_scale > 0 else 0.1
        station_mask = (df["Type"] == "station") & (~df["Node_Id"].isin(excluded_nodes))
        stations = df[station_mask]
        if not stations.empty:
            ax.scatter(stations["X"], stations["Y"], s=marker_size, color="red", zorder=5)
            for _, row in stations.iterrows():
                ax.text(
                    row["X"] - offset,
                    row["Y"] + offset,
                    row["Node_Id"],
                    fontsize=text_size,
                    ha="right",
                    va="bottom",
                    color="black",
                    zorder=10,
                )
```

- [ ] **Step 4: Run the image-regression and rendering tests**

Run: `uv run pytest tests/test_render_regression.py tests/test_survey_rendering.py -v`
Expected: all PASS.

- [ ] **Step 5: If a regression scenario fails on viewport/limits**

`ax.plot` auto-updated the data limits; `LineCollection` relies on `add_collection`'s `autolim` (default `True`). If the image diff shows a shifted/clipped viewport (not a style change), add `ax.autoscale_view()` immediately after `ax.add_collection(lc)` and re-run Step 4. If the diff is purely sub-pixel and within `TOL`, no action is needed.

- [ ] **Step 6: Run the full suite, type-check, and lint**

Run: `uv run pytest && uv run mypy cave_sketch/ && uv run ruff check .`
Expected: all PASS, no errors.

- [ ] **Step 7: Commit**

```bash
git add cave_sketch/backend_renders/matplotlib.py cave_sketch/survey/graphics/survey_plot.py
git commit -m "perf(render): batch matplotlib artists and drop debug prints"
```

- [ ] **Step 8 (manual, non-blocking): Measure on device and record results**

On the Samsung Galaxy S22, regenerate a survey PDF and record the warm `draw_survey` time. Add a before/after entry (parse + render timings, referencing the ~60 s baseline from `docs/mobile-app/phases/phase-1-survey-plot/review.md`) to both `DEVLOG.md` (core change) and `android/DEVLOG.md` (device impact). Confirm the on-screen PDF still looks correct.

---

## Self-Review

**Spec coverage:**
- §5 Component 1 (safety net): Task 1 (image regression) + Task 3 Step 1-2 (feature equality). ✓
- §5 Component 2 (O(n²) fix): Task 3. ✓
- §5 Component 3 (batch artists + remove prints): Task 4. ✓
- §5 Component 4 (parser read-once): Task 2. ✓
- §6 sequencing (Component 1 → 4 → 2 → 3, measure between): Tasks ordered 1→2→3→4 with manual device measurement in Task 3 Step 7 and Task 4 Step 8. ✓
- §7 edge cases (empty/missing-neighbour/excluded/mixed markers): Task 3 tests cover excluded + missing neighbour; mixed markers handled by per-marker scatter in Task 4. ✓
- §8 verification gates (ruff, mypy, pytest, device measurement): present in Tasks 2-4. ✓

**Placeholder scan:** No TBD/TODO; every code step shows full code; "manual, non-blocking" device steps are explicitly out of the automated gate, not placeholders. ✓

**Type consistency:** `extract_features_from_df` signature and line-dict keys (`coords`/`color`/`weight`/`dash`/`popup`) consistent between Task 1 consumer, Task 3 producer, and Task 4 consumer. `render_to_matplotlib(features, ax, layer_name="", config=None)` unchanged. Helper signatures in Task 2 (`msp`-based) consistent with `parse_dxf` call site. ✓
