from typing import Dict, List, Optional
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from cave_sketch.survey.graphics.north import _add_north_arrow
from cave_sketch.survey.graphics.rule import _add_rule
from cave_sketch.style import STYLE_MAP

def create_survey(
    df: pd.DataFrame,
    rule_flag: bool,
    north_flag: bool,
    config: Dict,
    rotation_deg: int = 0,
    rule_orientation: str = "horizontal",
    rule_length: Optional[float] = 20,
    excluded_nodes: Optional[List] = None,
    ax: Optional[Axes] = None,
):
    if ax is None:
        ax = plt.gca()

    if excluded_nodes is None:
        excluded_nodes = []

    if rotation_deg != 0:
        theta = np.radians(rotation_deg)
        cos_t, sin_t = np.cos(theta), np.sin(theta)
        x0, y0 = df['X'].mean(), df['Y'].mean()
        Xs, Ys = df['X'] - x0, df['Y'] - y0
        df['X'] = cos_t*Xs - sin_t*Ys + x0
        df['Y'] = sin_t*Xs + cos_t*Ys + y0

    x_span = df['X'].max() - df['X'].min()
    y_span = df['Y'].max() - df['Y'].min()
    ref_scale = max(x_span, y_span)
    mz = config.get("marker_zoom", 10)
    tz = config.get("text_zoom", 10)
    lz = config.get("line_width_zoom", 10)
    marker_size = 300/ref_scale * 10**mz
    text_size = 300/ref_scale * 10**tz
    lw_thin = 15/ref_scale * 10**lz
    lw_thick = 30/ref_scale * 10**lz

    for _, row in df.iterrows():
        nid, x, y, links, typ = row["Node_Id"], row["X"], row["Y"], row["Links"], row["Type"]

        if nid in excluded_nodes:
            continue

        if typ == "station" and config.get("show_details", True):
            ax.scatter(x, y, s=marker_size, color="red")
            ax.text(x, y, nid, fontsize=text_size, ha="right", va="bottom", color="black")

        if pd.notna(links) and links != "-":
            neighbors = [nbr.strip() for nbr in links.split("-") if nbr.strip() and nbr not in excluded_nodes]
            coords = []
            for nbr in neighbors:
                nbr_row = df[df["Node_Id"] == nbr]
                if nbr_row.empty:
                    continue
                x2, y2 = nbr_row.iloc[0][['X', 'Y']]
                coords.append((x2, y2))
                if STYLE_MAP.get(typ, {}).get("type", "line") == "line":
                    cfg = STYLE_MAP.get(typ, STYLE_MAP["L_wall"])
                    ax.plot([x, x2], [y, y2],
                            color=cfg["color"],
                            linestyle=cfg["linestyle"],
                            linewidth=lw_thick)

            # Draw area (A_water)  - NOT WORKING!
            if STYLE_MAP.get(typ, {}).get("type") == "area" and len(coords) >= 3:
                print("INSIDE")
                coords.insert(0, (x, y))  # start from current node
                xs, ys = zip(*coords)
                ax.fill(xs, ys, color=STYLE_MAP[typ]["color"], alpha=STYLE_MAP[typ]["alpha"])

    if rule_flag:
        if rule_orientation == "horizontal":
            xs = df['X'].min()
            ys = df['Y'].min() - ref_scale * 0.1
        else:
            xs = df['X'].min() - ref_scale * 0.03
            ys = df['Y'].min()
        rule_w = ref_scale * 0.005
        _add_rule(ax=ax, x_start=xs, y_start=ys,
                  orientation=rule_orientation,
                  scale_len=rule_length,
                  scale_width=rule_w,
                  segment_len=rule_length // 5)

    if north_flag:
        coord = (xs + rule_length / 2, ys + ref_scale * 0.025)
        arrow_len = ref_scale * 0.07
        _add_north_arrow(ax=ax, coords=coord, arrow_len=arrow_len, rotation_deg=rotation_deg)

    ax.axis('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    return ax
