# Magnetic Variation (Declination) Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a survey creator enter a signed magnetic variation (declination) once on the Survey Plot page; map coordinates get rotated to a true-north reference and the same correction automatically carries over to the Satellite Map page's georeferencing, with zero behavior change when the value is left at `0`.

**Architecture:** A new pure function `apply_magnetic_variation()` rotates a map DataFrame's `X`/`Y` columns about its own centroid, reusing the existing `rotate_points()` helper. It is called once inside `draw_survey()` (on the post-merge map only, never the section) and once inside `draw_map()` (before the existing manual rotation, which is left untouched and composes on top). The webapp's Survey Plot page collects the value and stores it in `st.session_state`; the Satellite Map page reads it automatically.

**Tech Stack:** Python 3.11+, pandas, numpy, matplotlib, Streamlit, pytest, ruff, mypy (`uv run` for all commands).

**Spec:** `docs/superpowers/specs/2026-09-30-magnetic-variation-design.md`

## Global Constraints

- Default `magnetic_variation_deg = 0.0` on every touched function must be a **no-op**: output byte-identical to omitting the argument entirely.
- Sign convention: **positive = East declination, negative = West** (true bearing = magnetic bearing + variation). This requires rotating coordinates by **`-variation_deg`** in `rotate_points()`'s CCW-positive (`mode="cartesian"`) convention — verified worked example: `variation_deg=+10`, point `(0, 10)` relative to a centroid of `(0, 0)` → `(1.7364817766693033, 9.848077530122081)`.
- The correction applies to the **map/plan view only** — the section/profile view is never touched.
- `cave_sketch/geo/georef.py` (`georeference()` / `GpsRef`) is dead code (only its own test imports it) — do not touch it.
- `cave_sketch/geo/declination.py` must have no Streamlit import and be fully type-annotated.
- `uv run ruff check .`, `uv run mypy cave_sketch/`, and `uv run pytest` must all pass after every task.
- Test fixtures must use non-purely-numeric `Node_Id`/`Links` values (e.g. `"st1"`, `"st2"`), matching existing test fixtures in this repo — pandas infers a numeric dtype for columns that are all digit-strings, which breaks string operations (`.split("-")`) elsewhere in the pipeline. This is a pre-existing repo-wide convention, not something to fix here.
- Android (Kotlin) code is out of scope for this plan — see the spec's "Handoff to Android story" section.

## Review Focus

- Omitted or `0.0` `magnetic_variation_deg` must reproduce byte-identical output from both `draw_survey()` and `draw_map()` — a silent regression here would corrupt every existing survey. Pinned in Task 1 (no-op test), Task 2, and Task 3.
- The East/West sign could be silently reversed, producing a plausible-looking but mirrored-wrong correction with no error. Pinned by Task 1's exact worked-example assertions for both signs.
- The correction could leak into the section/profile subplot, which has no compass-north meaning, silently distorting depth data. Pinned by Task 2's map-vs-section test.
- On the Satellite Map page, the new correction and the existing manual "Map rotation angle" could apply in the wrong order or one could silently clobber the other. Pinned by Task 3's call-order test.
- The Satellite Map page could crash with `AttributeError` if a user opens it before ever visiting the Survey Plot page (so `st.session_state.magnetic_variation_deg` was never initialized). Pinned by Task 4's session default and Task 5's read path.

---

## Task 1: Shared magnetic-variation correction utility

**Files:**
- Create: `cave_sketch/geo/declination.py`
- Test: `tests/test_declination.py`

**Interfaces:**
- Produces: `apply_magnetic_variation(df: pd.DataFrame, variation_deg: float) -> pd.DataFrame` — returns a new DataFrame with `X`/`Y` columns rotated; a no-op copy when `variation_deg == 0`. Consumed by Task 2 and Task 3.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_declination.py
import numpy as np
import pandas as pd
import pytest

from cave_sketch.geo.declination import apply_magnetic_variation


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "Links": ["st2", "st1"],
        "X": [0.0, 0.0],
        "Y": [-10.0, 10.0],
        "Type": ["station", "station"],
    })


def test_zero_variation_is_a_noop_copy():
    df = _sample_df()
    result = apply_magnetic_variation(df, 0.0)

    assert result is not df
    pd.testing.assert_series_equal(result["X"], df["X"])
    pd.testing.assert_series_equal(result["Y"], df["Y"])


