import matplotlib.pyplot as plt
import pytest

from cave_sketch.survey.graphics.grid import _add_grid


def test_add_grid_creates_lines():
    fig, ax = plt.subplots()
    
    # We pass data extents: x in [5, 25], y in [12, 38], and spacing = 10
    # Clean multiples of 10 in [5, 25] are 10, 20.
    # Clean multiples of 10 in [12, 38] are 20, 30.
    _add_grid(ax, x_min=5, x_max=25, y_min=12, y_max=38, grid_spacing=10)
    
    # We should have vertical lines at x = 10, 20
    # And horizontal lines at y = 20, 30
    
    # Matplotlib stores lines added via axvline/axhline in ax.lines
    lines = ax.lines
    assert len(lines) == 4, f"Expected 4 grid lines, got {len(lines)}"
    
    # Verify properties
    v_lines = []
    h_lines = []
    for line in lines:
        assert line.get_color() == "lightgray"
        assert line.get_linestyle() == ":"
        assert line.get_zorder() == 0
        
        # In matplotlib, axvline has xdata as [x, x] and ydata as [0, 1]
        # (or in data coords [5, 25] if drawn differently, but typically
        # axvline uses transform ax.get_xaxis_transform() where x is in
        # data coords and y in axes coords).
        # We can distinguish axvline and axhline by checking their transforms or xdata/ydata.
        # Alternatively, we can check their properties. Let's see how they are defined.
        # axvline sets xdata to [x, x] and ydata to [0, 1] (in axes coords).
        # Let's inspect xdata/ydata or get_xdata()/get_ydata().
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        
        # If xdata has two identical values (and not [0, 1] which is the
        # default axes coordinate for ydata in axvline), then it is a vertical line.
        if len(xdata) == 2 and xdata[0] == xdata[1]:
            v_lines.append(xdata[0])
        elif len(ydata) == 2 and ydata[0] == ydata[1]:
            h_lines.append(ydata[0])
            
    assert sorted(v_lines) == [10.0, 20.0]
    assert sorted(h_lines) == [20.0, 30.0]
    
    plt.close(fig)

def test_add_grid_invalid_spacing():
    fig, ax = plt.subplots()
    with pytest.raises(ValueError):
        _add_grid(ax, x_min=0, x_max=10, y_min=0, y_max=10, grid_spacing=0)
    with pytest.raises(ValueError):
        _add_grid(ax, x_min=0, x_max=10, y_min=0, y_max=10, grid_spacing=-5)
    plt.close(fig)
