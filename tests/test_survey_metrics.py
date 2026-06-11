import pandas as pd
import pytest

from cave_sketch.survey.metrics import compute_total_depth, compute_total_length


def test_compute_total_length_two_connected():
    df = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 3.0],
        "Y": [0.0, 4.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })
    # Distance should be 5.0
    assert compute_total_length(df) == pytest.approx(5.0)


def test_compute_total_length_three_station_chain():
    df = pd.DataFrame({
        "Node_Id": ["1", "2", "3"],
        "X": [0.0, 3.0, 3.0],
        "Y": [0.0, 4.0, 10.0],
        "Links": ["2", "1-3", "2"],
        "Type": ["station", "station", "station"]
    })
    # Legs: 1-2 (length 5.0) and 2-3 (length 6.0). Total: 11.0
    assert compute_total_length(df) == pytest.approx(11.0)


def test_compute_total_length_bidirectional_deduplicated():
    df = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })
    # Even if A links to B and B links to A, should only count once: 10.0
    assert compute_total_length(df) == pytest.approx(10.0)


def test_compute_total_length_excludes_polylines_and_blocks():
    df = pd.DataFrame({
        "Node_Id": ["1", "2", "1P1", "station_block"],
        "X": [0.0, 10.0, 5.0, 20.0],
        "Y": [0.0, 0.0, 5.0, 20.0],
        "Links": ["2-1P1", "1", "1", "-"],
        "Type": ["station", "station", "L_wall", "block"]
    })
    # Only 1 and 2 are numeric. 1P1 and station_block are excluded.
    # So the only leg between numeric nodes is 1-2 (length 10.0).
    assert compute_total_length(df) == pytest.approx(10.0)


def test_compute_total_length_empty_or_single_station():
    df_empty = pd.DataFrame(columns=["Node_Id", "Links", "X", "Y", "Type"])
    assert compute_total_length(df_empty) == 0.0

    df_single = pd.DataFrame({
        "Node_Id": ["1"],
        "X": [10.0],
        "Y": [20.0],
        "Links": ["-"],
        "Type": ["station"]
    })
    assert compute_total_length(df_single) == 0.0


def test_compute_total_depth_three_stations():
    df = pd.DataFrame({
        "Node_Id": ["1", "2", "3"],
        "X": [0.0, 10.0, 20.0],
        "Y": [5.0, 15.0, 2.0],
        "Links": ["-", "-", "-"],
        "Type": ["station", "station", "station"]
    })
    # Y range: max is 15.0, min is 2.0. Depth: 13.0
    assert compute_total_depth(df) == pytest.approx(13.0)


def test_compute_total_depth_excludes_polylines():
    df = pd.DataFrame({
        "Node_Id": ["1", "2", "1P1"],
        "X": [0.0, 10.0, 20.0],
        "Y": [5.0, 15.0, 100.0],
        "Links": ["-", "-", "-"],
        "Type": ["station", "station", "L_wall"]
    })
    # 1P1 has Y=100.0 but should be excluded.
    # Numeric stations 1 and 2: Y=5.0 and Y=15.0. Depth: 10.0
    assert compute_total_depth(df) == pytest.approx(10.0)


def test_compute_total_depth_empty_or_single_station():
    df_empty = pd.DataFrame(columns=["Node_Id", "Links", "X", "Y", "Type"])
    assert compute_total_depth(df_empty) == 0.0

    df_single = pd.DataFrame({
        "Node_Id": ["1"],
        "X": [10.0],
        "Y": [20.0],
        "Links": ["-"],
        "Type": ["station"]
    })
    assert compute_total_depth(df_single) == 0.0

    # Non-empty, but no numeric stations
    df_no_numeric = pd.DataFrame({
        "Node_Id": ["1P1", "2P2"],
        "X": [10.0, 20.0],
        "Y": [20.0, 30.0],
        "Links": ["-", "-"],
        "Type": ["L_wall", "R_wall"]
    })
    assert compute_total_depth(df_no_numeric) == 0.0


def test_compute_total_depth_none_when_no_section():
    assert compute_total_depth(None) is None
