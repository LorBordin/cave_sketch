from typing import Dict, List, Optional
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cave_sketch.graphics.north import _add_north_arrow
from cave_sketch.graphics.rule import _add_rule


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

    # --- Rotation (unchanged) ---
    if rotation_deg != 0:
        theta = np.radians(rotation_deg)
        cos_t, sin_t = np.cos(theta), np.sin(theta)
        x0, y0 = df['X'].mean(), df['Y'].mean()
        Xs, Ys = df['X'] - x0, df['Y'] - y0
        df['X'] = cos_t*Xs - sin_t*Ys + x0
        df['Y'] = sin_t*Xs + cos_t*Ys + y0

    # --- Reference scale & zooms (unchanged) ---
    x_span = df['X'].max() - df['X'].min()
    y_span = df['Y'].max() - df['Y'].min()
    ref_scale = max(x_span, y_span)
    mz = config.get("marker_zoom", 10)
    tz = config.get("text_zoom", 10)
    lz = config.get("line_width_zoom", 10)
    marker_size   = 300/ref_scale * 10**mz
    text_size     = 300/ref_scale * 10**tz
    lw_thin       =  15/ref_scale * 10**lz
    lw_thick      =  30/ref_scale * 10**lz

    # --- Style map by Type ---
    style_map = {
        "station":    {"color":"gray",       "linestyle":"solid",      "lw":lw_thin},
        "L_wall":     {"color":"black",      "linestyle":"solid",      "lw":lw_thick},
        "L_chimney":  {"color":"indigo",      "linestyle":(0,(1,2)),    "lw":lw_thick},  # dash pattern 1 on,2 off
        "L_border":   {"color":"green",      "linestyle":"solid",      "lw":lw_thick},
        "L_pit":      {"color":"indigo",      "linestyle":(0,(1,1)),    "lw":lw_thick},  # dash pattern 1 on,1 off
    }

    # --- Draw all nodes & links ---
    for _, row in df.iterrows():
        nid, x, y, links, typ = row["Node_Id"], row["X"], row["Y"], row["Links"], row["Type"]

        if nid in excluded_nodes:
            continue

        # draw the node marker & label (only for stations if show_details)
        if typ == "station" and config.get("show_details", True):
            ax.scatter(x, y, s=marker_size, color="red")
            ax.text(x, y, nid,
                    fontsize=text_size, ha="right", va="bottom", color="black")

        # draw each link
        if pd.notna(links) and links != "-":
            for nbr in links.split("-"):
                nbr = nbr.strip()
                if not nbr or nbr in excluded_nodes:
                    continue
                nbr_row = df[df["Node_Id"]==nbr]
                if nbr_row.empty:
                    continue

                x2, y2 = nbr_row.iloc[0][['X','Y']]
                # pick style by this row's Type (you could also decide per-segment or per-target)
                cfg = style_map.get(typ, style_map["L_wall"])
                ax.plot([x, x2], [y, y2],
                        color=cfg["color"],
                        linestyle=cfg["linestyle"],
                        linewidth=cfg["lw"])

    # --- Add rule & north arrow (unchanged) ---
    if rule_flag:
        if rule_orientation=="horizontal":
            xs = df['X'].min()
            ys = df['Y'].min() - ref_scale*0.1
        else:
            xs = df['X'].min() - ref_scale*0.03
            ys = df['Y'].min()
        rule_w = ref_scale*0.005
        _add_rule(
            ax=ax, x_start=xs, y_start=ys, 
            orientation=rule_orientation,
            scale_len=rule_length, 
            scale_width=rule_w, 
            segment_len=rule_length//5
        )

    if north_flag:
        # reuse xs, ys from rule
        coord = (xs + rule_length/2, ys + ref_scale*0.025)
        arrow_len = ref_scale*0.07
        _add_north_arrow(ax=ax, coords=coord,
                         arrow_len=arrow_len,
                         rotation_deg=rotation_deg)

    # --- Final touches (unchanged) ---
    ax.axis('equal')
    ax.set_xticks([]);  ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    return ax
