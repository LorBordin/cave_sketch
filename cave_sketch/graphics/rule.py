from matplotlib.axes._axes import Axes
import matplotlib.pyplot as plt
from typing import Tuple

def _add_rule(
        ax: Axes,
        x_start: int,
        y_start: int,
        scale_len: int = 20,
        scale_width: int = .5,
        segment_len: int = 4,
        orientation: str = "horizontal"
) -> None:
    # Add rule as a segmented rectangle
    assert scale_len % segment_len == 0, "Scale_length should be evenly divisible by segment_length"
    num_segments = scale_len // segment_len

    for i in range(num_segments):
        
        if orientation == "horizontal":
            dx, dy = segment_len, 0
            width, height = segment_len, scale_width
        
        elif orientation == "vertical":
            dx, dy = 0, segment_len
            width, height = scale_width, segment_len

        segment_color = "black" if i % 2 == 0 else "white"
        ax.add_patch(
            plt.Rectangle(
                (x_start + i * dx, y_start + i * dy),
                width,
                height,
                color=segment_color,
                ec="black",
                lw=.5
            )
        )

    # Add label
    if orientation == 'horizontal':
        ax.text(
            x_start + scale_len / 2,
            y_start - 2,
            f'{scale_len} m',
            ha='center',
            va='top',
            fontsize=10
        )
    else:
        ax.text(
            x_start - 1.5,  # distanza dal bordo sinistro della barra
            y_start + scale_len / 2,
            f'{scale_len} m',
            ha='center',
            va='center',
            fontsize=10,
            rotation=90
        )

def _add_rule_auto(
    ax: Axes,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    ax_position: str = "bottom",  # or "left"
    scale_ratio: float = 0.1,     # how much of the x-range the rule should cover
    segment_len: int = 4
):
    # Compute automatic scale length based on the x_range
    x_len = x_range[1] - x_range[0]
    y_len = y_range[1] - y_range[0]
    scale_len = int(x_len * scale_ratio)

    # Round scale_len to nearest multiple of 20
    scale_len = max(20, int(round(scale_len / 20)) * 20)

    # Set origin
    x_start = (x_range[0] + x_range[1]) / 2 - scale_len / 2
    y_start = y_range[0] + 5  # slightly above min Y

    # Call your original function
    _add_rule(
        ax,
        x_start=x_start,
        y_start=y_start,
        scale_len=scale_len,
        segment_len=segment_len,
        orientation="horizontal"
    )

    return x_start, y_start, scale_len