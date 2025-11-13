from pathlib import Path
import streamlit as st
import tempfile
import uuid
import json
import os

from cave_sketch.survey import draw_survey
from cave_sketch.parse_dxf import parse_dxf
from cave_sketch.satellite_view import draw_map

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
    map_file = st.file_uploader("Cave Map (.dxf)", type=["dxf", "csv"], key="map")
with col2:
    section_file = st.file_uploader("Cave Section (.dxf)", type=["dxf", "csv"], key="section")

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
            map_file_name = map_file.name.lower()
        
            if map_file_name.endswith(".dxf"):
                # Save DXF file and parse it to CSV
                map_path = files_dir / "map.dxf"
                map_path.write_bytes(map_file.read())
                map_csv = files_dir / "map.csv"
                map_df = parse_dxf(input_dxf_path=map_path, out_file_path=map_csv)
        
            elif map_file_name.endswith(".csv"):
                # Save CSV file directly
                map_csv = files_dir / "map.csv"
                map_csv.write_bytes(map_file.read())
        
            else:
                st.error("Unsupported file type. Please upload a .dxf or .csv file.")
                st.stop()

            st.session_state.map_loaded = True
            st.session_state.map_csv = map_csv
        
        if section_file:
            section_file.seek(0)
            section_file_name = section_file.name.lower()

            if section_file_name.endswith('.dxf'):
                map_path = files_dir / "section.dxf"
                section_path.write_bytes(section_file.read())
                section_csv = files_dir / "section.csv"
                _ = parse_dxf(input_dxf_path=section_path, out_file_path=section_csv)
            
            elif section_file_name.endswith(".csv"):
                section_csv = files_dir / "section.csv"
                section_csv.write_bytes(section_file.read())
                
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

# 🔹 NEW: Rotation angle input
rotation_angle = st.number_input(
    "🧭 Map rotation angle (degrees)",
    min_value=-180.0,
    max_value=180.0,
    value=0.0,
    step=1.0,
    help="Rotate the cave map around its center. Positive = counterclockwise, negative = clockwise."
)

# Save it to session_state (optional, so it persists)
st.session_state.rotation_angle = rotation_angle

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

col1, col2 = st.columns([1, 1])
with col1:
    st.button("➕ Add another known point", on_click=add_known_point)
with col2:
    st.button("➖ Remove last known point", on_click=remove_known_point)

if "html_map" not in st.session_state:
    st.session_state.html_map = None

# Add JSON map upload field
st.markdown("#### 📁 Upload Additional JSON Maps")
uploaded_json_maps = st.file_uploader(
    "Upload JSON map files to combine with current map", 
    type=["json"], 
    accept_multiple_files=True,
    help="Upload previously exported cave maps in JSON format to combine them with the current map"
)

# Initialize session state for uploaded JSON maps
if "uploaded_json_paths" not in st.session_state:
    st.session_state.uploaded_json_paths = []

# Process uploaded JSON maps
if uploaded_json_maps:
    files_dir = st.session_state.files_dir
    new_json_paths = []
    
    for uploaded_file in uploaded_json_maps:
        json_path = files_dir / f"uploaded_{uploaded_file.name}"
        json_path.write_bytes(uploaded_file.read())
        new_json_paths.append(str(json_path))
        
        # Try to get map name from JSON
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                map_name = data.get('name', uploaded_file.name.replace('.json', ''))
            st.success(f"✅ Uploaded JSON map: '{map_name}'")
        except:
            st.warning(f"⚠️ Could not read map name from {uploaded_file.name}")
    
    # Update session state with new paths
    st.session_state.uploaded_json_paths = new_json_paths

# Handle uploaded HTML or generate maps
col1, col2 = st.columns(2)

with col1:
    # Existing button
    generate_html_clicked = st.button("🌍 Generate HTML Map")

with col2:
    # NEW: JSON download button
    generate_json_clicked = st.button("📄 Generate & Download JSON")

# Process HTML map generation
if generate_html_clicked:
    files_dir = st.session_state.files_dir
    html_path = files_dir / "survey.html"

    if not validate_known_points(st.session_state.known_points):
        st.warning("⚠️ Please fill in all fields (Station ID, Latitude, Longitude) for each known point.")
    elif not st.session_state.map_loaded:
        st.warning("⚠️ Please load a map of the cave before creating the HTML Map.")
    else:
        # Use uploaded JSON maps if available
        additional_json_maps = st.session_state.uploaded_json_paths if st.session_state.uploaded_json_paths else None
        
        html_map, json_path = draw_map(
            map_path=str(st.session_state.map_csv), 
            gps_points=st.session_state.known_points, 
            output_path=str(html_path),
            map_name="Current Cave",
            additional_json_maps=additional_json_maps,
            rotation_angle=rotation_angle
        )
        st.session_state.current_json_path = json_path
        st.success("✅ HTML Map generated!")

    # Load and display the map
    if html_path.exists():
        with open(html_path, "r") as f:
            html_content = f.read()
            st.session_state.html_content = html_content
            st.session_state.html_path = html_path
    else:
        st.error("⚠️ Failed to load HTML map file.")

# Process JSON map generation and download
if generate_json_clicked:
    if not validate_known_points(st.session_state.known_points):
        st.warning("⚠️ Please fill in all fields (Station ID, Latitude, Longitude) for each known point.")
    elif not st.session_state.map_loaded:
        st.warning("⚠️ Please load a map of the cave before creating the JSON Map.")
    else:
        files_dir = st.session_state.files_dir
        json_path = files_dir / "survey.json"
        
        # Use uploaded JSON maps if available
        additional_json_maps = st.session_state.uploaded_json_paths if st.session_state.uploaded_json_paths else None
        
        # Generate map (we only need the JSON, but draw_map creates both)
        html_map, json_output_path = draw_map(
            map_path=str(st.session_state.map_csv), 
            gps_points=st.session_state.known_points, 
            output_path=str(files_dir / "temp_survey.html"),  # Temporary HTML file
            map_name="Current Cave",
            additional_json_maps=additional_json_maps
        )
        
        st.session_state.current_json_path = json_output_path
        st.success("✅ JSON Map generated!")

# Display map if it exists
if "html_content" in st.session_state and st.session_state.html_content is not None:
    st.markdown("### 🗺️ Map Preview")
    st.components.v1.html(st.session_state.html_content, height=400)

    # Download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if "html_path" in st.session_state and Path(st.session_state.html_path).exists():
            with open(st.session_state.html_path, "rb") as f:
                st.download_button(
                    label="📥 Download HTML Map",
                    data=f.read(),
                    file_name="cave_map.html",
                    mime="text/html"
                )
    
    with col2:
        if "current_json_path" in st.session_state and Path(st.session_state.current_json_path).exists():
            with open(st.session_state.current_json_path, "rb") as f:
                st.download_button(
                    label="📥 Download JSON Map",
                    data=f.read(),
                    file_name="cave_map.json",
                    mime="application/json"
                )

# Display uploaded JSON maps info
if st.session_state.uploaded_json_paths:
    st.markdown("### 📋 Currently Loaded JSON Maps")
    for i, json_path in enumerate(st.session_state.uploaded_json_paths):
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                map_name = data.get('name', f'Map {i+1}')
            st.info(f"📍 **{map_name}** - {Path(json_path).name}")
        except:
            st.info(f"📍 **Unknown Map** - {Path(json_path).name}")
    
    if st.button("🗑️ Clear All Uploaded JSON Maps"):
        st.session_state.uploaded_json_paths = []
        st.rerun()