import pandas as pd
import matplotlib.pyplot as plt
from unittest.mock import patch
from cave_sketch.survey.graphics.survey_plot import create_survey

def verify():
    print("Verifying Survey Plot Placement Integration...")
    
    # Case: Data in top-left, top-right, bottom-right. Bottom-left should be chosen.
    df = pd.DataFrame({
        "X": [0, 100, 100],
        "Y": [100, 100, 0],
        "Type": ["station"] * 3,
        "Node_Id": ["A", "B", "C"],
        "Links": ["-"] * 3
    })
    
    config = {"marker_zoom": 10, "text_zoom": 10, "show_details": True}
    
    with patch("cave_sketch.survey.graphics.survey_plot._add_north_arrow") as mock_north:
        with patch("cave_sketch.survey.graphics.survey_plot._add_rule") as mock_rule:
            create_survey(df, rule_flag=True, north_flag=True, config=config, rule_length=20)
            
            north_coord = mock_north.call_args[1]["coords"]
            rule_coords = (mock_rule.call_args[1]["x_start"], mock_rule.call_args[1]["y_start"])
            
            print(f"North Coord: {north_coord}")
            print(f"Rule Coord: {rule_coords}")
            
            # For 0-100 bbox, inset 2% is 2. 
            # bottom-left anchor is (2, 2)
            if north_coord == (2.0, 2.0):
                print("SUCCESS: North symbol placed in empty bottom-left corner.")
            else:
                print(f"FAILURE: Expected (2.0, 2.0), got {north_coord}")

if __name__ == "__main__":
    verify()
