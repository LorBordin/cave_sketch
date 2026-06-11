import streamlit as st

from cave_sketch.geo.coordinates import parse_coordinate


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
        
        # Get raw value or construct it from float representation
        lat_raw = point.get("lat_raw")
        if lat_raw is None:
            lat_float = point.get("lat")
            if lat_float is None:
                lat_raw = "0.000000"
            else:
                lat_raw = f"{lat_float:.6f}"
                
        lon_raw = point.get("lon_raw")
        if lon_raw is None:
            lon_float = point.get("lon")
            if lon_float is None:
                lon_raw = "0.000000"
            else:
                lon_raw = f"{lon_float:.6f}"

        lat_input = cols[1].text_input("Latitude", value=lat_raw, key=f"lat_{i}")
        lon_input = cols[2].text_input("Longitude", value=lon_raw, key=f"lon_{i}")

        point["lat_raw"] = lat_input
        point["lon_raw"] = lon_input

        point["lat"] = parse_coordinate(lat_input)
        point["lon"] = parse_coordinate(lon_input)

        if point["lat"] is None:
            cols[1].error("Invalid coordinate")
        if point["lon"] is None:
            cols[2].error("Invalid coordinate")

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
        if not str(pt.get("station", "")).strip():
            return False
        if pt.get("lat") is None or pt.get("lon") is None:
            return False
    return len(st.session_state.known_points) > 0
