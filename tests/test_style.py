from matplotlib.colors import is_color_like

from cave_sketch.style import ICON_LINE_WEIGHT, STYLE_MAP
from cave_sketch.style_icons import ICON_SHAPES

ICON_TYPES = ["B_blocks", "B_continuation", "B_entrance", "B_water-flow"]


def test_block_placeholder_is_replaced_by_real_dxf_name():
    assert "BLOCK" not in STYLE_MAP
    assert STYLE_MAP["B_blocks"]["type"] == "icon"


def test_icon_types_reference_existing_shapes_with_positive_size():
    expected = {
        "B_blocks": "blocks",
        "B_continuation": "continuation",
        "B_entrance": "entrance",
        "B_water-flow": "water_flow",
    }
    for typ, icon in expected.items():
        style = STYLE_MAP[typ]
        assert style["type"] == "icon"
        assert style["icon"] == icon and icon in ICON_SHAPES
        assert style["size_m"] > 0


def test_water_flow_line_has_chevron_decoration():
    style = STYLE_MAP["L_water-flow"]
    assert style["type"] == "line"
    assert style["line_decoration"] == "water_flow_chevron"
    assert style["line_decoration"] in ICON_SHAPES
    assert style["decoration_size_m"] > 0


def test_icon_line_weight_matches_wall():
    assert ICON_LINE_WEIGHT == STYLE_MAP["L_wall"]["weight"]


def test_ice_and_snow_stay_plain_markers():
    assert STYLE_MAP["B_ice"]["type"] == "point"
    assert STYLE_MAP["B_snow"]["type"] == "point"


def test_every_style_color_is_renderable():
    for style in STYLE_MAP.values():
        assert is_color_like(style["color"]), style["color"]
