# Title Block Metadata & Adaptive Placement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Print optional Comune / Disegnatore / Coordinate / Quota slm / Declinazione rows in the PDF title block, enter them from webapp and Android (plus Android magnetic variation), and place the measured box in the best free spot on the page.

**Architecture:** A validated `TitleBlockInfo` dataclass travels from each app into the shared `draw_survey`. `title_block.py` turns it into text rows and draws the box; a new `title_block_layout.py` measures the rows and chooses the box rectangle (header slot → free in-plot corner → grown header) after the plots are drawn. Both apps reuse the same Python renderer (Android via Chaquopy symlink).

**Tech Stack:** Python 3 / matplotlib (3.10.3 desktop, 3.8.4 on Android — use only APIs present in 3.8), Streamlit 1.45.1, Kotlin + Jetpack Compose, pytest (`uv run pytest`), JUnit + Robolectric (`./gradlew testDebugUnitTest`).

**Spec:** `docs/superpowers/specs/2026-10-09-title-block-metadata-design.md`

## Global Constraints

- PDF labels are Italian, exactly: `Rilevatore`, `Disegnatore`, `Data`, `Comune`, `Coordinate`, `Quota slm`, `Declinazione`, `Sviluppo`, `Dislivello`.
- Row order: Rilevatore, Disegnatore, Data, Comune, Coordinate, Quota slm, Declinazione, Sviluppo, Dislivello. Optional rows appear only when set.
- Coordinates: 5 decimals, absolute values, `N`/`S` and `E`/`W` suffixes: `45.12345° N, 11.54321° E`.
- Elevation: rounded integer metres: `Quota slm: 1250 m`.
- Magnetic variation printed only when `!= 0`, 1 decimal, `E` positive / `W` negative: `Declinazione: 2.5° E`.
- Lat ∈ [-90, 90], lon ∈ [-180, 180], lat and lon both set or both empty.
- Free-text values longer than 30 chars truncated with `…`.
- Placement order: header slot → map-axes corners (top-right, top-left, bottom-right, bottom-left) → section-axes corners → grow header.
- Grid lines never block a corner.
- UI labels (web + Android) stay English. No DXF/KML/satellite changes.
- matplotlib APIs must exist in 3.8.4 (Android).

## Review Focus

1. **Zero values** — latitude `0.0`, longitude `0.0`, elevation `0` are real values and must print (no truthiness checks). Pinned in Task 2.
2. **Southern/western hemisphere & negative variation** — negative lat/lon/variation print as `S`/`W` with absolute values. Pinned in Task 2.
3. **Comma decimal separator on Android** (`45,123`) — accepted the same as a dot, as `GpsPointsEditor` already does. Pinned in Task 7.
4. **Long cave name + large box** — in grow-header mode the box must not overlap a 2-line cave name. Pinned in Task 3.
5. **Section-only survey** — magnetic variation is not applied to a section, so it must not be printed; placement works with a single axes. Pinned in Task 5.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `cave_sketch/survey/config.py` | Add `TitleBlockInfo` (validated metadata); remove `SurveyConfig.surveyor_name` |
| `cave_sketch/survey/graphics/title_block.py` | Row content (`build_title_rows`), cave name, box drawing, orchestration (`draw_title_block`) |
| `cave_sketch/survey/graphics/title_block_layout.py` (new) | Box measurement and placement (`measure_title_block`, `place_title_block`, `Placement`) |
| `cave_sketch/survey/graphics/grid.py` | Tag grid lines with `gid="grid"` so placement ignores them |
| `cave_sketch/survey/renderer.py` | Draw name → plots → title block |
| `cave_sketch/survey/survey.py` | `draw_survey(title_block=...)`, forward variation for display |
| `app/components/title_block_inputs.py` (new) | Streamlit inputs → `TitleBlockInfo` |
| `app/pages/1_survey_plot.py`, `app/session.py` | Wire component, session defaults |
| `android/app/src/main/python/survey_bridge.py` | JSON → `TitleBlockInfo`, forward variation |
| `android/.../ui/SurveyPlotViewModel.kt` | `SurveyInputs` fields, validation, JSON |
| `android/.../ui/components/TitleBlockFields.kt` (new) | Compose fields for title block |
| `android/.../ui/components/SettingsForm.kt` | Magnetic variation field |
| `android/.../ui/SurveyPlotScreen.kt` | Use `TitleBlockFields`, gate Generate on validation |

---

### Task 1: `TitleBlockInfo` model

**Files:**
- Modify: `cave_sketch/survey/config.py`
- Test: `tests/test_title_block_info.py` (create)

**Interfaces:**
- Produces: `cave_sketch.survey.config.TitleBlockInfo(surveyor_name: str = "", drawer_name: str = "", municipality: str = "", latitude: Optional[float] = None, longitude: Optional[float] = None, elevation_m: Optional[float] = None)`; raises `ValueError` on invalid coordinates; strips string fields.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_title_block_info.py
import math

import pytest

from cave_sketch.survey.config import TitleBlockInfo


def test_defaults_are_empty():
    info = TitleBlockInfo()
    assert info.surveyor_name == ""
    assert info.drawer_name == ""
    assert info.municipality == ""
    assert info.latitude is None
    assert info.longitude is None
    assert info.elevation_m is None


def test_strings_are_stripped():
    info = TitleBlockInfo(surveyor_name="  Alice ", drawer_name="   ", municipality=" Genga ")
    assert info.surveyor_name == "Alice"
    assert info.drawer_name == ""
    assert info.municipality == "Genga"


def test_valid_coordinates_including_zero():
    info = TitleBlockInfo(latitude=0.0, longitude=0.0)
    assert info.latitude == 0.0
    assert info.longitude == 0.0


@pytest.mark.parametrize("lat, lon", [(45.0, None), (None, 11.0)])
def test_lat_and_lon_must_be_entered_together(lat, lon):
    with pytest.raises(ValueError, match="together"):
        TitleBlockInfo(latitude=lat, longitude=lon)


@pytest.mark.parametrize("lat", [-90.0001, 90.0001, math.nan])
def test_latitude_out_of_range(lat):
    with pytest.raises(ValueError, match="Latitude"):
        TitleBlockInfo(latitude=lat, longitude=0.0)


@pytest.mark.parametrize("lon", [-180.0001, 180.0001, math.nan])
def test_longitude_out_of_range(lon):
    with pytest.raises(ValueError, match="Longitude"):
        TitleBlockInfo(latitude=0.0, longitude=lon)


