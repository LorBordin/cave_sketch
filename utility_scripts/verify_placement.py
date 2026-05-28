import numpy as np
from cave_sketch.survey.graphics.placement import find_best_corner, is_fallback_needed

def verify():
    print("Verifying North Symbol Placement Logic...")
    
    # Case 1: Bottom-Left empty
    x = np.array([80, 80, 20, 20])
    y = np.array([80, 20, 80, 50]) # bottom-left (0-20, 0-20) is empty
    print(f"Case 1 (Expect bottom-left): {find_best_corner(x, y)}")
    
    # Case 2: Tie-break (all empty)
    x = np.array([50])
    y = np.array([50])
    print(f"Case 2 (Expect bottom-left - priority): {find_best_corner(x, y)}")
    
    # Case 3: Fallback needed (all corners full)
    x = np.array([5, 95, 5, 95])
    y = np.array([5, 5, 95, 95])
    print(f"Case 3 (Expect fallback=True): {is_fallback_needed(x, y)}")

if __name__ == "__main__":
    verify()
