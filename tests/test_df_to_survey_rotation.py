import math

import pandas as pd

from cave_sketch.survey.survey import _df_to_survey


def test_df_to_survey_preserves_rotation() -> None:
    df = pd.DataFrame([
        {
            "Node_Id": "entrance_1",
            "Links": "-",
            "X": 10.0,
            "Y": 20.0,
            "Type": "B_entrance",
            "Rotation": 170.17,
        },
        {
            "Node_Id": "station_1",
            "Links": "station_2",
            "X": 15.0,
            "Y": 25.0,
            "Type": "station",
            "Rotation": 0.0,
        },
        {
            "Node_Id": "station_2",
            "Links": "station_1",
            "X": 20.0,
            "Y": 30.0,
            "Type": "station",
            "Rotation": float("nan"),
        },
    ])

    survey = _df_to_survey(df, name="test_survey")
    assert len(survey.points) == 3

    p0 = survey.points[0]
    assert p0.id == "entrance_1"
    assert math.isclose(p0.rotation, 170.17, rel_tol=1e-5)

    p1 = survey.points[1]
    assert p1.id == "station_1"
    assert p1.rotation == 0.0

    p2 = survey.points[2]
    assert p2.id == "station_2"
    assert p2.rotation == 0.0


def test_df_to_survey_without_rotation_column_defaults_to_zero() -> None:
    df = pd.DataFrame([
        {
            "Node_Id": "station_1",
            "Links": "-",
            "X": 10.0,
            "Y": 20.0,
            "Type": "station",
        }
    ])

    survey = _df_to_survey(df, name="test_survey")
    assert len(survey.points) == 1
    assert survey.points[0].rotation == 0.0
