# Specification: Merged Survey Support in Satellite Map

## Overview
Currently, the satellite map only renders the parent map (`st.session_state.map_csv`). The goal is to support rendering the merged map when a child survey is merged in the Survey Plot section.

## Functional Requirements
1. When a user merges two surveys in `1_survey_plot.py` (by clicking "Generate Survey Plot"), the Streamlit glue code should save the merged map DataFrame to a temporary CSV file and store its path in `st.session_state.merged_map_csv`.
2. When a plot is generated **without** a child survey, `st.session_state.merged_map_csv` must be reset to `None` so that stale merge data does not persist across re-generations.
3. In `2_satellite_map.py`, when calling the `draw_map` function, it should pass `st.session_state.merged_map_csv` (if truthy) instead of `st.session_state.map_csv`.
4. **Constraints:** The `draw_map` and `draw_survey` function signatures must not be changed. The UI must remain unchanged. Only minimal changes to the Streamlit glue code are allowed.

## Testing
- Add unit tests in `tests/test_satellite_map.py` using plain `pytest` (no Streamlit AppTest needed) that verify:
  - When `merged_map_csv` is set, it is selected as `map_path` over `map_csv`.
  - When `merged_map_csv` is `None`, `map_csv` is used as fallback.
  - After a non-merged plot generation, `merged_map_csv` is `None`.
  - After a merged plot generation, `merged_map_csv` is a valid CSV path containing the merged data.