import streamlit as st


def gps_points_editor_component():
    """Component for editing known GPS points."""
    st.markdown("### 📍 Known GPS Points")
    st.markdown("Input known GPS coordinates for known survey stations.")

    known_points = st.session_state.known_points

    for i, point in enumerate(known_points):
        st.markdown(f"**Known Point {i + 1}**")
        cols = st.columns(3)
        point["station"] = cols[0].text_input(
            "Station ID", value=point["station"], key=f"station_{i}"
        )
        point["lat"] = cols[1].number_input(
            "Latitude", value=float(point["lat"] or 0.0), format="%0.6f", key=f"lat_{i}"
        )
        point["lon"] = cols[2].number_input(
            "Longitude", value=float(point["lon"] or 0.0), format="%0.6f", key=f"lon_{i}"
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add another known point"):
            st.session_state.known_points.append({"station": "", "lat": 0.0, "lon": 0.0})
            st.rerun()
    with col2:
        if st.button("➖ Remove last known point") and len(st.session_state.known_points) > 0:
            st.session_state.known_points.pop()
            st.rerun()


def validate_known_points():
    """Validate that all known points have required fields."""
    for pt in st.session_state.known_points:
        if not str(pt["station"]).strip() or not pt["lat"] or not pt["lon"]:
            return False
    return len(st.session_state.known_points) > 0
