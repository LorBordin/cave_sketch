from typing import Any, Dict, Optional, List
import pandas as pd
import re

from cave_sketch.style import STYLE_MAP

def extract_features_from_json(map_data: Dict[str, Any]) -> Dict[str, list]:
    """
    Extract abstract features (lines, polygons) with styles, 
    independent of rendering backend.
    """
    features = {"lines": [], "polygons": []}

    # Polygons
    for water_polygon in map_data.get("water_polygons", []):
        coords = water_polygon["coordinates"]
        features["polygons"].append({
            "coords": coords,
            "fill_color": "blue",
            "fill_opacity": 0.3,
            "edge_color": "blue",
            "popup": f"{map_data['name']}: Water Area {water_polygon.get('polygon_id', '')}"
        })

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

        features["lines"].append({
            "coords": [pt_from, pt_to],
            "color": color,
            "weight": weight,
            "dash": dash,
            "popup": f"{map_data['name']}: {line_type}"
        })

    return features


def extract_features_from_df(df: pd.DataFrame, excluded_nodes: Optional[List[str]] = None) -> Dict[str, list]:
    """Convert survey DataFrame into backend-agnostic drawable features, including area reconstruction."""
    if excluded_nodes is None:
        excluded_nodes = []

    features = {"lines": [], "polygons": [], "points": []}  # <-- added points

    # --- 1️⃣ Handle standard line features (walls, shots, etc.) ---
    for _, row in df.iterrows():
        nid, x, y, links, typ = row["Node_Id"], row["X"], row["Y"], row["Links"], row["Type"]

        if nid in excluded_nodes or typ.startswith("A_"):
            continue

        # --- New block: handle standalone point features ---
        style_type = STYLE_MAP.get(typ, {}).get("type", "line")
        if style_type == "point":
            style = STYLE_MAP.get(typ, {"color": "black", "marker": "o", "markersize": 6})
            features["points"].append({
                "coords": [y, x],  # lat/lon-like
                "color": style.get("color", "black"),
                "marker": style.get("marker", "o"),
                "size": style.get("markersize", 6),
                "popup": f"{typ} ({nid})"
            })
            continue  # skip to next row

        # --- Existing line logic ---
        if pd.notna(links) and links != "-":
            neighbors = [nbr.strip() for nbr in links.split("-") if nbr.strip() and nbr not in excluded_nodes]
            for nbr in neighbors:
                nbr_row = df[df["Node_Id"] == nbr]
                if nbr_row.empty:
                    continue
                x2, y2 = nbr_row.iloc[0][['X', 'Y']]

                if style_type == "line":
                    style = STYLE_MAP.get(typ, STYLE_MAP["L_wall"])
                    features["lines"].append({
                        "coords": [[y, x], [y2, x2]],
                        "color": style.get("color", "black"),
                        "weight": style.get("weight", 1),
                        "dash": None if style.get("linestyle", "solid") == "solid" else [3, 7],
                        "popup": f"{typ} ({nid}-{nbr})"
                    })

    # --- 2️⃣ Handle area features (A_water, A_sediment, etc.) ---
    area_rows = df[df["Type"].str.startswith("A_")].copy()
    if not area_rows.empty:
        area_rows["Area_ID"] = area_rows["Node_Id"].apply(
            lambda x: re.match(r"(\d+)P\d+", x).group(1) if re.match(r"(\d+)P\d+", x) else None
        )

        for area_id, group in area_rows.groupby("Area_ID"):
            if len(group) < 3:
                continue

            group = group.sort_values(
                by="Node_Id",
                key=lambda s: s.str.extract(r"P(\d+)", expand=False).astype(float)
            )

            xs = group["X"].to_numpy()
            ys = group["Y"].to_numpy()
            typ = group.iloc[0]["Type"]

            style = STYLE_MAP.get(typ, {"color": "blue", "alpha": 0.3})
            coords = [[yy, xx] for xx, yy in zip(xs, ys)]

            features["polygons"].append({
                "coords": coords,
                "fill_color": style.get("color", "blue"),
                "fill_opacity": style.get("alpha", 0.3),
                "edge_color": style.get("color", "blue"),
                "popup": f"{typ} (Area {area_id})"
            })

    return features

