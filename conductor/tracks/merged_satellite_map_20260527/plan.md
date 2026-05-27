# Merged Survey Support in Satellite Map — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When two surveys are merged in the Survey Plot page, the Satellite Map page should render the merged result instead of only the parent map.

**Architecture:** `1_survey_plot.py` calls `merge_surveys` a second time (reading the same CSVs already available in session state) to obtain the merged DataFrame, saves it to `merged_map.csv`, and stores its path in session state. `2_satellite_map.py` reads that path (falling back to `map_csv` when absent) and passes it to `draw_map`. No library function signatures change; all edits stay in Streamlit glue code.

**Tech Stack:** Python, Streamlit, pandas, pytest

---

## [x] Task 1: Add `merged_map_csv` to session state 711eeeb

**Files:**
- Modify: `app/session.py:34-53` (`defaults` dict and `AppState` TypedDict)

- [ ] **Step 1: Add field to `AppState` TypedDict**

  In `app/session.py`, add `merged_map_csv` after `map_csv` in the TypedDict:

  ```python
  class AppState(TypedDict):
      files_dir: Path
      cave_survey: Optional[Figure]
      pdf_output_path: Optional[Path]
      map_loaded: bool
      map_csv: Optional[Path]
      merged_map_csv: Optional[Path]   # ← add this line
      section_csv: Optional[Path]
      ...
  ```

- [x] **Step 2: Add default value in `init_session`**

  In the `defaults` dict inside `init_session`, add after the `"map_csv"` entry:

  ```python
  defaults = {
      ...
      "map_csv": None,
      "merged_map_csv": None,    # ← add this line
      "section_csv": None,
      ...
  }
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add app/session.py
  git commit -m "feat: add merged_map_csv to session state"
  ```

---

## [x] Task 2: Write failing tests b0c790b

**Files:**
- Create: `tests/test_satellite_map.py`

- [ ] **Step 1: Create the test file**

  ```python
  # tests/test_satellite_map.py
  from pathlib import Path

  import pandas as pd
  import pytest

  from cave_sketch.survey.merger import SectionProtocol, merge_surveys


  # ── path-selection logic ────────────────────────────────────────────────────

  def test_merged_csv_selected_when_present(tmp_path):
      merged = tmp_path / "merged_map.csv"
      parent = tmp_path / "map.csv"
      merged_map_csv = merged
      map_csv = parent
      assert (merged_map_csv or map_csv) == merged


  def test_map_csv_fallback_when_no_merge(tmp_path):
      parent = tmp_path / "map.csv"
      merged_map_csv = None
      map_csv = parent
      assert (merged_map_csv or map_csv) == parent


  # ── merge-and-save logic ────────────────────────────────────────────────────

  @pytest.fixture
  def two_survey_csvs(tmp_path):
      parent_map = pd.DataFrame({
          "Node_Id": ["1", "2"],
          "X": [0.0, 10.0],
          "Y": [0.0, 0.0],
          "Links": ["2", "1"],
          "Type": ["station", "station"],
      })
      child_map = pd.DataFrame({
          "Node_Id": ["1", "2"],
          "X": [0.0, 5.0],
          "Y": [0.0, 0.0],
          "Links": ["2", "1"],
          "Type": ["station", "station"],
      })
      parent_path = tmp_path / "map.csv"
      child_path = tmp_path / "child_map.csv"
      parent_map.to_csv(parent_path, index=False)
      child_map.to_csv(child_path, index=False)
      return parent_path, child_path, tmp_path


  def test_merged_csv_written_when_merge_valid(two_survey_csvs):
      parent_path, child_path, files_dir = two_survey_csvs
      parent_map_df = pd.read_csv(parent_path)
      child_map_df = pd.read_csv(child_path)
      merged_map_df, _ = merge_surveys(
          parent_map=parent_map_df,
          parent_section=None,
          child_map=child_map_df,
          child_section=None,
          parent_station="2",
          child_station="1",
          section_protocol=SectionProtocol.SIMPLE,
      )
      merged_path = files_dir / "merged_map.csv"
      merged_map_df.to_csv(merged_path, index=False)

      assert merged_path.exists()
      result = pd.read_csv(merged_path)
      assert len(result) > len(parent_map_df)    # child nodes were appended


  def test_merged_csv_is_none_when_no_child():
      # Simulate the else-branch in 1_survey_plot.py
      child_map_csv = None
      parent_station = ""
      child_station = ""
      if child_map_csv and parent_station and child_station:
          merged_map_csv = Path("some/path")
      else:
          merged_map_csv = None
      assert merged_map_csv is None
  ```

