# Implementation Plan: Merged Survey Support in Satellite Map

## Phase 1: State Initialization and Unit Tests
- [ ] Task: Update `app/session.py` to include `merged_map_csv` initialized to `None` in `init_session` and added to the `AppState` TypedDict.
- [ ] Task: Create a test for the satellite map argument selection.
    - [ ] Create `tests/test_satellite_map.py` (using `unittest.mock` or Streamlit's `AppTest`) to verify that the application correctly passes `st.session_state.merged_map_csv` instead of `st.session_state.map_csv` to the `draw_map` function when a merged survey exists.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: State Initialization and Unit Tests' (Protocol in workflow.md)

## Phase 2: Implementation
- [ ] Task: Update `app/pages/1_survey_plot.py` to save the merged map.
    - [ ] When the plot is generated with a valid merge (i.e., `child_map_csv`, `parent_station`, and `child_station` are present), call `merge_surveys` in the glue code to get the merged map DataFrame.
    - [ ] Save this DataFrame to a CSV file (`merged_map.csv` in `st.session_state.files_dir`) and assign its path to `st.session_state.merged_map_csv`.
- [ ] Task: Update `app/pages/2_satellite_map.py` to use the merged map.
    - [ ] Modify the code that calls `draw_map`. Pass `str(st.session_state.merged_map_csv)` if it exists; otherwise, pass `str(st.session_state.map_csv)`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation' (Protocol in workflow.md)