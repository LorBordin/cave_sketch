# ruff: noqa: E501
import os
import xml.etree.ElementTree as ET
import zipfile

from cave_sketch.backend_renders.google_earth import render_to_kml, render_to_kmz


def test_compact_kml_export():
    map_data = {
        "name": "Test Map",
        "lines": [
            {"from": {"id": "1", "lat": 1.0, "lon": 1.0}, "to": {"id": "2", "lat": 2.0, "lon": 2.0}, "type": "wall"},
            {"from": {"id": "2", "lat": 2.0, "lon": 2.0}, "to": {"id": "3", "lat": 3.0, "lon": 3.0}, "type": "wall"},
            {"from": {"id": "3", "lat": 3.0, "lon": 3.0}, "to": {"id": "4", "lat": 4.0, "lon": 4.0}, "type": "wall"},
        ],
        "nodes": [
            {"id": "5", "lat": 5.0, "lon": 5.0, "type": "BLOCK"},
        ],
        "water_polygons": [
            {
                "polygon_id": "1",
                "coordinates": [
                    [1.0, 1.0],
                    [2.0, 1.0],
                    [2.0, 2.0],
                    [1.0, 1.0],
                ]
            }
        ]
    }
    
    kml_str = render_to_kml([map_data])
    
    # Check that it's well-formed XML
    root = ET.fromstring(kml_str.encode('utf-8'))
    
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    
    # 1. One shared style for wall
    styles = root.findall(".//kml:Style", ns)
    style_ids = [s.get("id") for s in styles]
    assert "line_wall" in style_ids or "line_L_wall" in style_ids, "Should have a shared style for wall"
    
    # 2. MultiGeometry for wall lines
    placemarks = root.findall(".//kml:Placemark", ns)
    
    wall_placemarks = []
    water_placemarks = []
    point_placemarks = []
    
    for p in placemarks:
        if p.find(".//kml:MultiGeometry", ns) is not None:
            wall_placemarks.append(p)
        elif p.find(".//kml:Polygon", ns) is not None:
            water_placemarks.append(p)
        elif p.find(".//kml:Point", ns) is not None:
            point_placemarks.append(p)
            
    # The 3 segments should be chained into 1 MultiGeometry placemark
    assert len(wall_placemarks) == 1, "Expected exactly ONE MultiGeometry placemark for wall lines"
    
    # 1 polygon
    assert len(water_placemarks) == 1, "Expected exactly ONE Polygon placemark"
    
    # 1 point
    assert len(point_placemarks) == 1, "Expected exactly ONE Point placemark"
    
    # Check styleUrl
    style_url = wall_placemarks[0].find("kml:styleUrl", ns).text
    assert "wall" in style_url
    

def test_kmz_export(tmp_path):
    map_data = {
        "name": "Test Map",
        "lines": [
            {"from": {"id": "1", "lat": 1.0, "lon": 1.0}, "to": {"id": "2", "lat": 2.0, "lon": 2.0}, "type": "wall"},
        ],
        "nodes": [],
    }
    out_file = str(tmp_path / "test.kmz")
    res = render_to_kmz([map_data], out_file)
    assert res == out_file
    assert os.path.exists(out_file)
    
    with zipfile.ZipFile(out_file, "r") as zf:
        names = zf.namelist()
        assert "doc.kml" in names
        kml_content = zf.read("doc.kml").decode("utf-8")
        assert "<kml" in kml_content
        assert "<MultiGeometry" in kml_content
