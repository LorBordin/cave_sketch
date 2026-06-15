import pytest
from cave_sketch.survey.graphics.grid import snap_rule_to_grid

def test_snap_rule_to_grid_horizontal():
    # spacing = 10.0
    # Rule position: (12.3, 5.0) -> (10.0, 5.0) since rule is horizontal and x=12.3 snaps to nearest 10.0
    assert snap_rule_to_grid((12.3, 5.0), grid_spacing=10.0, rule_orientation="horizontal") == (10.0, 5.0)
    # Rule position: (17.8, 5.0) -> (20.0, 5.0)
    assert snap_rule_to_grid((17.8, 5.0), grid_spacing=10.0, rule_orientation="horizontal") == (20.0, 5.0)

def test_snap_rule_to_grid_vertical():
    # spacing = 10.0
    # Rule position: (5.0, 12.3) -> (5.0, 10.0) since rule is vertical and y=12.3 snaps to nearest 10.0
    assert snap_rule_to_grid((5.0, 12.3), grid_spacing=10.0, rule_orientation="vertical") == (5.0, 10.0)
    # Rule position: (5.0, 17.8) -> (5.0, 20.0)
    assert snap_rule_to_grid((5.0, 17.8), grid_spacing=10.0, rule_orientation="vertical") == (5.0, 20.0)

def test_snap_rule_to_grid_exact_multiples():
    # If already on grid line, should remain unchanged
    assert snap_rule_to_grid((10.0, 5.0), grid_spacing=10.0, rule_orientation="horizontal") == (10.0, 5.0)
    assert snap_rule_to_grid((5.0, 20.0), grid_spacing=10.0, rule_orientation="vertical") == (5.0, 20.0)

def test_snap_rule_to_grid_edge_cases():
    # Exactly between: 15.0 with spacing 10.0 should round to 10.0 or 20.0
    res_h = snap_rule_to_grid((15.0, 5.0), grid_spacing=10.0, rule_orientation="horizontal")
    assert res_h in [(10.0, 5.0), (20.0, 5.0)]

def test_snap_rule_to_grid_invalid_orientation():
    with pytest.raises(ValueError):
        snap_rule_to_grid((12.3, 5.0), grid_spacing=10.0, rule_orientation="invalid")
