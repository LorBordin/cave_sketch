import streamlit as st
import pandas as pd
import re

def merging_controls_component():
    """Component for station matching and section protocol selection."""
    if not (st.session_state.child_map_csv or st.session_state.child_section_csv):
        return
    
    st.markdown("## 🔗 Survey Merging Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        parent_station = st.text_input(
            "Matching Station ID in Main Survey (e.g., 30)",
            value=st.session_state.parent_station,
            key="parent_station_input"
        )
    with col2:
        child_station = st.text_input(
            "Matching Station ID in Child Survey (e.g., 47)",
            value=st.session_state.child_station,
            key="child_station_input"
        )
        
    st.session_state.parent_station = parent_station
    st.session_state.child_station = child_station

    # Validation
    valid_numeric = True
    if parent_station and not re.fullmatch(r"\d+", parent_station):
        st.error("⚠️ Main Station ID must be purely numeric (e.g., '30', not '12P4').")
        valid_numeric = False
    if child_station and not re.fullmatch(r"\d+", child_station):
        st.error("⚠️ Child Station ID must be purely numeric (e.g., '47', not '54P1').")
        valid_numeric = False
        
    # Check if station exists in DataFrames
    station_exists = True
    if valid_numeric and parent_station and child_station:
        if st.session_state.map_csv:
            df = pd.read_csv(st.session_state.map_csv)
            if parent_station not in df["Node_Id"].astype(str).values:
                st.error(f"⚠️ Station '{parent_station}' not found in Main Map survey.")
                station_exists = False
        elif st.session_state.section_csv:
            df = pd.read_csv(st.session_state.section_csv)
            if parent_station not in df["Node_Id"].astype(str).values:
                st.error(f"⚠️ Station '{parent_station}' not found in Main Section survey.")
                station_exists = False
                
        if st.session_state.child_map_csv:
            df = pd.read_csv(st.session_state.child_map_csv)
            if child_station not in df["Node_Id"].astype(str).values:
                st.error(f"⚠️ Station '{child_station}' not found in Child Map survey.")
                station_exists = False
        elif st.session_state.child_section_csv:
            df = pd.read_csv(st.session_state.child_section_csv)
            if child_station not in df["Node_Id"].astype(str).values:
                st.error(f"⚠️ Station '{child_station}' not found in Child Section survey.")
                station_exists = False

    # Section Protocol Selector (appears only if child section is uploaded)
    if st.session_state.child_section_csv:
        st.markdown("### 📐 Section View Merging Protocol")
        protocol = st.radio(
            "Select protocol for Section View merge:",
            options=["simple", "mirror", "displacement"],
            format_func=lambda x: x.capitalize(),
            index=["simple", "mirror", "displacement"].index(st.session_state.section_protocol),
            key="protocol_radio"
        )
        st.session_state.section_protocol = protocol

    return valid_numeric and station_exists and bool(parent_station and child_station)
