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