def test_range_bounds_are_inclusive():
    TitleBlockInfo(latitude=-90.0, longitude=-180.0)
    TitleBlockInfo(latitude=90.0, longitude=180.0)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_title_block_info.py -v`
Expected: FAIL with `ImportError: cannot import name 'TitleBlockInfo'`

- [ ] **Step 3: Implement**

In `cave_sketch/survey/config.py`, change the import line to `from dataclasses import dataclass` + `from typing import Optional` and append:

```python
@dataclass
class TitleBlockInfo:
    """Optional survey metadata printed in the PDF title block (cartiglio).

    This is the validation boundary for both the webapp and the Android bridge.
    """

    surveyor_name: str = ""
    drawer_name: str = ""
    municipality: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None

    def __post_init__(self) -> None:
        self.surveyor_name = self.surveyor_name.strip()
        self.drawer_name = self.drawer_name.strip()
        self.municipality = self.municipality.strip()
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be entered together.")
        # `not a <= x <= b` is also True for NaN, so NaN is rejected too.
        if self.latitude is not None and not -90.0 <= self.latitude <= 90.0:
            raise ValueError("Latitude must be between -90 and 90.")
        if self.longitude is not None and not -180.0 <= self.longitude <= 180.0:
            raise ValueError("Longitude must be between -180 and 180.")
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_title_block_info.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/survey/config.py tests/test_title_block_info.py
git commit -m "feat(survey): add validated TitleBlockInfo model"
```

---

### Task 2: Title block rows

**Files:**
- Modify: `cave_sketch/survey/graphics/title_block.py` (add functions; existing `draw_title_block` untouched until Task 5)
- Test: `tests/test_title_block_rows.py` (create)

**Interfaces:**
- Consumes: `TitleBlockInfo` (Task 1)
- Produces: `build_title_rows(info: TitleBlockInfo, magnetic_variation_deg: float, total_length: float, total_depth: Optional[float], today: Optional[datetime.date] = None) -> list[str]`. `today=None` means `datetime.date.today()` resolved inside `title_block.py` (the regression test monkeypatches `cave_sketch.survey.graphics.title_block.datetime.date`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_title_block_rows.py
import datetime

from cave_sketch.survey.config import TitleBlockInfo
from cave_sketch.survey.graphics.title_block import build_title_rows

DAY = datetime.date(2026, 1, 2)


def test_required_rows_only():
    rows = build_title_rows(TitleBlockInfo(), 0.0, 154.34, None, today=DAY)
    assert rows == ["Rilevatore: -", "Data: 02/01/2026", "Sviluppo: 154.3 m"]


def test_all_rows_in_order():
    info = TitleBlockInfo(
        surveyor_name="Alice",
        drawer_name="Bob",
        municipality="Genga",
        latitude=43.40123456,
        longitude=12.96543219,
        elevation_m=1249.6,
    )
    rows = build_title_rows(info, 2.54, 154.3, 45.2, today=DAY)
    assert rows == [
        "Rilevatore: Alice",
        "Disegnatore: Bob",
        "Data: 02/01/2026",
        "Comune: Genga",
        "Coordinate: 43.40123° N, 12.96543° E",
        "Quota slm: 1250 m",
        "Declinazione: 2.5° E",
        "Sviluppo: 154.3 m",
        "Dislivello: 45.2 m",
    ]


def test_zero_values_are_printed():
    info = TitleBlockInfo(latitude=0.0, longitude=0.0, elevation_m=0.0)
    rows = build_title_rows(info, 0.0, 1.0, None, today=DAY)
    assert "Coordinate: 0.00000° N, 0.00000° E" in rows
    assert "Quota slm: 0 m" in rows


def test_southern_western_hemisphere_and_west_variation():
    info = TitleBlockInfo(latitude=-33.5, longitude=-70.25)
    rows = build_title_rows(info, -1.25, 1.0, None, today=DAY)
    assert "Coordinate: 33.50000° S, 70.25000° W" in rows
    assert "Declinazione: 1.2° W" in rows


def test_zero_variation_is_omitted():
    rows = build_title_rows(TitleBlockInfo(), 0.0, 1.0, None, today=DAY)
    assert not any(r.startswith("Declinazione") for r in rows)


def test_long_values_are_truncated_to_30_chars():
    long_name = "Comunità Montana dell'Alta Valle dell'Esino"
    rows = build_title_rows(TitleBlockInfo(municipality=long_name), 0.0, 1.0, None, today=DAY)
    value = next(r for r in rows if r.startswith("Comune: ")).removeprefix("Comune: ")
    assert len(value) == 30
    assert value.endswith("…")


def test_today_defaults_to_current_date():
    rows = build_title_rows(TitleBlockInfo(), 0.0, 1.0, None)
    assert rows[1] == f"Data: {datetime.date.today().strftime('%d/%m/%Y')}"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_title_block_rows.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_title_rows'`

- [ ] **Step 3: Implement**

In `cave_sketch/survey/graphics/title_block.py` add `from cave_sketch.survey.config import TitleBlockInfo` to the imports and add below `wrap_text`:

```python
MAX_VALUE_CHARS = 30


def _truncate(value: str) -> str:
    if len(value) <= MAX_VALUE_CHARS:
        return value
    return value[: MAX_VALUE_CHARS - 1].rstrip() + "…"


def _format_coordinates(latitude: float, longitude: float) -> str:
    ns = "N" if latitude >= 0 else "S"
    ew = "E" if longitude >= 0 else "W"
    return f"{abs(latitude):.5f}° {ns}, {abs(longitude):.5f}° {ew}"


def build_title_rows(
    info: TitleBlockInfo,
    magnetic_variation_deg: float,
    total_length: float,
    total_depth: Optional[float],
    today: Optional[datetime.date] = None,
) -> list[str]:
    """Return the title block text rows (Italian labels), omitting unset optional fields."""
    if today is None:
        today = datetime.date.today()

    rows = [f"Rilevatore: {_truncate(info.surveyor_name) or '-'}"]
    if info.drawer_name:
        rows.append(f"Disegnatore: {_truncate(info.drawer_name)}")
    rows.append(f"Data: {today.strftime('%d/%m/%Y')}")
    if info.municipality:
        rows.append(f"Comune: {_truncate(info.municipality)}")
    if info.latitude is not None and info.longitude is not None:
        rows.append(f"Coordinate: {_format_coordinates(info.latitude, info.longitude)}")
    if info.elevation_m is not None:
        rows.append(f"Quota slm: {round(info.elevation_m)} m")
    if magnetic_variation_deg != 0:
        direction = "E" if magnetic_variation_deg > 0 else "W"
        rows.append(f"Declinazione: {abs(magnetic_variation_deg):.1f}° {direction}")
    rows.append(f"Sviluppo: {total_length:.1f} m")
    if total_depth is not None:
        rows.append(f"Dislivello: {total_depth:.1f} m")
    return rows
```

