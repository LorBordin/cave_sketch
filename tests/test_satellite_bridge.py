import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

# Load the bridge module (lives under android/, not a package).
_BRIDGE_PATH = (
    Path(__file__).parent.parent
    / "android/app/src/main/python/satellite_bridge.py"
)
_spec = importlib.util.spec_from_file_location("satellite_bridge", _BRIDGE_PATH)
satellite_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(satellite_bridge)


@pytest.fixture
def map_csv(tmp_path):
    df = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["st2", "st1"],
        "Type": ["station", "station"],
    })
    path = tmp_path / "map.csv"
    df.to_csv(path, index=False)
    return str(path)


def _inputs(map_path, points, **kw):
    base = {
        "map_path": map_path,
        "gps_points": points,
        "survey_name": "Test",
        "rotation_angle": 0,
        "additional_json_maps": [],
    }
    base.update(kw)
    return json.dumps(base)


def test_success_writes_three_outputs(map_csv, tmp_path):
    points = [{"station": "st1", "lat": "45.0", "lon": "7.0"}]
    inputs = _inputs(map_csv, points)
    out = json.loads(satellite_bridge.generate_satellite_map(inputs, str(tmp_path)))
    assert "error" not in out
    assert Path(out["html_path"]).exists()
    assert Path(out["json_path"]).exists()
    assert Path(out["kmz_path"]).exists()


def test_no_map_path_errors(tmp_path):
    out = json.loads(satellite_bridge.generate_satellite_map(_inputs("", []), str(tmp_path)))
    assert out["error"] == "no_map"


def test_empty_points_errors(map_csv, tmp_path):
    out = json.loads(satellite_bridge.generate_satellite_map(_inputs(map_csv, []), str(tmp_path)))
    assert out["error"] == "invalid_points"


def test_invalid_coordinate_errors(map_csv, tmp_path):
    points = [{"station": "st1", "lat": "abc", "lon": "7.0"}]
    inputs = _inputs(map_csv, points)
    out = json.loads(satellite_bridge.generate_satellite_map(inputs, str(tmp_path)))
    assert out["error"] == "invalid_points"


def test_no_anchor_match_errors(map_csv, tmp_path):
    points = [{"station": "nope", "lat": "45.0", "lon": "7.0"}]
    inputs = _inputs(map_csv, points)
    out = json.loads(satellite_bridge.generate_satellite_map(inputs, str(tmp_path)))
    assert out["error"] == "no_anchor_match"
