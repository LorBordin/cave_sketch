# ruff: noqa: E501
import pandas as pd
import pytest

from cave_sketch.features.render_features import extract_features_from_df
from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP
from cave_sketch.style_icons import ICON_SHAPES


def _xy_points(icon):
    """All stroke vertices of a DataFrame-path icon as (x, y); coords are stored [y, x]."""
    return [(px, py) for stroke in icon["strokes"] for py, px in stroke]


def test_df_icon_point_becomes_ground_sized_strokes():
    df = pd.DataFrame([
        {"Node_Id": "B_blocks_0", "X": 10.0, "Y": 20.0, "Links": "-", "Type": "B_blocks", "Rotation": 0.0},
    ])
    features = extract_features_from_df(df)
    assert features["points"] == []
    (icon,) = features["icons"]
    assert icon["type"] == "B_blocks"
    assert icon["color"] == STYLE_MAP["B_blocks"]["color"]
    assert icon["weight"] == ICON_LINE_WEIGHT == STYLE_MAP["L_wall"]["weight"]
    assert len(icon["strokes"]) == len(ICON_SHAPES["blocks"])
    xs = [x for x, _ in _xy_points(icon)]
    ys = [y for _, y in _xy_points(icon)]
    size = STYLE_MAP["B_blocks"]["size_m"]
    assert max(max(xs) - min(xs), max(ys) - min(ys)) == pytest.approx(size, abs=1e-2)
    assert (max(xs) + min(xs)) / 2 == pytest.approx(10.0, abs=1e-2)
    assert (max(ys) + min(ys)) / 2 == pytest.approx(20.0, abs=1e-2)


def test_df_icon_uses_rotation_column():
    # Rotation 270 CCW turns the arrow from north (+Y) to east (+X).
    df = pd.DataFrame([
        {"Node_Id": "B_water-flow_0", "X": 0.0, "Y": 0.0, "Links": "-", "Type": "B_water-flow", "Rotation": 270.0},
    ])
    (icon,) = extract_features_from_df(df)["icons"]
    tip = max(_xy_points(icon), key=lambda p: p[0])
    assert tip == pytest.approx((STYLE_MAP["B_water-flow"]["size_m"] / 2, 0.0), abs=1e-9)


@pytest.mark.parametrize("rotation", [None, float("nan")])
def test_df_icon_missing_or_nan_rotation_means_zero(rotation):
    row = {"Node_Id": "B_entrance_0", "X": 0.0, "Y": 0.0, "Links": "-", "Type": "B_entrance"}
    if rotation is not None:
        row["Rotation"] = rotation
    (icon,) = extract_features_from_df(pd.DataFrame([row]))["icons"]
    tip = max(_xy_points(icon), key=lambda p: p[1])
    assert tip == pytest.approx((0.0, STYLE_MAP["B_entrance"]["size_m"] / 2))


def test_df_plain_marker_points_unchanged():
    df = pd.DataFrame([{"Node_Id": "B_ice_0", "X": 1.0, "Y": 2.0, "Links": "-", "Type": "B_ice"}])
    features = extract_features_from_df(df)
    assert features["icons"] == []
    (point,) = features["points"]
    assert point["marker"] == STYLE_MAP["B_ice"]["marker"]


def _water_flow_df(rows):
    return pd.DataFrame(
        [{"Node_Id": nid, "X": x, "Y": y, "Links": links, "Type": "L_water-flow"} for nid, x, y, links in rows]
    )


def test_df_water_flow_line_gets_one_chevron_per_segment_pointing_downstream():
    df = _water_flow_df([
        ("0P0", 0.0, 0.0, "0P1"),
        ("0P1", 10.0, 0.0, "0P0-0P2"),
        ("0P2", 10.0, 10.0, "0P1"),
    ])
    features = extract_features_from_df(df)
    assert len(features["lines"]) == 4  # unchanged: both directions are still drawn
    chevrons = features["icons"]
    assert len(chevrons) == 2
    # Segment 1 runs east: chevron apex (unit (0, 0.25)) is its easternmost vertex.
    apex1 = chevrons[0]["strokes"][0][1]
    assert apex1 == pytest.approx([0.0, 5.0 + 0.25 * STYLE_MAP["L_water-flow"]["decoration_size_m"]])
    # Segment 2 runs north: apex is its northernmost vertex.
    apex2 = chevrons[1]["strokes"][0][1]
    assert apex2 == pytest.approx([5.0 + 0.25 * STYLE_MAP["L_water-flow"]["decoration_size_m"], 10.0])
    assert all(c["weight"] == ICON_LINE_WEIGHT for c in chevrons)
    assert all(c["color"] == STYLE_MAP["L_water-flow"]["color"] for c in chevrons)


def test_df_single_segment_gets_exactly_one_chevron():
    df = _water_flow_df([("3P0", 0.0, 0.0, "3P1"), ("3P1", 0.0, 5.0, "3P0")])
    assert len(extract_features_from_df(df)["icons"]) == 1


def test_df_two_polylines_do_not_interfere():
    df = _water_flow_df([
        ("0P0", 0.0, 0.0, "0P1"), ("0P1", 1.0, 0.0, "0P0"),
        ("1P0", 0.0, 5.0, "1P1"), ("1P1", 1.0, 5.0, "1P0"),
    ])
    assert len(extract_features_from_df(df)["icons"]) == 2


def test_df_missing_neighbor_is_skipped():
    df = _water_flow_df([("0P0", 0.0, 0.0, "0P1")])
    assert extract_features_from_df(df)["icons"] == []


def test_df_other_lines_get_no_decoration():
    df = pd.DataFrame([
        {"Node_Id": "0P0", "X": 0.0, "Y": 0.0, "Links": "0P1", "Type": "L_wall"},
        {"Node_Id": "0P1", "X": 1.0, "Y": 0.0, "Links": "0P0", "Type": "L_wall"},
    ])
    assert extract_features_from_df(df)["icons"] == []
