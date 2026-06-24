from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

from cave_sketch.backend_renders import render_to_matplotlib
from cave_sketch.features.geometry import rotate_points
from cave_sketch.features.render_features import extract_features_from_df
from cave_sketch.survey.graphics.grid import _add_grid, snap_rule_to_grid
from cave_sketch.survey.graphics.north import _add_north_arrow
from cave_sketch.survey.graphics.placement import (
    compute_data_bbox,
    compute_dual_layout,
)
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
    x_coords = df["X"].values
    y_coords = df["Y"].values
    x_min, x_max, y_min, y_max = compute_data_bbox(x_coords, y_coords)
    x_span = x_max - x_min
    y_span = y_max - y_min
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
        offset = ref_scale * 0.005 if ref_scale > 0 else 0.1
        stations = df[(df["Type"] == "station") & (~df["Node_Id"].isin(excluded_nodes))]
        if not stations.empty:
            ax.scatter(stations["X"], stations["Y"], s=marker_size, color="red", zorder=5)
            for row in stations.itertuples(index=False):
                ax.text(
                    row.X - offset,
                    row.Y + offset,
                    row.Node_Id,
                    fontsize=text_size,
                    ha="right",
                    va="bottom",
                    color="black",
                    zorder=10,
                )

    # --- Rule and North arrow ---
    if rule_flag or north_flag:
        arrow_len = ref_scale * 0.07
        arrow_coord, rule_pos, axes_expansion = compute_dual_layout(
            x_coords, y_coords, rule_length, arrow_len, ref_scale
        )

        if config.get("show_grid", True):
            grid_spacing = rule_length / 2
            rule_pos_snapped = snap_rule_to_grid(rule_pos, grid_spacing, rule_orientation)
            dx = rule_pos_snapped[0] - rule_pos[0]
            dy = rule_pos_snapped[1] - rule_pos[1]
            rule_pos = rule_pos_snapped
            arrow_coord = (arrow_coord[0] + dx, arrow_coord[1] + dy)
        
        # Apply axis expansion if triggered by fallback
        if axes_expansion:
            if "y_min" in axes_expansion:
                ax.set_ylim(axes_expansion["y_min"], y_max)
            if "x_min" in axes_expansion:
                ax.set_xlim(axes_expansion["x_min"], x_max)

        if rule_flag:
            rule_w = ref_scale * 0.005
            _add_rule(
                ax=ax,
                x_start=rule_pos[0],
                y_start=rule_pos[1],
                orientation=rule_orientation,
                scale_len=rule_length,
                scale_width=rule_w,
                segment_len=rule_length / 5,
            )

        if north_flag:
            _add_north_arrow(
                ax=ax, coords=arrow_coord, arrow_len=arrow_len, rotation_deg=rotation_deg
            )

    ax.axis("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    # --- Grid overlay (covers the full visible extent of the axes) ---
    if config.get("show_grid", True):
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        _add_grid(ax, xlim[0], xlim[1], ylim[0], ylim[1], rule_length / 2)

    return ax


