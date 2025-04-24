from pathlib import Path
import streamlit as st
import tempfile

from cave_sketch.survey import draw_survey
from cave_sketch.parse_dxf import parse_dxf

st.set_page_config(page_title="Cave Survey Plot Generator", layout="centered")

st.title("🗺️ CaveSketch")
st.markdown("Generate beautifully formatted cave survey plots from your DXF files.")

st.markdown("## 📄 Upload your files")

col1, col2 = st.columns(2)
with col1:
    map_file = st.file_uploader("Cave Map (.dxf)", type=["dxf"], key="map")
with col2:
    section_file = st.file_uploader("Cave Section (.dxf)", type=["dxf"], key="section")

# Centra il titolo
st.markdown("<h3>📝 Survey name</h3>", unsafe_allow_html=True)
title = st.text_input("", value="MySurvey", label_visibility="collapsed")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ⚙️ Survey Settings")
    rule_length = st.number_input("📏 Rule length (m)", min_value=5, max_value=1000, step=5, value=100)
    rotation_deg = st.number_input("🧭 Map rotation (°)", min_value=-180, max_value=180, step=1, value=0)
    show_details = st.checkbox("Show Stations Markers", value=True)

with col2:
    st.markdown("### 🔍 Zoom settings")
    marker_zoom = st.number_input("🔍 Marker zoom [-1, 1]", min_value=-1., max_value=1., value=0., step=.1)
    text_zoom = st.number_input("🔠 Text zoom [-1, 1]", min_value=-1., max_value=1., value=0., step=.1)
    line_width_zoom = st.number_input("📏 Line width zoom [-1, 1]", min_value=-1., max_value=1., value=0., step=.1)

st.markdown("---")

if st.button("✨ Generate Survey Plot"):

    if map_file or section_file:

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # File paths
            map_path = tmpdir_path / "map.dxf"
            section_path = tmpdir_path / "section.dxf"
            pdf_output_path = tmpdir_path / "survey.pdf"

            map_csv = section_csv = None

            if map_file:
                map_file.seek(0)
                map_path.write_bytes(map_file.read())
                map_csv = tmpdir_path / "map.csv"
                _ = parse_dxf(input_dxf_path=map_path, out_file_path=map_csv)

            if section_file:
                section_file.seek(0)
                section_path.write_bytes(section_file.read())
                section_csv = tmpdir_path / "section.csv"
                _ = parse_dxf(input_dxf_path=section_path, out_file_path=section_csv)

            with st.spinner("🛠️ Creating survey plot..."):
                survey_options = {
                    "show_details": show_details,
                    "marker_zoom": marker_zoom,
                    "text_zoom": text_zoom,
                    "line_width_zoom": line_width_zoom,
                    "rotation_deg": rotation_deg
                }
                fig = draw_survey(
                    title=title,
                    rule_length=rule_length,
                    csv_map_path=map_csv,
                    csv_section_path=section_csv,
                    output_path=pdf_output_path,
                    config=survey_options
                )

            st.pyplot(fig)

            st.success("✅ PDF Created!")

            with open(pdf_output_path, "rb") as f:
                st.download_button(
                    label="📥 Download PDF",
                    data=f,
                    file_name="survey.pdf",
                    mime="application/pdf"
                )
    else:
        st.warning("⚠️ Please upload at least one .dxf file (map or section).")
