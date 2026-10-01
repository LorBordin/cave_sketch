import json
import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from cave_sketch.satellite_view.map import _meters_per_degree_wgs84, draw_map


@pytest.fixture
def map_csv(tmp_path: Path) -> Path:
    df = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "Links": ["st2", "st1"],
        "X": [0.0, 0.0],
        "Y": [-10.0, 10.0],
        "Type": ["station", "station"],
    })
    path = tmp_path / "map.csv"
    df.to_csv(path, index=False)
    return path


def test_zero_variation_matches_omitted_kwarg(map_csv: Path, tmp_path: Path) -> None:
    gps_points = [{"station": "st1", "lat": 45.0, "lon": 10.0}]

    _, json_default, _ = draw_map(
        map_path=str(map_csv), gps_points=gps_points,
        output_path=str(tmp_path / "a.html"),
    )
    _, json_zero, _ = draw_map(
        map_path=str(map_csv), gps_points=gps_points,
        output_path=str(tmp_path / "b.html"), magnetic_variation_deg=0.0,
    )

    data_default = json.loads(Path(json_default).read_text())
    data_zero = json.loads(Path(json_zero).read_text())
    assert data_default["nodes"]["st2"] == data_zero["nodes"]["st2"]


def test_variation_rotates_georeferenced_output(map_csv: Path, tmp_path: Path) -> None:
    gps_points = [{"station": "st1", "lat": 45.0, "lon": 10.0}]

    _, json_path, _ = draw_map(
        map_path=str(map_csv), gps_points=gps_points,
        output_path=str(tmp_path / "out.html"), magnetic_variation_deg=10.0,
    )
    data = json.loads(Path(json_path).read_text())

    # The delta between st2 and the anchor st1, (0, 20), rotates by -10 deg
    # (East declination) regardless of the rotation pivot (a rigid rotation
    # preserves point-to-point deltas up to the rotation angle itself).
    theta = math.radians(-10.0)
    dx = math.cos(theta) * 0.0 - math.sin(theta) * 20.0
    dy = math.sin(theta) * 0.0 + math.cos(theta) * 20.0
    m_per_deg_lat, m_per_deg_lon = _meters_per_degree_wgs84(45.0)
    expected_lat = 45.0 + dy / m_per_deg_lat
    expected_lon = 10.0 + dx / m_per_deg_lon

    assert data["nodes"]["st2"]["lat"] == pytest.approx(expected_lat, abs=1e-9)
    assert data["nodes"]["st2"]["lon"] == pytest.approx(expected_lon, abs=1e-9)


@patch("cave_sketch.satellite_view.map.apply_magnetic_variation")
def test_variation_applied_before_manual_rotation(
    mock_apply: MagicMock, map_csv: Path, tmp_path: Path
) -> None:
    """The declination correction must run on the raw CSV data, before the
    existing manual `rotation_angle` block — so the two compose instead of
    one silently overriding the other."""
    mock_apply.side_effect = lambda df, variation_deg: df
    gps_points = [{"station": "st1", "lat": 45.0, "lon": 10.0}]

    draw_map(
        map_path=str(map_csv), gps_points=gps_points,
        output_path=str(tmp_path / "out.html"),
        magnetic_variation_deg=12.5, rotation_angle=0,
    )

    mock_apply.assert_called_once()
    called_df, called_variation = mock_apply.call_args.args
    assert called_variation == 12.5
    assert called_df["X"].tolist() == [0.0, 0.0]
    assert called_df["Y"].tolist() == [-10.0, 10.0]