def test_east_variation_rotates_clockwise():
    """Worked example from the design spec: +10 deg East declination rotates
    a point on the local +Y axis, (0, 10), to approximately (1.736, 9.848)."""
    result = apply_magnetic_variation(_sample_df(), 10.0)
    row = result[result["Node_Id"] == "st2"].iloc[0]

    assert row["X"] == pytest.approx(1.7364817766693033, abs=1e-6)
    assert row["Y"] == pytest.approx(9.848077530122081, abs=1e-6)


def test_west_variation_rotates_counterclockwise():
    """-10 deg West mirrors the East case across the X axis."""
    result = apply_magnetic_variation(_sample_df(), -10.0)
    row = result[result["Node_Id"] == "st2"].iloc[0]

    assert row["X"] == pytest.approx(-1.7364817766693033, abs=1e-6)
    assert row["Y"] == pytest.approx(9.848077530122081, abs=1e-6)


def test_round_trip_restores_original_coordinates():
    df = _sample_df()
    rotated = apply_magnetic_variation(df, 7.5)
    restored = apply_magnetic_variation(rotated, -7.5)

    np.testing.assert_allclose(restored["X"].to_numpy(), df["X"].to_numpy(), atol=1e-9)
    np.testing.assert_allclose(restored["Y"].to_numpy(), df["Y"].to_numpy(), atol=1e-9)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_declination.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cave_sketch.geo.declination'`

- [ ] **Step 3: Write the implementation**

```python
# cave_sketch/geo/declination.py
import pandas as pd

from cave_sketch.features.geometry import rotate_points


def apply_magnetic_variation(df: pd.DataFrame, variation_deg: float) -> pd.DataFrame:
    """Rotate map X/Y coordinates from a magnetic-north to a true-north reference.

    Positive `variation_deg` is East declination, negative is West (true
    bearing = magnetic bearing + variation). A station recorded on the
    magnetic-north axis must end up at its true azimuth, which is a
    clockwise turn of `variation_deg` — hence the negation before calling
    the CCW-positive `rotate_points`.
    """
    df = df.copy()
    if variation_deg == 0:
        return df

    center = (float(df["X"].mean()), float(df["Y"].mean()))
    df[["X", "Y"]] = rotate_points(df[["X", "Y"]].values, center, -variation_deg)
    return df
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_declination.py -v`
Expected: 4 passed

- [ ] **Step 5: Lint and type-check**

Run: `uv run ruff check cave_sketch/geo/declination.py tests/test_declination.py && uv run mypy cave_sketch/geo/declination.py`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add cave_sketch/geo/declination.py tests/test_declination.py
git commit -m "feat(geo): add apply_magnetic_variation coordinate correction"
```

---

## Task 2: Wire the correction into `draw_survey()` (Survey Plot backend)

**Files:**
- Modify: `cave_sketch/survey/survey.py:1-100` (import + signature + merge block)
- Test: `tests/test_survey_declination.py`

**Interfaces:**
- Consumes: `apply_magnetic_variation(df, variation_deg)` from Task 1.
- Produces: `draw_survey(..., magnetic_variation_deg: float = 0.0, ...)` — new keyword argument, default `0.0`. Existing callers (webapp, Android bridge) are unaffected since they never pass it.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_survey_declination.py
import numpy as np
import pandas as pd
import pytest

from cave_sketch.survey import draw_survey


@pytest.fixture
def map_csv(tmp_path):
    df = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "Links": ["st2", "st1"],
        "X": [0.0, 0.0],
        "Y": [-10.0, 10.0],
        "Type": ["station", "station"],
    })
    path = tmp_path / "map.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def section_csv(tmp_path):
    df = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "Links": ["st2", "st1"],
        "X": [0.0, 20.0],
        "Y": [0.0, -5.0],
        "Type": ["station", "station"],
    })
    path = tmp_path / "section.csv"
    df.to_csv(path, index=False)
    return path


def _map_view_axes(fig):
    """Filter out the title-block axes, same convention as test_survey_rendering.py."""
    return [ax for ax in fig.get_axes() if ax.get_position().y0 < 0.8]


def test_default_variation_matches_omitted_kwarg(map_csv, tmp_path):
    fig_default = draw_survey(
        title="A", rule_length=20, csv_map_path=str(map_csv),
        output_path=str(tmp_path / "a.pdf"),
    )
    fig_explicit_zero = draw_survey(
        title="A", rule_length=20, csv_map_path=str(map_csv),
        magnetic_variation_deg=0.0, output_path=str(tmp_path / "b.pdf"),
    )

    offsets_default = sorted(_map_view_axes(fig_default)[0].collections[-1].get_offsets().tolist())
    offsets_zero = sorted(_map_view_axes(fig_explicit_zero)[0].collections[-1].get_offsets().tolist())

    np.testing.assert_allclose(offsets_default, offsets_zero)
    np.testing.assert_allclose(offsets_default, sorted([[0.0, -10.0], [0.0, 10.0]]))


def test_variation_rotates_map_but_not_section(map_csv, section_csv, tmp_path):
    fig = draw_survey(
        title="A", rule_length=20,
        csv_map_path=str(map_csv), csv_section_path=str(section_csv),
        magnetic_variation_deg=10.0,
        output_path=str(tmp_path / "c.pdf"),
    )
    axes = _map_view_axes(fig)
    assert len(axes) == 2
    section_ax, map_ax = axes

    section_offsets = sorted(section_ax.collections[-1].get_offsets().tolist())
    np.testing.assert_allclose(section_offsets, sorted([[0.0, 0.0], [20.0, -5.0]]))

    map_offsets = sorted(map_ax.collections[-1].get_offsets().tolist())
    expected = sorted([
        [-1.7364817766693033, -9.848077530122081],
        [1.7364817766693033, 9.848077530122081],
    ])
    np.testing.assert_allclose(map_offsets, expected, atol=1e-6)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_survey_declination.py -v`
