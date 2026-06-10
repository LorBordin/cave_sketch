import unittest
from unittest.mock import MagicMock, patch

def test_render_sidebar_imports():
    """Test that the sidebar component can be imported."""
    try:
        from app.components.sidebar import render_sidebar
    except ImportError:
        assert False, "Could not import render_sidebar"

@patch("app.components.sidebar.st")
def test_render_sidebar_calls_st(mock_st):
    """Test that render_sidebar calls streamlit sidebar and button."""
    from app.components.sidebar import render_sidebar
    
    # Mock the context manager st.sidebar
    mock_st.sidebar = MagicMock()
    mock_st.sidebar.__enter__ = MagicMock()
    mock_st.sidebar.__exit__ = MagicMock()
    
    render_sidebar()
    
    mock_st.sidebar.__enter__.assert_called_once()
    mock_st.button.assert_called_with("🗑️ Clear Session Files")
