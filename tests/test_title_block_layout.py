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
