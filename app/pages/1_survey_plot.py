from pathlib import Path

import streamlit as st

from app.components.file_upload import file_uploader_component
from app.components.settings_panel import settings_panel_component
from app.session import init_session
from cave_sketch.survey import draw_survey

st.set_page_config(page_title="Cave Survey Plot", layout="centered")
init_session()

st.title("📐 Cave Survey Plot")
title = file_uploader_component()
st.markdown("---")
settings = settings_panel_component()

if st.button("✨ Generate Survey Plot"):
    if st.session_state.map_csv or st.session_state.section_csv:
        pdf_path = st.session_state.files_dir / "survey.pdf"
        with st.spinner("🛠️ Creating survey plot..."):
            fig = draw_survey(
                title=title,
                rule_length=settings.pop("rule_length"),
                csv_map_path=st.session_state.map_csv,
                csv_section_path=st.session_state.section_csv,
                output_path=pdf_path,
                config=settings
            )
            st.session_state.cave_survey = fig
            st.session_state.pdf_output_path = pdf_path
    else:
        st.warning("⚠️ Please upload at least one file first.")

if st.session_state.cave_survey is not None:
    st.markdown("### 🗺️ Survey Preview")    
    st.pyplot(st.session_state.cave_survey)
    st.success("✅ PDF Created!")
    
    if st.session_state.pdf_output_path and Path(st.session_state.pdf_output_path).exists():
        with open(st.session_state.pdf_output_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name="survey.pdf", mime="application/pdf")
