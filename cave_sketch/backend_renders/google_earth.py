import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Dict, List
from xml.dom import minidom

from cave_sketch.features.chaining import chain_segments_by_type
from cave_sketch.features.render_features import extract_features_from_json
from cave_sketch.style import STYLE_MAP


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
        "indigo": "ff82004b",
        "deepskyblue": "ffffbf00",
        "aliceblue": "fffff8f0",
        "saddlebrown": "ff13458b",
    }
    base = color_map.get(color.lower(), "ffffffff")
    alpha = int(opacity * 255)
    return f"{alpha:02x}{base[2:]}"


def render_to_kml(map_list: List[Dict[str, Any]], layer_name: str = "All Maps") -> str:
    """
    Convert a list of map JSONs into a single KML string, grouped by map name.
    Each JSON is processed by `extract_features_from_json` and chained.
    """
    # Root KML structure
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    ET.SubElement(doc, "name").text = layer_name

    # We need to collect all unique types so we can define shared styles at the document level
    # Or we can just define them for all styles in STYLE_MAP
    for stype, sdict in STYLE_MAP.items():
        style_id = str(sdict.get("type", "line")) + "_" + stype
        style = ET.SubElement(doc, "Style", id=style_id)
        
        if sdict.get("type") == "area":
            poly_style = ET.SubElement(style, "PolyStyle")
            ET.SubElement(poly_style, "color").text = rgba_to_kml_color(
                str(sdict.get("color", "blue")), float(str(sdict.get("alpha", 0.3)))
            )
            ET.SubElement(poly_style, "fill").text = "1"
            ET.SubElement(poly_style, "outline").text = "1"

            line_style = ET.SubElement(style, "LineStyle")
            ET.SubElement(line_style, "color").text = rgba_to_kml_color(
                str(sdict.get("color", "blue")), 1.0
            )
            ET.SubElement(line_style, "width").text = "1"
        elif sdict.get("type") == "point":
            icon_style = ET.SubElement(style, "IconStyle")
            color_kml = rgba_to_kml_color(str(sdict.get("color", "black")))
            ET.SubElement(icon_style, "color").text = color_kml
            scale_str = str(float(str(sdict.get("markersize", 4))) / 4)
            ET.SubElement(icon_style, "scale").text = scale_str
        else: # line
            line_style = ET.SubElement(style, "LineStyle")
            ET.SubElement(line_style, "color").text = rgba_to_kml_color(
                str(sdict.get("color", "black"))
            )
            ET.SubElement(line_style, "width").text = str(sdict.get("weight", 2))

    # Process each JSON
    for map_data in map_list:
        features = extract_features_from_json(map_data)
        folder = ET.SubElement(doc, "Folder")
        ET.SubElement(folder, "name").text = map_data.get("name", "Unnamed Map")

        # --- POLYGONS ---
        for p in features.get("polygons", []):
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = p.get("popup", "")
            
            # Use shared style if available, otherwise fallback
            style_id = "#area_A_water" # By default in old code it was water
            ET.SubElement(placemark, "styleUrl").text = style_id

            # ---- GEOMETRY ----
            polygon = ET.SubElement(placemark, "Polygon")
            outer = ET.SubElement(polygon, "outerBoundaryIs")
            ring = ET.SubElement(outer, "LinearRing")

            # Coordinates without altitude
            coord_str = " ".join([f"{lon},{lat}" for lat, lon in p["coords"]])
            ET.SubElement(ring, "coordinates").text = coord_str

        # --- LINES ---
        # Get raw lines from map_data, chain them by type
        raw_lines = map_data.get("lines", [])
        chained = chain_segments_by_type(raw_lines)
        
        for ltype, polylines in chained.items():
            if not polylines:
                continue
                
            placemark = ET.SubElement(folder, "Placemark")
            ET.SubElement(placemark, "name").text = ltype
            
            # Reference shared style
            ET.SubElement(placemark, "styleUrl").text = f"#line_{ltype}"
            
            multi_geo = ET.SubElement(placemark, "MultiGeometry")
            for polyline in polylines:
                ls = ET.SubElement(multi_geo, "LineString")
                ET.SubElement(ls, "tessellate").text = "1"
                coord_str = " ".join([f"{lon},{lat},0" for lat, lon in polyline])
                ET.SubElement(ls, "coordinates").text = coord_str

        # --- POINTS ---
        for n in map_data.get("nodes", []):
            ntype = n.get("type", "")
            style_info = STYLE_MAP.get(ntype)
            if style_info and style_info.get("type") == "point":
                placemark = ET.SubElement(folder, "Placemark")
                ET.SubElement(placemark, "name").text = n.get("id", "")
                
                # Reference shared style
                ET.SubElement(placemark, "styleUrl").text = f"#point_{ntype}"
                
                point = ET.SubElement(placemark, "Point")
                lat, lon = n["lat"], n["lon"]
                ET.SubElement(point, "coordinates").text = f"{lon},{lat},0"

    # Pretty-print XML
    rough_string = ET.tostring(kml, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def render_to_kmz(
    map_list: List[Dict[str, Any]], output_path: str, layer_name: str = "All Maps"
) -> str:
    """
    Generate KML and zip it into a KMZ file.
    """
    kml_str = render_to_kml(map_list, layer_name)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_str)
    return output_path
