import datetime
from typing import Optional

from matplotlib.figure import Figure


def draw_title_block(
    fig: Figure,
    cave_name: str,
    surveyor_name: str,
    total_length: float,
    total_depth: Optional[float] = None,
) -> None:
    """
    Draw a technical title block in the top margin.
    - Cave name is centered (no box).
    - Metadata box is placed on the top right in Italian (no double language,
      vertical alignment to prevent overlap).

    Args:
        fig: The matplotlib Figure.
        cave_name: Name of the cave.
        surveyor_name: Name of the surveyor.
        total_length: Computed total surveyed length in meters.
        total_depth: Computed total depth in meters, or None to omit.
    """
    # 1. Render cave name in the center of the top margin (large, bold, no box)
    fig.text(
        0.5,
        0.92,
        cave_name,
        fontsize=16,
        weight="bold",
        va="center",
        ha="center",
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
