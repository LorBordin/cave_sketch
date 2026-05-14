import streamlit as st


def settings_panel_component():
    """Component for survey plot settings sliders and inputs."""
    st.markdown("### 📐 Survey Settings")
    col1, col2 = st.columns(2)

    with col1:
        rule_length = st.number_input(
            "📏 Rule length (m)", min_value=5, max_value=1000, step=5, value=100
        )
        rotation_deg = st.number_input(
            "🧭 Map rotation (°)", min_value=-180, max_value=180, step=1, value=0
        )
        show_details = st.checkbox("Show Stations Markers", value=True)

    with col2:
        marker_zoom = st.number_input(
            "🔍 Marker zoom [-1, 1]", min_value=-1.0, max_value=1.0, value=0.0, step=0.1
        )
        text_zoom = st.number_input(
            "🔠 Text zoom [-1, 1]", min_value=-1.0, max_value=1.0, value=0.0, step=0.1
        )
        line_width_zoom = st.number_input(
            "📏 Line width zoom [-1, 1]", min_value=-1.0, max_value=1.0, value=0.0, step=0.1
        )

    return {
        "rule_length": rule_length,
        "rotation_deg": rotation_deg,
        "show_details": show_details,
        "marker_zoom": marker_zoom,
        "text_zoom": text_zoom,
        "line_width_zoom": line_width_zoom,
    }
