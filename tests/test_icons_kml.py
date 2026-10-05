# ruff: noqa: E501
import xml.etree.ElementTree as ET

from cave_sketch.backend_renders.google_earth import render_to_kml, rgba_to_kml_color
from cave_sketch.style import STYLE_MAP
from cave_sketch.style_icons import ICON_SHAPES

NS = {"kml": "http://www.opengis.net/kml/2.2"}
LAT, LON = 46.5, 11.3


def _kml_root(map_data):
    return ET.fromstring(render_to_kml([map_data]).encode("utf-8"))


def test_kml_icon_style_uses_wall_width_and_icon_color():
    root = _kml_root({"name": "M", "lines": [], "nodes": []})
    styles = {s.get("id"): s for s in root.findall(".//kml:Style", NS)}
    for typ in ["B_blocks", "B_continuation", "B_entrance", "B_water-flow", "L_water-flow"]:
        line_style = styles[f"icon_{typ}"].find("kml:LineStyle", NS)
        assert line_style.find("kml:width", NS).text == str(STYLE_MAP["L_wall"]["weight"])
        assert line_style.find("kml:color", NS).text == rgba_to_kml_color(STYLE_MAP[typ]["color"])
        assert styles[f"icon_{typ}"].find("kml:IconStyle", NS) is None


def test_kml_icon_is_ground_geometry_not_pushpin():
    map_data = {
        "name": "M",
        "lines": [],
        "nodes": {"c": {"lat": LAT, "lon": LON, "type": "B_continuation", "rotation": 0.0}},
    }
    root = _kml_root(map_data)
    (placemark,) = [p for p in root.findall(".//kml:Placemark", NS)
                    if p.find("kml:styleUrl", NS).text == "#icon_B_continuation"]
    assert placemark.find(".//kml:Point", NS) is None
    strings = placemark.findall("kml:MultiGeometry/kml:LineString", NS)
    assert len(strings) == len(ICON_SHAPES["continuation"])
    assert root.find(".//kml:Icon", NS) is None  # no pushpin / PNG anywhere


def test_kml_water_flow_line_gets_chevron_placemark():
    a = {"id": "0P0", "lat": LAT, "lon": LON}
    b = {"id": "0P1", "lat": LAT + 0.0001, "lon": LON}
    map_data = {
        "name": "M",
        "lines": [{"from": a, "to": b, "type": "L_water-flow"}, {"from": b, "to": a, "type": "L_water-flow"}],
        "nodes": [],
    }
    urls = [p.find("kml:styleUrl", NS).text for p in _kml_root(map_data).findall(".//kml:Placemark", NS)]
    assert urls.count("#line_L_water-flow") == 1
    assert urls.count("#icon_L_water-flow") == 1


def test_kml_color_map_covers_every_style_color():
    for style in STYLE_MAP.values():
        assert rgba_to_kml_color(style["color"]) != "ffffffff" or style["color"] == "white", style["color"]
