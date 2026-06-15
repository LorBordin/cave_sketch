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


def snap_rule_to_grid(
    rule_pos: tuple[float, float],
    grid_spacing: float,
    rule_orientation: str,
) -> tuple[float, float]:
    """
    Snap the leading coordinate of the ruler to the nearest multiple of grid_spacing.

    For horizontal rulers, snaps the X coordinate.
    For vertical rulers, snaps the Y coordinate.
    """
    if rule_orientation not in ("horizontal", "vertical"):
        raise ValueError(
            f"Invalid rule_orientation '{rule_orientation}'. "
            "Must be 'horizontal' or 'vertical'."
        )

    x, y = rule_pos
    if rule_orientation == "horizontal":
        x = round(x / grid_spacing) * grid_spacing
    elif rule_orientation == "vertical":
        y = round(y / grid_spacing) * grid_spacing

    return (x, y)
