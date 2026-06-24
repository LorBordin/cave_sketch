import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from cave_sketch.survey.merger import SectionProtocol

_BRIDGE_PATH = (
    Path(__file__).parent.parent
    / "android/app/src/main/python/survey_bridge.py"
)
_spec = importlib.util.spec_from_file_location("survey_bridge", _BRIDGE_PATH)
survey_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(survey_bridge)


@pytest.fixture
def two_csvs(tmp_path):
    parent = pd.DataFrame({
        "Node_Id": ["st1", "st2"], "X": [0.0, 10.0], "Y": [0.0, 0.0],
        "Links": ["st2", "st1"], "Type": ["station", "station"],
    })
    child = pd.DataFrame({
        "Node_Id": ["st1", "st2"], "X": [0.0, 5.0], "Y": [0.0, 0.0],
        "Links": ["st2", "st1"], "Type": ["station", "station"],
    })
    p = tmp_path / "map.csv"
    c = tmp_path / "child_map.csv"
    parent.to_csv(p, index=False)
    child.to_csv(c, index=False)
    return str(p), str(c), tmp_path


def test_no_merge_returns_parsed_map_csv(two_csvs, tmp_path):
    map_csv, _, _ = two_csvs
    out = survey_bridge.effective_map_csv(
        map_csv, None, "", "", SectionProtocol.SIMPLE, str(tmp_path)
    )
    assert out == map_csv


def test_no_map_returns_none(tmp_path):
    out = survey_bridge.effective_map_csv(
        None, None, "", "", SectionProtocol.SIMPLE, str(tmp_path)
    )
    assert out is None


def test_merge_writes_and_returns_merged_csv(two_csvs):
    map_csv, child_csv, work_dir = two_csvs
    out = survey_bridge.effective_map_csv(
        map_csv, child_csv, "st2", "st1", SectionProtocol.SIMPLE, str(work_dir)
    )
    assert out == str(work_dir / "merged_map.csv")
    assert Path(out).exists()
    assert len(pd.read_csv(out)) > len(pd.read_csv(map_csv))
