from unittest.mock import MagicMock, patch


class MockSessionState:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get(self, key, default=None):
        return getattr(self, key, default)


@patch("app.components.settings_panel.st")
def test_settings_panel_centerline_enabled(mock_st):
    from app.components.settings_panel import settings_panel_component

    # Mock st.columns
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    # Setup session_state mock
    mock_st.session_state = MockSessionState(
        show_grid=True,
        show_centerline=True,
        show_details=True,
    )

    # Setup checkbox mock values
    mock_st.checkbox.side_effect = [True, True, True]

    # Setup number_input mock values
    mock_st.number_input.side_effect = [100, 0, 0.0, 0.0, 0.0]

    # Run the component
    res = settings_panel_component()

    # Verify that st.checkbox was called for "Show Polygonal Line"
    mock_st.checkbox.assert_any_call("Show Polygonal Line", value=True)
    # Verify that st.checkbox for "Show Stations Markers" was called with disabled=False
    mock_st.checkbox.assert_any_call("Show Stations Markers", value=True, disabled=False)

    assert res["show_centerline"] is True
    assert res["show_details"] is True


@patch("app.components.settings_panel.st")
def test_settings_panel_centerline_disabled(mock_st):
    from app.components.settings_panel import settings_panel_component

    # Mock st.columns
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    # Setup session_state mock
    mock_st.session_state = MockSessionState(
        show_grid=True,
        show_centerline=False,
        show_details=True,
    )

    # Setup checkbox mock values
    mock_st.checkbox.side_effect = [False, True, True]

    # Setup number_input mock values
    mock_st.number_input.side_effect = [100, 0, 0.0, 0.0, 0.0]

    # Run the component
    res = settings_panel_component()

    # Verify that st.checkbox was called for "Show Polygonal Line"
    mock_st.checkbox.assert_any_call("Show Polygonal Line", value=False)
    # Verify that st.checkbox for "Show Stations Markers" was called with disabled=True
    mock_st.checkbox.assert_any_call("Show Stations Markers", value=True, disabled=True)

    assert res["show_centerline"] is False
    assert res["show_details"] is True
