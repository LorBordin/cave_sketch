import math

from matplotlib.axes._axes import Axes


def _add_grid(
    ax: Axes,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    grid_spacing: float,
) -> None:
    """
    Draw a regular grid of horizontal and vertical lines on the matplotlib Axes.
    
    Grid lines are aligned to clean multiples of grid_spacing, rendered behind
    all other features (zorder=0) and style is lightgray dotted.
    """
    if grid_spacing <= 0:
        raise ValueError("grid_spacing must be positive and greater than zero.")

    # Vertical lines (snapped to multiples of grid_spacing)
    start_k_x = int(math.ceil(x_min / grid_spacing))
    end_k_x = int(math.floor(x_max / grid_spacing))
    for k in range(start_k_x, end_k_x + 1):
        x = k * grid_spacing
        ax.axvline(x, color="lightgray", linestyle=":", zorder=0)

    # Horizontal lines (snapped to multiples of grid_spacing)
    start_k_y = int(math.ceil(y_min / grid_spacing))
    end_k_y = int(math.floor(y_max / grid_spacing))
    for k in range(start_k_y, end_k_y + 1):
        y = k * grid_spacing
        ax.axhline(y, color="lightgray", linestyle=":", zorder=0)
