from pathlib import Path
import streamlit as st
import tempfile

from cave_sketch.survey import draw_survey
from cave_sketch.parse_dxf import parse_dxf

st.title("Cave Survey Plot Generator")

# Upload widgets
map_file = st.file_uploader(
    "Upload Cave Map (.dxf)", 
    type=["dxf"], 
    key="map"
)
section_file = st.file_uploader(
    "Upload Cave Section (.dxf)", 
    type=["dxf"], 
    key="section"
)

# Run the survey function
if st.button("Generate Survey Plot"):
    
    if map_file and section_file:

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            map_path = tmpdir_path / "map.dxf"
            section_path = tmpdir_path / "section.dxf"

            # Save uploaded files
            map_path.write_bytes(map_file.read())
            section_path.write_bytes(section_file.read())

            with st.spinner("Creating survey plot..."):

                map_df = parse_dxf(
                    input_dxf_path=tmpdir_path/"map.dxf", 
                    out_file_path=tmpdir_path/"map.csv")
                section_df = parse_dxf(
                    input_dxf_path =tmpdir_path/"section.dxf",
                    out_file_path=tmpdir_path/"section.csv"
                )
                draw_survey(
                    title="Test",
                    csv_map_path=tmpdir_path/"map.csv",
                    csv_section_path=tmpdir_path/"section.csv",
                    output_path=tmpdir_path/"survey.pdf"
                )
            st.success("PDF Created!")
            with open(tmpdir_path/"survey.pdf", "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name="survey.pdf",
                    mime="application/pdf"
                )
    else:
        st.warning("Please upload both the cave map and section files.")
