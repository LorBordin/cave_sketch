from typing import Dict

import folium


def render_to_folium(features: Dict[str, list], folium_map, layer_name: str):
    """Render extracted features onto a Folium map."""
    fg = folium.FeatureGroup(name=layer_name)

    # ---- POLYGONS ----
    for p in features.get("polygons", []):
        folium.Polygon(
            locations=p["coords"],
            color=p.get("edge_color", p.get("fill_color", "blue")),
            weight=0,
            fillColor=p.get("fill_color", "blue"),
            fillOpacity=p.get("fill_opacity", 0.3),
            popup=p.get("popup")
        ).add_to(fg)

    # ---- LINES ----
    for line in features.get("lines", []):
        kwargs = dict(
            locations=line["coords"],
            color=line.get("color", "black"),
            weight=line.get("weight", 1),
            opacity=0.8,
            popup=line.get("popup", "")
        )
        if line.get("dash"):
            kwargs["dashArray"] = ",".join(map(str, line["dash"]))
        folium.PolyLine(**kwargs).add_to(fg)

    # ---- POINTS (B_ice, BLOCK, etc.) ----
    for p in features.get("points", []):
        folium.CircleMarker(
            location=p["coords"],
            radius=p.get("size", 6),
            color=p.get("color", "black"),
            fill=True,
            fillColor=p.get("color", "black"),
            fillOpacity=0.9,
            popup=p.get("popup", "")
        ).add_to(fg)

    fg.add_to(folium_map)
