from unittest.mock import patch

import matplotlib.pyplot as plt
import pytest

from cave_sketch.survey.graphics.grid import _add_grid


def test_add_grid_creates_lines():
    fig, ax = plt.subplots()
    
    # We pass data extents: x in [5, 25], y in [12, 38], and spacing = 10
    # Clean multiples of 10 in [5, 25] are 10, 20.
    # Clean multiples of 10 in [12, 38] are 20, 30.
    _add_grid(ax, x_min=5, x_max=25, y_min=12, y_max=38, grid_spacing=10)
    
    # We should have vertical lines at x = 10, 20
    # And horizontal lines at y = 20, 30
    
    # Matplotlib stores lines added via axvline/axhline in ax.lines
    lines = ax.lines
    assert len(lines) == 4, f"Expected 4 grid lines, got {len(lines)}"
    
    # Verify properties
    v_lines = []
    h_lines = []
    for line in lines:
        assert line.get_color() == "lightgray"
        assert line.get_linestyle() == ":"
        assert line.get_zorder() == 0
        
        # In matplotlib, axvline has xdata as [x, x] and ydata as [0, 1]
        # (or in data coords [5, 25] if drawn differently, but typically
        # axvline uses transform ax.get_xaxis_transform() where x is in
        # data coords and y in axes coords).
        # We can distinguish axvline and axhline by checking their transforms or xdata/ydata.
        # Alternatively, we can check their properties. Let's see how they are defined.
        # axvline sets xdata to [x, x] and ydata to [0, 1] (in axes coords).
        # Let's inspect xdata/ydata or get_xdata()/get_ydata().
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        
        # If xdata has two identical values (and not [0, 1] which is the
        # default axes coordinate for ydata in axvline), then it is a vertical line.
        if len(xdata) == 2 and xdata[0] == xdata[1]:
            v_lines.append(xdata[0])
        elif len(ydata) == 2 and ydata[0] == ydata[1]:
            h_lines.append(ydata[0])
            
    assert sorted(v_lines) == [10.0, 20.0]
    assert sorted(h_lines) == [20.0, 30.0]
    
    plt.close(fig)

def test_add_grid_invalid_spacing():
    fig, ax = plt.subplots()
    with pytest.raises(ValueError):
        _add_grid(ax, x_min=0, x_max=10, y_min=0, y_max=10, grid_spacing=0)
    with pytest.raises(ValueError):
        _add_grid(ax, x_min=0, x_max=10, y_min=0, y_max=10, grid_spacing=-5)
    plt.close(fig)


@pytest.fixture
def sample_df():
    import pandas as pd
    return pd.DataFrame({
        "X": [0.0, 10.0, 20.0],
        "Y": [0.0, 10.0, 20.0],
        "Type": ["station", "station", "station"],
        "Node_Id": ["A", "B", "C"],
        "Links": ["-", "-", "-"]
    })


def test_create_survey_shows_grid_by_default(sample_df):
    from cave_sketch.survey.graphics.survey_plot import create_survey
    fig, ax = plt.subplots()
    create_survey(
        df=sample_df,
        rule_flag=False,
        north_flag=False,
        config={},
        rule_length=20,
        ax=ax
    )
    lines = [
        line for line in ax.lines
        if line.get_color() == "lightgray" and line.get_linestyle() == ":"
    ]
    assert len(lines) == 6, f"Expected 6 grid lines, got {len(lines)}"
    plt.close(fig)


def test_create_survey_no_grid_when_disabled(sample_df):
    from cave_sketch.survey.graphics.survey_plot import create_survey
    fig, ax = plt.subplots()
    create_survey(
        df=sample_df,
        rule_flag=False,
        north_flag=False,
        config={"show_grid": False},
        rule_length=20,
        ax=ax
    )
    lines = [
        line for line in ax.lines
        if line.get_color() == "lightgray" and line.get_linestyle() == ":"
    ]
    assert len(lines) == 0, f"Expected 0 grid lines, got {len(lines)}"
    plt.close(fig)


def test_create_survey_grid_spacing_adapts(sample_df):
    from cave_sketch.survey.graphics.survey_plot import create_survey
    fig, ax = plt.subplots()
    create_survey(
        df=sample_df,
        rule_flag=False,
        north_flag=False,
        config={"show_grid": True},
        rule_length=40,
        ax=ax
    )
    lines = [
        line for line in ax.lines
        if line.get_color() == "lightgray" and line.get_linestyle() == ":"
    ]
    assert len(lines) == 4, f"Expected 4 grid lines, got {len(lines)}"
    plt.close(fig)


def test_render_survey_respects_show_grid():
    from unittest.mock import patch

    from cave_sketch.dxf.models import CaveSurvey, SurveyPoint
    from cave_sketch.survey.config import SurveyConfig
    from cave_sketch.survey.renderer import render_survey

    survey = CaveSurvey(name="Sample", points=[
        SurveyPoint(id="1", x=0, y=0, links=["2"], point_type="station"),
        SurveyPoint(id="2", x=10, y=0, links=["1"], point_type="station"),
    ])
    config = SurveyConfig(rule_length=20, show_grid=False)
    
    with patch("cave_sketch.survey.graphics.survey_plot._add_grid") as mock_grid:
        fig = render_survey(survey=survey, config=config, section_survey=None)
        mock_grid.assert_not_called()
        plt.close(fig)

    config_enabled = SurveyConfig(rule_length=20, show_grid=True)
    with patch("cave_sketch.survey.graphics.survey_plot._add_grid") as mock_grid:
        fig = render_survey(survey=survey, config=config_enabled, section_survey=None)
        mock_grid.assert_called()
        plt.close(fig)


@patch("app.session.st")
def test_init_session_sets_show_grid_default(mock_st):
    from app.session import init_session
    class MockSessionState(dict):
        def __getattr__(self, name):
            return self[name]
        def __setattr__(self, name, value):
            self[name] = value

    mock_st.session_state = MockSessionState()
    init_session()
    assert mock_st.session_state.get("show_grid") is True


def test_draw_survey_passes_show_grid_to_config():
    from unittest.mock import patch

    from cave_sketch.survey import draw_survey
    
    with patch("cave_sketch.survey.survey.render_survey") as mock_render:
        draw_survey(
            title="Test UI Grid",
            rule_length=20,
            csv_map_path="tests/fixtures/test_survey.csv",
            config={"show_grid": False}
        )
        args, kwargs = mock_render.call_args
        config = kwargs.get("config") or args[1]
        assert config.show_grid is False


@patch("app.components.settings_panel.st")
def test_settings_panel_component_returns_show_grid(mock_st):
    from unittest.mock import MagicMock

    from app.components.settings_panel import settings_panel_component
    class MockSessionState(dict):
        def __getattr__(self, name):
            return self[name]
        def __setattr__(self, name, value):
            self[name] = value

    mock_st.session_state = MockSessionState(show_grid=True)
    mock_col = MagicMock()
    mock_st.columns.return_value = [mock_col, mock_col]
    mock_st.checkbox.return_value = True
    mock_st.number_input.return_value = 0.0
    
    res = settings_panel_component()
    assert "show_grid" in res
    assert res["show_grid"] is True

