import streamlit as st
from components.gps_points import gps_points_editor_component, validate_known_points
from session import init_session

from cave_sketch.satellite_view import draw_map

st.set_page_config(page_title="Satellite Map", layout="centered")
init_session()

st.title("🌍 Satellite Map")
gps_points_editor_component()

rotation_angle = st.number_input("🧭 Map rotation angle (°)", value=st.session_state.rotation_angle)
st.session_state.rotation_angle = rotation_angle

st.markdown("#### 📁 Upload Additional JSON Maps")
uploaded_json = st.file_uploader("JSON maps", type=["json"], accept_multiple_files=True)

if uploaded_json:
    for f in uploaded_json:
        path = st.session_state.files_dir / f"uploaded_{f.name}"
        path.write_bytes(f.read())
        if str(path) not in st.session_state.uploaded_json_paths:
            st.session_state.uploaded_json_paths.append(str(path))

col1, col2 = st.columns(2)
if col1.button("🌍 Generate HTML Map"):
    if not validate_known_points():
        st.warning("⚠️ Please fill in all GPS point fields.")
    elif not st.session_state.map_loaded:
        st.warning("⚠️ Please load a map in the Survey Plot page first.")
    else:
        html_path = st.session_state.files_dir / "survey.html"
        html_map, json_path = draw_map(
            map_path=str(st.session_state.map_csv),
            gps_points=st.session_state.known_points,
            output_path=str(html_path),
            map_name="Current Cave",
            additional_json_maps=st.session_state.uploaded_json_paths,
            rotation_angle=rotation_angle,
        )
        st.session_state.current_json_path = json_path
        st.session_state.html_path = html_path
        with open(html_path, "r") as html_f:
            st.session_state.html_content = html_f.read()

if "html_content" in st.session_state and st.session_state.html_content:
    st.components.v1.html(st.session_state.html_content, height=400)
    col1, col2 = st.columns(2)
    with open(st.session_state.html_path, "rb") as html_f_bin:
        col1.download_button("📥 Download HTML Map", html_f_bin, file_name="cave_map.html")
    with open(st.session_state.current_json_path, "rb") as json_f_bin:
        col2.download_button("📥 Download JSON Map", json_f_bin, file_name="cave_map.json")
