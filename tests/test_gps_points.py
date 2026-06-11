from unittest.mock import MagicMock, patch

import streamlit as st

from app.components.gps_points import validate_known_points


def test_validate_known_points_valid():
    st.session_state.known_points = [
        {"station": "A1", "lat": 45.678901, "lon": 12.345678}
    ]
    assert validate_known_points() is True


def test_validate_known_points_zero_coordinate():
    st.session_state.known_points = [
        {"station": "A1", "lat": 0.0, "lon": 0.0}
    ]
    assert validate_known_points() is True


def test_validate_known_points_invalid_station():
    st.session_state.known_points = [
        {"station": "   ", "lat": 45.678901, "lon": 12.345678}
    ]
    assert validate_known_points() is False


def test_validate_known_points_invalid_coordinate():
    st.session_state.known_points = [
        {"station": "A1", "lat": None, "lon": 12.345678}
    ]
    assert validate_known_points() is False


def test_validate_known_points_empty_points():
    st.session_state.known_points = []
    assert validate_known_points() is False


@patch("app.components.gps_points.st")
def test_gps_points_editor_component(mock_st):
    from app.components.gps_points import gps_points_editor_component

    mock_st.session_state = MagicMock()
    mock_st.session_state.known_points = [
        {"station": "A1", "lat": 45.678901, "lon": 12.345678}
    ]

    # Mock columns
    col_mock = MagicMock()
    col_mock.text_input = MagicMock(return_value="A1")
    mock_st.columns.side_effect = lambda n: [col_mock] * n

    gps_points_editor_component()

    # Verify we did call columns
    mock_st.columns.assert_any_call(3)
