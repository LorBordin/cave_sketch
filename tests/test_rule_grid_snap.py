import pytest
from cave_sketch.survey.graphics.grid import snap_rule_to_grid

def test_snap_rule_to_grid_horizontal():
    # spacing = 10.0
    # Rule position: (12.3, 5.0) -> (10.0, 5.0) since rule is horizontal and x=12.3 snaps to nearest 10.0
    assert snap_rule_to_grid((12.3, 5.0), grid_spacing=10.0, rule_orientation="horizontal") == (10.0, 5.0)
    # Rule position: (17.8, 5.0) -> (20.0, 5.0)
    assert snap_rule_to_grid((17.8, 5.0), grid_spacing=10.0, rule_orientation="horizontal") == (20.0, 5.0)

def test_snap_rule_to_grid_vertical():
    # spacing = 10.0
    # Rule position: (5.0, 12.3) -> (5.0, 10.0) since rule is vertical and y=12.3 snaps to nearest 10.0
    assert snap_rule_to_grid((5.0, 12.3), grid_spacing=10.0, rule_orientation="vertical") == (5.0, 10.0)
    # Rule position: (5.0, 17.8) -> (5.0, 20.0)
    assert snap_rule_to_grid((5.0, 17.8), grid_spacing=10.0, rule_orientation="vertical") == (5.0, 20.0)

def test_snap_rule_to_grid_exact_multiples():
    # If already on grid line, should remain unchanged
    assert snap_rule_to_grid((10.0, 5.0), grid_spacing=10.0, rule_orientation="horizontal") == (10.0, 5.0)
    assert snap_rule_to_grid((5.0, 20.0), grid_spacing=10.0, rule_orientation="vertical") == (5.0, 20.0)

def test_snap_rule_to_grid_edge_cases():
    # Exactly between: 15.0 with spacing 10.0 should round to 10.0 or 20.0
    res_h = snap_rule_to_grid((15.0, 5.0), grid_spacing=10.0, rule_orientation="horizontal")
    assert res_h in [(10.0, 5.0), (20.0, 5.0)]

def test_snap_rule_to_grid_invalid_orientation():
    with pytest.raises(ValueError):
        snap_rule_to_grid((12.3, 5.0), grid_spacing=10.0, rule_orientation="invalid")


from unittest.mock import patch, MagicMock
import pandas as pd
from cave_sketch.survey.graphics.survey_plot import create_survey

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "X": [0, 100],
        "Y": [0, 100],
        "Type": ["station", "station"],
        "Node_Id": ["A", "B"],
        "Links": ["-", "-"]
    })

@patch("cave_sketch.survey.graphics.survey_plot._add_north_arrow")
@patch("cave_sketch.survey.graphics.survey_plot._add_rule")
@patch("cave_sketch.survey.graphics.survey_plot.compute_dual_layout")
def test_create_survey_snaps_rule_when_grid_enabled(
    mock_compute_layout, mock_add_rule, mock_add_north, sample_df
):
    arrow_pos = (22.3, 20.0)
    rule_pos = (12.3, 5.0)
    mock_compute_layout.return_value = (arrow_pos, rule_pos, None)

    ax = MagicMock()
    # rule_length = 20 -> grid_spacing = 10. (12.3, 5.0) X coordinate snaps to 10.0.
    # Delta X = -2.3. Arrow X shifts from 22.3 to 20.0.
    create_survey(
        df=sample_df,
        rule_flag=True,
        north_flag=True,
        config={"show_grid": True},
        rule_length=20,
        rule_orientation="horizontal",
        ax=ax
    )

    mock_add_rule.assert_called_once()
    _, kwargs_rule = mock_add_rule.call_args
    assert kwargs_rule["x_start"] == 10.0
    assert kwargs_rule["y_start"] == 5.0

    mock_add_north.assert_called_once()
    _, kwargs_north = mock_add_north.call_args
    assert kwargs_north["coords"] == (20.0, 20.0)

@patch("cave_sketch.survey.graphics.survey_plot._add_north_arrow")
@patch("cave_sketch.survey.graphics.survey_plot._add_rule")
@patch("cave_sketch.survey.graphics.survey_plot.compute_dual_layout")
def test_create_survey_no_snap_when_grid_disabled(
    mock_compute_layout, mock_add_rule, mock_add_north, sample_df
):
    arrow_pos = (22.3, 20.0)
    rule_pos = (12.3, 5.0)
    mock_compute_layout.return_value = (arrow_pos, rule_pos, None)

    ax = MagicMock()
    create_survey(
        df=sample_df,
        rule_flag=True,
        north_flag=True,
        config={"show_grid": False},
        rule_length=20,
        rule_orientation="horizontal",
        ax=ax
    )

    mock_add_rule.assert_called_once()
    _, kwargs_rule = mock_add_rule.call_args
    assert kwargs_rule["x_start"] == 12.3
    assert kwargs_rule["y_start"] == 5.0

    mock_add_north.assert_called_once()
    _, kwargs_north = mock_add_north.call_args
    assert kwargs_north["coords"] == (22.3, 20.0)

