
import streamlit as st

from cave_sketch.parse_dxf import parse_dxf


def file_uploader_component():
    """Shared component for uploading DXF or CSV files."""
    st.markdown("## 📄 Upload your files")
    
    col1, col2 = st.columns(2)
    with col1:
        map_file = st.file_uploader(
            "Cave Map (.dxf)", type=["dxf", "csv"], key="map_uploader"
        )
    with col2:
        section_file = st.file_uploader(
            "Cave Section (.dxf)", type=["dxf", "csv"], key="section_uploader"
        )
        
    st.markdown("<h3>📝 Survey name</h3>", unsafe_allow_html=True)
    title = st.text_input("Survey Name", value="MySurvey", label_visibility="collapsed")
    
    if st.button("📥 Process Uploaded Files"):
        _process_files(map_file, section_file)
        
    return title

def _process_files(map_file, section_file):
    if not (map_file or section_file):
        st.warning("⚠️ Please upload at least one file.")
        return

    files_dir = st.session_state.files_dir
    
    if map_file:
        map_file.seek(0)
        name = map_file.name.lower()
        map_csv = files_dir / "map.csv"
        
        if name.endswith(".dxf"):
            dxf_path = files_dir / "map.dxf"
            dxf_path.write_bytes(map_file.read())
            parse_dxf(input_path=dxf_path, output_path=map_csv)
        elif name.endswith(".csv"):
            map_csv.write_bytes(map_file.read())
            
        st.session_state.map_csv = map_csv
        st.session_state.map_loaded = True
        st.success(f"✅ Map loaded: {map_file.name}")

    if section_file:
        section_file.seek(0)
        name = section_file.name.lower()
        section_csv = files_dir / "section.csv"
        
        if name.endswith(".dxf"):
            dxf_path = files_dir / "section.dxf"
            dxf_path.write_bytes(section_file.read())
            parse_dxf(input_path=dxf_path, output_path=section_csv)
        elif name.endswith(".csv"):
            section_csv.write_bytes(section_file.read())
            
        st.session_state.section_csv = section_csv
        st.success(f"✅ Section loaded: {section_file.name}")
