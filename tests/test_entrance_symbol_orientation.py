from pathlib import Path

import matplotlib
import pandas as pd
import pytest
from matplotlib.collections import LineCollection

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.survey import draw_survey


def test_parse_dxf_sample_entrance_rotation() -> None:
    dxf_path = Path("tests/fixtures/sample_entrance.dxf")
    survey = parse_dxf(dxf_path)

    entrance_pts = [p for p in survey.points if p.point_type == "B_entrance"]
    assert len(entrance_pts) == 1
    entrance = entrance_pts[0]
    assert entrance.rotation == pytest.approx(170.17, abs=0.01)


def test_draw_survey_preserves_entrance_orientation(tmp_path: Path) -> None:
    dxf_path = Path("tests/fixtures/sample_entrance.dxf")
    csv_path = tmp_path / "sample_entrance.csv"
    survey = parse_dxf(dxf_path, output_path=csv_path)

    entrance_pt = [p for p in survey.points if p.point_type == "B_entrance"][0]

    fig = draw_survey(
        title="Entrance Survey",
        rule_length=20,
        csv_map_path=str(csv_path),
    )

    # Get the survey plot axes (excluding title block)
    axes = [ax for ax in fig.get_axes() if ax.get_position().y0 < 0.8]
    assert len(axes) == 1
    ax = axes[0]

    # Find line collections (walls and icon strokes)
    line_colls = [c for c in ax.collections if isinstance(c, LineCollection)]
    # Look for the closed 3-segment triangle (4 coordinates where first == last)
    entrance_segments = None
    for coll in line_colls:
        for seg in coll.get_segments():
            if len(seg) == 4 and (seg[0] == seg[-1]).all():
                entrance_segments = seg
                break
        if entrance_segments is not None:
            break

    assert entrance_segments is not None, "Entrance icon triangle not found in rendered plot"

    # In ICON_SHAPES['entrance'], index 0 is the apex (0, 0.5)
    apex_x, apex_y = entrance_segments[0]
    base1_y = entrance_segments[1][1]
    base2_y = entrance_segments[2][1]

    # With rotation ~170.17°, apex points downward (towards entrance),
    # meaning apex_y < center_y and apex_y < base_y.
    # If rotation had been lost (0°), apex would point upward (apex_y > center_y).
    assert apex_y < entrance_pt.y
    assert apex_y < base1_y and apex_y < base2_y
    plt.close(fig)


def test_draw_survey_backward_compatibility_without_rotation(tmp_path: Path) -> None:
    csv_path = tmp_path / "legacy.csv"
    df = pd.DataFrame([
        {"Node_Id": "1", "Links": "2", "X": 0.0, "Y": 0.0, "Type": "station"},
        {"Node_Id": "2", "Links": "1", "X": 10.0, "Y": 0.0, "Type": "station"},
        {"Node_Id": "B_blocks_0", "Links": "-", "X": 5.0, "Y": 5.0, "Type": "B_blocks"},
    ])
    df.to_csv(csv_path, index=False)

    fig = draw_survey(
        title="Legacy Survey",
        rule_length=20,
        csv_map_path=str(csv_path),
    )
    assert fig is not None
    plt.close(fig)
