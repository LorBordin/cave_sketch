# app/components/sidebar.py
import shutil

import streamlit as st


def render_sidebar() -> None:
    """Render the persistent sidebar content, including the clear session button."""
    with st.sidebar:
        if st.button("🗑️ Clear Session Files"):
            shutil.rmtree(st.session_state.files_dir, ignore_errors=True)
            st.session_state.clear()
            st.toast("Session cleared!", icon="✅")
            st.rerun()
