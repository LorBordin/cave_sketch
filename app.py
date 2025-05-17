from pathlib import Path
import streamlit as st
import tempfile
import os
import uuid

from cave_sketch.survey import draw_survey
from cave_sketch.parse_dxf import parse_dxf
from cave_sketch.map import draw_map

st.set_page_config(page_title="Cave Survey Plot Generator", layout="centered")

st.title("🗺️ CaveSketch")
st.markdown("Generate beautifully formatted cave survey plots from your DXF files.")

# Initialize session state variables if they don't exist
if "files_dir" not in st.session_state:
    # Create a unique directory name for this session
    session_id = str(uuid.uuid4())
    temp_root = tempfile.gettempdir()
    st.session_state.files_dir = Path(temp_root) / f"cavesketch_{session_id}"
    os.makedirs(st.session_state.files_dir, exist_ok=True)

if "cave_survey" not in st.session_state:
    st.session_state.cave_survey = None
    
if "pdf_output_path" not in st.session_state:
    st.session_state.pdf_output_path = None
    
if "map_loaded" not in st.session_state:
    st.session_state.map_loaded = False
    
if "map_csv" not in st.session_state:
    st.session_state.map_csv = None
    
if "section_csv" not in st.session_state:
    st.session_state.section_csv = None

if "known_points" not in st.session_state:
    st.session_state.known_points = [{"station": "", "lat": "", "lon": ""}]

# -------------------------------
# 1. Upload Files Section
# -------------------------------
st.markdown("## 📄 Upload your files")

col1, col2 = st.columns(2)
with col1:
    map_file = st.file_uploader("Cave Map (.dxf)", type=["dxf"], key="map")
with col2:
    section_file = st.file_uploader("Cave Section (.dxf)", type=["dxf"], key="section")

# Centra il titolo
st.markdown("<h3>📝 Survey name</h3>", unsafe_allow_html=True)
title = st.text_input("", value="MySurvey", label_visibility="collapsed")

# -------------------------------
# 2. Survey Plot Section
# -------------------------------
st.markdown("---")
st.markdown("## Cave Survey")
st.markdown("### 📐 Survey Settings")

col1, col2 = st.columns(2)

with col1:
    rule_length = st.number_input("📏 Rule length (m)", min_value=5, max_value=1000, step=5, value=100)
    rotation_deg = st.number_input("🧭 Map rotation (°)", min_value=-180, max_value=180, step=1, value=0)
    show_details = st.checkbox("Show Stations Markers", value=True)

with col2:
    marker_zoom = st.number_input("🔍 Marker zoom [-1, 1]", min_value=-1., max_value=1., value=0., step=.1)
    text_zoom = st.number_input("🔠 Text zoom [-1, 1]", min_value=-1., max_value=1., value=0., step=.1)
    line_width_zoom = st.number_input("📏 Line width zoom [-1, 1]", min_value=-1., max_value=1., value=0., step=.1)

# Process files outside the temporary directory context
if st.button("✨ Generate Survey Plot"):
    if map_file or section_file:
        files_dir = st.session_state.files_dir
        
        map_path = files_dir / "map.dxf"
        section_path = files_dir / "section.dxf"
        pdf_output_path = files_dir / "survey.pdf"
        
        map_csv = section_csv = None
        
        if map_file:
            map_file.seek(0)
            map_path.write_bytes(map_file.read())
            map_csv = files_dir / "map.csv"
            map_df = parse_dxf(input_dxf_path=map_path, out_file_path=map_csv)
            st.session_state.map_loaded = True
            st.session_state.map_csv = map_csv
        
        if section_file:
            section_file.seek(0)
            section_path.write_bytes(section_file.read())
            section_csv = files_dir / "section.csv"
            _ = parse_dxf(input_dxf_path=section_path, out_file_path=section_csv)
            st.session_state.section_csv = section_csv
        
        with st.spinner("🛠️ Creating survey plot..."):
            survey_options = {
                "show_details": show_details,
                "marker_zoom": marker_zoom,
                "text_zoom": text_zoom,
                "line_width_zoom": line_width_zoom,
                "rotation_deg": rotation_deg
            }
            cave_survey = draw_survey(
                title=title,
                rule_length=rule_length,
                csv_map_path=map_csv,
                csv_section_path=section_csv,
                output_path=pdf_output_path,
                config=survey_options
            )
            st.session_state.cave_survey = cave_survey
            st.session_state.pdf_output_path = pdf_output_path
    else:
        st.warning("⚠️ Please upload at least one .dxf file (map or section).")

# Display survey if it exists in session state
if st.session_state.cave_survey is not None:
    st.markdown("### 🗺️ Survey Preview")    
    st.pyplot(st.session_state.cave_survey)
    st.success("✅ PDF Created!")
    
    if st.session_state.pdf_output_path and Path(st.session_state.pdf_output_path).exists():
        with open(st.session_state.pdf_output_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="survey.pdf", mime="application/pdf")

# -------------------------------
# 3. GPS Map Section
# -------------------------------
st.markdown("---")
st.markdown("## 🌍 Position Cave on Map")

st.markdown("Input known GPS coordinates for known survey stations.")

def validate_known_points(points):
    for pt in points:
        if not pt["station"].strip() or not pt["lat"] or not pt["lon"]:
            return False
    return True

for i, point in enumerate(st.session_state.known_points):
    st.markdown(f"**Known Point {i + 1}**")
    cols = st.columns(3)
    point["station"] = cols[0].text_input("Station ID", value=point["station"], key=f"station_{i}")
    point["lat"] = cols[1].number_input("Latitude", value=float(point["lat"] or 0), format="%0.6f", key=f"lat_{i}")
    point["lon"] = cols[2].number_input("Longitude", value=float(point["lon"] or 0), format="%0.6f", key=f"lon_{i}")


def add_known_point():
    st.session_state.known_points.append({"station": "", "lat": "", "lon": ""})
    
def remove_known_point():
    if st.session_state.known_points:
        st.session_state.known_points.pop()

col1, col2 = st.columns([1, 1])  # You can tweak the ratio as needed

with col1:
    st.button("➕ Add another known point", on_click=add_known_point)

with col2:
    st.button("➖ Remove last known point", on_click=remove_known_point)

if "html_map" not in st.session_state:
    st.session_state.html_map = None

if st.button("🌍 Generate Geo Map"):
    if not validate_known_points(st.session_state.known_points):
        st.warning("⚠️ Please fill in all fields (Station ID, Latitude, Longitude) for each known point.")
    elif not st.session_state.map_loaded:
        st.warning("⚠️ Please load a map of the cave before creating the Geo Map.")
    else:
        # Generate HTML map
        files_dir = st.session_state.files_dir
        html_path = files_dir / "survey.html"
        html_map = draw_map(
            map_path=st.session_state.map_csv, 
            gps_points=st.session_state.known_points, 
            output_path=html_path
        )
        
        # Read the HTML content from the file
        if html_path.exists():
            with open(html_path, "r") as f:
                html_content = f.read()
                st.session_state.html_content = html_content
                st.session_state.html_path = html_path
            st.success("✅ Map generated!")
        else:
            st.error("Failed to generate HTML map file.")

# Display HTML map if it exists
if "html_content" in st.session_state and st.session_state.html_content is not None:
    st.markdown("### 🗺️ Map Preview")
    st.components.v1.html(st.session_state.html_content, height=400)
    
    if "html_path" in st.session_state and Path(st.session_state.html_path).exists():
        with open(st.session_state.html_path, "rb") as f:
            st.download_button(
                label="📥 Download HTML Map",
                data=f.read(),
                file_name="cave_map.html",
                mime="text/html"
            )