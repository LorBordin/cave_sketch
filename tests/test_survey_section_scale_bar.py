import matplotlib.pyplot as plt
import pandas as pd

from cave_sketch.survey.graphics.survey_plot import create_survey


def test_section_scale_bar_no_intersection():
    # Load the problematic section data
    csv_path = "tests/fixtures/scale_bar_test/monte_10_25_sezione.csv"
    df = pd.read_csv(csv_path)
    
    # Configure parameters
    rule_length = 100.0
    config_dict = {
        "show_details": True,
        "marker_zoom": 10.0,
        "text_zoom": 10.0,
        "line_width_zoom": 10.0,
        "rotation_deg": 0.0,
        "show_grid": False,
    }
    
    # Create a matplotlib axes to draw on
    fig, ax = plt.subplots()
    
    # Call create_survey with vertical rule orientation
    create_survey(
        df,
        rule_flag=True,
        rule_length=rule_length,
        north_flag=False,
        excluded_nodes=None,
        rule_orientation="vertical",
        config=config_dict,
        ax=ax,
    )
    
    # Extract the rule position by looking at the drawn patches (Rectangles)
    rectangles = [p for p in ax.patches if isinstance(p, plt.Rectangle)]
    assert len(rectangles) >= 5, "Scale bar rule should be drawn as at least 5 segments"
    
    # Compute the scale bar bounding box
    x_starts = [r.get_x() for r in rectangles]
    y_starts = [r.get_y() for r in rectangles]
    widths = [r.get_width() for r in rectangles]
    heights = [r.get_height() for r in rectangles]
    
    # Total extent of the rectangles
    rule_x_min = min(x_starts)
    rule_x_max = max(x + w for x, w in zip(x_starts, widths))
    rule_y_min = min(y_starts)
    rule_y_max = max(y + h for y, h in zip(y_starts, heights))
    
    # The text label is positioned at x_start - 6, so we extend the boundary to the left
    # by 8 units to account for the label offset and label text width/margin.
    scale_bar_x_min = rule_x_min - 8
    scale_bar_x_max = rule_x_max
    scale_bar_y_min = rule_y_min
    scale_bar_y_max = rule_y_max
    
    # Assert that no survey data point is inside this bounding box
    x_coords = df["X"].values
    y_coords = df["Y"].values
    
    points_inside = (
        (x_coords >= scale_bar_x_min) &
        (x_coords <= scale_bar_x_max) &
        (y_coords >= scale_bar_y_min) &
        (y_coords <= scale_bar_y_max)
    )
    
    num_intersecting_points = sum(points_inside)
    
    # Clean up figure
    plt.close(fig)
    
    assert num_intersecting_points == 0, (
        f"Scale bar bounding box [{scale_bar_x_min}, {scale_bar_x_max}] x "
        f"[{scale_bar_y_min}, {scale_bar_y_max}] intersects with "
        f"{num_intersecting_points} survey data points!"
    )