Note: `abs(-1.25)` formatted `.1f` is `1.2` (banker's rounding of the binary value) — the test expects `1.2`.

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_title_block_rows.py tests/test_title_block.py -v`
Expected: all PASS (old title block tests still pass — nothing else changed)

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/survey/graphics/title_block.py tests/test_title_block_rows.py
git commit -m "feat(survey): build title block rows from TitleBlockInfo"
```

---

### Task 3: Measure the box; header slot and grow-header placement

**Files:**
- Create: `cave_sketch/survey/graphics/title_block_layout.py`
- Test: `tests/test_title_block_layout.py` (create)

**Interfaces:**
- Produces:
  - Constants `FONT_SIZE = 8.5`, `LINE_HEIGHT_IN`, `PAD_IN`, `MIN_WIDTH = 0.27`, `MIN_HEIGHT = 0.08`, `HEADER_RIGHT = 0.95`, `HEADER_TOP = 0.96`, `GAP = 0.01`.
  - `Rect = Tuple[float, float, float, float]` — `(x0, y0, width, height)` in figure fraction.
  - `@dataclass(frozen=True) class Placement: rect: Rect; strategy: str` — strategy is `"header"`, `"corner"` or `"grow-header"`.
  - `measure_title_block(fig: Figure, rows: List[str]) -> Tuple[float, float]` — `(width, height)` figure fraction.
  - `place_title_block(fig: Figure, size: Tuple[float, float], name_text: Text, plot_axes: List[Axes]) -> Placement` — may call `fig.subplots_adjust(top=...)` in grow-header mode. `plot_axes` order = corner preference (map first).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_title_block_layout.py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox

from cave_sketch.survey.graphics.title_block import wrap_text
from cave_sketch.survey.graphics.title_block_layout import (
    GAP,
    MIN_HEIGHT,
    MIN_WIDTH,
    measure_title_block,
    place_title_block,
)

FOUR_ROWS = ["Rilevatore: -", "Data: 01/01/2026", "Sviluppo: 10.0 m", "Dislivello: 5.0 m"]
NINE_ROWS = [
    "Rilevatore: Alice",
    "Disegnatore: Bob",
    "Data: 01/01/2026",
    "Comune: Genga",
    "Coordinate: 43.40123° N, 12.96543° E",
    "Quota slm: 1250 m",
    "Declinazione: 2.5° E",
    "Sviluppo: 154.3 m",
    "Dislivello: 45.2 m",
]


def _page(name="Grotta"):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.subplots_adjust(top=0.86)
    name_text = fig.text(0.05, 0.92, wrap_text(name, 35), fontsize=15, weight="bold",
                         va="center", ha="left")
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    return fig, name_text, ax


def _fill_axes(ax):
    """A filled patch covering the whole axes blocks every corner."""
    ax.add_patch(Rectangle((0, 0), 10, 10, facecolor="blue", alpha=0.3))


def _fig_bbox(fig, artist):
    renderer = fig.canvas.get_renderer()
    return artist.get_window_extent(renderer).transformed(fig.transFigure.inverted())


def test_measure_small_box_uses_minimum_size():
    fig, _, _ = _page()
    width, height = measure_title_block(fig, FOUR_ROWS)
    assert width == pytest.approx(MIN_WIDTH)
    assert height == pytest.approx(MIN_HEIGHT)
    plt.close(fig)


def test_measure_grows_with_rows_and_text_width():
    fig, _, _ = _page()
    _, h4 = measure_title_block(fig, FOUR_ROWS)
    w9, h9 = measure_title_block(fig, NINE_ROWS)
    w_wide, _ = measure_title_block(fig, ["X" * 80])
    assert h9 > h4
    assert w_wide > w9 >= MIN_WIDTH
    plt.close(fig)


def test_small_box_goes_to_header_slot():
    fig, name_text, ax = _page()
    _fill_axes(ax)
    placement = place_title_block(fig, measure_title_block(fig, FOUR_ROWS), name_text, [ax])
    assert placement.strategy == "header"
    x0, y0, w, h = placement.rect
    assert (x0, y0, w, h) == pytest.approx((0.68, 0.88, 0.27, 0.08))
    assert ax.get_position().y1 == pytest.approx(0.86)
    plt.close(fig)


def test_large_box_on_dense_data_grows_header():
    fig, name_text, ax = _page()
    _fill_axes(ax)
    placement = place_title_block(fig, measure_title_block(fig, NINE_ROWS), name_text, [ax])
    assert placement.strategy == "grow-header"
    _, y0, _, _ = placement.rect
    assert ax.get_position().y1 <= y0 - GAP + 1e-9
    plt.close(fig)


def test_grow_header_box_never_overlaps_long_cave_name():
    long_name = "Abisso di Frasassi con Sviluppo Eccezionale e Molto Lungo"
    fig, name_text, ax = _page(long_name)
    _fill_axes(ax)
    rows = NINE_ROWS + ["Comune: " + "W" * 30]
    placement = place_title_block(fig, measure_title_block(fig, rows), name_text, [ax])
    assert placement.strategy == "grow-header"
    box = Bbox.from_bounds(*placement.rect)
    assert not box.overlaps(_fig_bbox(fig, name_text))
    assert ax.get_position().y1 <= placement.rect[1]
    plt.close(fig)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_title_block_layout.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cave_sketch.survey.graphics.title_block_layout'`

- [ ] **Step 3: Implement**

```python
# cave_sketch/survey/graphics/title_block_layout.py
"""Measure the title block and choose where it goes on the page.

All rectangles are (x0, y0, width, height) in figure-fraction coordinates.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple

from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.transforms import Bbox

FONT_SIZE = 8.5
LINE_HEIGHT_IN = FONT_SIZE * 1.5 / 72
PAD_IN = 0.08
# Minimum size matches the historical fixed box, so small blocks look unchanged.
MIN_WIDTH = 0.27
MIN_HEIGHT = 0.08
HEADER_RIGHT = 0.95
HEADER_TOP = 0.96
GAP = 0.01

Rect = Tuple[float, float, float, float]


@dataclass(frozen=True)
class Placement:
    rect: Rect
    strategy: str  # "header" | "corner" | "grow-header"


def measure_title_block(fig: Figure, rows: List[str]) -> Tuple[float, float]:
    """Return the (width, height) in figure fraction needed to draw `rows`."""
    renderer = fig.canvas.get_renderer()
    widest_px = 0.0
    for row in rows:
        probe = fig.text(0, 0, row, fontsize=FONT_SIZE)
        widest_px = max(widest_px, probe.get_window_extent(renderer).width)
        probe.remove()
    fig_w_in, fig_h_in = fig.get_size_inches()
    width = (widest_px / fig.dpi + 2 * PAD_IN) / fig_w_in
    height = (len(rows) * LINE_HEIGHT_IN + 2 * PAD_IN) / fig_h_in
    return max(width, MIN_WIDTH), max(height, MIN_HEIGHT)


def place_title_block(
    fig: Figure, size: Tuple[float, float], name_text: Text, plot_axes: List[Axes]
) -> Placement:
    """Pick the box rectangle: header slot, else a free plot corner, else grow the header."""
    width, height = size
    fig.draw_without_rendering()  # applies aspect ratios so axes boxes are final
    renderer = fig.canvas.get_renderer()
    name_box = name_text.get_window_extent(renderer).transformed(fig.transFigure.inverted())

    header = _header_rect(width, height, HEADER_TOP)
    plots_top = max(ax.get_position().y1 for ax in plot_axes)
    if header[1] >= plots_top + GAP and not _overlaps(header, name_box):
        return Placement(header, "header")

    corner = _find_free_corner(fig, renderer, width, height, plot_axes)
    if corner is not None:
        return Placement(corner, "corner")

    return _grow_header(fig, width, height, name_box)


def _header_rect(width: float, height: float, top: float) -> Rect:
    return (HEADER_RIGHT - width, top - height, width, height)


def _overlaps(rect: Rect, bbox: Bbox) -> bool:
    return Bbox.from_bounds(*rect).overlaps(bbox)


def _find_free_corner(
    fig: Figure, renderer: RendererBase, width: float, height: float, plot_axes: List[Axes]
) -> Optional[Rect]:
    return None  # implemented in Task 4


def _grow_header(fig: Figure, width: float, height: float, name_box: Bbox) -> Placement:
    rect = _header_rect(width, height, HEADER_TOP)
    if _overlaps(rect, name_box):
        rect = _header_rect(width, height, name_box.y0 - GAP)
    fig.subplots_adjust(top=rect[1] - GAP)
    return Placement(rect, "grow-header")
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_title_block_layout.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/survey/graphics/title_block_layout.py tests/test_title_block_layout.py
git commit -m "feat(survey): measure title block and place it in header or grown header"
```

---

### Task 4: Free in-plot corner search

**Files:**
- Modify: `cave_sketch/survey/graphics/title_block_layout.py` (replace `_find_free_corner` stub)
- Modify: `cave_sketch/survey/graphics/grid.py:28,35` (add `gid="grid"`)
- Test: `tests/test_title_block_layout.py` (append)

**Interfaces:**
- Consumes: Task 3 module.
- Produces: `place_title_block` now returns `strategy="corner"` when a corner of a plot axes is free. Grid lines from `_add_grid` carry `gid="grid"`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_title_block_layout.py`)

```python
from matplotlib.patches import Circle

from cave_sketch.survey.graphics.grid import _add_grid


def _assert_inside_axes(fig, rect, ax):
    ax_box = ax.get_window_extent(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted()
    )
    x0, y0, w, h = rect
    assert ax_box.x0 <= x0 and x0 + w <= ax_box.x1
    assert ax_box.y0 <= y0 and y0 + h <= ax_box.y1


def test_large_box_goes_to_first_free_corner():
    fig, name_text, ax = _page()
    ax.plot([0, 10], [0, 10], color="black")  # blocks top-right and bottom-left
    placement = place_title_block(fig, measure_title_block(fig, NINE_ROWS), name_text, [ax])
    assert placement.strategy == "corner"
    x0, y0, w, h = placement.rect
    assert x0 < 0.5 and y0 > 0.5  # top-left
    _assert_inside_axes(fig, placement.rect, ax)
    plt.close(fig)


def test_patches_block_corners():
    fig, name_text, ax = _page()
    ax.plot([0, 10], [0, 10], color="black")
    ax.add_patch(Circle((1.5, 8.5), 1.0, fill=False))  # north-arrow-like ring, top-left
    placement = place_title_block(fig, measure_title_block(fig, NINE_ROWS), name_text, [ax])
    assert placement.strategy == "corner"
    x0, y0, _, _ = placement.rect
    assert x0 > 0.5 and y0 < 0.5  # bottom-right
    plt.close(fig)


def test_scatter_markers_block_corners():
    fig, name_text, ax = _page()
    ax.scatter([9.5], [9.5], s=20)  # single station in the top-right
    placement = place_title_block(fig, measure_title_block(fig, NINE_ROWS), name_text, [ax])
    assert placement.strategy == "corner"
    x0, y0, _, _ = placement.rect
    assert x0 < 0.5 and y0 > 0.5  # top-left
    plt.close(fig)


def test_grid_lines_do_not_block_corners():
    fig, name_text, ax = _page()
    _add_grid(ax, 0, 10, 0, 10, 1.0)
    placement = place_title_block(fig, measure_title_block(fig, NINE_ROWS), name_text, [ax])
    assert placement.strategy == "corner"
    x0, y0, _, _ = placement.rect
    assert x0 > 0.5 and y0 > 0.5  # top-right, first preference
    plt.close(fig)


def test_map_axes_preferred_over_section_axes():
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.subplots_adjust(top=0.86)
    name_text = fig.text(0.05, 0.92, "Grotta", fontsize=15)
    section_ax = fig.add_subplot(2, 1, 1)
    map_ax = fig.add_subplot(2, 1, 2)
    for ax in (section_ax, map_ax):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
    rows = NINE_ROWS[:7]
    placement = place_title_block(fig, measure_title_block(fig, rows), name_text, [map_ax, section_ax])
    assert placement.strategy == "corner"
    _assert_inside_axes(fig, placement.rect, map_ax)
    plt.close(fig)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_title_block_layout.py -v`
Expected: the five new tests FAIL (`strategy == "grow-header"`); Task 3 tests still PASS.

- [ ] **Step 3: Implement**

In `grid.py` change both line calls:

```python
        ax.axvline(x, color="lightgray", linestyle=":", zorder=0, gid="grid")
```
```python
        ax.axhline(y, color="lightgray", linestyle=":", zorder=0, gid="grid")
```

In `title_block_layout.py` add imports:

```python
import numpy as np
from matplotlib.artist import Artist
from matplotlib.axis import Axis
from matplotlib.collections import Collection, PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.spines import Spine
```

add constants:

```python
CORNER_INSET = 0.01
MARKER_MARGIN_PX = 4.0
```

and replace the `_find_free_corner` stub with:

```python
def _find_free_corner(
    fig: Figure, renderer: RendererBase, width: float, height: float, plot_axes: List[Axes]
) -> Optional[Rect]:
    for ax in plot_axes:
        ax_box = ax.get_window_extent(renderer).transformed(fig.transFigure.inverted())
        obstacles = [a for a in ax.get_children() if not _ignored(ax, a)]
        for rect in _corner_rects(ax_box, width, height):
            box_px = Bbox.from_bounds(*rect).transformed(fig.transFigure)
            if not any(_hits(a, box_px, renderer) for a in obstacles):
                return rect
    return None


def _corner_rects(ax_box: Bbox, width: float, height: float) -> List[Rect]:
    """Candidate rects in preference order: top-right, top-left, bottom-right, bottom-left."""
    x0, y0 = ax_box.x0 + CORNER_INSET, ax_box.y0 + CORNER_INSET
    x1, y1 = ax_box.x1 - CORNER_INSET, ax_box.y1 - CORNER_INSET
    if x1 - x0 < width or y1 - y0 < height:
        return []
    return [
        (x1 - width, y1 - height, width, height),
        (x0, y1 - height, width, height),
        (x1 - width, y0, width, height),
        (x0, y0, width, height),
    ]


def _ignored(ax: Axes, artist: Artist) -> bool:
    # Grid lines are covered by the box's opaque face, so they never block it.
    return (
        artist is ax.patch
        or isinstance(artist, (Spine, Axis))
        or not artist.get_visible()
        or artist.get_gid() == "grid"
    )


def _hits(artist: Artist, box_px: Bbox, renderer: RendererBase) -> bool:
    """Whether `artist` draws anything inside `box_px` (display coordinates)."""
    if isinstance(artist, Text):
        return bool(artist.get_text()) and artist.get_window_extent(renderer).overlaps(box_px)
    if isinstance(artist, Line2D):
        path = artist.get_transform().transform_path(artist.get_path())
        return path.intersects_bbox(box_px, filled=False)
    if isinstance(artist, Patch):
        path = artist.get_transform().transform_path(artist.get_path())
        return path.intersects_bbox(box_px, filled=artist.get_fill())
    if isinstance(artist, PathCollection):
        points = artist.get_offset_transform().transform(artist.get_offsets())
        if len(points) == 0:
            return False
        m = MARKER_MARGIN_PX
        x, y = points[:, 0], points[:, 1]
        inside = (x >= box_px.x0 - m) & (x <= box_px.x1 + m) & (y >= box_px.y0 - m) & (y <= box_px.y1 + m)
        return bool(np.any(inside))
    if isinstance(artist, Collection):
        transform = artist.get_transform()
        return any(
            transform.transform_path(p).intersects_bbox(box_px, filled=False)
            for p in artist.get_paths()
        )
    # Unknown artist type: be conservative and use its bounding box.
    return artist.get_window_extent(renderer).overlaps(box_px)
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_title_block_layout.py tests/test_grid.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add cave_sketch/survey/graphics/title_block_layout.py cave_sketch/survey/graphics/grid.py tests/test_title_block_layout.py
git commit -m "feat(survey): place title block in a free plot corner when header is too small"
```

---

### Task 5: Wire title block into rendering and `draw_survey`

**Files:**
- Modify: `cave_sketch/survey/graphics/title_block.py` (replace old `draw_title_block`)
- Modify: `cave_sketch/survey/renderer.py`
- Modify: `cave_sketch/survey/survey.py`
- Modify: `cave_sketch/survey/config.py` (remove `SurveyConfig.surveyor_name`)
- Modify: `tests/test_title_block.py`, `tests/test_title_block_integration.py`, `tests/test_render_regression.py`
- Regenerate: `tests/fixtures/render_baselines/{plan_only,dual}.png`; create `full_metadata.png`

**Interfaces:**
- Consumes: `build_title_rows` (Task 2), `measure_title_block`, `place_title_block`, `Placement`, `FONT_SIZE`, `LINE_HEIGHT_IN`, `PAD_IN` (Tasks 3–4).
- Produces:
  - `draw_cave_name(fig: Figure, cave_name: str) -> Text`
  - `draw_title_block(fig: Figure, name_text: Text, rows: List[str], plot_axes: List[Axes]) -> Placement`
  - `render_survey(..., title_block: Optional[TitleBlockInfo] = None, magnetic_variation_deg: float = 0.0) -> Figure`
  - `draw_survey(..., title_block: Optional[TitleBlockInfo] = None, magnetic_variation_deg: float = 0.0, ...)` — the `surveyor_name` kwarg is removed.

- [ ] **Step 1: Rewrite the title block unit tests (failing)**

Replace the four `test_draw_title_block_*` tests in `tests/test_title_block.py` (keep `test_wrap_text_logic`) and change the import:

```python
import matplotlib.pyplot as plt
import pytest

from cave_sketch.survey.graphics.title_block import draw_cave_name, draw_title_block

ROWS = ["Rilevatore: John Doe", "Data: 01/01/2026", "Sviluppo: 154.3 m", "Dislivello: 45.2 m"]


def _page():
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.subplots_adjust(top=0.86)
    ax = fig.add_subplot(1, 1, 1)
    return fig, ax


def test_draw_title_block_draws_rows_in_header():
    fig, ax = _page()
    name_text = draw_cave_name(fig, "Grotta del Vento")
    placement = draw_title_block(fig, name_text, ROWS, [ax])

    assert placement.strategy == "header"
    title_ax = fig.axes[-1]
    assert tuple(title_ax.get_position().bounds) == pytest.approx(placement.rect)
    assert [t.get_text() for t in title_ax.texts] == ROWS
    assert "Grotta del Vento" in [t.get_text() for t in fig.texts]
    plt.close(fig)


def test_rows_are_evenly_spaced_top_to_bottom():
    fig, ax = _page()
    draw_title_block(fig, draw_cave_name(fig, "G"), ROWS, [ax])
    ys = [t.get_position()[1] for t in fig.axes[-1].texts]
    steps = [a - b for a, b in zip(ys, ys[1:])]
    assert all(s > 0 for s in steps)
    assert max(steps) - min(steps) < 1e-9
    plt.close(fig)


def test_draw_cave_name_wraps_long_names():
    fig, _ = _page()
    text = draw_cave_name(fig, "Abisso di Frasassi con Sviluppo Eccezionale e Molto Lungo")
    assert text.get_text() == "Abisso di Frasassi con Sviluppo\nEccezionale e Molto Lungo"
    plt.close(fig)
```

In `tests/test_title_block_integration.py`, add `from cave_sketch.survey.config import TitleBlockInfo` and replace each `surveyor_name="<Name>",` with `title_block=TitleBlockInfo(surveyor_name="<Name>"),`:

```bash
sed -i '' -E 's/surveyor_name="([^"]*)",/title_block=TitleBlockInfo(surveyor_name="\1"),/' tests/test_title_block_integration.py
```

Append to the same file:

```python
def _write_csvs(tmp_path):
    map_csv = tmp_path / "map.csv"
    section_csv = tmp_path / "section.csv"
    pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 10.0], "Y": [0.0, 0.0],
        "Links": ["2", "1"], "Type": ["station", "station"],
    }).to_csv(map_csv, index=False)
    pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 10.0], "Y": [0.0, -5.0],
        "Links": ["-", "-"], "Type": ["station", "station"],
    }).to_csv(section_csv, index=False)
    return str(map_csv), str(section_csv)


