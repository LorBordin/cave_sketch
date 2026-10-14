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

st.markdown("#### 👤 Surveyor name")
surveyor_name = st.text_input(
    "Surveyor Name",
    value=st.session_state.surveyor_name,
    label_visibility="collapsed",
)
st.session_state.surveyor_name = surveyor_name

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
                magnetic_variation_deg=settings.pop("magnetic_variation_deg", 0.0),
                csv_map_path=st.session_state.map_csv,
                csv_section_path=st.session_state.section_csv,
                child_csv_map_path=st.session_state.child_map_csv,
                child_csv_section_path=st.session_state.child_section_csv,
                parent_station=st.session_state.parent_station,
                child_station=st.session_state.child_station,
                section_protocol=SectionProtocol(st.session_state.section_protocol),
                output_path=pdf_path,
                surveyor_name=surveyor_name,
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
            st.session_state.effective_map_csv = (
                st.session_state.merged_map_csv or st.session_state.map_csv
            )

            if (
                st.session_state.child_section_csv
                and st.session_state.parent_station
                and st.session_state.child_station
            ):
                _parent_sec_df = pd.read_csv(st.session_state.section_csv)
                _child_sec_df = pd.read_csv(st.session_state.child_section_csv)
                _, _merged_sec_df = merge_surveys(
                    parent_map=None,
                    parent_section=_parent_sec_df,
                    child_map=None,
                    child_section=_child_sec_df,
                    parent_station=st.session_state.parent_station,
                    child_station=st.session_state.child_station,
                    section_protocol=SectionProtocol(st.session_state.section_protocol),
                )
                _merged_sec_path = st.session_state.files_dir / "merged_section.csv"
                if _merged_sec_df is not None:
                    _merged_sec_df.to_csv(_merged_sec_path, index=False)
                    st.session_state.merged_section_csv = _merged_sec_path
                else:
                    st.session_state.merged_section_csv = None
            else:
                st.session_state.merged_section_csv = None
            st.session_state.effective_section_csv = (
                st.session_state.merged_section_csv or st.session_state.section_csv
            )
    else:
        st.warning("⚠️ Please upload at least one file first.")

if st.session_state.cave_survey is not None:
    st.markdown("### 🗺️ Survey Preview")
    st.pyplot(st.session_state.cave_survey)
    st.success("✅ PDF Created!")

    from cave_sketch.utils.filename import sanitize_filename
    sanitized_name = sanitize_filename(st.session_state.survey_name)

    buttons = []
    if st.session_state.pdf_output_path and Path(st.session_state.pdf_output_path).exists():
        buttons.append(
            (
                "📥 Download PDF",
                st.session_state.pdf_output_path,
                f"{sanitized_name}.pdf",
                "application/pdf",
            )
        )

    effective_map = (
        st.session_state.effective_map_csv
        or st.session_state.merged_map_csv
        or st.session_state.map_csv
    )
    if effective_map and Path(effective_map).exists():
        buttons.append(
            ("📥 Download Map CSV", effective_map, f"{sanitized_name}_map.csv", "text/csv")
        )

    effective_sec = (
        st.session_state.effective_section_csv
        or st.session_state.merged_section_csv
        or st.session_state.section_csv
    )
    if effective_sec and Path(effective_sec).exists():
        buttons.append(
            ("📥 Download Section CSV", effective_sec, f"{sanitized_name}_section.csv", "text/csv")
        )

    if buttons:
        cols = st.columns(len(buttons))
        for col, (label, file_path, fname, mime) in zip(cols, buttons):
            with open(file_path, "rb") as f:
                col.download_button(
                    label, f, file_name=fname, mime=mime
                )
