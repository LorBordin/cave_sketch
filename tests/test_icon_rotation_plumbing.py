# ruff: noqa: E501
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import cave_sketch.survey.graphics.survey_plot as survey_plot
from cave_sketch.satellite_view.map import export_map_data
from cave_sketch.survey.graphics.survey_plot import create_survey

LAT, LON = 46.5, 11.3


def test_export_map_data_writes_node_rotation(tmp_path):
    df = pd.DataFrame([
        {"Node_Id": "B_water-flow_0", "Links": "-", "X": 0.0, "Y": 0.0, "Type": "B_water-flow",
         "Rotation": 280.0, "Latitude": LAT, "Longitude": LON},
        {"Node_Id": "1", "Links": "-", "X": 1.0, "Y": 1.0, "Type": "station",
         "Rotation": float("nan"), "Latitude": LAT, "Longitude": LON},
    ])
    out = tmp_path / "m.json"
    export_map_data(df, "M", str(out))
    nodes = json.loads(out.read_text())["nodes"]
    assert nodes["B_water-flow_0"]["rotation"] == 280.0
    assert nodes["1"]["rotation"] == 0.0


def test_export_map_data_without_rotation_column(tmp_path):
    df = pd.DataFrame([{"Node_Id": "1", "Links": "-", "X": 0.0, "Y": 0.0, "Type": "station",
                        "Latitude": LAT, "Longitude": LON}])
    out = tmp_path / "m.json"
    export_map_data(df, "M", str(out))
    assert json.loads(out.read_text())["nodes"]["1"]["rotation"] == 0.0


def test_create_survey_view_rotation_also_rotates_icons(monkeypatch):
    captured = {}
    real_extract = survey_plot.extract_features_from_df

    def spy(df, *args, **kwargs):
        captured["df"] = df
        return real_extract(df, *args, **kwargs)

    monkeypatch.setattr(survey_plot, "extract_features_from_df", spy)
    df = pd.DataFrame([
        {"Node_Id": "0", "Links": "-", "X": 0.0, "Y": 0.0, "Type": "station", "Rotation": 0.0},
        {"Node_Id": "B_water-flow_0", "Links": "-", "X": 10.0, "Y": 10.0, "Type": "B_water-flow", "Rotation": 280.0},
    ])
    fig, ax = plt.subplots()
    create_survey(df, rule_flag=False, north_flag=False, config={}, rotation_deg=30.0, ax=ax)
    assert captured["df"]["Rotation"].tolist() == [30.0, 310.0]
    assert df["Rotation"].tolist() == [0.0, 280.0]  # caller's frame untouched
    plt.close(fig)
