# Specification: Merged Survey Support in Satellite Map

## Overview
Currently, the satellite map only renders the parent map (`st.session_state.map_csv`). The goal is to support rendering the merged map when a child survey is merged in the Survey Plot section.

## Functional Requirements
1. When a user merges two surveys in `1_survey_plot.py` (by clicking "Generate Survey Plot"), the Streamlit glue code should save the merged map DataFrame to a temporary CSV file and store its path in `st.session_state.merged_map_csv`.
2. In `2_satellite_map.py`, when calling the `draw_map` function, it should pass `st.session_state.merged_map_csv` (if it exists) instead of `st.session_state.map_csv`.
3. **Constraints:** The `draw_map` and `draw_survey` function signatures must not be changed. The UI must remain unchanged. Only minimal changes to the Streamlit glue code are allowed.

## Testing
- Add a unit test (likely using Streamlit's `AppTest` framework or a simple mock test for the session state logic) to ensure that the correct argument (the merged map) is passed to `draw_map` when a merged survey is present.