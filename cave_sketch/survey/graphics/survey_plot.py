from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from cave_sketch.backend_renders import render_to_matplotlib
from cave_sketch.features.geometry import rotate_points
from cave_sketch.features.render_features import extract_features_from_df
from cave_sketch.survey.graphics.north import _add_north_arrow
from cave_sketch.survey.graphics.rule import _add_rule


def create_survey(
    df: pd.DataFrame,
    rule_flag: bool,
    north_flag: bool,
    config: dict,
    rotation_deg: float = 0,
    rule_orientation: str = "horizontal",
    rule_length: float = 20,
    excluded_nodes: Optional[List[str]] = None,
    ax=None,
):
    """Draw survey on Matplotlib using backend renderer (non-destructive rotation)."""

    if ax is None:
        ax = plt.gca()

    # --- Make a copy to avoid mutating the original ---
    df = df.copy()
    if excluded_nodes is None:
        excluded_nodes = []

    # --- Apply rotation safely using shared helper ---
    if rotation_deg != 0:
        points = df[["X", "Y"]].values
        center: Tuple[float, float] = (float(df["X"].mean()), float(df["Y"].mean()))
        df[["X", "Y"]] = rotate_points(points, center, rotation_deg)

    # --- Compute scale parameters ---
    x_span = df["X"].max() - df["X"].min()
    y_span = df["Y"].max() - df["Y"].min()
    ref_scale = max(x_span, y_span)
    mz = config.get("marker_zoom", 10)
    tz = config.get("text_zoom", 10)
    marker_size = 300 / ref_scale * 10**mz
    text_size = 300 / ref_scale * 10**tz

    # --- Extract features (using your backend-agnostic system) ---
    features = extract_features_from_df(df, excluded_nodes)

    # --- Render using Matplotlib backend ---
    render_to_matplotlib(
        features,
        ax,
        layer_name="Survey",
        config={"line_width_zoom": config.get("line_width_zoom", 10), "ref_scale": ref_scale},
    )

    # --- Stations ---
    if config.get("show_details", True):
        for _, row in df.iterrows():
            if row["Type"] == "station" and row["Node_Id"] not in excluded_nodes:
                ax.scatter(row["X"], row["Y"], s=marker_size, color="red", zorder=5)
                ax.text(
                    row["X"],
                    row["Y"],
                    row["Node_Id"],
                    fontsize=text_size,
                    ha="right",
                    va="bottom",
                    color="black",
                )

    # --- Rule and North arrow as before ---
    if rule_flag:
        xs, ys = float(df["X"].min()), float(df["Y"].min())
        if rule_orientation == "horizontal":
            ys -= ref_scale * 0.1
        else:
            xs -= ref_scale * 0.03
        rule_w = ref_scale * 0.005
        _add_rule(
            ax=ax,
            x_start=xs,
            y_start=ys,
            orientation=rule_orientation,
            scale_len=rule_length,
            scale_width=rule_w,
            segment_len=rule_length / 5,
        )

    if north_flag:
        coord: Tuple[float, float] = (
            float(df["X"].min() + rule_length / 2),
            float(df["Y"].min() + ref_scale * 0.025),
        )
        arrow_len = ref_scale * 0.07
        _add_north_arrow(ax=ax, coords=coord, arrow_len=arrow_len, rotation_deg=rotation_deg)

    ax.axis("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    return ax
