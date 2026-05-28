import numpy as np

from cave_sketch.survey.graphics.placement import find_best_corner_with_padding, get_dual_placement


def test_dual_placement_vertical_stack():
    # Arrow above Rule, Arrow centered on Rule
    x_min, x_max, y_min, y_max = 0, 100, 0, 100
    rule_width = 20
    rule_height = 2
    arrow_height = 10
    
    # Test bottom-left
    # Expected: 
    # Rule at (inset, inset)
    # Arrow at (inset + rule_width/2, inset + rule_height + vertical_gap + arrow_height/2)
    # Wait, the anchor for rule and arrow might be different depending on how
    # _add_rule and _add_north_arrow work.
    # _add_rule(x_start, y_start, ...)
    # _add_north_arrow(coords=(x,y), ...)
    
    # Let's assume the function returns (arrow_coords, rule_coords)
    # where arrow_coords is (x, y) for _add_north_arrow and rule_coords is (x, y) for _add_rule
    
    # Inset is 2% by default
    inset = 2 
    gap = 2 # Vertical gap between elements
    
    arrow_pos, rule_pos = get_dual_placement(
        "bottom-left", x_min, x_max, y_min, y_max, 
        rule_width=rule_width, arrow_height=arrow_height, 
        vertical_gap=gap
    )
    
    # Rule starts at inset
    assert rule_pos == (inset, inset)
    # Arrow is centered on rule and above it
    assert arrow_pos == (inset + rule_width / 2, inset + rule_height + gap + arrow_height / 2)

def test_find_best_corner_with_3_percent_padding():
    # Axes range is 0 to 100.
    # Data is at (2.5, 2.5) which is within 3% of the (0,0) corner.
    # We add another point far away to define the range.
    x = np.array([2.5, 50, 95])
    y = np.array([2.5, 50, 95])
    
    # Range is 2.5 to 95. Width = 92.5.
    # 3% of 92.5 is 2.775.
    # bottom-left is (2.5, 2.5). 
    # Point at (2.5, 2.5) is inside the padded zone of bottom-left.
    
    # Wait, find_best_corner_with_padding uses the data bbox.
    # Data bbox is (2.5, 95, 2.5, 95).
    # Padded zone for bottom-left: [2.5, 2.5 + 0.03*92.5] = [2.5, 5.275].
    # Point (2.5, 2.5) is in it.
    
    # Top-right is (95, 95). Padded zone: [95 - 2.775, 95] = [92.225, 95].
    # Point (95, 95) is in it.
    
    # Let's make it simpler.
    x = np.array([0, 50, 100])
    y = np.array([0, 50, 100])
    # Points at corners (0,0) and (100,100).
    # bottom-left and top-right should be penalized.
    # bottom-right and top-left should NOT be penalized.
    # Tie-break priority: bottom-left > bottom-right > top-left > top-right.
    # Since bottom-left is penalized, it should pick bottom-right.
    
    best_corner = find_best_corner_with_padding(x, y, padding_fraction=0.03)
    assert best_corner == "bottom-right"

def test_dual_placement_center_alignment():
    x_min, x_max, y_min, y_max = 0, 100, 0, 100
    rule_width = 40
    arrow_pos, rule_pos = get_dual_placement(
        "bottom-left", x_min, x_max, y_min, y_max, 
        rule_width=rule_width, arrow_height=10
    )
    
    # Arrow X should be rule_pos X + rule_width / 2
    assert arrow_pos[0] == rule_pos[0] + rule_width / 2

def test_dual_placement_vertical_stack_scaled():
    # Test that ref_scale overrides vertical_gap and sets rule_height
    x_min, x_max, y_min, y_max = 0, 1000, 0, 1000
    rule_width = 100
    arrow_height = 50
    ref_scale = 100
    
    # Expected scaling:
    # rule_height = ref_scale * 0.01 = 1.0
    # vertical_gap = ref_scale * 0.02 = 2.0
    # inset = 1000 * 0.02 = 20.0
    
    arrow_pos, rule_pos = get_dual_placement(
        "bottom-left", x_min, x_max, y_min, y_max,
        rule_width=rule_width, arrow_height=arrow_height,
        ref_scale=ref_scale
    )
    
    expected_rule_pos = (20.0, 20.0)
    expected_rule_height = 1.0
    expected_gap = 2.0
    expected_arrow_pos = (
        expected_rule_pos[0] + rule_width / 2,
        expected_rule_pos[1] + expected_rule_height + expected_gap + arrow_height / 2
    )
    
    assert rule_pos == expected_rule_pos
    assert arrow_pos == expected_arrow_pos

