import pytest

from cave_sketch.dxf.models import CaveSurvey, SurveyPoint
from cave_sketch.geo.georef import georeference
from cave_sketch.geo.models import GpsRef


def test_georef_success():
    # Setup a simple survey
    survey = CaveSurvey(name="test", points=[
        SurveyPoint(id="0", x=0.0, y=0.0),
        SurveyPoint(id="1", x=100.0, y=0.0),
        SurveyPoint(id="2", x=0.0, y=100.0),
    ])
    
    # 2 known GPS refs
    gps_refs = [
        GpsRef(station_id="0", lat=45.0, lon=10.0),
        GpsRef(station_id="1", lat=45.0, lon=10.0012), # Roughly 100m east
    ]
    
    geo_points = georeference(survey, gps_refs)
    
    assert len(geo_points) == 3
    
    # Check station 0 (should be very close to ref lat/lon)
    pt0 = next(p for p in geo_points if p.station_id == "0")
    assert pytest.approx(pt0.lat, abs=1e-4) == 45.0
    assert pytest.approx(pt0.lon, abs=1e-4) == 10.0
    
    # Check station 2 (should be north of station 0)
    pt2 = next(p for p in geo_points if p.station_id == "2")
    assert pt2.lat > 45.0
    assert pytest.approx(pt2.lon, abs=1e-4) == 10.0

def test_georef_too_few_points():
    survey = CaveSurvey(name="test", points=[SurveyPoint(id="0", x=0, y=0)])
    gps_refs = [GpsRef(station_id="0", lat=45.0, lon=10.0)]
    
    with pytest.raises(ValueError, match="At least 2 reference points are required"):
        georeference(survey, gps_refs)
