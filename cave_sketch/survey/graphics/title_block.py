import datetime
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


def wrap_text(text: str, max_chars: int = 35) -> str:
    """
    Wrap text to at most 2 lines, ensuring each line is at most max_chars.
    If it's too long, split it into 2 lines. If it's still too long,
    truncate the second line with "...".
    """
    if not text:
        return ""
    
    words = text.split(" ")
    lines: list[str] = []
    current_line: list[str] = []
    current_len = 0
    
    for word in words:
        if not word:
            continue
        # If the word itself is longer than max_chars, we need to split the word.
        if len(word) > max_chars:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []
                current_len = 0
            
            for i in range(0, len(word), max_chars):
                chunk = word[i:i+max_chars]
                lines.append(chunk)
            if lines:
                last_chunk = lines.pop()
                current_line = [last_chunk]
                current_len = len(last_chunk)
            continue

        space_len = 1 if current_line else 0
        if current_len + space_len + len(word) > max_chars:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)
        else:
            current_line.append(word)
            current_len += space_len + len(word)
            
    if current_line:
        lines.append(" ".join(current_line))
        
    if len(lines) <= 1:
        return "\n".join(lines)
    
    line1 = lines[0]
    line2 = " ".join(lines[1:])
    
    if len(line2) > max_chars:
        line2 = line2[:max_chars - 3].rstrip() + "..."
        
    return f"{line1}\n{line2}"


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
