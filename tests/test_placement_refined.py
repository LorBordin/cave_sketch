import numpy as np
import pytest
from cave_sketch.survey.graphics.placement import get_dual_placement, find_best_corner_with_padding

def test_dual_placement_vertical_stack():
    # Arrow above Rule, Arrow centered on Rule
    x_min, x_max, y_min, y_max = 0, 100, 0, 100
    rule_width = 20
    rule_height = 2
    arrow_width = 5
    arrow_height = 10
    
    # Test bottom-left
    # Expected: 
    # Rule at (inset, inset)
    # Arrow at (inset + rule_width/2, inset + rule_height + vertical_gap + arrow_height/2)
    # Wait, the anchor for rule and arrow might be different depending on how _add_rule and _add_north_arrow work.
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
