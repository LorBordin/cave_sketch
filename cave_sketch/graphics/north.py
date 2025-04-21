from matplotlib.axes._axes import Axes
import matplotlib.pyplot as plt

def _add_north_arrow(
    ax: Axes,
    base_x: int,
    base_y: int,
    arrow_len: int
):
    triangle_height = arrow_len / 2
    triangle_base = triangle_height / 2

    # Draw black triangle
    ax.add_patch(
        plt.Polygon(
            [[base_x, base_y], 
             [base_x - triangle_base, base_y - triangle_height], 
             [base_x, base_y - 2 / 3 * triangle_height],
             [base_x + triangle_base, base_y - triangle_height]],
            closed=True, color='black'
        )
    )
    # Add N label
    ax.text(
        base_x + 1,
        base_y, 
        "N",
        fontsize=12, 
        ha="center",
        va="bottom",
        color="black"
    ) 