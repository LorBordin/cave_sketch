import os
from cave_sketch.dxf.models import CaveSurvey, SurveyPoint, SurveyLine
from cave_sketch.geo.models import GeoPoint
from cave_sketch.geo.kml import export_kml

def generate_sample_kml():
    # Setup simple data for a hypothetical cave near Rome
    # Station 0: Entrance (41.8902, 12.4922)
    # Station 1: 50m North, 10m deep
    # Station 2: 30m East from Station 1
    
    points = [
        GeoPoint(station_id="ENT", lat=41.8902, lon=12.4922, x=0.0, y=0.0, z=0.0),
        GeoPoint(station_id="S1", lat=41.89065, lon=12.4922, x=0.0, y=50.0, z=-10.0),
        GeoPoint(station_id="S2", lat=41.89065, lon=12.49256, x=30.0, y=50.0, z=-12.0),
    ]
    
    lines = [
        SurveyLine(from_id="ENT", to_id="S1", line_type="centerline"),
        SurveyLine(from_id="S1", to_id="S2", line_type="centerline"),
    ]
    
    survey = CaveSurvey(name="Colosseum Cave", lines=lines)
    
    kml_content = export_kml(survey, points)
    
    output_path = "sample_cave.kml"
    with open(output_path, "w") as f:
        f.write(kml_content)
    
    print(f"Sample KML generated at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    generate_sample_kml()
