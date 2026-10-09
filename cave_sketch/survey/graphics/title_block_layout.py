"""Measure the title block and choose where it goes on the page.

All rectangles are (x0, y0, width, height) in figure-fraction coordinates.
"""
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.backend_bases import RendererBase
from matplotlib.collections import Collection, PathCollection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.spines import Spine
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
CORNER_INSET = 0.01
MARKER_MARGIN_PX = 4.0

Rect = Tuple[float, float, float, float]


@dataclass(frozen=True)
class Placement:
    rect: Rect
    strategy: str  # "header" | "corner" | "grow-header"


def _get_renderer(fig: Figure) -> RendererBase:
    canvas: Any = fig.canvas
    return canvas.get_renderer()


def measure_title_block(fig: Figure, rows: List[str]) -> Tuple[float, float]:
    """Return the (width, height) in figure fraction needed to draw `rows`."""
    renderer = _get_renderer(fig)
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
    renderer = _get_renderer(fig)

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
        in_x = (x >= box_px.x0 - m) & (x <= box_px.x1 + m)
        in_y = (y >= box_px.y0 - m) & (y <= box_px.y1 + m)
        return bool(np.any(in_x & in_y))
    if isinstance(artist, Collection):
        transform = artist.get_transform()
        return any(
            transform.transform_path(p).intersects_bbox(box_px, filled=False)
            for p in artist.get_paths()
        )
    # Unknown artist type: be conservative and use its bounding box.
    return artist.get_window_extent(renderer).overlaps(box_px)


def _grow_header(fig: Figure, width: float, height: float, name_box: Bbox) -> Placement:
    rect = _header_rect(width, height, HEADER_TOP)
    if _overlaps(rect, name_box):
        rect = _header_rect(width, height, name_box.y0 - GAP)
    fig.subplots_adjust(top=rect[1] - GAP)
    return Placement(rect, "grow-header")
