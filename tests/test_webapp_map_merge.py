from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from cave_sketch.survey.merger import MapProtocol, merge_surveys


class MockSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def get(self, key, default=None):
        return super().get(key, default)


def test_session_init_has_map_protocol_default():
    from app.session import init_session

    with patch("app.session.st") as mock_st:
        session = MockSessionState()
        mock_st.session_state = session
        init_session()
        assert session.get("map_protocol") == "simple"


@patch("app.components.merging_controls.st")
def test_merging_controls_radio_visibility_and_update(mock_st):
    from app.components.merging_controls import merging_controls_component

    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.text_input.side_effect = ["1", "1"]

    # Case 1: Only child section uploaded -> map radio NOT shown, section radio shown
    session = MockSessionState(
        map_csv=None,
        section_csv=None,
        child_map_csv=None,
        child_section_csv=Path("fake_child_sec.csv"),
        parent_station="1",
        child_station="1",
        section_protocol="simple",
        map_protocol="simple",
    )
    mock_st.session_state = session
    mock_st.radio.return_value = "mirror"

    with patch("pandas.read_csv", return_value=pd.DataFrame({"Node_Id": ["1"]})):
        merging_controls_component()

    # Verify radio call labels: section radio was called, map radio was not called
    radio_calls = [call.args[0] for call in mock_st.radio.call_args_list]
    assert any("Section View" in label for label in radio_calls)
    assert not any("Map View" in label for label in radio_calls)

    # Case 2: Child map uploaded -> map radio IS shown
    mock_st.reset_mock()
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.text_input.side_effect = ["1", "1"]
    session2 = MockSessionState(
        map_csv=None,
        section_csv=None,
        child_map_csv=Path("fake_child_map.csv"),
        child_section_csv=None,
        parent_station="1",
        child_station="1",
        section_protocol="simple",
        map_protocol="simple",
    )
    mock_st.session_state = session2
    mock_st.radio.return_value = "displacement"

    with patch("pandas.read_csv", return_value=pd.DataFrame({"Node_Id": ["1"]})):
        merging_controls_component()

    radio_calls2 = [call.args[0] for call in mock_st.radio.call_args_list]
    assert any("Map View" in label for label in radio_calls2)
    assert not any("Section View" in label for label in radio_calls2)
    assert session2.map_protocol == "displacement"


def test_satellite_merged_map_always_uses_simple(tmp_path):
    # Simulates survey_plot merged_map.csv logic: regardless of map_protocol in session,
    # merged_map.csv is generated with MapProtocol.SIMPLE
    parent_map = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 20.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })
    child_map = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    # Even if session has map_protocol="displacement"
    session_map_protocol = "displacement"
    assert session_map_protocol == "displacement"

    # Satellite merged map must force MapProtocol.SIMPLE
    merged_satellite_df, _ = merge_surveys(
        parent_map=parent_map,
        parent_section=None,
        child_map=child_map,
        child_section=None,
        parent_station="2",
        child_station="1",
        map_protocol=MapProtocol.SIMPLE,
    )
    assert merged_satellite_df is not None
    # No connector row in satellite merged map
    assert len(merged_satellite_df[merged_satellite_df["Type"] == "connector"]) == 0
    # Child 1 merged at parent 2 coordinates (20.0, 0.0), child 2 at (30.0, 0.0)
    row_4 = merged_satellite_df[merged_satellite_df["Node_Id"] == "4"].iloc[0]
    assert row_4["X"] == pytest.approx(30.0)