def _title_texts(fig):
    return [t.get_text() for t in fig.axes[-1].texts]


def test_draw_survey_full_metadata_prints_all_rows(tmp_path):
    map_csv, section_csv = _write_csvs(tmp_path)
    fig = draw_survey(
        title="Full Cave",
        rule_length=10.0,
        csv_map_path=map_csv,
        csv_section_path=section_csv,
        magnetic_variation_deg=2.5,
        title_block=TitleBlockInfo(
            surveyor_name="Alice", drawer_name="Bob", municipality="Genga",
            latitude=43.4, longitude=12.9, elevation_m=320,
        ),
    )
    labels = [t.split(":")[0] for t in _title_texts(fig)]
    assert labels == [
        "Rilevatore", "Disegnatore", "Data", "Comune", "Coordinate",
        "Quota slm", "Declinazione", "Sviluppo", "Dislivello",
    ]


def test_section_only_survey_does_not_print_variation(tmp_path):
    _, section_csv = _write_csvs(tmp_path)
    fig = draw_survey(
        title="Section Only",
        rule_length=10.0,
        csv_section_path=section_csv,
        magnetic_variation_deg=2.5,
    )
    assert not any(t.startswith("Declinazione") for t in _title_texts(fig))
```

In `tests/test_render_regression.py` add `from cave_sketch.survey.config import TitleBlockInfo`, replace both `surveyor_name="Test Surveyor"` with `title_block=TitleBlockInfo(surveyor_name="Test Surveyor")`, change the parametrize list to `["plan_only", "dual", "full_metadata"]`, and turn the `else:  # dual` branch into:

