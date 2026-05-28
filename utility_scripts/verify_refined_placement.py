import numpy as np
from cave_sketch.survey.graphics.placement import get_dual_placement, find_best_corner_with_padding

def verify():
    print("Verifying Refined Placement Logic...")
    
    # Case 1: Padding check
    x = np.array([0, 50, 100])
    y = np.array([0, 50, 100])
    best = find_best_corner_with_padding(x, y, padding_fraction=0.03)
    print(f"Case 1 (Points at corners): Best corner (should be bottom-right): {best}")
    
    # Case 2: Dual placement check
    arrow_pos, rule_pos = get_dual_placement(
        "bottom-left", 0, 100, 0, 100, 
        rule_width=20, arrow_height=10, 
        vertical_gap=2
    )
    print(f"Case 2 (Bottom-left): Rule {rule_pos}, Arrow {arrow_pos}")
    # Rule (2, 2)
    # Arrow (2 + 10, 2 + 2 + 2 + 5) = (12, 11)
    
    expected_rule = (2.0, 2.0)
    expected_arrow = (12.0, 11.0)
    
    if rule_pos == expected_rule and arrow_pos == expected_arrow:
        print("Case 2 SUCCESS: Stacking and alignment correct.")
    else:
        print(f"Case 2 FAILURE: Expected R{expected_rule} A{expected_arrow}, got R{rule_pos} A{arrow_pos}")

if __name__ == "__main__":
    verify()
