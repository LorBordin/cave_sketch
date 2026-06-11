from pathlib import Path

import pandas as pd
import streamlit as st
from components.file_upload import (
    child_file_uploader_component,
    file_uploader_component,
    survey_name_component,
)
from components.settings_panel import settings_panel_component
from components.sidebar import render_sidebar
from session import init_session

from cave_sketch.survey import draw_survey

st.set_page_config(page_title="Cave Survey Plot", layout="centered")
init_session()
render_sidebar()

st.title("📐 Cave Survey Plot")
file_uploader_component()
child_file_uploader_component()

st.markdown("---")
title = survey_name_component()

merge_valid = True
if st.session_state.child_map_csv or st.session_state.child_section_csv:
    from components.merging_controls import merging_controls_component
    merge_valid = merging_controls_component()

settings = settings_panel_component()

if st.button("✨ Generate Survey Plot"):
    if not merge_valid:
        st.error("⚠️ Please resolve the merging errors before generating the plot.")
    elif st.session_state.map_csv or st.session_state.section_csv:
        from cave_sketch.survey.merger import SectionProtocol, merge_surveys
        pdf_path = st.session_state.files_dir / "survey.pdf"
        with st.spinner("🛠️ Creating survey plot..."):
            fig = draw_survey(
                title=title,
                rule_length=settings.pop("rule_length"),
                csv_map_path=st.session_state.map_csv,
                csv_section_path=st.session_state.section_csv,
                child_csv_map_path=st.session_state.child_map_csv,
                child_csv_section_path=st.session_state.child_section_csv,
                parent_station=st.session_state.parent_station,
                child_station=st.session_state.child_station,
                section_protocol=SectionProtocol(st.session_state.section_protocol),
                output_path=pdf_path,
                config=settings,
            )
            st.session_state.cave_survey = fig
            st.session_state.pdf_output_path = pdf_path
            if (
                st.session_state.child_map_csv
                and st.session_state.parent_station
                and st.session_state.child_station
            ):
                _parent_df = pd.read_csv(st.session_state.map_csv)
                _child_df = pd.read_csv(st.session_state.child_map_csv)
                _merged_df, _ = merge_surveys(
                    parent_map=_parent_df,
                    parent_section=None,
                    child_map=_child_df,
                    child_section=None,
                    parent_station=st.session_state.parent_station,
                    child_station=st.session_state.child_station,
                    section_protocol=SectionProtocol(st.session_state.section_protocol),
                )
                _merged_path = st.session_state.files_dir / "merged_map.csv"
                if _merged_df is not None:
                    _merged_df.to_csv(_merged_path, index=False)
                    st.session_state.merged_map_csv = _merged_path
                else:
                    st.session_state.merged_map_csv = None
            else:
                st.session_state.merged_map_csv = None
    else:
        st.warning("⚠️ Please upload at least one file first.")

if st.session_state.cave_survey is not None:
    st.markdown("### 🗺️ Survey Preview")
    st.pyplot(st.session_state.cave_survey)
    st.success("✅ PDF Created!")

    if st.session_state.pdf_output_path and Path(st.session_state.pdf_output_path).exists():
        from cave_sketch.utils.filename import sanitize_filename
        sanitized_name = sanitize_filename(st.session_state.survey_name)
        with open(st.session_state.pdf_output_path, "rb") as f:
            st.download_button(
                "📥 Download PDF", f, file_name=f"{sanitized_name}.pdf", mime="application/pdf"
            )
