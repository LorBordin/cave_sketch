import math
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from cave_sketch.geo.georef import meters_per_degree_wgs84
from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP
from cave_sketch.style_icons import icon_strokes

_POLYLINE_NODE_RE = re.compile(r"^(\d+)P(\d+)$")


def _is_forward_segment(from_id: Any, to_id: Any) -> bool:
    """True when ``from_id -> to_id`` is one step along a DXF polyline in drawing
    order (``"{i}P{j}" -> "{i}P{j+1}"``).

    Every polyline segment appears twice in the data (once from each end).
    Keeping only the forward copy gives exactly one decoration per segment,
    oriented the way the line was drawn (TopoDroid draws water-flow lines
    downstream).
    """
    a = _POLYLINE_NODE_RE.match(str(from_id))
    b = _POLYLINE_NODE_RE.match(str(to_id))
    return bool(a and b and a.group(1) == b.group(1) and int(b.group(2)) == int(a.group(2)) + 1)


def _rotation_value(value: Any) -> float:
    """Rotation from a CSV/JSON cell; missing or NaN (old CSVs, merge connectors) means 0."""
    try:
        rotation = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(rotation) else rotation


def _heading_deg(dx: float, dy: float) -> float:
    """Icon rotation (CCW degrees, 0 = icon up along +Y) pointing the icon along (dx, dy)."""
    return math.degrees(math.atan2(dy, dx)) - 90.0


def _icon_strokes_latlon(
    name: str, lat: float, lon: float, size_m: float, rotation_deg: float
) -> List[List[List[float]]]:
    """Icon strokes as ``[lat, lon]`` polylines, sized in meters on the ground."""
    m_per_deg_lat, m_per_deg_lon = meters_per_degree_wgs84(lat)
    return [
        [[lat + dy / m_per_deg_lat, lon + dx / m_per_deg_lon] for dx, dy in stroke]
        for stroke in icon_strokes(name, 0.0, 0.0, size_m, rotation_deg)
    ]


def _icon_feature(strokes: list, typ: str, color: str, popup: str) -> Dict[str, Any]:
    return {
        "type": typ,
        "strokes": strokes,
        "color": color,
        "weight": ICON_LINE_WEIGHT,
        "popup": popup,
    }


def extract_features_from_json(map_data: Dict[str, Any]) -> Dict[str, list]:
    """
    Extract abstract features (lines, polygons, points, icons) with styles,
    independent of rendering backend. Coordinates are ``[lat, lon]``.
    """
    features: Dict[str, List[Dict[str, Any]]] = {
        "lines": [],
        "polygons": [],
        "points": [],
        "icons": [],
    }

    # Polygons
    for water_polygon in map_data.get("water_polygons", []):
        coords = water_polygon["coordinates"]
        features["polygons"].append(
            {
                "coords": coords,
                "fill_color": "blue",
                "fill_opacity": 0.3,
                "edge_color": "blue",
                "popup": f"{map_data['name']}: Water Area {water_polygon.get('polygon_id', '')}",
            }
        )

    # Lines
    for line in map_data.get("lines", []):
        line_type = line["type"]
        style = STYLE_MAP.get(line_type, {"color": "black", "type": "line"})
        color = style.get("color", "black")
        weight = style.get("weight", 1)
        linestyle = style.get("linestyle", "solid")

        dash = None
        if linestyle == (0, (1, 1)):
            dash = [5, 5]
        elif linestyle == (0, (1, 2)):
            dash = [3, 7]

        pt_from = [line["from"]["lat"], line["from"]["lon"]]
        pt_to = [line["to"]["lat"], line["to"]["lon"]]

        features["lines"].append(
            {
                "coords": [pt_from, pt_to],
                "color": color,
                "weight": weight,
                "dash": dash,
                "popup": f"{map_data['name']}: {line_type}",
            }
        )

        decoration = style.get("line_decoration")
        if decoration and _is_forward_segment(line["from"].get("id"), line["to"].get("id")):
            mid_lat = (pt_from[0] + pt_to[0]) / 2
            mid_lon = (pt_from[1] + pt_to[1]) / 2
            m_per_deg_lat, m_per_deg_lon = meters_per_degree_wgs84(mid_lat)
            heading = _heading_deg(
                (pt_to[1] - pt_from[1]) * m_per_deg_lon, (pt_to[0] - pt_from[0]) * m_per_deg_lat
            )
            strokes = _icon_strokes_latlon(
                str(decoration), mid_lat, mid_lon, float(str(style["decoration_size_m"])), heading
            )
            features["icons"].append(
                _icon_feature(strokes, line_type, str(color), f"{map_data['name']}: {line_type}")
            )

    # Points and icons (B_* blocks)
    nodes = map_data.get("nodes", {})
    node_list = nodes if isinstance(nodes, list) else [{"id": k, **v} for k, v in nodes.items()]
    for node in node_list:
        node_type = node.get("type", "")
        style = STYLE_MAP.get(node_type, {})
        popup = f"{map_data.get('name', '')}: {node_type} ({node.get('id', '')})"
        if style.get("type") == "point":
            features["points"].append(
                {
                    "coords": [node["lat"], node["lon"]],
                    "color": style["color"],
                    "marker": style.get("marker", "o"),
                    "size": style.get("markersize", 6),
                    "popup": popup,
                }
            )
        elif style.get("type") == "icon":
            strokes = _icon_strokes_latlon(
                str(style["icon"]),
                node["lat"],
                node["lon"],
                float(str(style["size_m"])),
                _rotation_value(node.get("rotation", 0.0)),
            )
            features["icons"].append(_icon_feature(strokes, node_type, str(style["color"]), popup))

    return features


