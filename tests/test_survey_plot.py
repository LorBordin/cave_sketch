import matplotlib.pyplot as plt
import pandas as pd
import pytest

from cave_sketch.survey.graphics.survey_plot import create_survey


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "X": [0.0, 10.0, 20.0],
        "Y": [0.0, 10.0, 20.0],
        "Type": ["station", "station", "station"],
        "Node_Id": ["A", "B", "C"],
        "Links": ["-", "-", "-"]
    })


def test_station_id_visibility_and_offset(sample_df):
    """
    Verify each station ID text artist has zorder >= 10 and is offset 
    from the station marker coordinates.
    """
    fig, ax = plt.subplots()
    config = {
        "show_details": True,
        "marker_zoom": 10,
        "text_zoom": 10
    }
    
    create_survey(
        df=sample_df,
        rule_flag=False,
        north_flag=False,
        config=config,
        ax=ax
    )
    
    texts = ax.texts
    assert len(texts) == 3, f"Expected 3 station text labels, found {len(texts)}"
    
    # Map from Node_Id to expected raw coordinates
    coord_map = {
        "A": (0.0, 0.0),
        "B": (10.0, 10.0),
        "C": (20.0, 20.0),
    }
    
    for text_artist in texts:
        node_id = text_artist.get_text()
        assert node_id in coord_map, f"Unexpected text label: {node_id}"
        
        # Verify Z-order is >= 10
        zorder = text_artist.get_zorder()
        assert zorder >= 10, f"Expected zorder >= 10 for node {node_id}, got {zorder}"
        
        # Verify position is offset
        pos_x, pos_y = text_artist.get_position()
        orig_x, orig_y = coord_map[node_id]
        
        assert pos_x != orig_x or pos_y != orig_y, (
            f"Expected text for node {node_id} to be offset from ({orig_x}, {orig_y}), "
            f"but got ({pos_x}, {pos_y})"
        )

    plt.close(fig)
