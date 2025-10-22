from typing import Dict
import folium

def render_to_folium(features: Dict[str, list], folium_map, layer_name: str):
    """Render extracted features onto a Folium map."""
    fg = folium.FeatureGroup(name=layer_name)

    # Polygons
    for p in features["polygons"]:
        folium.Polygon(
            locations=p["coords"],
            color=p["edge_color"],
            weight=0,
            fillColor=p["fill_color"],
            fillOpacity=p["fill_opacity"],
            popup=p["popup"]
        ).add_to(fg)

    # Lines
    for l in features["lines"]:
        kwargs = dict(
            locations=l["coords"],
            color=l["color"],
            weight=l["weight"],
            opacity=0.8,
            popup=l["popup"]
        )
        if l["dash"]:
            kwargs["dashArray"] = ",".join(map(str, l["dash"]))
        folium.PolyLine(**kwargs).add_to(fg)

    fg.add_to(folium_map)