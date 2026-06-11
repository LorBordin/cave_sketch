# Plan: PDF Survey Title Block

## Phase 1: Survey Metrics Computation (Library) [checkpoint: 2fb77e2]

- [x] Task: Write tests for `compute_total_length()` (ac4e1ba)
    - [x] Create `tests/test_survey_metrics.py`
    - [x] Test: two connected numeric stations → correct Euclidean distance
    - [x] Test: three-station chain (A→B→C) → sum of two legs
    - [x] Test: polyline nodes (`xxPyy`) and block features are excluded from computation
    - [x] Test: bidirectional links (A→B and B→A) count the leg only once
    - [x] Test: empty or single-station DataFrame returns 0.0
- [x] Task: Implement `compute_total_length()` in `cave_sketch/survey/metrics.py` (ac4e1ba)
    - [x] Accept a DataFrame with columns `Node_Id`, `Links`, `X`, `Y`, `Type`
    - [x] Filter to numeric-only station IDs (`^\d+$`)
    - [x] Iterate connected pairs, compute Euclidean distance, deduplicate legs
    - [x] Return total length as `float`
- [x] Task: Write tests for `compute_total_depth()` (ac4e1ba)
    - [x] Test: three numeric stations at different Y values → correct max−min
    - [x] Test: polyline nodes excluded from min/max computation
    - [x] Test: empty or single-station DataFrame returns 0.0
    - [x] Test: returns `None` when no section data is provided
- [x] Task: Implement `compute_total_depth()` in `cave_sketch/survey/metrics.py` (ac4e1ba)
    - [x] Accept an optional section DataFrame
    - [x] Filter to numeric-only station IDs
    - [x] Return `max(Y) - min(Y)` as `float`, or `None` if no section data
- [x] Task: Conductor - User Manual Verification 'Phase 1: Survey Metrics Computation' (Protocol in workflow.md) (ac4e1ba)

## Phase 2: Title Block Rendering (Library) [checkpoint: 5c5b40a]

- [x] Task: Write tests for `draw_title_block()` (a07b17f)
    - [x] Create `tests/test_title_block.py`
    - [x] Test: title block renders all 5 fields (cave name, surveyor, date, length, depth) when all data present
    - [x] Test: title block omits depth field when `total_depth` is `None`
    - [x] Test: title block renders within the expected figure region (top margin), no overlap with subplot area
    - [x] Test: empty surveyor name renders gracefully (blank field or placeholder)
- [x] Task: Implement `draw_title_block()` in `cave_sketch/survey/graphics/title_block.py` (a07b17f)
    - [x] Create a bordered rectangle in the top margin of the figure
    - [x] Render cave name in a prominent (larger) font
    - [x] Render metadata fields (surveyor, date, length, depth) in a structured grid layout
    - [x] Use `fig.text()` or a dedicated `Axes` for precise positioning
    - [x] Ensure legibility at A4 print size
- [x] Task: Extend `SurveyConfig` with `surveyor_name: str = ""` (a07b17f)
    - [x] Update `cave_sketch/survey/config.py`
    - [x] Update any existing tests that construct `SurveyConfig` if needed
- [x] Task: Conductor - User Manual Verification 'Phase 2: Title Block Rendering' (Protocol in workflow.md) (a07b17f)

## Phase 3: Pipeline Integration

- [ ] Task: Write integration tests for `draw_survey()` with title block
    - [ ] Test: `draw_survey()` with map + section produces a figure containing the title block
    - [ ] Test: `draw_survey()` with merged surveys computes metrics from merged data
    - [ ] Test: `draw_survey()` without section omits depth in title block
- [ ] Task: Integrate metrics + title block into `render_survey()` in `cave_sketch/survey/renderer.py`
    - [ ] Replace `fig.suptitle()` with `draw_title_block()` call
    - [ ] Compute `total_length` from map DataFrame, `total_depth` from section DataFrame
    - [ ] Adjust `fig.subplots_adjust(top=...)` to accommodate the title block height
    - [ ] Pass `surveyor_name` from `SurveyConfig`
- [ ] Task: Update `draw_survey()` in `cave_sketch/survey/survey.py`
    - [ ] Accept `surveyor_name` parameter and pass it into `SurveyConfig`
    - [ ] Ensure metrics are computed **after** merge when child survey is present
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Pipeline Integration' (Protocol in workflow.md)

## Phase 4: Streamlit UI

- [ ] Task: Add "Surveyor Name" text input to `app/pages/1_survey_plot.py`
    - [ ] Place the input below the existing "Survey Name" field
    - [ ] Pass the value to `draw_survey()` as `surveyor_name` parameter
- [ ] Task: Verify end-to-end: upload DXF → fill surveyor name → generate PDF → title block appears with all fields
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Streamlit UI' (Protocol in workflow.md)
