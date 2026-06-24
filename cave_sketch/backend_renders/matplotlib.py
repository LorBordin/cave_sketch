from typing import Any, Dict, List, Optional

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon as MplPolygon


def render_to_matplotlib(
    features: Dict[str, list], ax, layer_name: str = "", config: Optional[Dict] = None
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
    segments = []
    colors = []
    linewidths = []
    linestyles = []

    for line in features.get("lines", []):
        coords = np.array(line["coords"], dtype=float)
        # coords is [[y1, x1], [y2, x2]], we need [[x1, y1], [x2, y2]]
        segment = [(coords[0, 1], coords[0, 0]), (coords[1, 1], coords[1, 0])]
        segments.append(segment)

        colors.append(line.get("color", "black"))

        base_weight = line.get("weight", 1)
        lw = base_weight * zoom_factor / ref_scale
        lw = np.clip(lw, 0.2, 4)
        linewidths.append(lw)

        dash = line.get("dash")
        linestyle = (0, tuple(dash)) if dash else "solid"
        linestyles.append(linestyle)

    if segments:
        lc = LineCollection(
            segments,
            colors=colors,
            linewidths=linewidths,
            linestyles=linestyles,
            alpha=0.9,
            zorder=2,
        )
        ax.add_collection(lc)
        ax.autoscale_view()

    # ---- POINTS (B_ice, BLOCK, etc.) ----
    points_by_marker: Dict[str, List[Dict[str, Any]]] = {}
    for p in features.get("points", []):
        marker = p.get("marker", "o")
        points_by_marker.setdefault(marker, []).append(p)

    for marker, plist in points_by_marker.items():
        xs = []
        ys = []
        sizes = []
        colors = []
        zorder = 3
        for p in plist:
            y, x = p["coords"]
            xs.append(x)
            ys.append(y)
            size_pts = p.get("size", 6)
            s_area = size_pts**2 * 0.5
            sizes.append(s_area)
            colors.append(p.get("color", "black"))
            zorder = p.get("zorder", 3)

        ax.scatter(
            xs,
            ys,
            s=sizes,
            c=colors,
            marker=marker,
            edgecolors="none",
            alpha=0.9,
            zorder=zorder,
        )

        # Optional text label
        if config.get("show_labels", False):
            for p in plist:
                y, x = p["coords"]
                ax.text(
                    x,
                    y,
                    p.get("popup", ""),
                    fontsize=5,
                    ha="left",
                    va="bottom",
                    color=p.get("color", "black"),
                    zorder=4,
                )

    if layer_name:
        ax.set_title(layer_name, fontsize=10)

    ax.set_aspect("equal", "datalim")
