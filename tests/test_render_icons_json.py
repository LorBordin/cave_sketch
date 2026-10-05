# ruff: noqa: E501
import math

import pytest

from cave_sketch.features.render_features import extract_features_from_json
from cave_sketch.geo.georef import meters_per_degree_wgs84
from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP

LAT, LON = 46.5, 11.3


def _ground_extent_m(icon):
    m_lat, m_lon = meters_per_degree_wgs84(LAT)
    lats = [lat for stroke in icon["strokes"] for lat, _ in stroke]
    lons = [lon for stroke in icon["strokes"] for _, lon in stroke]
    return (max(lons) - min(lons)) * m_lon, (max(lats) - min(lats)) * m_lat


def test_json_dict_nodes_produce_icons_and_points():
    map_data = {
        "name": "M",
        "lines": [],
        "nodes": {
            "B_blocks_0": {"lat": LAT, "lon": LON, "type": "B_blocks", "rotation": 0.0},
            "B_ice_0": {"lat": LAT, "lon": LON, "type": "B_ice"},
            "0P0": {"lat": LAT, "lon": LON, "type": "L_wall"},
        },
    }
    features = extract_features_from_json(map_data)
    (icon,) = features["icons"]
    assert icon["type"] == "B_blocks" and icon["weight"] == ICON_LINE_WEIGHT
    width_m, height_m = _ground_extent_m(icon)
    assert max(width_m, height_m) == pytest.approx(STYLE_MAP["B_blocks"]["size_m"], abs=1e-2)
    (point,) = features["points"]
    assert point["coords"] == [LAT, LON]


def test_json_list_nodes_and_rotation():
    map_data = {
        "name": "M",
        "lines": [],
        "nodes": [{"id": "w", "lat": LAT, "lon": LON, "type": "B_water-flow", "rotation": 270.0}],
    }
    (icon,) = extract_features_from_json(map_data)["icons"]
    tip = max((p for stroke in icon["strokes"] for p in stroke), key=lambda p: p[1])  # easternmost
    assert tip[0] == pytest.approx(LAT, abs=1e-9)
    assert tip[1] > LON


def test_json_without_nodes_key():
    features = extract_features_from_json({"name": "M", "lines": []})
    assert features["points"] == [] and features["icons"] == []


def test_json_water_flow_both_directions_give_one_northward_chevron():
    a = {"id": "0P0", "lat": LAT, "lon": LON}
    b = {"id": "0P1", "lat": LAT + 0.0001, "lon": LON}
    map_data = {
        "name": "M",
        "lines": [
            {"from": a, "to": b, "type": "L_water-flow"},
            {"from": b, "to": a, "type": "L_water-flow"},
        ],
        "nodes": {},
    }
    (chevron,) = extract_features_from_json(map_data)["icons"]
    apex = chevron["strokes"][0][1]
    assert apex[1] == pytest.approx(LON, abs=1e-12)
    assert apex[0] > LAT + 0.00005  # north of the segment midpoint
    assert math.isclose(max(_ground_extent_m(chevron)), STYLE_MAP["L_water-flow"]["decoration_size_m"], abs_tol=1e-2)
