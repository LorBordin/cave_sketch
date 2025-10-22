from typing import Dict

def render_to_matplotlib(features: Dict[str, list], ax, layer_name: str = ""):
    """Render extracted features onto a Matplotlib Axes."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

    # Polygons
    for p in features["polygons"]:
        poly = MplPolygon(
            [(lon, lat) for lat, lon in p["coords"]],
            facecolor=p["fill_color"],
            edgecolor=p["edge_color"],
            alpha=p["fill_opacity"]
        )
        ax.add_patch(poly)

    # Lines
    for l in features["lines"]:
        xs = [pt[1] for pt in l["coords"]]
        ys = [pt[0] for pt in l["coords"]]
        ax.plot(xs, ys, color=l["color"], linewidth=l["weight"],
                linestyle=(0, tuple(l["dash"])) if l["dash"] else 'solid')

    ax.set_aspect('equal', 'datalim')
    ax.set_title(layer_name or "Cave Map")