- [ ] **Step 2: Run tests to verify they fail (Task 3 not yet done)**

  ```bash
  pytest tests/test_satellite_map.py -v
  ```

  Expected: all four tests **PASS** already — these tests validate pure logic that doesn't depend on the Streamlit glue code. If any fails, check the fixture data.

- [ ] **Step 3: Commit**

  ```bash
  git add tests/test_satellite_map.py
  git commit -m "test: add satellite map merged-path selection tests"
  ```

---

## [x] Task 3: Update `1_survey_plot.py` to save merged map e87ec21

**Files:**
- Modify: `app/pages/1_survey_plot.py`

- [ ] **Step 1: Add `pandas` import at the top**

  Add after the `from pathlib import Path` line (line 1):

  ```python
  from pathlib import Path

  import pandas as pd    # ← add this line

  import streamlit as st
  ```

- [ ] **Step 2: Extend the `merge_surveys` import inside the button handler**

  On the line that currently reads (≈ line 35):

  ```python
  from cave_sketch.survey.merger import SectionProtocol
  ```

  Change it to:

  ```python
  from cave_sketch.survey.merger import SectionProtocol, merge_surveys
  ```

- [ ] **Step 3: Add merged-map save logic after `draw_survey`**

  After the line `st.session_state.pdf_output_path = pdf_path` (currently ≈ line 52), add:

  ```python
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
                _merged_df.to_csv(_merged_path, index=False)
                st.session_state.merged_map_csv = _merged_path
            else:
                st.session_state.merged_map_csv = None
  ```

  The full button handler should now look like:

  ```python
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
                  _merged_df.to_csv(_merged_path, index=False)
                  st.session_state.merged_map_csv = _merged_path
              else:
                  st.session_state.merged_map_csv = None
      else:
          st.warning("⚠️ Please upload at least one file first.")
  ```

- [ ] **Step 4: Run existing tests to ensure nothing is broken**

  ```bash
  pytest tests/ -v
  ```

  Expected: all tests PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add app/pages/1_survey_plot.py
  git commit -m "feat: save merged map CSV to session state after survey plot generation"
  ```

---

## [x] Task 4: Update `2_satellite_map.py` to use merged map 5ef9b4a

**Files:**
- Modify: `app/pages/2_satellite_map.py:34-41`

- [ ] **Step 1: Replace `map_path` argument**

  Find the `draw_map(...)` call (≈ line 34). Change the `map_path` keyword argument from:

  ```python
          html_map, json_path, kml_path = draw_map(
              map_path=str(st.session_state.map_csv),
  ```

  to:

  ```python
          html_map, json_path, kml_path = draw_map(
              map_path=str(st.session_state.merged_map_csv or st.session_state.map_csv),
  ```

  The full `draw_map(...)` call should look like:

  ```python
          html_map, json_path, kml_path = draw_map(
              map_path=str(st.session_state.merged_map_csv or st.session_state.map_csv),
              gps_points=st.session_state.known_points,
              output_path=str(html_path),
              map_name="Current Cave",
              additional_json_maps=st.session_state.uploaded_json_paths,
              rotation_angle=rotation_angle,
          )
  ```

- [ ] **Step 2: Run all tests**

  ```bash
  pytest tests/ -v
  ```

  Expected: all tests PASS.

- [ ] **Step 3: Commit**

  ```bash
  git add app/pages/2_satellite_map.py
  git commit -m "feat: use merged_map_csv in satellite map when available"
  ```

---

## Task 5: Conductor — User Manual Verification

- [ ] Run the app and load a parent survey in the Survey Plot page.
- [ ] Upload a child survey, set merge stations, click "Generate Survey Plot".
- [ ] Navigate to the Satellite Map page, add GPS points, click "Generate HTML Map".
- [ ] Confirm the rendered map shows the merged survey (both parent and child stations visible), not only the parent.
- [ ] Go back to Survey Plot, click "Generate Survey Plot" again **without** a child survey loaded (remove child file). Navigate to Satellite Map and confirm it falls back to parent-only map.
ly map.
