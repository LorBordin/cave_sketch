from typing import Optional

import streamlit as st

from cave_sketch.survey.config import TitleBlockInfo


def title_block_inputs_component() -> Optional[TitleBlockInfo]:
    """Inputs for the PDF title block. Returns None (after showing an error) when invalid."""
    st.markdown("#### 👤 Title block")
    col1, col2 = st.columns(2)
    with col1:
        surveyor_name = st.text_input("Surveyor name", value=st.session_state.surveyor_name)
    with col2:
        drawer_name = st.text_input("Drawer name", value=st.session_state.drawer_name)
    municipality = st.text_input("Municipality", value=st.session_state.municipality)

    lat_col, lon_col, elev_col = st.columns(3)
    with lat_col:
        latitude = st.number_input(
            "Latitude (° N)",
            min_value=-90.0,
            max_value=90.0,
            step=0.00001,
            format="%.5f",
            value=st.session_state.cave_latitude,
            placeholder="optional",
        )
    with lon_col:
        longitude = st.number_input(
            "Longitude (° E)",
            min_value=-180.0,
            max_value=180.0,
            step=0.00001,
            format="%.5f",
            value=st.session_state.cave_longitude,
            placeholder="optional",
        )
    with elev_col:
        elevation_m = st.number_input(
            "Elevation (m a.s.l.)",
            step=1.0,
            format="%.0f",
            value=st.session_state.cave_elevation_m,
            placeholder="optional",
        )

    st.session_state.surveyor_name = surveyor_name
    st.session_state.drawer_name = drawer_name
    st.session_state.municipality = municipality
    st.session_state.cave_latitude = latitude
    st.session_state.cave_longitude = longitude
    st.session_state.cave_elevation_m = elevation_m

    try:
        return TitleBlockInfo(
            surveyor_name=surveyor_name,
            drawer_name=drawer_name,
            municipality=municipality,
            latitude=latitude,
            longitude=longitude,
            elevation_m=elevation_m,
        )
    except ValueError as e:
        st.error(f"⚠️ {e}")
        return None
