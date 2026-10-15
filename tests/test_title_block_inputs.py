# tests/test_title_block_inputs.py
from unittest.mock import MagicMock, patch

from cave_sketch.survey.config import TitleBlockInfo


class MockSessionState:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _state():
    return MockSessionState(
        surveyor_name="", drawer_name="", municipality="",
        cave_latitude=None, cave_longitude=None, cave_elevation_m=None,
    )


def _setup(mock_st, texts, numbers):
    mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n)]
    mock_st.session_state = _state()
    mock_st.text_input.side_effect = texts      # surveyor, drawer, municipality
    mock_st.number_input.side_effect = numbers  # lat, lon, elevation


@patch("app.components.title_block_inputs.st")
def test_returns_info_and_persists_session(mock_st):
    from app.components.title_block_inputs import title_block_inputs_component

    _setup(mock_st, ["Alice", "Bob", "Genga"], [43.4, 12.9, 320.0])
    info = title_block_inputs_component()

    assert info == TitleBlockInfo(
        surveyor_name="Alice", drawer_name="Bob", municipality="Genga",
        latitude=43.4, longitude=12.9, elevation_m=320.0,
    )
    assert mock_st.session_state.drawer_name == "Bob"
    assert mock_st.session_state.cave_latitude == 43.4
    assert mock_st.session_state.cave_elevation_m == 320.0
    mock_st.error.assert_not_called()


@patch("app.components.title_block_inputs.st")
def test_empty_optional_numbers_are_none(mock_st):
    from app.components.title_block_inputs import title_block_inputs_component

    _setup(mock_st, ["", "", ""], [None, None, None])
    assert title_block_inputs_component() == TitleBlockInfo()


@patch("app.components.title_block_inputs.st")
def test_latitude_without_longitude_shows_error(mock_st):
    from app.components.title_block_inputs import title_block_inputs_component

    _setup(mock_st, ["", "", ""], [43.4, None, None])
    assert title_block_inputs_component() is None
    mock_st.error.assert_called_once()
    assert "together" in mock_st.error.call_args[0][0]
