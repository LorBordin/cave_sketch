from typing import List

from cave_sketch.dxf.models import CaveSurvey
from cave_sketch.geo.models import GeoPoint


def export_kml(survey: CaveSurvey, geo_points: List[GeoPoint]) -> str:
    """
    Export a georeferenced cave survey to KML format.
    
    Args:
        survey: The CaveSurvey containing line connections.
        geo_points: The georeferenced points with lat/lon/z.
        
    Returns:
        A string containing the KML XML content.
    """
    # Map station IDs to GeoPoints for quick lookup
    point_map = {p.station_id: p for p in geo_points}
    
    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <Style id="centerline">
      <LineStyle>
        <color>ff0000ff</color>
        <width>2</width>
      </LineStyle>
    </Style>
""".format(name=survey.name)

    kml_footer = """  </Document>
</kml>
"""

    placemarks = []
    
    # Group lines by type for better organization in KML if needed
    # For now, just export all lines as segments in a single Folder
    placemarks.append("    <Folder>")
    placemarks.append("      <name>Survey Lines</name>")
    
    for line in survey.lines:
        p_from = point_map.get(line.from_id)
        p_to = point_map.get(line.to_id)
        
        if p_from and p_to:
            coords = "{lon1},{lat1},{alt1} {lon2},{lat2},{alt2}".format(
                lon1=p_from.lon, lat1=p_from.lat, alt1=p_from.z,
                lon2=p_to.lon, lat2=p_to.lat, alt2=p_to.z
            )
            
            pm = """      <Placemark>
        <name>{from_id} to {to_id}</name>
        <styleUrl>#centerline</styleUrl>
        <LineString>
          <tessellate>1</tessellate>
          <coordinates>{coords}</coordinates>
        </LineString>
      </Placemark>""".format(from_id=line.from_id, to_id=line.to_id, coords=coords)
            placemarks.append(pm)
            
    placemarks.append("    </Folder>")
    
    return kml_header + "\n".join(placemarks) + "\n" + kml_footer
