import math

import pytest

from cave_sketch.survey.config import TitleBlockInfo


def test_defaults_are_empty():
    info = TitleBlockInfo()
    assert info.surveyor_name == ""
    assert info.drawer_name == ""
    assert info.municipality == ""
    assert info.latitude is None
    assert info.longitude is None
    assert info.elevation_m is None


def test_strings_are_stripped():
    info = TitleBlockInfo(surveyor_name="  Alice ", drawer_name="   ", municipality=" Genga ")
    assert info.surveyor_name == "Alice"
    assert info.drawer_name == ""
    assert info.municipality == "Genga"


def test_valid_coordinates_including_zero():
    info = TitleBlockInfo(latitude=0.0, longitude=0.0)
    assert info.latitude == 0.0
    assert info.longitude == 0.0


@pytest.mark.parametrize("lat, lon", [(45.0, None), (None, 11.0)])
def test_lat_and_lon_must_be_entered_together(lat, lon):
    with pytest.raises(ValueError, match="together"):
        TitleBlockInfo(latitude=lat, longitude=lon)


@pytest.mark.parametrize("lat", [-90.0001, 90.0001, math.nan])
def test_latitude_out_of_range(lat):
    with pytest.raises(ValueError, match="Latitude"):
        TitleBlockInfo(latitude=lat, longitude=0.0)


@pytest.mark.parametrize("lon", [-180.0001, 180.0001, math.nan])
def test_longitude_out_of_range(lon):
    with pytest.raises(ValueError, match="Longitude"):
        TitleBlockInfo(latitude=0.0, longitude=lon)


def test_range_bounds_are_inclusive():
    TitleBlockInfo(latitude=-90.0, longitude=-180.0)
    TitleBlockInfo(latitude=90.0, longitude=180.0)
