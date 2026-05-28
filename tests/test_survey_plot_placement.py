from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from cave_sketch.survey.graphics.survey_plot import create_survey


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "X": [0, 100, 0, 100],
        "Y": [0, 0, 100, 100],
        "Type": ["station", "station", "station", "station"],
        "Node_Id": ["A", "B", "C", "D"],
        "Links": ["-", "-", "-", "-"]
    })

@patch("cave_sketch.survey.graphics.survey_plot._add_north_arrow")
@patch("cave_sketch.survey.graphics.survey_plot._add_rule")
@patch("cave_sketch.survey.graphics.survey_plot.compute_dual_layout")
def test_create_survey_uses_dynamic_placement(
    mock_compute_layout, mock_add_rule, mock_add_north, sample_df
):
    arrow_pos = (98, 98)
    rule_pos = (90, 90)
    mock_compute_layout.return_value = (arrow_pos, rule_pos, None)
    
    config = {"marker_zoom": 10, "text_zoom": 10}
    
    ax = MagicMock()
    create_survey(
        df=sample_df,
        rule_flag=True,
        north_flag=True,
        config=config,
        rule_length=20,
        ax=ax
    )
    
    # Verify compute_dual_layout was called
    mock_compute_layout.assert_called_once()
    
    # Verify North arrow is placed at the coord from compute_dual_layout
    mock_add_north.assert_called_once()
    args, kwargs = mock_add_north.call_args
    assert kwargs["coords"] == arrow_pos
    
    # Verify Rule is placed at the coord from compute_dual_layout
    mock_add_rule.assert_called_once()
    args, kwargs = mock_add_rule.call_args
    assert kwargs["x_start"] == rule_pos[0]
    assert kwargs["y_start"] == rule_pos[1]

@patch("cave_sketch.survey.graphics.survey_plot.compute_dual_layout")
@patch("matplotlib.axes.Axes.set_xlim")
@patch("matplotlib.axes.Axes.set_ylim")
def test_create_survey_fallback_behavior(
    mock_set_ylim, mock_set_xlim, mock_compute_layout, sample_df
):
    arrow_pos = (10, -10)
    rule_pos = (10, -20)
    mock_compute_layout.return_value = (arrow_pos, rule_pos, {"y_min": -30})
    
    config = {"marker_zoom": 10, "text_zoom": 10}
    
    ax = MagicMock()
    create_survey(
        df=sample_df,
        rule_flag=True,
        north_flag=True,
        config=config,
        rule_length=20,
        ax=ax
    )
    
    # Fallback should extend limits
    ax.set_ylim.assert_called()
    args, _ = ax.set_ylim.call_args
    assert args[0] == -30
