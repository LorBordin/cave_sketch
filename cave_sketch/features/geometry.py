import copy
import math
from typing import List, Tuple, Union

import numpy as np


def rotate_points(
    points: Union[List[float], List[List[float]], np.ndarray],
    center: Union[List[float], Tuple[float, float]],
    angle_deg: float,
    mode: str = "cartesian"
) -> np.ndarray:
    """
    Rotate one or more 2D points around a center by a given angle (degrees).

    Parameters
    ----------
    points : [x, y] or list of [x, y] or np.ndarray shape (N, 2)
    center : [x, y]
    angle_deg : rotation angle in degrees
    mode : "cartesian" or "geo"

    Returns
    -------
    np.ndarray
        Rotated points of shape (N, 2) or (2,) if a single point was passed.
    """
    theta = math.radians(angle_deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    pts = np.atleast_2d(points).astype(float)
    cx, cy = center

    if mode == "geo":
        shifted = np.column_stack((pts[:, 1] - cy, pts[:, 0] - cx))
        rotated = np.empty_like(shifted)
        rotated[:, 0] = cos_t * shifted[:, 0] - sin_t * shifted[:, 1]
        rotated[:, 1] = sin_t * shifted[:, 0] + cos_t * shifted[:, 1]
        result = np.column_stack((rotated[:, 1] + cx, rotated[:, 0] + cy))
    else:
        shifted = pts - np.array(center)
        rotated = np.empty_like(shifted)
        rotated[:, 0] = cos_t * shifted[:, 0] - sin_t * shifted[:, 1]
        rotated[:, 1] = sin_t * shifted[:, 0] + cos_t * shifted[:, 1]
        result = rotated + np.array(center)

    # Return same shape as input (single point or list of points)
    return result[0] if np.ndim(points) == 1 else result

def rotate_cave_map(data, angle_deg, center_lat, center_lon):
    """
    Rotates all coordinates (nodes, lines, water_polygons, and center)
    in a cave map dictionary around a given center point.

    Args:
        data (dict): cave map dictionary (from JSON)
        angle_deg (float): rotation angle in degrees (positive = counterclockwise)
        center_lat (float): center latitude
        center_lon (float): center longitude

    Returns:
        dict: new dictionary with rotated coordinates
    """
    angle_rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

    def rotate_point(lat, lon):
        """Rotate a single (lat, lon) around the center."""
        x = lon - center_lon
        y = lat - center_lat
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        return center_lat + new_y, center_lon + new_x

    rotated = copy.deepcopy(data)

    # Rotate the center
    if "center" in rotated and "Latitude" in rotated["center"]:
        new_lat, new_lon = rotate_point(rotated["center"]["Latitude"], rotated["center"]["Longitude"])
        rotated["center"]["Latitude"], rotated["center"]["Longitude"] = new_lat, new_lon

    # Rotate nodes
    if "nodes" in rotated:
        for node in rotated["nodes"].values():
            node["lat"], node["lon"] = rotate_point(node["lat"], node["lon"])

    # Rotate lines (both 'from' and 'to')
    if "lines" in rotated:
        for line in rotated["lines"]:
            for endpoint in ("from", "to"):
                if "lat" in line[endpoint] and "lon" in line[endpoint]:
                    new_lat, new_lon = rotate_point(line[endpoint]["lat"], line[endpoint]["lon"])
                    line[endpoint]["lat"], line[endpoint]["lon"] = new_lat, new_lon

    # Rotate water polygons
    if "water_polygons" in rotated:
        for poly in rotated["water_polygons"]:
            new_coords = []
            for lat, lon in poly["coordinates"]:
                new_lat, new_lon = rotate_point(lat, lon)
                new_coords.append([new_lat, new_lon])
            poly["coordinates"] = new_coords

    return rotated