import matplotlib.pyplot as plt
import pandas as pd

from cave_sketch.features.render_features import extract_features_from_df
from cave_sketch.survey.config import SurveyConfig
from cave_sketch.survey.graphics.survey_plot import create_survey


def test_survey_config_has_show_centerline():
    config = SurveyConfig()
    assert hasattr(config, "show_centerline")
    assert config.show_centerline is True


def test_extract_features_with_show_centerline_true():
    df = pd.DataFrame([
        {"Node_Id": "A", "X": 0.0, "Y": 0.0, "Links": "B", "Type": "station"},
        {"Node_Id": "B", "X": 10.0, "Y": 0.0, "Links": "A", "Type": "station"},
    ])
    features = extract_features_from_df(df, show_centerline=True)
    # Since type is "station" and show_centerline is True, should extract the lines
    assert len(features["lines"]) == 2
    assert features["lines"][0]["color"] == "black"  # station color


def test_extract_features_with_show_centerline_false():
    df = pd.DataFrame([
        {"Node_Id": "A", "X": 0.0, "Y": 0.0, "Links": "B", "Type": "station"},
        {"Node_Id": "B", "X": 10.0, "Y": 0.0, "Links": "A", "Type": "station"},
        {"Node_Id": "C", "X": 0.0, "Y": 0.0, "Links": "D", "Type": "L_wall"},
        {"Node_Id": "D", "X": 10.0, "Y": 0.0, "Links": "C", "Type": "L_wall"},
    ])
    features = extract_features_from_df(df, show_centerline=False)
    # The 'station' lines should be excluded, but L_wall lines should be present
    assert len(features["lines"]) == 2
    # Verify they are wall type (color is red)
    for line in features["lines"]:
        assert line["color"] == "red"


def test_station_markers_and_centerline_rendering():
    df = pd.DataFrame([
        {"Node_Id": "A", "X": 0.0, "Y": 0.0, "Links": "B", "Type": "station"},
        {"Node_Id": "B", "X": 10.0, "Y": 0.0, "Links": "A", "Type": "station"},
    ])

    # Case 1: show_centerline=False, show_details=True -> markers and centerline hidden
    fig, ax = plt.subplots()
    create_survey(
        df=df,
        rule_flag=False,
        north_flag=False,
        config={"show_details": True, "show_centerline": False},
        ax=ax
    )
    # Checks that station texts are suppressed
    assert len(ax.texts) == 0
    # Check that scatter points (markers) are not drawn
    assert len(ax.collections) == 0
    plt.close(fig)

    # Case 2: show_centerline=True, show_details=True -> station markers should be drawn
    fig, ax = plt.subplots()
    create_survey(
        df=df,
        rule_flag=False,
        north_flag=False,
        config={"show_details": True, "show_centerline": True},
        ax=ax
    )
    assert len(ax.texts) == 2
    assert len(ax.collections) == 2
    plt.close(fig)

    # Case 3: show_centerline=True, show_details=False -> centerline drawn, station markers hidden
    fig, ax = plt.subplots()
    create_survey(
        df=df,
        rule_flag=False,
        north_flag=False,
        config={"show_details": False, "show_centerline": True},
        ax=ax
    )
    assert len(ax.texts) == 0
    assert len(ax.collections) == 1
    plt.close(fig)
