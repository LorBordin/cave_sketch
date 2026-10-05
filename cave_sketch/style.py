STYLE_MAP = {
    "station": {
        "color": "black",  # "gray",
        "linestyle": "solid",
        "type": "line",
        "weight": 1,
    },
    "L_wall": {
        "color": "red",
        "linestyle": "solid",
        "type": "line",
        "weight": 3,
    },
    "L_slope": {"color": "black", "linestyle": "solid", "type": "line", "weight": 2},
    "L_chimney": {"color": "indigo", "linestyle": (0, (1, 2)), "type": "line", "weight": 1},
    "L_border": {"color": "green", "linestyle": "solid", "type": "line", "weight": 2},
    "L_pit": {"color": "indigo", "linestyle": (0, (1, 1)), "type": "line", "weight": 1},
    "L_wall-presumed": {"color": "red", "linestyle": (0, (1, 2)), "type": "line", "weight": 1},
    "A_water": {"color": "blue", "alpha": 0.3, "type": "area"},
    "B_ice": {
        "color": "deepskyblue",
        "marker": ".",
        "markersize": 2,
        "type": "point",
    },
    "B_snow": {
        "color": "aliceblue",
        "marker": "*",
        "markersize": 2,
        "type": "point",
    },
    "L_water-flow": {
        "color": "steelblue",
        "linestyle": "solid",
        "type": "line",
        "weight": 1,
        "line_decoration": "water_flow_chevron",  # one chevron per segment
        "decoration_size_m": 1.0,
    },
    "B_blocks": {"color": "tan", "icon": "blocks", "size_m": 1.5, "type": "icon"},
    "B_continuation": {"color": "firebrick", "icon": "continuation", "size_m": 1.5, "type": "icon"},
    "B_entrance": {"color": "firebrick", "icon": "entrance", "size_m": 1.5, "type": "icon"},
    "B_water-flow": {"color": "mediumpurple", "icon": "water_flow", "size_m": 1.5, "type": "icon"},
    "connector": {
        "color": "gray",
        "linestyle": "dotted",
        "type": "line",
        "weight": 0.5,
    },
}

# Icons are stroked exactly as thick as walls, in every backend.
ICON_LINE_WEIGHT = STYLE_MAP["L_wall"]["weight"]