```python
    elif scenario == "dual":
        fig = draw_survey(
            title="Sample Survey Dual",
            rule_length=20.0,
            csv_map_path=csv_path_str,
            csv_section_path=csv_path_str,
            title_block=TitleBlockInfo(surveyor_name="Test Surveyor"),
        )
    else:  # full_metadata
        fig = draw_survey(
            title="Sample Survey Full Metadata",
            rule_length=20.0,
            csv_map_path=csv_path_str,
            csv_section_path=csv_path_str,
            magnetic_variation_deg=2.5,
            title_block=TitleBlockInfo(
                surveyor_name="Test Surveyor",
                drawer_name="Test Drawer",
                municipality="Genga",
                latitude=43.40123,
                longitude=12.96543,
                elevation_m=320,
            ),
        )
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_title_block.py tests/test_title_block_integration.py -v`
Expected: FAIL — `ImportError: cannot import name 'draw_cave_name'` / `TypeError: draw_survey() got an unexpected keyword argument 'title_block'`

- [ ] **Step 3: Implement `title_block.py` drawing**

Replace the old `draw_title_block` function with the following, and extend the imports:

```python
from typing import List, Optional

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text

from cave_sketch.survey.config import TitleBlockInfo
from cave_sketch.survey.graphics.title_block_layout import (
    FONT_SIZE,
    LINE_HEIGHT_IN,
    PAD_IN,
    Placement,
    Rect,
    measure_title_block,
    place_title_block,
)
```

```python
def draw_cave_name(fig: Figure, cave_name: str) -> Text:
    """Draw the bold, left-aligned cave name in the header (wrapped to max 2 lines)."""
    return fig.text(
        0.05,
        0.92,
        wrap_text(cave_name, max_chars=35),
        fontsize=15,
        weight="bold",
        va="center",
        ha="left",
    )


def draw_title_block(
    fig: Figure, name_text: Text, rows: List[str], plot_axes: List[Axes]
) -> Placement:
    """Measure, place and draw the metadata box. Call after the plots are drawn."""
    placement = place_title_block(fig, measure_title_block(fig, rows), name_text, plot_axes)
    _draw_box(fig, rows, placement.rect)
    return placement


def _draw_box(fig: Figure, rows: List[str], rect: Rect) -> Axes:
    ax = fig.add_axes(rect)
    # Keep only the border spines; white face hides grid lines under the box.
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("white")

    fig_w_in, fig_h_in = fig.get_size_inches()
    line = LINE_HEIGHT_IN / (rect[3] * fig_h_in)
    x = PAD_IN / (rect[2] * fig_w_in)
    top = 0.5 + len(rows) * line / 2  # rows are centred vertically in the box
    for i, row in enumerate(rows):
        ax.text(x, top - (i + 0.5) * line, row, fontsize=FONT_SIZE, va="center", ha="left")
    return ax
```

- [ ] **Step 4: Implement `renderer.py`**

```python
from cave_sketch.survey.config import SurveyConfig, TitleBlockInfo
from cave_sketch.survey.graphics.title_block import (
    build_title_rows,
    draw_cave_name,
    draw_title_block,
)
```

Signature gains (after `total_depth`):

```python
    title_block: Optional[TitleBlockInfo] = None,
    magnetic_variation_deg: float = 0.0,
```

Document both in the docstring (`title_block: Metadata shown in the title block.`, `magnetic_variation_deg: Variation applied to the map, printed when non-zero.`). Body changes:

```python
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.subplots_adjust(top=0.86)
    name_text = draw_cave_name(fig, survey.name)
```

Store the section axes: in the section block, rename `ax` to `section_ax` (keep `section_ax = None` before the `if`); in the map block, rename `ax` to `map_ax`. Before `return fig` add:

```python
    # The plan view gets first pick of free corners for the title block.
    plot_axes = [map_ax] + ([section_ax] if section_ax is not None else [])
    rows = build_title_rows(
        title_block or TitleBlockInfo(), magnetic_variation_deg, total_length, total_depth
    )
    draw_title_block(fig, name_text, rows, plot_axes)
```

- [ ] **Step 5: Implement `survey.py` and `config.py`**

`config.py`: delete the `surveyor_name: str = ""` line from `SurveyConfig`.

`survey.py`: import `from cave_sketch.survey.config import SurveyConfig, TitleBlockInfo`; replace the `surveyor_name: str = "",` parameter with `title_block: Optional[TitleBlockInfo] = None,`; delete `surveyor_name=surveyor_name,` from the `SurveyConfig(...)` call; pass to `render_survey`:

```python
        title_block=title_block,
        # Variation only rotates the map; a section-only survey must not claim it.
        magnetic_variation_deg=magnetic_variation_deg if merged_map is not None else 0.0,
```

- [ ] **Step 6: Run the unit + integration tests**

Run: `uv run pytest tests/test_title_block.py tests/test_title_block_integration.py tests/test_title_block_rows.py tests/test_title_block_layout.py tests/test_grid.py tests/test_survey_rendering.py -v`
Expected: all PASS

- [ ] **Step 7: Regenerate render baselines and inspect them**

Run: `CAVE_SKETCH_GENERATE_BASELINES=1 uv run pytest tests/test_render_regression.py -v`
Expected: 3 SKIPPED ("Generated baseline …").

Open `tests/fixtures/render_baselines/plan_only.png`, `dual.png`, `full_metadata.png` (Read tool) and check: `plan_only`/`dual` box is top-right in the header as before; `full_metadata` box shows all 9 rows and does not overlap geometry, north arrow, scale rule or cave name. If anything overlaps, stop and fix the placement before continuing.

Run: `uv run pytest tests/test_render_regression.py -v`
Expected: 3 PASS

- [ ] **Step 8: Full suite**

Run: `uv run pytest -q`
Expected: all PASS. (`survey_bridge.py` still passes `surveyor_name`, but its tests mock `draw_survey`, so they stay green; the bridge is migrated in Task 7. Do not ship between Task 5 and Task 7.)

- [ ] **Step 9: Commit**

```bash
git add cave_sketch/survey tests/test_title_block.py tests/test_title_block_integration.py tests/test_render_regression.py tests/fixtures/render_baselines
git commit -m "feat(survey): render extended title block with adaptive placement"
```

---

### Task 6: Webapp inputs

**Files:**
- Create: `app/components/title_block_inputs.py`
- Modify: `app/pages/1_survey_plot.py:27-33,47,61`
- Modify: `app/session.py` (`AppState` + defaults)
- Test: `tests/test_title_block_inputs.py` (create)