Expected: FAIL with `TypeError: draw_survey() got an unexpected keyword argument 'magnetic_variation_deg'`

- [ ] **Step 3: Modify `cave_sketch/survey/survey.py`**

Add the import in alphabetical order (ruff's `I` isort rule), between the
`cave_sketch.dxf.models` import and the `cave_sketch.survey.config` import:

```python
from cave_sketch.dxf.models import CaveSurvey, SurveyPoint
from cave_sketch.geo.declination import apply_magnetic_variation
from cave_sketch.survey.config import SurveyConfig
```

Add `magnetic_variation_deg: float = 0.0,` to `draw_survey()`'s signature, right after `surveyor_name: str = "",` and before `config: Dict = {},`.

Insert the correction right after the merge/no-merge branch resolves `merged_map`, before the "Compute metrics after merge" comment:

```python
    if (child_map is not None or child_section is not None) and parent_station and child_station:
        merged_map, merged_section = merge_surveys(
            parent_map=parent_map,
            parent_section=parent_section,
            child_map=child_map,
            child_section=child_section,
            parent_station=parent_station,
            child_station=child_station,
            section_protocol=section_protocol
        )
    else:
        merged_map, merged_section = parent_map, parent_section

    if merged_map is not None:
        merged_map = apply_magnetic_variation(merged_map, magnetic_variation_deg)

    # Compute metrics after merge
    total_length = compute_total_length(merged_map)
    total_depth = compute_total_depth(merged_section)
```

`merged_section` is never passed to `apply_magnetic_variation` — the section/profile view keeps its original coordinates.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_survey_declination.py -v`
Expected: 2 passed

- [ ] **Step 5: Run the full existing survey test suite (regression check)**

Run: `uv run pytest tests/test_survey_rendering.py tests/test_survey_plot.py tests/test_survey_plot_placement.py tests/test_survey_bridge.py tests/test_survey_metrics.py tests/test_survey_section_scale_bar.py -v`
Expected: all pass, unchanged from before this task

- [ ] **Step 6: Lint and type-check**

Run: `uv run ruff check cave_sketch/survey/survey.py tests/test_survey_declination.py && uv run mypy cave_sketch/survey/survey.py`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add cave_sketch/survey/survey.py tests/test_survey_declination.py
git commit -m "feat(survey): apply magnetic variation correction in draw_survey"
```

---

## Task 3: Wire the correction into `draw_map()` (Satellite Map backend)

**Files:**
- Modify: `cave_sketch/satellite_view/map.py:1-40`
- Test: `tests/test_map_declination.py`

**Interfaces:**
- Consumes: `apply_magnetic_variation(df, variation_deg)` from Task 1.
- Produces: `draw_map(..., magnetic_variation_deg: float = 0.0, ...)` — new keyword argument, default `0.0`. Existing callers (webapp, Android bridge) are unaffected since they never pass it.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_map_declination.py
import json
import math
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from cave_sketch.satellite_view.map import _meters_per_degree_wgs84, draw_map


@pytest.fixture
def map_csv(tmp_path):
    df = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "Links": ["st2", "st1"],
        "X": [0.0, 0.0],
        "Y": [-10.0, 10.0],
        "Type": ["station", "station"],
    })
    path = tmp_path / "map.csv"
    df.to_csv(path, index=False)
    return path


