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


def test_generate_survey_plot_respects_show_centerline(two_csvs):
    from unittest.mock import patch
    map_csv, _, work_dir = two_csvs
    inputs_json = {
        "map_path": map_csv,
        "survey_name": "TestCenterlineBridge",
        "settings": {
            "rule_length": "100",
            "show_centerline": False
        }
    }
    with patch.object(survey_bridge, "draw_survey") as mock_draw:
        import json
        survey_bridge.generate_survey_plot(json.dumps(inputs_json), str(work_dir))
        mock_draw.assert_called_once()
        _, kwargs = mock_draw.call_args
        assert kwargs["config"]["show_centerline"] is False


def test_no_merge_returns_parsed_section_csv(two_csvs, tmp_path):
    section_csv, _, _ = two_csvs
    out = survey_bridge.effective_section_csv(
        section_csv, None, "", "", SectionProtocol.SIMPLE, str(tmp_path)
    )
    assert out == section_csv


def test_no_section_returns_none(tmp_path):
    out = survey_bridge.effective_section_csv(
        None, None, "", "", SectionProtocol.SIMPLE, str(tmp_path)
    )
    assert out is None


def test_section_merge_writes_and_returns_merged_section_csv(two_csvs):
    section_csv, child_csv, work_dir = two_csvs
    out = survey_bridge.effective_section_csv(
        section_csv, child_csv, "st2", "st1", SectionProtocol.SIMPLE, str(work_dir)
    )
    assert out == str(work_dir / "merged_section.csv")
    assert Path(out).exists()
    assert len(pd.read_csv(out)) > len(pd.read_csv(section_csv))


def test_generate_survey_plot_returns_map_and_section_csv_paths(two_csvs):
    import json
    from unittest.mock import patch
    map_csv, child_csv, work_dir = two_csvs
    sec_csv = str(work_dir / "section.csv")
    child_sec_csv = str(work_dir / "child_section.csv")
    pd.read_csv(map_csv).to_csv(sec_csv, index=False)
    pd.read_csv(child_csv).to_csv(child_sec_csv, index=False)

    inputs_json = {
        "map_path": map_csv,
        "section_path": sec_csv,
        "child_map_path": child_csv,
        "child_section_path": child_sec_csv,
        "parent_station": "st2",
        "child_station": "st1",
        "section_protocol": "simple",
        "survey_name": "TestBothCsvs",
    }
    with patch.object(survey_bridge, "draw_survey"):
        resp_json = survey_bridge.generate_survey_plot(json.dumps(inputs_json), str(work_dir))
        resp = json.loads(resp_json)
        assert "pdf_path" in resp
        assert "map_csv_path" in resp
        assert resp["map_csv_path"] == str(work_dir / "merged_map.csv")
        assert "section_csv_path" in resp
        assert resp["section_csv_path"] == str(work_dir / "merged_section.csv")

