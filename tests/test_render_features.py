import pandas as pd
import pytest
from cave_sketch.features.render_features import extract_features_from_df

def test_extract_features_basic():
    df = pd.DataFrame([
        {"Node_Id": "A", "X": 0.0, "Y": 0.0, "Links": "B", "Type": "L_wall"},
        {"Node_Id": "B", "X": 10.0, "Y": 0.0, "Links": "A-C", "Type": "L_wall"},
        {"Node_Id": "C", "X": 10.0, "Y": 10.0, "Links": "B", "Type": "L_wall"},
    ])
    
    features = extract_features_from_df(df)
    
    # 4 lines: A->B, B->A, B->C, C->B
    assert len(features["lines"]) == 4
    assert len(features["polygons"]) == 0
    assert len(features["points"]) == 0
    
    # Check shape of features
    for line in features["lines"]:
        assert set(line.keys()) == {"coords", "color", "weight", "dash", "popup"}
        
    # Verify exact coords mapping
    # A->B
    assert features["lines"][0]["coords"] == [[0.0, 0.0], [0.0, 10.0]]  # [Y, X] style
    # B->A
    assert features["lines"][1]["coords"] == [[0.0, 10.0], [0.0, 0.0]]
    # B->C
    assert features["lines"][2]["coords"] == [[0.0, 10.0], [10.0, 10.0]]
    # C->B
    assert features["lines"][3]["coords"] == [[10.0, 10.0], [0.0, 10.0]]

def test_extract_features_exclusion():
    df = pd.DataFrame([
        {"Node_Id": "A", "X": 0.0, "Y": 0.0, "Links": "B", "Type": "L_wall"},
        {"Node_Id": "B", "X": 10.0, "Y": 0.0, "Links": "A-C", "Type": "L_wall"},
        {"Node_Id": "C", "X": 10.0, "Y": 10.0, "Links": "B", "Type": "L_wall"},
    ])
    
    features = extract_features_from_df(df, excluded_nodes=["B"])
    # If B is excluded, A has link "B" (excluded), C has link "B" (excluded).
    # Since B itself is excluded, no lines should be generated.
    assert len(features["lines"]) == 0

def test_extract_features_missing_neighbor():
    df = pd.DataFrame([
        {"Node_Id": "A", "X": 0.0, "Y": 0.0, "Links": "Z", "Type": "L_wall"},
    ])
    
    features = extract_features_from_df(df)
    # Z is missing, so no line should be generated
    assert len(features["lines"]) == 0
