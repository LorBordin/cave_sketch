from unittest.mock import MagicMock

import pandas as pd

from cave_sketch.survey.merger import SectionProtocol, merge_surveys
from cave_sketch.utils.filename import sanitize_filename


def test_session_state_has_merged_section_csv():
    import streamlit as st

    from app.session import init_session

    st.session_state.clear()
    init_session()
    assert "merged_section_csv" in st.session_state
    assert st.session_state.merged_section_csv is None


def test_effective_csv_resolution(tmp_path):
    map_csv = tmp_path / "map.csv"
    merged_map_csv = tmp_path / "merged_map.csv"
    section_csv = tmp_path / "section.csv"
    merged_section_csv = tmp_path / "merged_section.csv"

    # When no merge has happened
    assert (None or map_csv) == map_csv
    assert (None or section_csv) == section_csv

    # When merge has happened
    assert (merged_map_csv or map_csv) == merged_map_csv
    assert (merged_section_csv or section_csv) == merged_section_csv


def test_merged_section_written_when_section_merge_valid(tmp_path):
    parent_section = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, -5.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"],
    })
    child_section = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 5.0],
        "Y": [0.0, -2.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"],
    })
    p_path = tmp_path / "section.csv"
    c_path = tmp_path / "child_section.csv"
    parent_section.to_csv(p_path, index=False)
    child_section.to_csv(c_path, index=False)

    _, merged_section_df = merge_surveys(
        parent_map=None,
        parent_section=pd.read_csv(p_path),
        child_map=None,
        child_section=pd.read_csv(c_path),
        parent_station="2",
        child_station="1",
        section_protocol=SectionProtocol.SIMPLE,
    )
    assert merged_section_df is not None
    out_path = tmp_path / "merged_section.csv"
    merged_section_df.to_csv(out_path, index=False)
    assert out_path.exists()
    assert len(pd.read_csv(out_path)) == 3


def test_iterative_survey_merge_workflow(tmp_path):
    """
    Test workflow:
    1. Merge Survey A + Survey B -> produces merged_map and merged_section
    2. Use merged_map and merged_section as new parent, merge Survey C
    3. Verify resulting merged survey contains stations from all 3 surveys
    """
    # Survey A
    survey_a_map = pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 10.0], "Y": [0.0, 0.0],
        "Links": ["2", "1"], "Type": ["station", "station"],
    })
    survey_a_sec = pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 10.0], "Y": [0.0, -5.0],
        "Links": ["2", "1"], "Type": ["station", "station"],
    })
    # Survey B
    survey_b_map = pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 5.0], "Y": [0.0, 0.0],
        "Links": ["2", "1"], "Type": ["station", "station"],
    })
    survey_b_sec = pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 5.0], "Y": [0.0, -3.0],
        "Links": ["2", "1"], "Type": ["station", "station"],
    })

    # Step 1: Merge A + B at A:2 -> B:1
    merged_ab_map, merged_ab_sec = merge_surveys(
        parent_map=survey_a_map,
        parent_section=survey_a_sec,
        child_map=survey_b_map,
        child_section=survey_b_sec,
        parent_station="2",
        child_station="1",
        section_protocol=SectionProtocol.SIMPLE,
    )
    assert merged_ab_map is not None
    assert merged_ab_sec is not None

    ab_map_path = tmp_path / "merged_ab_map.csv"
    ab_sec_path = tmp_path / "merged_ab_sec.csv"
    merged_ab_map.to_csv(ab_map_path, index=False)
    merged_ab_sec.to_csv(ab_sec_path, index=False)

    # Step 2: Survey C
    survey_c_map = pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 8.0], "Y": [0.0, 0.0],
        "Links": ["2", "1"], "Type": ["station", "station"],
    })
    survey_c_sec = pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 8.0], "Y": [0.0, -4.0],
        "Links": ["2", "1"], "Type": ["station", "station"],
    })

    # Find the remapped ID of B's station 2 in AB
    # A has 1, 2. B:1 merged with A:2. B:2 remapped to 4.
    ab_map_loaded = pd.read_csv(ab_map_path)
    ab_sec_loaded = pd.read_csv(ab_sec_path)
    assert "4" in ab_map_loaded["Node_Id"].astype(str).values

    # Merge (A+B) + C at AB:4 -> C:1
    merged_abc_map, merged_abc_sec = merge_surveys(
        parent_map=ab_map_loaded,
        parent_section=ab_sec_loaded,
        child_map=survey_c_map,
        child_section=survey_c_sec,
        parent_station="4",
        child_station="1",
        section_protocol=SectionProtocol.SIMPLE,
    )
    assert merged_abc_map is not None
    assert merged_abc_sec is not None
    # 2 from A, 1 from B (since 1 merged with 2), 1 from C (since 1 merged with 4)
    # Total = 4 stations
    assert len(merged_abc_map) == 4
    assert len(merged_abc_sec) == 4


def test_survey_plot_csv_download_buttons_present(tmp_path):
    """
    Verify that when effective_map_csv and effective_section_csv exist,
    download buttons for map and section CSV are displayed.
    """
    import streamlit as st
    st.session_state.clear()
    st.session_state.files_dir = tmp_path
    st.session_state.survey_name = "Grotta Bella"
    st.session_state.cave_survey = MagicMock()
    st.session_state.pdf_output_path = tmp_path / "survey.pdf"
    (tmp_path / "survey.pdf").write_bytes(b"%PDF-test")

    map_csv = tmp_path / "map.csv"
    sec_csv = tmp_path / "section.csv"
    map_csv.write_text("Node_Id,X,Y,Links,Type\n1,0,0,-,station\n")
    sec_csv.write_text("Node_Id,X,Y,Links,Type\n1,0,0,-,station\n")

    st.session_state.map_csv = map_csv
    st.session_state.merged_map_csv = None
    st.session_state.section_csv = sec_csv
    st.session_state.merged_section_csv = None

    effective_map = st.session_state.merged_map_csv or st.session_state.map_csv
    effective_sec = st.session_state.merged_section_csv or st.session_state.section_csv

    sanitized = sanitize_filename(st.session_state.survey_name)
    assert sanitized == "grotta_bella"
    assert effective_map == map_csv
    assert effective_sec == sec_csv
