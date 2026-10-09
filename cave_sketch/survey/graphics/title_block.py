import datetime
from typing import Optional

from matplotlib.figure import Figure

from cave_sketch.survey.config import TitleBlockInfo


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


def draw_title_block(
    fig: Figure,
    cave_name: str,
    surveyor_name: str,
    total_length: float,
    total_depth: Optional[float] = None,
) -> None:
    """
    Draw a technical title block in the top margin.
    - Cave name is left-aligned, wrapped to max 2 lines if too long.
    - Metadata box is placed on the top right in Italian (vertical layout to prevent overlaps).

    Args:
        fig: The matplotlib Figure.
        cave_name: Name of the cave.
        surveyor_name: Name of the surveyor.
        total_length: Computed total surveyed length in meters.
        total_depth: Computed total depth in meters, or None to omit.
    """
    # 1. Left-aligned wrapped cave name
    wrapped_name = wrap_text(cave_name, max_chars=35)
    fig.text(
        0.05,
        0.92,
        wrapped_name,
        fontsize=15,
        weight="bold",
        va="center",
        ha="left",
    )

    # 2. Add metadata box on the top right
    # Left: 68%, Bottom: 88%, Width: 27%, Height: 8%
    ax = fig.add_axes((0.68, 0.88, 0.27, 0.08))

    # Hide ticks and labels, keeping only the border spines
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("white")

    # Get current date in DD/MM/YYYY format
    current_date = datetime.date.today().strftime("%d/%m/%Y")

    # Render fields vertically to prevent any horizontal overlap
    y_pos = 0.82
    y_step = 0.22 if total_depth is not None else 0.3

    ax.text(
        0.05,
        y_pos,
        f"Rilevatore: {surveyor_name if surveyor_name else '-'}",
        fontsize=8.5,
        va="center",
        ha="left",
    )
    y_pos -= y_step

    ax.text(
        0.05,
        y_pos,
        f"Data: {current_date}",
        fontsize=8.5,
        va="center",
        ha="left",
    )
    y_pos -= y_step

    ax.text(
        0.05,
        y_pos,
        f"Sviluppo: {total_length:.1f} m",
        fontsize=8.5,
        va="center",
        ha="left",
    )

    if total_depth is not None:
        y_pos -= y_step
        ax.text(
            0.05,
            y_pos,
            f"Dislivello: {total_depth:.1f} m",
            fontsize=8.5,
            va="center",
            ha="left",
        )
