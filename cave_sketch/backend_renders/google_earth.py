import xml.etree.ElementTree as ET
from typing import Any, Dict, List
from xml.dom import minidom

from cave_sketch.features.render_features import extract_features_from_json


def render_to_kml(map_list: List[Dict[str, Any]], layer_name: str = "All Maps") -> str:
    """
    Convert a list of map JSONs into a single KML string, grouped by map name.
    Each JSON is processed by `extract_features_from_json`.
    """
    # Root KML structure
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    ET.SubElement(doc, "name").text = layer_name

    # Helper for KML color
    def rgba_to_kml_color(color: str, opacity: float = 1.0) -> str:
        """Convert human color names + opacity to KML color (AABBGGRR)."""
        color_map = {
            "blue": "ffff0000",
            "red": "ff0000ff",
            "green": "ff00ff00",
            "black": "ff000000",
            "yellow": "ff00ffff",
            "gray": "ff888888",
            "white": "ffffffff",
        }
        base = color_map.get(color.lower(), "ffffffff")
        alpha = int(opacity * 255)
        return f"{alpha:02x}{base[2:]}" 

    # Process each JSON
    for map_data in map_list:
        features = extract_features_from_json(map_data)
        folder = ET.SubElement(doc, "Folder")
        ET.SubElement(folder, "name").text = map_data.get("name", "Unnamed Map")

        # --- POLYGONS ---
        for p in features.get("polygons", []):
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = p.get("popup", "")
        
            # ---- STYLE ----
            style = ET.SubElement(placemark, "Style")
        
            poly_style = ET.SubElement(style, "PolyStyle")
            ET.SubElement(poly_style, "color").text = rgba_to_kml_color(
                p.get("fill_color", "blue"), p.get("fill_opacity", 0.3)
            )
            ET.SubElement(poly_style, "fill").text = "1"
            ET.SubElement(poly_style, "outline").text = "1"
        
            line_style = ET.SubElement(style, "LineStyle")
            ET.SubElement(line_style, "color").text = rgba_to_kml_color(
                p.get("edge_color", p.get("fill_color", "blue")), 1.0
            )
            ET.SubElement(line_style, "width").text = "1"
        
            # ---- GEOMETRY ----
            polygon = ET.SubElement(placemark, "Polygon")
            outer = ET.SubElement(polygon, "outerBoundaryIs")
            ring = ET.SubElement(outer, "LinearRing")
        
            # Coordinates without altitude (Google Maps hates the ',0')
            coord_str = " ".join(
                [f"{lon},{lat}" for lat, lon in p["coords"]]
            )
            ET.SubElement(ring, "coordinates").text = coord_str


        # --- LINES ---
        for l in features.get("lines", []):
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = l.get("popup", "")
            style = ET.SubElement(placemark, "Style")
            line_style = ET.SubElement(style, "LineStyle")
            ET.SubElement(line_style, "color").text = rgba_to_kml_color(
                l.get("color", "black")
            )
            ET.SubElement(line_style, "width").text = str(l.get("weight", 2))
            line = ET.SubElement(placemark, "LineString")
            ET.SubElement(line, "tessellate").text = "1"
            coord_str = " ".join(
                [f"{lon},{lat},0" for lat, lon in l["coords"]]
            )
            ET.SubElement(line, "coordinates").text = coord_str

        # --- POINTS ---
        for p in features.get("points", []):
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = p.get("popup", "")
            style = ET.SubElement(placemark, "Style")
            icon_style = ET.SubElement(style, "IconStyle")
            ET.SubElement(icon_style, "color").text = rgba_to_kml_color(
                p.get("color", "black")
            )
            ET.SubElement(icon_style, "scale").text = str(p.get("size", 1) / 4)
            point = ET.SubElement(placemark, "Point")
            lat, lon = p["coords"]
            ET.SubElement(point, "coordinates").text = f"{lon},{lat},0"

    # Pretty-print XML
    rough_string = ET.tostring(kml, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
