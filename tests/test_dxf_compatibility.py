from pathlib import Path
import pytest
from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.dxf.models import CaveSurvey


def test_parse_v14_produces_same_survey_as_v9():
    dxf_v9_path = Path("tests/fixtures/sample_v9.dxf")
    dxf_v14_path = Path("tests/fixtures/sample_v14.dxf")

    survey_v9 = parse_dxf(dxf_v9_path)
    survey_v14 = parse_dxf(dxf_v14_path)

    # Assert point count and line count are equal
    assert len(survey_v14.points) == len(survey_v9.points)
    assert len(survey_v14.lines) == len(survey_v9.lines)

    # Check distributions of point types
    v9_point_types = [p.point_type for p in survey_v9.points]
    v14_point_types = [p.point_type for p in survey_v14.points]
    assert sorted(v9_point_types) == sorted(v14_point_types)

    # Check distributions of line types
    v9_line_types = [l.line_type for l in survey_v9.lines]
    v14_line_types = [l.line_type for l in survey_v14.lines]
    assert sorted(v9_line_types) == sorted(v14_line_types)


def test_parse_v14_polyline_linetypes():
    dxf_v14_path = Path("tests/fixtures/sample_v14.dxf")
    survey = parse_dxf(dxf_v14_path)

    line_types = {l.line_type for l in survey.lines}
    expected_types = {"L_wall", "L_wall-presumed", "L_pit", "A_water", "station_leg"}
    assert expected_types.issubset(line_types)


def test_parse_v9_backward_compat():
    dxf_v9_path = Path("tests/fixtures/sample_v9.dxf")
    survey = parse_dxf(dxf_v9_path)

    assert isinstance(survey, CaveSurvey)
    assert len(survey.points) > 0
    assert len(survey.lines) > 0

    # Ensure station points exist
    station_ids = [p.id for p in survey.points if p.point_type == "station"]
    assert len(station_ids) > 0
