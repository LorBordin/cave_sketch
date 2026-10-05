# ruff: noqa: E501
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.collections import LineCollection

from cave_sketch.backend_renders import render_to_matplotlib
from cave_sketch.features.render_features import extract_features_from_df
from cave_sketch.style import STYLE_MAP
from cave_sketch.style_icons import ICON_SHAPES


def _df_wall_and_block():
    return pd.DataFrame([
        {"Node_Id": "0P0", "X": 0.0, "Y": 0.0, "Links": "0P1", "Type": "L_wall", "Rotation": 0.0},
        {"Node_Id": "0P1", "X": 10.0, "Y": 0.0, "Links": "0P0", "Type": "L_wall", "Rotation": 0.0},
        {"Node_Id": "B_blocks_0", "X": 5.0, "Y": 5.0, "Links": "-", "Type": "B_blocks", "Rotation": 0.0},
    ])


@pytest.mark.parametrize("config", [None, {"line_width_zoom": 10, "ref_scale": 2.0}])
def test_matplotlib_icon_linewidth_equals_wall_linewidth(config):
    fig, ax = plt.subplots()
    render_to_matplotlib(extract_features_from_df(_df_wall_and_block()), ax, config=config)
    walls, icons = [c for c in ax.collections if isinstance(c, LineCollection)]
    assert len(icons.get_segments()) == len(ICON_SHAPES["blocks"])
    assert set(icons.get_linewidths()) == {walls.get_linewidths()[0]}
    assert icons.get_zorder() > walls.get_zorder()
    plt.close(fig)


def test_matplotlib_icon_strokes_are_in_data_coordinates():
    fig, ax = plt.subplots()
    render_to_matplotlib(extract_features_from_df(_df_wall_and_block()), ax)
    icons = [c for c in ax.collections if isinstance(c, LineCollection)][1]
    xs = [x for seg in icons.get_segments() for x, _ in seg]
    assert min(xs) == pytest.approx(5.0 - STYLE_MAP["B_blocks"]["size_m"] / 2, abs=1e-2)
    plt.close(fig)
