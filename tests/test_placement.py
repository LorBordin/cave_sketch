import numpy as np

from cave_sketch.survey.graphics.placement import (
    corner_anchor,
    find_best_corner,
    is_fallback_needed,
)


def test_find_best_corner_top_right_empty():
    # Data points concentrated in top-left, bottom-left, bottom-right
    # top-right (X > 50, Y > 50) is empty
    x = np.array([10, 20, 10, 20, 80, 90, 80, 90])
    y = np.array([10, 10, 20, 20, 10, 10, 20, 20])
    # Corners are:
    # bottom-left: (0-20, 0-20) -> has points (10,10), (20,10), (10,20), (20,20)
    # bottom-right: (80-100, 0-20) -> has points (80,10), (90,10), (80,20), (90,20)
    # top-left: (0-20, 80-100) -> empty
    # top-right: (80-100, 80-100) -> empty
    
    # Wait, the bbox of this data is (10, 90, 10, 20).
    # Let's make it clearer.
    x = np.concatenate([
        np.linspace(0, 20, 5), # bottom-left
        np.linspace(80, 100, 5), # bottom-right
        np.linspace(0, 20, 5) # top-left
    ])
    y = np.concatenate([
        np.linspace(0, 20, 5), # bottom-left
        np.linspace(0, 20, 5), # bottom-right
        np.linspace(80, 100, 5) # top-left
    ])
    # top-right (80-100, 80-100) is empty
    assert find_best_corner(x, y) == "top-right"

def test_find_best_corner_tie_break():
    # All corners empty except maybe some middle points
    x = np.array([50, 50, 50])
    y = np.array([50, 50, 50])
    # Priority: bottom-left > bottom-right > top-left > top-right
    assert find_best_corner(x, y) == "bottom-left"

def test_is_fallback_needed_dense():
    # Points in all corners
    x = np.array([5, 95, 5, 95])
    y = np.array([5, 5, 95, 95])
    # Each corner has 1 point. 
    # With 4 points total, max density is 1 point per corner.
    # All corners have 100% of max density, which is > 50%.
    assert is_fallback_needed(x, y) is True

def test_is_fallback_needed_not_dense():
    # Three corners dense, one empty
    x = np.array([5, 95, 5])
    y = np.array([5, 5, 95])
    assert is_fallback_needed(x, y) is False

def test_corner_anchor():
    x_min, x_max, y_min, y_max = 0, 100, 0, 100
    # Inset is 2% of width/height
    # bottom-left: (2, 2)
    assert corner_anchor("bottom-left", x_min, x_max, y_min, y_max) == (2, 2)
    # top-right: (98, 98)
    assert corner_anchor("top-right", x_min, x_max, y_min, y_max) == (98, 98)