def test_score_corners_absolute_padding():
    from cave_sketch.survey.graphics.placement import score_corners
    # x_min=0, x_max=100, y_min=0, y_max=100.
    # Point at (5, 95) is near top-left corner (0, 100).
    x = np.array([0.0, 5.0, 100.0])
    y = np.array([0.0, 95.0, 100.0])
    
    # Padding zone for top-left: x in [0, padding_x], y in [100-padding_y, 100].
    # Point (5, 95):
    # - In zone if padding_x >= 5 AND padding_y >= 5.
    
    # 1. Smaller padding: point is OUTSIDE
    scores = score_corners(x, y, padding_x_units=2.0, padding_y_units=2.0)
    assert scores["top-left"] < 1000000
    
    # 2. Larger padding: point is INSIDE
    scores = score_corners(x, y, padding_x_units=10.0, padding_y_units=10.0)
    assert scores["top-left"] >= 1000000

def test_compute_dual_layout_returns_best_corner():
    from cave_sketch.survey.graphics.placement import compute_dual_layout
    # Expand range to 0-100, data in the middle/top-right
    x = np.array([0, 100, 80, 90])
    y = np.array([0, 100, 80, 90])
    # bottom-left (near 0,0) has point (0,0)
    # top-right (near 100,100) has point (100,100)
    # bottom-right (near 100,0) and top-left (near 0,100) should be clear
    
    rule_length = 20
    arrow_len = 10
    ref_scale = 100
    
    arrow_pos, rule_pos, axes_expansion = compute_dual_layout(
        x, y, rule_length, arrow_len, ref_scale
    )
    
    assert axes_expansion is None
    # Should pick one of the clear corners
    assert rule_pos is not None
    assert arrow_pos[1] > rule_pos[1]

def test_compute_dual_layout_fallback_wide_cave():
    from cave_sketch.survey.graphics.placement import compute_dual_layout
    # Dense data covering all corners
    x = np.array([0, 100, 0, 100, 50])
    y = np.array([0, 0, 100, 100, 50])
    # x_span = 100, y_span = 100 (x_span >= y_span)
    rule_length = 20
    arrow_len = 10
    ref_scale = 100
    
    arrow_pos, rule_pos, axes_expansion = compute_dual_layout(
        x, y, rule_length, arrow_len, ref_scale
    )
    
    assert axes_expansion is not None
    assert "y_min" in axes_expansion
    assert axes_expansion["y_min"] < 0 # Expanded downwards

def test_compute_dual_layout_fallback_tall_cave():
    from cave_sketch.survey.graphics.placement import compute_dual_layout
    # Dense data covering all corners
    x = np.array([0, 0, 100, 100, 50])
    y = np.array([0, 200, 0, 200, 100])
    # x_span = 100, y_span = 200 (y_span > x_span)
    rule_length = 20
    arrow_len = 10
    ref_scale = 100
    
    arrow_pos, rule_pos, axes_expansion = compute_dual_layout(
        x, y, rule_length, arrow_len, ref_scale
    )
    
    assert axes_expansion is not None
    assert "x_min" in axes_expansion
    assert axes_expansion["x_min"] < 0 # Expanded leftwards

def test_compute_data_bbox_empty():
    from cave_sketch.survey.graphics.placement import compute_data_bbox
    assert compute_data_bbox(np.array([]), np.array([])) == (0, 0, 0, 0)

def test_is_fallback_needed_variations():
    from cave_sketch.survey.graphics.placement import is_fallback_needed
    # No data
    assert not is_fallback_needed(np.array([]), np.array([]))
    
    # Dense data
    x = np.array([0, 100, 0, 100, 50])
    y = np.array([0, 0, 100, 100, 50])
    assert is_fallback_needed(x, y)
    
    # Clear corner
    x = np.array([0, 100, 100])
    y = np.array([0, 0, 100])
    # bottom-left, bottom-right, top-right are occupied. top-left is clear.
    assert not is_fallback_needed(x, y)

def test_corner_anchor_all_corners():
    from cave_sketch.survey.graphics.placement import corner_anchor
    corners = ["bottom-left", "bottom-right", "top-left", "top-right", "invalid"]
    for c in corners:
        res = corner_anchor(c, 0, 100, 0, 100)
        assert len(res) == 2

def test_get_dual_placement_all_corners():
    # Verify all corners compute something plausible
    corners = ["bottom-left", "bottom-right", "top-left", "top-right", "invalid"]
    for c in corners:
        arrow_pos, rule_pos = get_dual_placement(
            c, 0, 100, 0, 100, rule_width=20, arrow_height=10
        )
        assert len(arrow_pos) == 2
        assert len(rule_pos) == 2
