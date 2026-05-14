from pathlib import Path

import pandas as pd
import pytest

from cave_sketch.dxf.models import CaveSurvey
from cave_sketch.dxf.parser import parse_dxf


def test_parse_valid_dxf():
    dxf_path = Path("tests/fixtures/sample.dxf")
    survey = parse_dxf(dxf_path)

    assert isinstance(survey, CaveSurvey)
    assert len(survey.points) > 0
    assert survey.name == "sample"

    # Check if stations were found
    station_ids = [p.id for p in survey.points if p.point_type == "station"]
    assert "0" in station_ids
    assert "1" in station_ids


def test_parse_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_dxf(Path("non_existent.dxf"))


def test_parse_writes_csv(tmp_path):
    dxf_path = Path("tests/fixtures/sample.dxf")
    csv_path = tmp_path / "output.csv"

    survey = parse_dxf(dxf_path, output_path=csv_path)

    assert csv_path.exists()
    df = pd.read_csv(csv_path)
    assert len(df) == len(survey.points)
    assert set(df.columns) == {"Node_Id", "Links", "X", "Y", "Type"}