**Interfaces:**
- Consumes: `TitleBlockInfo` (Task 1), `draw_survey(title_block=...)` (Task 5).
- Produces: `title_block_inputs_component() -> Optional[TitleBlockInfo]` — returns `None` after showing `st.error` when invalid. Session keys: `surveyor_name`, `drawer_name`, `municipality`, `cave_latitude`, `cave_longitude`, `cave_elevation_m`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_title_block_inputs.py
from unittest.mock import MagicMock, patch

from cave_sketch.survey.config import TitleBlockInfo


class MockSessionState:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _state():
    return MockSessionState(
        surveyor_name="", drawer_name="", municipality="",
        cave_latitude=None, cave_longitude=None, cave_elevation_m=None,
    )


def _setup(mock_st, texts, numbers):
    mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
    mock_st.session_state = _state()
    mock_st.text_input.side_effect = texts      # surveyor, drawer, municipality
    mock_st.number_input.side_effect = numbers  # lat, lon, elevation


@patch("app.components.title_block_inputs.st")
def test_returns_info_and_persists_session(mock_st):
    from app.components.title_block_inputs import title_block_inputs_component

    _setup(mock_st, ["Alice", "Bob", "Genga"], [43.4, 12.9, 320.0])
    info = title_block_inputs_component()

    assert info == TitleBlockInfo(
        surveyor_name="Alice", drawer_name="Bob", municipality="Genga",
        latitude=43.4, longitude=12.9, elevation_m=320.0,
    )
    assert mock_st.session_state.drawer_name == "Bob"
    assert mock_st.session_state.cave_latitude == 43.4
    assert mock_st.session_state.cave_elevation_m == 320.0
    mock_st.error.assert_not_called()


@patch("app.components.title_block_inputs.st")
def test_empty_optional_numbers_are_none(mock_st):
    from app.components.title_block_inputs import title_block_inputs_component

    _setup(mock_st, ["", "", ""], [None, None, None])
    assert title_block_inputs_component() == TitleBlockInfo()


@patch("app.components.title_block_inputs.st")
def test_latitude_without_longitude_shows_error(mock_st):
    from app.components.title_block_inputs import title_block_inputs_component

    _setup(mock_st, ["", "", ""], [43.4, None, None])
    assert title_block_inputs_component() is None
    mock_st.error.assert_called_once()
    assert "together" in mock_st.error.call_args[0][0]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_title_block_inputs.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.components.title_block_inputs'`

- [ ] **Step 3: Implement the component**

```python
# app/components/title_block_inputs.py
from typing import Optional

import streamlit as st

from cave_sketch.survey.config import TitleBlockInfo


def title_block_inputs_component() -> Optional[TitleBlockInfo]:
    """Inputs for the PDF title block. Returns None (after showing an error) when invalid."""
    st.markdown("#### 👤 Title block")
    col1, col2 = st.columns(2)
    with col1:
        surveyor_name = st.text_input("Surveyor name", value=st.session_state.surveyor_name)
    with col2:
        drawer_name = st.text_input("Drawer name", value=st.session_state.drawer_name)
    municipality = st.text_input("Municipality", value=st.session_state.municipality)

    lat_col, lon_col, elev_col = st.columns(3)
    with lat_col:
        latitude = st.number_input(
            "Latitude (°)", min_value=-90.0, max_value=90.0, step=0.00001, format="%.5f",
            value=st.session_state.cave_latitude, placeholder="optional",
        )
    with lon_col:
        longitude = st.number_input(
            "Longitude (°)", min_value=-180.0, max_value=180.0, step=0.00001, format="%.5f",
            value=st.session_state.cave_longitude, placeholder="optional",
        )
    with elev_col:
        elevation_m = st.number_input(
            "Elevation (m a.s.l.)", step=1.0, format="%.0f",
            value=st.session_state.cave_elevation_m, placeholder="optional",
        )

    st.session_state.surveyor_name = surveyor_name
    st.session_state.drawer_name = drawer_name
    st.session_state.municipality = municipality
    st.session_state.cave_latitude = latitude
    st.session_state.cave_longitude = longitude
    st.session_state.cave_elevation_m = elevation_m

    try:
        return TitleBlockInfo(
            surveyor_name=surveyor_name,
            drawer_name=drawer_name,
            municipality=municipality,
            latitude=latitude,
            longitude=longitude,
            elevation_m=elevation_m,
        )
    except ValueError as e:
        st.error(f"⚠️ {e}")
        return None
```

- [ ] **Step 4: Wire the page and session**

`app/session.py` — add to `AppState`:

```python
    surveyor_name: str
    drawer_name: str
    municipality: str
    cave_latitude: Optional[float]
    cave_longitude: Optional[float]
    cave_elevation_m: Optional[float]
```

and to `defaults` after `"surveyor_name": "",`:

```python
        "drawer_name": "",
        "municipality": "",
        "cave_latitude": None,
        "cave_longitude": None,
        "cave_elevation_m": None,
```

`app/pages/1_survey_plot.py` — add `from components.title_block_inputs import title_block_inputs_component`; replace the "Surveyor name" block (lines 27-33) with:

```python
title_block = title_block_inputs_component()
```

change the button's first branches to:

```python
    if not merge_valid:
        st.error("⚠️ Please resolve the merging errors before generating the plot.")
    elif title_block is None:
        st.error("⚠️ Please fix the title block fields before generating the plot.")
    elif st.session_state.map_csv or st.session_state.section_csv:
```

and replace `surveyor_name=surveyor_name,` in the `draw_survey(...)` call with `title_block=title_block,`.

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_title_block_inputs.py tests/test_settings_panel.py -v`
Expected: all PASS

- [ ] **Step 6: Manual check**

Run: `uv run streamlit run app/main.py` (if the entry differs, use the command in `README.md`). Upload `tests/fixtures/sample.dxf`, fill all title block fields + magnetic variation 2.5, generate, and confirm the preview shows all rows and no overlap. Enter only Latitude → error shown, Generate blocked.

- [ ] **Step 7: Commit**

```bash
git add app/components/title_block_inputs.py app/pages/1_survey_plot.py app/session.py tests/test_title_block_inputs.py
git commit -m "feat(app): add title block metadata inputs to survey plot page"
```

---

### Task 7: Android bridge + `SurveyInputs` model

**Files:**
- Modify: `android/app/src/main/python/survey_bridge.py`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt:18-19`
- Test: `tests/test_survey_bridge.py` (append), `android/app/src/test/java/com/cavesketch/app/SurveyPlotViewModelTest.kt` (append)

**Interfaces:**
- Consumes: `TitleBlockInfo`, `draw_survey(title_block=..., magnetic_variation_deg=...)`.
- Produces:
  - Bridge JSON input keys: `surveyor_name`, `drawer_name`, `municipality`, `latitude`, `longitude`, `elevation_m` (number or `null`), `settings.magnetic_variation_deg` (number). Invalid title block → `{"error": "invalid_title_block", "detail": <message>}`.
  - Kotlin: `fun parseDecimalOrNull(value: String): Double?` (package `com.cavesketch.app.ui`); `SurveyInputs` new `String` fields `drawerName`, `municipality`, `latitude`, `longitude`, `elevationM`, `magneticVariationDeg` (all default `""`); member `fun titleBlockError(): String?` on `SurveyInputs`.

- [ ] **Step 1: Write failing bridge tests** (append to `tests/test_survey_bridge.py`)