def extract_features_from_df(
    df: pd.DataFrame,
    excluded_nodes: Optional[List[str]] = None,
    show_centerline: bool = True,
) -> Dict[str, list]:
    """Convert survey DataFrame into backend-agnostic drawable features."""
    if excluded_nodes is None:
        excluded_nodes = []

    features: Dict[str, list] = {"lines": [], "polygons": [], "points": [], "icons": []}

    # Build coordinate index with first-occurrence-wins semantics
    coord_index: Dict[Any, Tuple[float, float]] = {}
    for row in df.itertuples(index=False):
        if row.Node_Id not in coord_index:
            coord_index[row.Node_Id] = (row.X, row.Y)

    # --- 1️⃣ Handle standard line features (walls, shots, etc.) ---
    for row in df.itertuples(index=False):
        nid, x, y, links, typ = row.Node_Id, row.X, row.Y, row.Links, row.Type

        if nid in excluded_nodes or typ.startswith("A_"):
            continue

        if not show_centerline and typ == "station":
            continue

        style_type = STYLE_MAP.get(typ, {}).get("type", "line")

        # --- Icon features (B_blocks, B_water-flow, ...), sized in meters ---
        if style_type == "icon":
            style = STYLE_MAP[typ]
            rotation = _rotation_value(getattr(row, "Rotation", 0.0))
            strokes = icon_strokes(str(style["icon"]), x, y, float(str(style["size_m"])), rotation)
            features["icons"].append(
                _icon_feature(
                    [[[py, px] for px, py in stroke] for stroke in strokes],
                    typ,
                    str(style["color"]),
                    f"{typ} ({nid})",
                )
            )
            continue

        # --- Standalone point features (B_ice, B_snow) ---
        if style_type == "point":
            style = STYLE_MAP.get(typ, {"color": "black", "marker": "o", "markersize": 6})
            features["points"].append(
                {
                    "coords": [y, x],  # lat/lon-like
                    "color": style.get("color", "black"),
                    "marker": style.get("marker", "o"),
                    "size": style.get("markersize", 6),
                    "popup": f"{typ} ({nid})",
                }
            )
            continue  # skip to next row

        # --- Existing line logic ---
        if pd.notna(links) and links != "-":
            neighbors = [
                nbr.strip() for nbr in links.split("-") if nbr.strip() and nbr not in excluded_nodes
            ]
            for nbr in neighbors:
                if nbr not in coord_index:
                    continue
                x2, y2 = coord_index[nbr]

                if style_type == "line":
                    style = STYLE_MAP.get(typ, STYLE_MAP["L_wall"])
                    features["lines"].append(
                        {
                            "coords": [[y, x], [y2, x2]],
                            "color": style.get("color", "black"),
                            "weight": style.get("weight", 1),
                            "dash": None if style.get("linestyle", "solid") == "solid" else [3, 7],
                            "popup": f"{typ} ({nid}-{nbr})",
                        }
                    )

                    decoration = style.get("line_decoration")
                    if decoration and _is_forward_segment(nid, nbr):
                        strokes = icon_strokes(
                            str(decoration),
                            (x + x2) / 2,
                            (y + y2) / 2,
                            float(str(style["decoration_size_m"])),
                            _heading_deg(x2 - x, y2 - y),
                        )
                        features["icons"].append(
                            _icon_feature(
                                [[[py, px] for px, py in stroke] for stroke in strokes],
                                typ,
                                str(style["color"]),
                                f"{typ} ({nid}-{nbr})",
                            )
                        )

    # --- 2️⃣ Handle area features (A_water, A_sediment, etc.) ---
    area_rows = df[df["Type"].str.startswith("A_")].copy()
    if not area_rows.empty:

        def get_area_id(node_id: str) -> Optional[str]:
            m = re.match(r"(\d+)P\d+", node_id)
            return m.group(1) if m else None

        area_rows["Area_ID"] = area_rows["Node_Id"].apply(get_area_id)

        for area_id, group in area_rows.groupby("Area_ID"):
            if len(group) < 3:
                continue

            group = group.sort_values(
                by="Node_Id", key=lambda s: s.str.extract(r"P(\d+)", expand=False).astype(float)
            )

            xs = group["X"].to_numpy()
            ys = group["Y"].to_numpy()
            typ = group.iloc[0]["Type"]

            style = STYLE_MAP.get(typ, {"color": "blue", "alpha": 0.3})
            coords = [[yy, xx] for xx, yy in zip(xs, ys)]

            features["polygons"].append(
                {
                    "coords": coords,
                    "fill_color": style.get("color", "blue"),
                    "fill_opacity": style.get("alpha", 0.3),
                    "edge_color": style.get("color", "blue"),
                    "popup": f"{typ} (Area {area_id})",
                }
            )

    return features
