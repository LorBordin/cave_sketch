
import streamlit as st

from cave_sketch.parse_dxf import parse_dxf


def file_uploader_component():
    """Component for uploading the main (parent) survey files."""
    st.markdown("## 📄 Upload your files (Main Survey)")

    col1, col2 = st.columns(2)
    with col1:
        map_file = st.file_uploader("Cave Map (.dxf)", type=["dxf", "csv"], key="map_uploader")
    with col2:
        section_file = st.file_uploader(
            "Cave Section (.dxf)", type=["dxf", "csv"], key="section_uploader"
        )

    if st.button("📥 Process Main Survey Files"):
        _process_files(map_file, section_file, is_child=False)

def survey_name_component():
    """Component for entering the survey name."""
    st.markdown("### 📝 Survey name")
    title = st.text_input("Survey Name", value="MySurvey", label_visibility="collapsed")
    return title

def child_file_uploader_component():
    """Component for uploading an additional (child) survey to merge."""
    # Keep open if files are loaded OR if files are currently in the uploader
    is_expanded = bool(
        st.session_state.child_map_csv or 
        st.session_state.child_section_csv or
        st.session_state.get("child_map_uploader") or
        st.session_state.get("child_section_uploader")
    )
    with st.expander("➕ Click here to merge another survey (Optional)", expanded=is_expanded):
        st.markdown("## 📎 Upload Child Survey")
        
        col1, col2 = st.columns(2)
        with col1:
            child_map_file = st.file_uploader(
                "Child Map (.dxf)", type=["dxf", "csv"], key="child_map_uploader"
            )
        with col2:
            child_section_file = st.file_uploader(
                "Child Section (.dxf)", type=["dxf", "csv"], key="child_section_uploader"
            )

        if st.button("📥 Process Child Survey Files"):
            _process_files(child_map_file, child_section_file, is_child=True)

def _process_files(map_file, section_file, is_child: bool = False):
    if not (map_file or section_file):
        st.warning("⚠️ Please upload at least one file.")
        return

    files_dir = st.session_state.files_dir
    prefix = "child_" if is_child else ""

    if map_file:
        map_file.seek(0)
        name = map_file.name.lower()
        map_csv = files_dir / f"{prefix}map.csv"

        if name.endswith(".dxf"):
            dxf_path = files_dir / f"{prefix}map.dxf"
            dxf_path.write_bytes(map_file.read())
            parse_dxf(input_path=dxf_path, output_path=map_csv)
        elif name.endswith(".csv"):
            map_csv.write_bytes(map_file.read())

        st.session_state[f"{prefix}map_csv"] = map_csv
        if not is_child:
            st.session_state.map_loaded = True
        st.success(f"✅ {'Child ' if is_child else ''}Map loaded: {map_file.name}")

    if section_file:
        section_file.seek(0)
        name = section_file.name.lower()
        section_csv = files_dir / f"{prefix}section.csv"

        if name.endswith(".dxf"):
            dxf_path = files_dir / f"{prefix}section.dxf"
            dxf_path.write_bytes(section_file.read())
            parse_dxf(input_path=dxf_path, output_path=section_csv)
        elif name.endswith(".csv"):
            section_csv.write_bytes(section_file.read())

        st.session_state[f"{prefix}section_csv"] = section_csv
        st.success(f"✅ {'Child ' if is_child else ''}Section loaded: {section_file.name}")
