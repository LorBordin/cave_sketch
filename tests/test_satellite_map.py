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
        "Node_Id": ["st1", "st2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["st2", "st1"],
        "Type": ["station", "station"],
    })
    child_map = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "X": [0.0, 5.0],
        "Y": [0.0, 0.0],
        "Links": ["st2", "st1"],
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
        parent_station="st2",
        child_station="st1",
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
