import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
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
@patch("cave_sketch.survey.graphics.survey_plot.find_best_corner")
@patch("cave_sketch.survey.graphics.survey_plot.corner_anchor")
@patch("cave_sketch.survey.graphics.survey_plot.is_fallback_needed")
def test_create_survey_uses_dynamic_placement(
    mock_fallback, mock_anchor, mock_find_corner, mock_add_rule, mock_add_north, sample_df
):
    mock_find_corner.return_value = "top-right"
    mock_anchor.return_value = (98, 98)
    mock_fallback.return_value = False
    
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
    
    # Verify find_best_corner was called with rotated X/Y
    # (In this case rotation=0, so original X/Y)
    mock_find_corner.assert_called()
    
    # Verify North arrow is placed at the anchor
    mock_add_north.assert_called()
    args, kwargs = mock_add_north.call_args
    assert kwargs["coords"] == (98, 98)
    
    # Verify Rule is placed in the same corner (side-by-side)
    mock_add_rule.assert_called()
    # Check that it's near (98, 98)
    args, kwargs = mock_add_rule.call_args
    # Current implementation will fail because it doesn't use these mocks yet
    assert abs(kwargs["x_start"] - 98) < 10
    assert abs(kwargs["y_start"] - 98) < 10

@patch("cave_sketch.survey.graphics.survey_plot.is_fallback_needed")
@patch("matplotlib.axes.Axes.set_xlim")
@patch("matplotlib.axes.Axes.set_ylim")
def test_create_survey_fallback_behavior(mock_set_ylim, mock_set_xlim, mock_fallback, sample_df):
    mock_fallback.return_value = True
    
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
    # Exact values depend on implementation, but at least one of set_xlim/ylim should be called
    assert ax.set_xlim.called or ax.set_ylim.called
