import folium

from cave_sketch.backend_renders import render_to_folium
from cave_sketch.style import ICON_LINE_WEIGHT

LAT, LON = 46.5, 11.3


def test_folium_icon_is_polyline_with_wall_weight():
    features = {
        "icons": [{
            "type": "B_entrance",
            "strokes": [[[LAT, LON], [LAT + 1e-5, LON]], [[LAT, LON], [LAT, LON + 1e-5]]],
            "color": "firebrick",
            "weight": ICON_LINE_WEIGHT,
            "popup": "M: B_entrance (e)",
        }],
        "points": [{"coords": [LAT, LON], "color": "deepskyblue", "size": 2, "popup": "ice"}],
    }
    fmap = folium.Map(location=[LAT, LON])
    render_to_folium(features, fmap, "Test")
    html = fmap.get_root().render()
    assert html.count("L.polyline(") == 1
    assert '"color": "firebrick"' in html
    assert f'"weight": {ICON_LINE_WEIGHT}' in html
    assert "L.circleMarker(" in html  # plain points unchanged