```python
def _generate_with(two_csvs, extra, settings=None):
    import json
    from unittest.mock import patch

    map_csv, _, work_dir = two_csvs
    inputs = {"map_path": map_csv, "survey_name": "T", "settings": settings or {}, **extra}
    with patch.object(survey_bridge, "draw_survey") as mock_draw:
        out = json.loads(survey_bridge.generate_survey_plot(json.dumps(inputs), str(work_dir)))
    return out, mock_draw


def test_generate_passes_title_block_and_variation(two_csvs):
    from cave_sketch.survey.config import TitleBlockInfo

    _, mock_draw = _generate_with(
        two_csvs,
        {"surveyor_name": "Alice", "drawer_name": "Bob", "municipality": "Genga",
         "latitude": 43.4, "longitude": 12.9, "elevation_m": 320},
        settings={"magnetic_variation_deg": 2.5},
    )
    _, kwargs = mock_draw.call_args
    assert kwargs["title_block"] == TitleBlockInfo(
        surveyor_name="Alice", drawer_name="Bob", municipality="Genga",
        latitude=43.4, longitude=12.9, elevation_m=320.0,
    )
    assert kwargs["magnetic_variation_deg"] == 2.5


def test_generate_defaults_when_fields_missing_or_null(two_csvs):
    from cave_sketch.survey.config import TitleBlockInfo

    _, mock_draw = _generate_with(two_csvs, {"latitude": None, "longitude": None, "elevation_m": None})
    _, kwargs = mock_draw.call_args
    assert kwargs["title_block"] == TitleBlockInfo()
    assert kwargs["magnetic_variation_deg"] == 0.0


def test_generate_rejects_invalid_title_block(two_csvs):
    out, mock_draw = _generate_with(two_csvs, {"latitude": 43.4, "longitude": None})
    assert out["error"] == "invalid_title_block"
    assert "together" in out["detail"]
    mock_draw.assert_not_called()
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_survey_bridge.py -v`
Expected: the three new tests FAIL (`KeyError: 'title_block'` / no `invalid_title_block` error).

- [ ] **Step 3: Implement the bridge**

In `survey_bridge.py` add `from cave_sketch.survey.config import TitleBlockInfo` and a helper near the top-level helpers:

```python
def _optional_float(value) -> Optional[float]:
    return None if value is None or value == "" else float(value)
```

Inside `generate_survey_plot`, before `pdf_path = ...`:

```python
        try:
            title_block = TitleBlockInfo(
                surveyor_name=data.get("surveyor_name") or "",
                drawer_name=data.get("drawer_name") or "",
                municipality=data.get("municipality") or "",
                latitude=_optional_float(data.get("latitude")),
                longitude=_optional_float(data.get("longitude")),
                elevation_m=_optional_float(data.get("elevation_m")),
            )
        except ValueError as e:
            return json.dumps({"error": "invalid_title_block", "detail": str(e)})
```

In the `draw_survey(...)` call replace `surveyor_name=data.get("surveyor_name", ""),` with:

```python
            title_block=title_block,
            magnetic_variation_deg=float(settings.get("magnetic_variation_deg", 0.0)),
```

Update the `inputs_json` shape described in the module docstring/Interfaces comment with the new keys.

- [ ] **Step 4: Run bridge tests**

Run: `uv run pytest tests/test_survey_bridge.py -v && uv run pytest -q`
Expected: all PASS (full suite green now)

- [ ] **Step 5: Write failing Kotlin tests** (append inside `SurveyPlotViewModelTest`)

```kotlin
    @Test
    fun toJson_includes_title_block_fields_and_variation() {
        val json = org.json.JSONObject(
            SurveyInputs(
                surveyorName = "Alice", drawerName = "Bob", municipality = "Genga",
                latitude = "43,4", longitude = "12.9", elevationM = "320",
                magneticVariationDeg = "-1,5",
            ).toJson()
        )
        assertEquals("Bob", json.getString("drawer_name"))
        assertEquals("Genga", json.getString("municipality"))
        assertEquals(43.4, json.getDouble("latitude"), 1e-9)
        assertEquals(12.9, json.getDouble("longitude"), 1e-9)
        assertEquals(320.0, json.getDouble("elevation_m"), 1e-9)
        assertEquals(-1.5, json.getJSONObject("settings").getDouble("magnetic_variation_deg"), 1e-9)
    }

    @Test
    fun toJson_emits_null_for_empty_numbers_and_zero_variation() {
        val json = org.json.JSONObject(SurveyInputs().toJson())
        assertTrue(json.isNull("latitude"))
        assertTrue(json.isNull("longitude"))
        assertTrue(json.isNull("elevation_m"))
        assertEquals(0.0, json.getJSONObject("settings").getDouble("magnetic_variation_deg"), 0.0)
    }

    @Test
    fun titleBlockError_validates_inputs() {
        assertEquals(null, SurveyInputs().titleBlockError())
        assertEquals(null, SurveyInputs(latitude = "-90", longitude = "180").titleBlockError())
        assertEquals(null, SurveyInputs(latitude = "0", longitude = "0", elevationM = "0").titleBlockError())
        assertTrue(SurveyInputs(latitude = "45").titleBlockError()!!.contains("both"))
        assertTrue(SurveyInputs(latitude = "91", longitude = "0").titleBlockError()!!.contains("Latitude"))
        assertTrue(SurveyInputs(latitude = "0", longitude = "-181").titleBlockError()!!.contains("Longitude"))
        assertTrue(SurveyInputs(latitude = "abc", longitude = "0").titleBlockError()!!.contains("Latitude"))
        assertTrue(SurveyInputs(elevationM = "high").titleBlockError()!!.contains("Elevation"))
        assertTrue(SurveyInputs(magneticVariationDeg = "200").titleBlockError()!!.contains("Magnetic"))
    }
```

- [ ] **Step 6: Run to verify failure**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.SurveyPlotViewModelTest"`
Expected: compilation FAIL (`No parameter with name 'drawerName'`).

- [ ] **Step 7: Implement Kotlin model**

In `SurveyPlotViewModel.kt` add, above `data class SurveyInputs`:

```kotlin
/** Parses a user-typed decimal, accepting a comma as the decimal separator. */
fun parseDecimalOrNull(value: String): Double? = value.trim().replace(",", ".").toDoubleOrNull()
```

Add to `SurveyInputs` after `surveyorName`:

```kotlin
    val drawerName: String = "",
    val municipality: String = "",
    val latitude: String = "",
    val longitude: String = "",
    val elevationM: String = "",
```

and after `showCenterline`:

```kotlin
    val magneticVariationDeg: String = "",
```

Inside `SurveyInputs`, add:

```kotlin
    /** First validation error for title block / variation inputs, or null. Mirrors TitleBlockInfo (Python). */
    fun titleBlockError(): String? {
        if (latitude.isBlank() != longitude.isBlank()) return "Enter both latitude and longitude, or neither."
        if (latitude.isNotBlank()) {
            val lat = parseDecimalOrNull(latitude)
            if (lat == null || lat !in -90.0..90.0) return "Latitude must be a number between -90 and 90."
            val lon = parseDecimalOrNull(longitude)
            if (lon == null || lon !in -180.0..180.0) return "Longitude must be a number between -180 and 180."
        }
        if (elevationM.isNotBlank() && parseDecimalOrNull(elevationM) == null) return "Elevation must be a number."
        if (magneticVariationDeg.isNotBlank()) {
            val mv = parseDecimalOrNull(magneticVariationDeg)
            if (mv == null || mv !in -180.0..180.0) return "Magnetic variation must be a number between -180 and 180."
        }
        return null
    }
```

In `toJson()` add to `settings`:

```kotlin
            .put("magnetic_variation_deg", parseDecimalOrNull(magneticVariationDeg) ?: 0.0)
```

and to the outer object after `surveyor_name`:

```kotlin
            .put("drawer_name", drawerName)
            .put("municipality", municipality)
            .put("latitude", parseDecimalOrNull(latitude) ?: JSONObject.NULL)
            .put("longitude", parseDecimalOrNull(longitude) ?: JSONObject.NULL)
            .put("elevation_m", parseDecimalOrNull(elevationM) ?: JSONObject.NULL)
```

In `GpsPointsEditor.kt` reuse the parser (add `import com.cavesketch.app.ui.parseDecimalOrNull`):

```kotlin
fun parsesAsCoordinate(value: String): Boolean = parseDecimalOrNull(value) != null
```

- [ ] **Step 8: Run Kotlin tests**

Run: `cd android && ./gradlew testDebugUnitTest`
Expected: BUILD SUCCESSFUL, all tests pass.

- [ ] **Step 9: Commit**

```bash
git add android/app/src/main/python/survey_bridge.py tests/test_survey_bridge.py android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt android/app/src/test/java/com/cavesketch/app/SurveyPlotViewModelTest.kt
git commit -m "feat(android): send title block metadata and magnetic variation to the bridge"
```

---

### Task 8: Android UI fields

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/TitleBlockFields.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt:54,94-100`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/SettingsForm.kt`
- Test: `android/app/src/test/java/com/cavesketch/app/ui/components/TitleBlockFieldsTest.kt` (create), `SettingsFormTest.kt` (append)

