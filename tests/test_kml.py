from cave_sketch.dxf.models import CaveSurvey, SurveyLine
from cave_sketch.geo.kml import export_kml
from cave_sketch.geo.models import GeoPoint


def test_export_kml_basic():
    # Setup simple data
    points = [
        GeoPoint(station_id="0", lat=45.0, lon=10.0, x=0.0, y=0.0, z=0.0),
        GeoPoint(station_id="1", lat=45.0001, lon=10.0, x=0.0, y=10.0, z=-5.0),
    ]
    lines = [
        SurveyLine(from_id="0", to_id="1", line_type="L_wall")
    ]
    survey = CaveSurvey(name="Test Cave", lines=lines)
    
    kml_content = export_kml(survey, points)
    
    assert "<?xml" in kml_content
    assert "<kml" in kml_content
    assert "Test Cave" in kml_content
    assert "10.0,45.0,0.0" in kml_content
    assert "10.0,45.0001,-5.0" in kml_content
