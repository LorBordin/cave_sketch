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
    Draw a technical blueprint-style title block (cartouche) in the top margin of the figure.

    Args:
        fig: The matplotlib Figure.
        cave_name: Name of the cave.
        surveyor_name: Name of the surveyor.
        total_length: Computed total surveyed length in meters.
        total_depth: Computed total depth in meters, or None to omit.
    """
    # Adding a dedicated axes in the top margin
    # Left: 5% of figure width
    # Bottom: 89% of figure height
    # Width: 90% of figure width
    # Height: 7% of figure height
    ax = fig.add_axes((0.05, 0.89, 0.9, 0.07))

    # Hide ticks and labels, keeping only the border spines
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("white")

    # Draw a vertical dividing line at 50% width
    ax.axvline(x=0.5, color="black", linewidth=1.0)

    # Get current date in DD/MM/YYYY format
    current_date = datetime.date.today().strftime("%d/%m/%Y")

    # Left Column: Cave name
    ax.text(
        0.02,
        0.75,
        "Nome Grotta / Cave Name",
        fontsize=7,
        color="dimgray",
        va="top",
        ha="left",
    )
    ax.text(
        0.02,
        0.2,
        cave_name,
        fontsize=14,
        weight="bold",
        va="bottom",
        ha="left",
    )

    # Right Column: Metadata grid
    # Row 1, Col 1: Surveyor
    ax.text(
        0.52,
        0.72,
        f"Rilevatore / Surveyor: {surveyor_name if surveyor_name else '-'}",
        fontsize=9,
        va="top",
        ha="left",
    )
    # Row 1, Col 2: Date
    ax.text(
        0.76,
        0.72,
        f"Data / Date: {current_date}",
        fontsize=9,
        va="top",
        ha="left",
    )
    # Row 2, Col 1: Total Length
    ax.text(
        0.52,
        0.28,
        f"Sviluppo / Length: {total_length:.1f} m",
        fontsize=9,
        va="bottom",
        ha="left",
    )
    # Row 2, Col 2: Total Depth
    if total_depth is not None:
        ax.text(
            0.76,
            0.28,
            f"Dislivello / Depth: {total_depth:.1f} m",
            fontsize=9,
            va="bottom",
            ha="left",
        )