**Interfaces:**
- Consumes: `SurveyInputs` fields + `titleBlockError()` (Task 7).
- Produces: `@Composable fun TitleBlockFields(inputs: SurveyInputs, onChange: (SurveyInputs) -> Unit)`; test tags `drawer_field`, `municipality_field`, `latitude_field`, `longitude_field`, `elevation_field`, `title_block_error`, `magnetic_variation_field`.

- [ ] **Step 1: Write failing UI tests**

```kotlin
// android/app/src/test/java/com/cavesketch/app/ui/components/TitleBlockFieldsTest.kt
package com.cavesketch.app.ui.components

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTextInput
import com.cavesketch.app.ui.SurveyInputs
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class TitleBlockFieldsTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun typing_updates_inputs() {
        var latest = SurveyInputs()
        composeTestRule.setContent { TitleBlockFields(latest) { latest = it } }
        composeTestRule.onNodeWithTag("drawer_field").performTextInput("Bob")
        assertEquals("Bob", latest.drawerName)
        composeTestRule.onNodeWithTag("latitude_field").performTextInput("43,4")
        assertEquals("43,4", latest.latitude)
    }

    @Test
    fun shows_error_when_only_latitude_entered() {
        composeTestRule.setContent { TitleBlockFields(SurveyInputs(latitude = "43.4")) {} }
        composeTestRule.onNodeWithTag("title_block_error").assertExists()
    }

    @Test
    fun no_error_for_valid_inputs() {
        composeTestRule.setContent {
            TitleBlockFields(SurveyInputs(latitude = "43.4", longitude = "12.9")) {}
        }
        composeTestRule.onNodeWithTag("title_block_error").assertDoesNotExist()
    }
}
```

Append to `SettingsFormTest`:

```kotlin
    @Test
    fun typing_magnetic_variation_updates_inputs() {
        var latest = SurveyInputs()
        composeTestRule.setContent { SettingsForm(latest) { latest = it } }
        composeTestRule.onNodeWithTag("magnetic_variation_field")
            .performTextInput("2.5")
        assertEquals("2.5", latest.magneticVariationDeg)
    }
```

(add `import androidx.compose.ui.test.performTextInput` to `SettingsFormTest.kt`).

- [ ] **Step 2: Run to verify failure**

Run: `cd android && ./gradlew testDebugUnitTest --tests "*TitleBlockFieldsTest" --tests "*SettingsFormTest"`
Expected: compilation FAIL (`Unresolved reference: TitleBlockFields`).

- [ ] **Step 3: Implement `TitleBlockFields.kt`**

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.SurveyInputs

/** Optional metadata printed in the PDF title block. */
@Composable
fun TitleBlockFields(inputs: SurveyInputs, onChange: (SurveyInputs) -> Unit) {
    val decimal = KeyboardOptions(keyboardType = KeyboardType.Decimal)
    val error = inputs.titleBlockError()
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(
            value = inputs.surveyorName,
            onValueChange = { onChange(inputs.copy(surveyorName = it)) },
            label = { Text("Surveyor name") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = inputs.drawerName,
            onValueChange = { onChange(inputs.copy(drawerName = it)) },
            label = { Text("Drawer name") },
            modifier = Modifier.fillMaxWidth().testTag("drawer_field"),
        )
        OutlinedTextField(
            value = inputs.municipality,
            onValueChange = { onChange(inputs.copy(municipality = it)) },
            label = { Text("Municipality") },
            modifier = Modifier.fillMaxWidth().testTag("municipality_field"),
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = inputs.latitude,
                onValueChange = { onChange(inputs.copy(latitude = it)) },
                label = { Text("Latitude (°)") },
                keyboardOptions = decimal,
                modifier = Modifier.weight(1f).testTag("latitude_field"),
            )
            OutlinedTextField(
                value = inputs.longitude,
                onValueChange = { onChange(inputs.copy(longitude = it)) },
                label = { Text("Longitude (°)") },
                keyboardOptions = decimal,
                modifier = Modifier.weight(1f).testTag("longitude_field"),
            )
        }
        OutlinedTextField(
            value = inputs.elevationM,
            onValueChange = { onChange(inputs.copy(elevationM = it)) },
            label = { Text("Elevation (m a.s.l.)") },
            keyboardOptions = decimal,
            modifier = Modifier.fillMaxWidth().testTag("elevation_field"),
        )
        if (error != null) {
            Text(
                error,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.testTag("title_block_error"),
            )
        }
    }
}
```

Note: one error line under the fields (no per-field `isError`) keeps the message and field state from drifting apart. It also reports magnetic variation errors, since Generate is gated on the same function; SettingsForm additionally marks its own field with `isError`.

- [ ] **Step 4: Magnetic variation in `SettingsForm.kt`**

Add imports `androidx.compose.foundation.text.KeyboardOptions`, `androidx.compose.material3.OutlinedTextField`, `androidx.compose.ui.text.input.KeyboardType`, `com.cavesketch.app.ui.parseDecimalOrNull`; after the "Map rotation (°)" `StepperControl` add:

```kotlin
    OutlinedTextField(
        value = inputs.magneticVariationDeg,
        onValueChange = { onChange(inputs.copy(magneticVariationDeg = it)) },
        label = { Text("Magnetic variation (°, +E/-W)") },
        placeholder = { Text("0") },
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        isError = inputs.magneticVariationDeg.isNotBlank() &&
            parseDecimalOrNull(inputs.magneticVariationDeg)?.let { it in -180.0..180.0 } != true,
        modifier = Modifier.fillMaxWidth().testTag("magnetic_variation_field"),
    )
```

- [ ] **Step 5: Use it in `SurveyPlotScreen.kt`**

Replace the surveyor `OutlinedTextField` in the "Survey details" card with:

```kotlin
                TitleBlockFields(inputs) { inputs = it }
```

(import `com.cavesketch.app.ui.components.TitleBlockFields`), and change line 54 to:

```kotlin
    val canGenerate = (inputs.mapPath != null || inputs.sectionPath != null) &&
        inputs.titleBlockError() == null
```

- [ ] **Step 6: Run tests and build**

Run: `cd android && ./gradlew testDebugUnitTest assembleDebug`
Expected: BUILD SUCCESSFUL, all tests pass.

- [ ] **Step 7: Manual check on emulator/device**

Install the debug APK, open Survey Plot, pick a map, fill all title block fields with comma decimals and magnetic variation `2,5`, generate: the PDF preview shows every row and the map is rotated as on the webapp for the same file and variation. Enter only latitude: error text shown, Generate disabled.

- [ ] **Step 8: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui android/app/src/test/java/com/cavesketch/app/ui/components
git commit -m "feat(android): add title block fields and magnetic variation input"
```

---

### Task 9: Docs and DEVLOG

**Files:**
- Modify: `android/app/src/main/assets/guide/guide_en.md:13`, `android/app/src/main/assets/guide/guide_it.md` (matching line)
- Modify: `docs/android/README.md`, `docs/android/README.it.md` (where "surveyor" is mentioned)
- Modify: `DEVLOG.md`, `android/DEVLOG.md`

- [ ] **Step 1: Update the guides**

In `guide_en.md` replace `- **Survey name** and **surveyor**` with:

```markdown
- **Survey name**, **surveyor**, and the optional title block fields: **drawer**, **municipality**, **latitude/longitude** (decimal degrees, both or neither) and **elevation** (m a.s.l.). Only filled-in fields are printed.
- **Magnetic variation** (in Settings, +E/−W): rotates the map to true north and is printed in the title block when not 0.
```

Make the equivalent Italian change in `guide_it.md` (Disegnatore, Comune, Latitudine/Longitudine, Quota slm, Declinazione magnetica). Apply the same wording where `docs/android/README.md` / `README.it.md` mention the surveyor field.

- [ ] **Step 2: DEVLOG entries**

Add a `## [2026-10-09 HH:MM] Title Block Metadata — Implementation` entry to `DEVLOG.md` and `android/DEVLOG.md` following the existing format (`**Files:**`, `**Deviations from spec:**`, `**Assumptions:**`, `**Next session notes:**`). Record: baselines regenerated (and why), `surveyor_name` kwarg removed from `draw_survey`, placement strategy order.

- [ ] **Step 3: Final verification**

Run: `uv run pytest -q && (cd android && ./gradlew testDebugUnitTest)`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add android/app/src/main/assets/guide docs/android DEVLOG.md android/DEVLOG.md
git commit -m "docs: document title block metadata fields and Android magnetic variation"
```
