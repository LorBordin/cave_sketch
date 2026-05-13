from typing import Dict, Optional

import numpy as np
from matplotlib.patches import Polygon as MplPolygon


def render_to_matplotlib(
    features: Dict[str, list],
    ax,
    layer_name: str = "",
    config: Optional[Dict] = None
):
    """
    Render extracted features onto a Matplotlib Axes with stable line scaling.
    """
    if config is None:
        config = {}

    # Extract parameters
    lz = config.get("line_width_zoom", 10)
    ref_scale = config.get("ref_scale", 1.0)
    zoom_factor = 10 ** (lz - 10)

    # ---- POLYGONS ----
    for p in features.get("polygons", []):
        coords = np.array(p["coords"], dtype=float)
        xy = np.column_stack((coords[:, 1], coords[:, 0]))
        poly = MplPolygon(
            xy,
            closed=True,
            facecolor=p.get("fill_color", "blue"),
            edgecolor=p.get("edge_color", p.get("fill_color", "blue")),
            alpha=p.get("fill_opacity", 0.3),
            linewidth=0.5,
            zorder=p.get("zorder", 1),
        )
        ax.add_patch(poly)

    # ---- LINES ----
    for line in features.get("lines", []):
        coords = np.array(line["coords"], dtype=float)
        xs = coords[:, 1]
        ys = coords[:, 0]

        base_weight = line.get("weight", 1)
        lw = base_weight * zoom_factor / ref_scale
        lw = np.clip(lw, 0.2, 4)

        dash = line.get("dash")
        linestyle = (0, tuple(dash)) if dash else "solid"

        ax.plot(xs, ys,
                color=line.get("color", "black"),
                linewidth=lw,
                linestyle=linestyle,
                alpha=0.9,
                zorder=line.get("zorder", 2))

    # ---- POINTS (B_ice, BLOCK, etc.) ----
    for p in features.get("points", []):
        y, x = p["coords"]

        # interpret 'size' as diameter in points, not area
        size_pts = p.get("size", 6)
        s_area = size_pts ** 2 * 0.5  # dampen to avoid huge circles

        marker = p.get("marker", "o")
        color = p.get("color", "black")
        if color == "saddlebrown":
            print("BLOCK!!")
        elif color == "deepskyblue":
            print("ICE")

        ax.scatter(
            x, y,
            s=s_area,
            c=color,
            marker=marker,
            edgecolors="none",
            alpha=0.9,
            zorder=p.get("zorder", 3)
        )

        # Optional text label
        if config.get("show_labels", False):
            ax.text(
                x, y, p.get("popup", ""),
                fontsize=5, ha="left", va="bottom",
                color=color, zorder=4
            )

    if layer_name:
        ax.set_title(layer_name, fontsize=10)

    ax.set_aspect('equal', 'datalim')
