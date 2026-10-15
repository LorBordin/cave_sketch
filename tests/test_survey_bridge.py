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


def _generate_with(two_csvs, extra, settings=None):
    import json
    from unittest.mock import patch

    map_csv, _, work_dir = two_csvs
    inputs = {"map_path": map_csv, "survey_name": "T", "settings": settings or {}, **extra}
    with patch.object(survey_bridge, "draw_survey") as mock_draw:
        out = json.loads(survey_bridge.generate_survey_plot(json.dumps(inputs), str(work_dir)))
    return out, mock_draw


def test_generate_passes_title_block_and_variation(two_csvs):
    from cave_sketch.survey.config import TitleBlockInfo

    _, mock_draw = _generate_with(
        two_csvs,
        {
            "surveyor_name": "Alice",
            "drawer_name": "Bob",
            "municipality": "Genga",
            "latitude": 43.4,
            "longitude": 12.9,
            "elevation_m": 320,
        },
        settings={"magnetic_variation_deg": 2.5},
    )
    _, kwargs = mock_draw.call_args
    assert kwargs["title_block"] == TitleBlockInfo(
        surveyor_name="Alice",
        drawer_name="Bob",
        municipality="Genga",
        latitude=43.4,
        longitude=12.9,
        elevation_m=320.0,
    )
    assert kwargs["magnetic_variation_deg"] == 2.5


def test_generate_defaults_when_fields_missing_or_null(two_csvs):
    from cave_sketch.survey.config import TitleBlockInfo

    _, mock_draw = _generate_with(
        two_csvs, {"latitude": None, "longitude": None, "elevation_m": None}
    )
    _, kwargs = mock_draw.call_args
    assert kwargs["title_block"] == TitleBlockInfo()
    assert kwargs["magnetic_variation_deg"] == 0.0


def test_generate_rejects_invalid_title_block(two_csvs):
    out, mock_draw = _generate_with(two_csvs, {"latitude": 43.4, "longitude": None})
    assert out["error"] == "invalid_title_block"
    assert "together" in out["detail"]
    mock_draw.assert_not_called()

