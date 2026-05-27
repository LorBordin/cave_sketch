import pandas as pd
import pytest
from unittest.mock import patch
import matplotlib.pyplot as plt
from cave_sketch.survey import draw_survey
from cave_sketch.survey.config import SurveyConfig
from cave_sketch.survey.renderer import render_survey
from cave_sketch.dxf.models import CaveSurvey, SurveyPoint

@pytest.fixture
def sample_survey():
    return CaveSurvey(name="Sample", points=[
        SurveyPoint(id="1", x=0, y=0, links=["2"], point_type="station"),
        SurveyPoint(id="2", x=10, y=0, links=["1"], point_type="station"),
    ])

def test_draw_survey_section_only_title_and_no_north(tmp_path):
    """
    Generating a PDF with only the Section view (csv_map_path=None, csv_section_path provided) 
    produces a plot without a north symbol and with subplot title "Sezione".
    """
    csv_path = "tests/fixtures/test_survey.csv"
    output_pdf = tmp_path / "output.pdf"

    with patch("cave_sketch.survey.graphics.survey_plot._add_north_arrow") as mock_north:
        fig = draw_survey(
            title="Test Section Only",
            rule_length=20,
            csv_map_path=None,
            csv_section_path=csv_path,
            output_path=str(output_pdf)
        )
        
        axes = fig.get_axes()
        assert len(axes) == 1
        # Currently this will FAIL: title is "Pianta"
        assert axes[0].get_title() == "Sezione"
        
        # Currently this will FAIL: mock_north is called
        mock_north.assert_not_called()

def test_draw_survey_plan_only_title_and_north(tmp_path):
    """
    Generating a PDF with only the Plan view produces a plot with a north symbol 
    (if enabled) and subplot title "Pianta".
    """
    csv_path = "tests/fixtures/test_survey.csv"
    output_pdf = tmp_path / "output.pdf"

    with patch("cave_sketch.survey.graphics.survey_plot._add_north_arrow") as mock_north:
        fig = draw_survey(
            title="Test Plan Only",
            rule_length=20,
            csv_map_path=csv_path,
            csv_section_path=None,
            output_path=str(output_pdf)
        )
        
        axes = fig.get_axes()
        assert len(axes) == 1
        assert axes[0].get_title() == "Pianta"
        
        # Verify north arrow IS called
        mock_north.assert_called()

def test_render_survey_config_show_north(sample_survey):
    """
    Test that render_survey respects config.show_north.
    Note: This will fail until show_north is added to SurveyConfig.
    """
    try:
        config = SurveyConfig(rule_length=20, show_north=False)
    except TypeError:
        # Fallback for when show_north is not yet in SurveyConfig
        pytest.fail("SurveyConfig does not yet support show_north")
    
    with patch("cave_sketch.survey.graphics.survey_plot._add_north_arrow") as mock_north:
        render_survey(survey=sample_survey, config=config, section_survey=None)
        mock_north.assert_not_called()
