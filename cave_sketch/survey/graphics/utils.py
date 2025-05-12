from typing import Tuple
import numpy as np
import re

def is_integer_node(node_id):
    return re.fullmatch(r"\d+", node_id) is not None

def rotate_point(
    point: Tuple[float, float],
    center: Tuple[float, float],
    rotation_deg: float
) -> Tuple[float, float]:
    theta = np.radians(rotation_deg)
    cos_theta, sin_theta = np.cos(theta), np.sin(theta)

    x, y = point
    x_center, y_center = center
    x_shifted, y_shifted = x - x_center, y - y_center

    x_rot = cos_theta * x_shifted - sin_theta * y_shifted + x_center
    y_rot = sin_theta * x_shifted + cos_theta * y_shifted + y_center

    return (x_rot, y_rot)