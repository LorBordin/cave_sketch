from cave_sketch.survey.graphics.utils import rotate_point
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.axes._axes import Axes
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from typing import Tuple
import numpy as np

def _add_north_arrow(
    ax: Axes,
    coords: Tuple[int, int],
    arrow_len: int,
    rotation_deg: float
):  
    n_segments = 5
    unit_len = arrow_len / n_segments

    x_o, y_o = coords
    x_left, y_left = x_o - unit_len, y_o + unit_len
    x_top, y_top = x_o, y_o + unit_len * n_segments
    x_right, y_right = x_o + unit_len, y_o + unit_len
    center = (x_o, y_o + arrow_len / 2)

    if rotation_deg !=0: 
        x_o, y_o = rotate_point((x_o, y_o), center, rotation_deg)
        x_left, y_left = rotate_point((x_left, y_left), center, rotation_deg)
        x_top, y_top = rotate_point((x_top, y_top), center, rotation_deg)
        x_right, y_right = rotate_point((x_right, y_right), center, rotation_deg)

    # Draw black triangle
    ax.add_patch(
        plt.Polygon(
            [[x_o, y_o], 
             [x_right, y_right], 
             [x_top, y_top]],
            closed=True, color='black'
        )
    )
    # Draw white triangle
    ax.add_patch(
        plt.Polygon(
            [[x_o, y_o], 
             [x_left, y_left], 
             [x_top, y_top]],
            closed=True, facecolor="white", edgecolor='black'
        )
    )

    ax.add_patch(plt.Circle(center, arrow_len / 2, fill=False))