def test_zero_variation_matches_omitted_kwarg(map_csv, tmp_path):
    gps_points = [{"station": "st1", "lat": 45.0, "lon": 10.0}]

    _, json_default, _ = draw_map(
        map_path=str(map_csv), gps_points=gps_points,
        output_path=str(tmp_path / "a.html"),
    )
    _, json_zero, _ = draw_map(
        map_path=str(map_csv), gps_points=gps_points,
        output_path=str(tmp_path / "b.html"), magnetic_variation_deg=0.0,
    )

    data_default = json.loads(Path(json_default).read_text())
    data_zero = json.loads(Path(json_zero).read_text())
    assert data_default["nodes"]["st2"] == data_zero["nodes"]["st2"]


def test_variation_rotates_georeferenced_output(map_csv, tmp_path):
    gps_points = [{"station": "st1", "lat": 45.0, "lon": 10.0}]

    _, json_path, _ = draw_map(
        map_path=str(map_csv), gps_points=gps_points,
        output_path=str(tmp_path / "out.html"), magnetic_variation_deg=10.0,
    )
    data = json.loads(Path(json_path).read_text())

    # The delta between st2 and the anchor st1, (0, 20), rotates by -10 deg
    # (East declination) regardless of the rotation pivot (a rigid rotation
    # preserves point-to-point deltas up to the rotation angle itself).
    theta = math.radians(-10.0)
    dx = math.cos(theta) * 0.0 - math.sin(theta) * 20.0
    dy = math.sin(theta) * 0.0 + math.cos(theta) * 20.0
    m_per_deg_lat, m_per_deg_lon = _meters_per_degree_wgs84(45.0)
    expected_lat = 45.0 + dy / m_per_deg_lat
    expected_lon = 10.0 + dx / m_per_deg_lon

    assert data["nodes"]["st2"]["lat"] == pytest.approx(expected_lat, abs=1e-9)
    assert data["nodes"]["st2"]["lon"] == pytest.approx(expected_lon, abs=1e-9)


