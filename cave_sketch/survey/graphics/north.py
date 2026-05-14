from typing import Tuple

import matplotlib.pyplot as plt
from matplotlib.axes._axes import Axes

from cave_sketch.features.geometry import rotate_points


def _add_north_arrow(ax: Axes, coords: Tuple[float, float], arrow_len: float, rotation_deg: float):
    n_segments = 5
    unit_len = arrow_len / n_segments

    x_o, y_o = coords
    x_left, y_left = x_o - unit_len, y_o + unit_len
    x_top, y_top = x_o, y_o + unit_len * n_segments
    x_right, y_right = x_o + unit_len, y_o + unit_len
    center: Tuple[float, float] = (x_o, y_o + arrow_len / 2)

    if rotation_deg != 0:
        p_o = rotate_points([x_o, y_o], center, rotation_deg)
        x_o, y_o = float(p_o[0]), float(p_o[1])

        p_left = rotate_points([x_left, y_left], center, rotation_deg)
        x_left, y_left = float(p_left[0]), float(p_left[1])

        p_top = rotate_points([x_top, y_top], center, rotation_deg)
        x_top, y_top = float(p_top[0]), float(p_top[1])

        p_right = rotate_points([x_right, y_right], center, rotation_deg)
        x_right, y_right = float(p_right[0]), float(p_right[1])

    # Draw black triangle
    ax.add_patch(
        plt.Polygon([[x_o, y_o], [x_right, y_right], [x_top, y_top]], closed=True, color="black")
    )
    # Draw white triangle
    ax.add_patch(
        plt.Polygon(
            [[x_o, y_o], [x_left, y_left], [x_top, y_top]],
            closed=True,
            facecolor="white",
            edgecolor="black",
        )
    )

    ax.add_patch(plt.Circle(center, arrow_len / 2, fill=False))
