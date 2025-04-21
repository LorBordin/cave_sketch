from matplotlib.axes._axes import Axes
import matplotlib.pyplot as plt

def _add_rule(
        ax: Axes,
        x_start: int,
        y_start: int,
        scale_len: int = 20,
        segment_len: int = 4,
        orientation: str = "horizontal"
) -> None:
    # Add rule as a segmented rectangle
    assert scale_len % segment_len == 0, "Scale_length should be evenly divisible by segment_length"
    num_segments = scale_len // segment_len

    rect_thickness = .5

    for i in range(num_segments):
        
        if orientation == "horizontal":
            dx, dy = segment_len, 0
            width, height = segment_len, rect_thickness
        
        elif orientation == "vertical":
            dx, dy = 0, segment_len
            width, height = rect_thickness, segment_len

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