@patch("cave_sketch.satellite_view.map.apply_magnetic_variation")
def test_variation_applied_before_manual_rotation(mock_apply, map_csv, tmp_path):
    """The declination correction must run on the raw CSV data, before the
    existing manual `rotation_angle` block — so the two compose instead of
    one silently overriding the other."""
    mock_apply.side_effect = lambda df, variation_deg: df
    gps_points = [{"station": "st1", "lat": 45.0, "lon": 10.0}]

    draw_map(
        map_path=str(map_csv), gps_points=gps_points,
        output_path=str(tmp_path / "out.html"),
        magnetic_variation_deg=12.5, rotation_angle=0,
    )

    mock_apply.assert_called_once()
    called_df, called_variation = mock_apply.call_args.args
    assert called_variation == 12.5
    assert called_df["X"].tolist() == [0.0, 0.0]
    assert called_df["Y"].tolist() == [-10.0, 10.0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_map_declination.py -v`
Expected: FAIL — `TypeError: draw_map() got an unexpected keyword argument 'magnetic_variation_deg'` (first two tests), and an `AttributeError`/`ModuleNotFoundError`-style failure on the patch target for the third (no `apply_magnetic_variation` name in `cave_sketch.satellite_view.map` yet)

- [ ] **Step 3: Modify `cave_sketch/satellite_view/map.py`**

Add the import in alphabetical order (ruff's `I` isort rule), after the
`cave_sketch.features.render_features` import (the last import in that block):

```python
from cave_sketch.backend_renders import render_to_folium, render_to_kmz
from cave_sketch.features.geometry import rotate_points
from cave_sketch.features.render_features import extract_features_from_json
from cave_sketch.geo.declination import apply_magnetic_variation
```

Add `magnetic_variation_deg: float = 0.0,` to `draw_map()`'s signature, right after `rotation_angle: float = 0,`.

Apply the correction immediately after reading the CSV, before the existing manual-rotation block:

```python
    # Load and process the main map data
    map_df = pd.read_csv(map_path)
    map_df = apply_magnetic_variation(map_df, magnetic_variation_deg)
    if rotation_angle != 0:
        mask = map_df["Node_Id"] == "13"
        center_x = map_df[mask]["X"].mean()
        center_y = map_df[mask]["Y"].mean()
        center = (float(center_x), float(center_y))
        map_df[["X", "Y"]] = rotate_points(map_df[["X", "Y"]].values, center, rotation_angle)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_map_declination.py -v`
Expected: 3 passed

- [ ] **Step 5: Run the full existing satellite test suite (regression check)**

Run: `uv run pytest tests/test_satellite_map.py tests/test_satellite_bridge.py -v`
Expected: all pass, unchanged from before this task

- [ ] **Step 6: Lint and type-check**

Run: `uv run ruff check cave_sketch/satellite_view/map.py tests/test_map_declination.py && uv run mypy cave_sketch/satellite_view/map.py`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add cave_sketch/satellite_view/map.py tests/test_map_declination.py
git commit -m "feat(satellite): apply magnetic variation correction in draw_map"
```

---

## Task 4: Survey Plot page — magnetic variation input

**Files:**
- Modify: `app/components/settings_panel.py:1-52`
- Modify: `app/session.py:11-27` (AppState) and `:37-61` (defaults)
- Modify: `app/pages/1_survey_plot.py:49-62` (draw_survey call)
- Modify: `tests/test_settings_panel.py`

**Interfaces:**
- Consumes: nothing new from earlier tasks directly (feeds `draw_survey`'s `magnetic_variation_deg` kwarg from Task 2 via the page).
- Produces: `st.session_state.magnetic_variation_deg: float` (default `0.0`), read by Task 5. `settings_panel_component()`'s returned dict gains a `"magnetic_variation_deg"` key.

- [ ] **Step 1: Update the failing tests**

Modify both test functions in `tests/test_settings_panel.py` to account for the new `number_input` call (inserted right after "Map rotation" and before the checkboxes) and to assert the new returned key. In each test, change:

```python
    mock_st.number_input.side_effect = [100, 0, 0.0, 0.0, 0.0]
```

to:

```python
    mock_st.number_input.side_effect = [100, 0, 0.0, 0.0, 0.0, 0.0]
```

and add, at the end of each test function:

```python
    assert res["magnetic_variation_deg"] == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_settings_panel.py -v`
Expected: FAIL with `KeyError: 'magnetic_variation_deg'`

- [ ] **Step 3: Modify `app/components/settings_panel.py`**

Insert a new `number_input` right after the existing `rotation_deg` one, and persist it to session state the same way `show_centerline`/`show_details`/`show_grid` already are:

```python
        rotation_deg = st.number_input(
            "🧭 Map rotation (°)", min_value=-180, max_value=180, step=1, value=0
        )
        magnetic_variation_deg = st.number_input(
            "🧭 Magnetic variation (°, +E/-W)",
            min_value=-180.0,
            max_value=180.0,
            step=0.1,
            value=st.session_state.get("magnetic_variation_deg", 0.0),
        )
        st.session_state.magnetic_variation_deg = magnetic_variation_deg
        show_centerline = st.checkbox(
```

Add `"magnetic_variation_deg": magnetic_variation_deg,` to the dict returned at the end of `settings_panel_component()`.

- [ ] **Step 4: Modify `app/session.py`**

Add to the `AppState` TypedDict, next to `rotation_angle: float`:

```python
    magnetic_variation_deg: float
```

Add to the `defaults` dict in `init_session()`, next to `"rotation_angle": 0.0,`:

```python
        "magnetic_variation_deg": 0.0,
```

- [ ] **Step 5: Modify `app/pages/1_survey_plot.py`**

In the `draw_survey(...)` call inside the `st.button("✨ Generate Survey Plot")` handler, add the new kwarg by popping it out of `settings` (same pattern already used for `rule_length`):

```python
            fig = draw_survey(
                title=title,
                rule_length=settings.pop("rule_length"),
                magnetic_variation_deg=settings.pop("magnetic_variation_deg", 0.0),
                csv_map_path=st.session_state.map_csv,
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_settings_panel.py -v`
Expected: 2 passed

- [ ] **Step 7: Lint and type-check**

Run: `uv run ruff check app/ tests/test_settings_panel.py && uv run mypy cave_sketch/`
Expected: no errors

- [ ] **Step 8: Commit**

```bash
git add app/components/settings_panel.py app/session.py app/pages/1_survey_plot.py tests/test_settings_panel.py
git commit -m "feat(webapp): add magnetic variation input to Survey Plot settings"
```

---

## Task 5: Satellite Map page — auto-apply the survey's magnetic variation

**Files:**
- Modify: `app/pages/2_satellite_map.py:1-45`

**Interfaces:**
- Consumes: `st.session_state.magnetic_variation_deg: float` (from Task 4) and `draw_map(..., magnetic_variation_deg: float = 0.0, ...)` (from Task 3).

There is no existing precedent in this repo for unit-testing a numbered Streamlit page module directly (they are not valid Python import names, and existing tests for satellite behavior — `tests/test_satellite_map.py` — test the underlying library calls, already covered by Task 3). This task is verified manually against the running app instead.

- [ ] **Step 1: Modify `app/pages/2_satellite_map.py`**

Read the survey-level variation and pass it into `draw_map(...)`, and surface it to the user when non-zero:

```python
rotation_angle = st.number_input("🧭 Map rotation angle (°)", value=st.session_state.rotation_angle)
st.session_state.rotation_angle = rotation_angle

magnetic_variation_deg = st.session_state.magnetic_variation_deg
if magnetic_variation_deg:
    st.caption(
        f"🧭 Magnetic variation correction: {magnetic_variation_deg:+g}° "
        "applied automatically from Survey Plot"
    )
```

And in the `draw_map(...)` call inside the "Generate HTML Map" button handler, add:

```python
        html_map, json_path, kmz_path = draw_map(
            map_path=str(st.session_state.merged_map_csv or st.session_state.map_csv),
            gps_points=st.session_state.known_points,
            output_path=str(html_path),
            map_name="Current Cave",
            additional_json_maps=st.session_state.uploaded_json_paths,
            rotation_angle=rotation_angle,
            magnetic_variation_deg=magnetic_variation_deg,
        )
```

- [ ] **Step 2: Run the full automated suite (regression check)**

Run: `uv run pytest`
Expected: all tests pass

- [ ] **Step 3: Lint and type-check**

Run: `uv run ruff check app/pages/2_satellite_map.py && uv run mypy cave_sketch/`
Expected: no errors

- [ ] **Step 4: Manual verification**

Run: `uv run streamlit run app/app.py`

1. On the **Cave Survey Plot** page, upload `tests/fixtures/test_survey.csv` as the map file, set "🧭 Magnetic variation (°, +E/-W)" to `10`, click "✨ Generate Survey Plot". Confirm the plotted stations visibly rotate compared to leaving the field at `0`, while the north arrow stays fixed pointing straight up.
2. Navigate to the **Satellite Map** page without changing anything. Confirm the caption `🧭 Magnetic variation correction: +10° applied automatically from Survey Plot` is shown above/near the "Map rotation angle" field.
3. Fill in a station/lat/lon GPS point matching a station from the uploaded CSV, click "🌍 Generate HTML Map". Confirm it renders without error.
4. Go back to Survey Plot, reset "Magnetic variation" to `0`, regenerate, return to Satellite Map: confirm the caption disappears and the map regenerates without error.
5. Restart the app fresh (clear session) and open the **Satellite Map** page first, before ever visiting Survey Plot. Confirm no `AttributeError` is raised (the page loads normally, with the field defaulting to `0`).

- [ ] **Step 5: Commit**

```bash
git add app/pages/2_satellite_map.py
git commit -m "feat(webapp): auto-apply survey magnetic variation on Satellite Map page"
```

---

## Self-Review Notes

- **Spec coverage:** FR-1 → Task 1. FR-2 → Task 2. FR-3 → Task 3. FR-4 → Task 4. FR-5 → Task 5. Non-functional requirements (type annotations, no Streamlit import in the geo module, lint/type/test gates, backward compatibility) are enforced in every task's steps. The "Handoff to Android story" and "Out of Scope" sections require no implementation task — they are carried forward unchanged into the spec, which travels with this plan.
- **Type consistency:** `apply_magnetic_variation(df: pd.DataFrame, variation_deg: float) -> pd.DataFrame` (Task 1) is called identically in Task 2 and Task 3. `magnetic_variation_deg` is the key name used consistently across `draw_survey`, `draw_map`, the settings dict, and `st.session_state` — matching the exact key the spec's Android handoff section names for the follow-up story.
- **Review Focus:** all five items map to an owning task's test, listed above.
