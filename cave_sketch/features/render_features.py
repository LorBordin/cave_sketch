from typing import Any, Dict

from cave_sketch.features.geometry import rotate_point
from cave_sketch.style import STYLE_MAP

def extract_features(map_data: Dict[str, Any], rotation_angle: float = 0) -> Dict[str, list]:
    """Extract abstract features (lines, polygons) with styles, independent of rendering backend."""
    features = {"lines": [], "polygons": []}
    data_center = [map_data["center"]["Latitude"], map_data["center"]["Longitude"]]

    # Polygons
    for water_polygon in map_data.get("water_polygons", []):
        coords = water_polygon["coordinates"]
        if rotation_angle:
            coords = [rotate_point(pt, data_center, rotation_angle) for pt in coords]
        features["polygons"].append({
            "coords": coords,
            "fill_color": "blue",
            "fill_opacity": 0.3,
            "edge_color": "blue",
            "popup": f"{map_data['name']}: Water Area {water_polygon.get('polygon_id', '')}"
        })

    # Lines
    for line in map_data.get("lines", []):
        line_type = line["type"]
        style = STYLE_MAP.get(line_type, {"color": "black", "type": "line"})
        color = style.get("color", "black")
        weight = style.get("weight", 1)
        linestyle = style.get("linestyle", "solid")

        dash = None
        if linestyle == (0, (1, 1)):
            dash = [5, 5]
        elif linestyle == (0, (1, 2)):
            dash = [3, 7]

        pt_from = [line["from"]["lat"], line["from"]["lon"]]
        pt_to = [line["to"]["lat"], line["to"]["lon"]]
        if rotation_angle:
            pt_from = rotate_point(pt_from, data_center, rotation_angle)
            pt_to = rotate_point(pt_to, data_center, rotation_angle)

        features["lines"].append({
            "coords": [pt_from, pt_to],
            "color": color,
            "weight": weight,
            "dash": dash,
            "popup": f"{map_data['name']}: {line_type}"
        })

    return features