from pathlib import Path

import ezdxf
import pandas as pd
import pytest

from cave_sketch.dxf.models import CaveSurvey
from cave_sketch.dxf.parser import _get_features, parse_dxf


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
    assert set(df.columns) == {"Node_Id", "Links", "X", "Y", "Type", "Rotation"}


def _doc_with_inserts(names_and_rotations):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for name, rotation in names_and_rotations:
        if name not in doc.blocks:
            doc.blocks.new(name=name)
        msp.add_blockref(name, (1.0, 2.0), dxfattribs={"rotation": rotation})
    return msp


def test_get_features_recognizes_all_supported_blocks():
    names = ["B_ice", "B_snow", "B_blocks", "B_water-flow", "B_continuation", "B_entrance"]
    blocks = _get_features(_doc_with_inserts([(n, 0.0) for n in names]))
    assert sorted(b["Type"] for b in blocks) == sorted(names)


def test_get_features_ignores_unsupported_blocks():
    assert _get_features(_doc_with_inserts([("B_user", 0.0)])) == []


def test_get_features_keeps_insert_rotation_normalized():
    blocks = _get_features(_doc_with_inserts([("B_water-flow", 280.5), ("B_blocks", 360.0)]))
    assert [b["Rotation"] for b in blocks] == [pytest.approx(280.5), pytest.approx(0.0)]


def test_parse_sample_v14_includes_blocks_and_oriented_water_flow():
    survey = parse_dxf(Path("tests/fixtures/sample_v14.dxf"))
    types = {p.point_type for p in survey.points}
    assert {"B_blocks", "B_water-flow"} <= types
    flows = [p for p in survey.points if p.point_type == "B_water-flow"]
    assert any(p.rotation != 0.0 for p in flows)
    assert all(0.0 <= p.rotation < 360.0 for p in survey.points)

