import math

import pandas as pd

from cave_sketch.survey.merger import _compute_displacement


def _bbox(df: pd.DataFrame, dx: float = 0.0, dy: float = 0.0):
    return (
        float(df["X"].min() + dx),
        float(df["X"].max() + dx),
        float(df["Y"].min() + dy),
        float(df["Y"].max() + dy),
    )


def _bbox_dist(b1, b2) -> float:
    dx = max(0.0, b1[0] - b2[1], b2[0] - b1[1])
    dy = max(0.0, b1[2] - b2[3], b2[2] - b1[3])
    return math.hypot(dx, dy)


def test_displacement_padding_degenerate_and_normal():
    # Degenerate single point parent: diagonal = 0 -> padding floor = 1.0 m
    parent_deg = pd.DataFrame({
        "Node_Id": ["1"],
        "X": [0.0],
        "Y": [0.0],
        "Links": ["-"],
        "Type": ["station"],
    })
    child = pd.DataFrame({
        "Node_Id": ["1"],
        "X": [0.0],
        "Y": [0.0],
        "Links": ["-"],
        "Type": ["station"],
    })

    dx, dy = _compute_displacement(parent_deg, child, anchor_dx=0.0, anchor_dy=0.0)
    p_box = _bbox(parent_deg)
    c_box = _bbox(child, dx, dy)
    dist = _bbox_dist(p_box, c_box)
    assert dist >= 1.0 - 1e-6

    # Normal parent: 60x80 box -> diagonal = 100 -> padding = 10.0 m
    parent_normal = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 60.0],
        "Y": [0.0, 80.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"],
    })
    dx_norm, dy_norm = _compute_displacement(parent_normal, child, anchor_dx=0.0, anchor_dy=0.0)
    p_box_norm = _bbox(parent_normal)
    c_box_norm = _bbox(child, dx_norm, dy_norm)
    dist_norm = _bbox_dist(p_box_norm, c_box_norm)
    assert dist_norm >= 10.0 - 1e-6


def test_displacement_wide_flat_parent_prefers_below():
    # Wide/flat parent: width = 100, height = 10
    parent = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 100.0],
        "Y": [0.0, 10.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"],
    })
    child = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 50.0],
        "Y": [0.0, 50.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"],
    })
    # Simple alignment places child at anchor (0, 0)
    dx, dy = _compute_displacement(parent, child, anchor_dx=0.0, anchor_dy=0.0)
    # Placing child to the right would expand width from 100 to ~160.
    # Placing child below preserves width at 100, yielding smaller combined area.
    assert dy < -10.0
    p_box = _bbox(parent)
    c_box = _bbox(child, dx, dy)
    assert _bbox_dist(p_box, c_box) >= 0.10 * math.hypot(100.0, 10.0) - 1e-6


def test_displacement_tall_narrow_parent_prefers_right():
    # Tall/narrow parent: width = 10, height = 100
    parent = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 100.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"],
    })
    child = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 50.0],
        "Y": [0.0, 50.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"],
    })
    # Simple alignment puts child at anchor (0, 0)
    dx, dy = _compute_displacement(parent, child, anchor_dx=0.0, anchor_dy=0.0)
    # Placing child to the right preserves height at 100, yielding smaller combined area.
    assert dx > 10.0
    p_box = _bbox(parent)
    c_box = _bbox(child, dx, dy)
    assert _bbox_dist(p_box, c_box) >= 0.10 * math.hypot(10.0, 100.0) - 1e-6


def test_displacement_intermediate_angle_wins():
    # A case where sliding diagonally cuts the corner and achieves smaller area
    parent = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 50.0],
        "Y": [0.0, 50.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"],
    })
    child = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 30.0],
        "Y": [0.0, 30.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"],
    })
    # Simple alignment at (25.0, 50.0)
    dx, dy = _compute_displacement(parent, child, anchor_dx=25.0, anchor_dy=50.0)
    disp_x = dx - 25.0
    disp_y = dy - 50.0
    # Both disp_x > 0 and disp_y < 0 (intermediate angle between 0 and -90 deg)
    assert disp_x > 0.1
    assert disp_y < -0.1
    angle_deg = math.degrees(math.atan2(disp_y, disp_x))
    assert -85 <= angle_deg <= -5

    p_box = _bbox(parent)
    c_box = _bbox(child, dx, dy)
    assert _bbox_dist(p_box, c_box) >= 0.10 * math.hypot(50.0, 50.0) - 1e-6


def test_displacement_clears_padding_and_deterministic():
    parent = pd.DataFrame({
        "Node_Id": ["1", "2", "3"],
        "X": [10.0, 40.0, 25.0],
        "Y": [20.0, 30.0, 50.0],
        "Links": ["-", "-", "-"],
        "Type": ["station", "station", "station"],
    })
    child = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 15.0],
        "Y": [0.0, 10.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"],
    })
    # Call twice to ensure determinism
    res1 = _compute_displacement(parent, child, anchor_dx=25.0, anchor_dy=30.0)
    res2 = _compute_displacement(parent, child, anchor_dx=25.0, anchor_dy=30.0)
    assert res1 == res2

    p_box = _bbox(parent)
    c_box = _bbox(child, res1[0], res1[1])
    diag = math.hypot(
        parent["X"].max() - parent["X"].min(), parent["Y"].max() - parent["Y"].min()
    )
    padding = max(1.0, 0.10 * diag)
    assert _bbox_dist(p_box, c_box) >= padding - 1e-6


def test_displacement_connector_rendering():
    import matplotlib.pyplot as plt

    from cave_sketch.features.render_features import extract_features_from_df
    from cave_sketch.survey.graphics.survey_plot import create_survey

    df = pd.DataFrame({
        "Node_Id": ["1", "2", "CONN_1"],
        "X": [0.0, 10.0, 0.0],
        "Y": [0.0, 0.0, 0.0],
        "Links": ["-", "-", "2"],
        "Type": ["station", "station", "connector"],
    })

    features = extract_features_from_df(df)
    # Line features must include the connector
    conn_lines = [line for line in features["lines"] if line.get("dash") is not None]
    assert len(conn_lines) == 1
    assert conn_lines[0]["color"] == "firebrick"
    assert conn_lines[0]["dash"] == [8, 4]
    assert conn_lines[0]["weight"] == 1.5

    # Check matplotlib rendering: only stations get text labels
    fig, ax = plt.subplots()
    create_survey(df, rule_flag=False, north_flag=False, config={}, ax=ax)
    texts = [t.get_text() for t in ax.texts]
    assert "1" in texts
    assert "2" in texts
    assert "CONN_1" not in texts
    plt.close(fig)

