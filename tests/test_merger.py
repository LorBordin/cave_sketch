
import pandas as pd

from cave_sketch.survey import draw_survey
from cave_sketch.survey.merger import SectionProtocol, merge_surveys


def test_merge_surveys_id_remapping():
    # Parent: stations 1, 2
    parent_map = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    # Child: stations 1, 2 (will be remapped)
    child_map = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 5.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    # Merge at Parent:2 and Child:1
    merged_map, _ = merge_surveys(
        parent_map=parent_map,
        parent_section=None,
        child_map=child_map,
        child_section=None,
        parent_station="2",
        child_station="1",
        section_protocol=SectionProtocol.SIMPLE
    )

    assert merged_map is not None
    # Parent IDs: 1, 2. Max is 2.
    # Child IDs: 1, 2. Min is 1.
    # Offset = 2 + 1 - 1 = 2.
    # Child 1 -> 1+2 = 3. Child 2 -> 2+2 = 4.

    # Let's check the remapped IDs in the merged dataframe
    node_ids = merged_map["Node_Id"].tolist()
    assert "1" in node_ids
    assert "2" in node_ids
    assert "4" in node_ids  # Child 2 remapped to 4
    assert "3" not in node_ids  # Child 1 was the matching node, merged with Parent 2

    # Check Links remapping
    # Child 2 linked to 1. Remapped: 4 linked to 2.
    row_4 = merged_map[merged_map["Node_Id"] == "4"].iloc[0]
    assert row_4["Links"] == "2"


def test_merge_surveys_coordinate_translation():
    parent_map = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [100.0, 110.0],
        "Y": [200.0, 200.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    child_map = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 5.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    # Merge at Parent:2 (110, 200) and Child:1 (0, 0)
    merged_map, _ = merge_surveys(
        parent_map=parent_map,
        parent_section=None,
        child_map=child_map,
        child_section=None,
        parent_station="2",
        child_station="1"
    )

    # Child 2 was at (5, 0). Translated by (110-0, 200-0) -> (115, 200)
    row_4 = merged_map[merged_map["Node_Id"] == "4"].iloc[0]
    assert row_4["X"] == 115.0
    assert row_4["Y"] == 200.0


def test_merge_surveys_mixed_ids():
    parent_map = pd.DataFrame({
        "Node_Id": ["1", "1P1"],
        "X": [0.0, 1.0],
        "Y": [0.0, 1.0],
        "Links": ["1P1", "1"],
        "Type": ["station", "L_wall"]
    })

    child_map = pd.DataFrame({
        "Node_Id": ["1", "1P1"],
        "X": [0.0, 2.0],
        "Y": [0.0, 2.0],
        "Links": ["1P1", "1"],
        "Type": ["station", "L_wall"]
    })

    # Merge at Parent:1 and Child:1
    merged_map, _ = merge_surveys(
        parent_map=parent_map,
        parent_section=None,
        child_map=child_map,
        child_section=None,
        parent_station="1",
        child_station="1"
    )

    node_ids = merged_map["Node_Id"].tolist()
    assert "1" in node_ids
    assert "1P1" in node_ids
    assert "2P1" in node_ids


def test_merge_surveys_mirror_protocol():
    parent_section = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    child_section = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 5.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    # Merge at Parent:2 (10, 0) and Child:1 (0, 0) with MIRROR
    _, merged_section = merge_surveys(
        parent_map=None,
        parent_section=parent_section,
        child_map=None,
        child_section=child_section,
        parent_station="2",
        child_station="1",
        section_protocol=SectionProtocol.MIRROR
    )

    # Original child 2 was at (5, 0).
    # Mirrored across child 1 (X=0): X' = 2*0 - 5 = -5.
    # Translated by delta_x = 10 - 0 = 10: X'' = -5 + 10 = 5.

    row_4 = merged_section[merged_section["Node_Id"] == "4"].iloc[0]
    assert row_4["X"] == 5.0
    assert row_4["Y"] == 0.0


def test_draw_survey_no_child(tmp_path):
    csv_path = "tests/fixtures/test_survey.csv"
    output_pdf = tmp_path / "output.pdf"

    fig = draw_survey(
        title="Test Survey",
        rule_length=20,
        csv_map_path=csv_path,
        output_path=str(output_pdf)
    )

    assert fig is not None
    assert output_pdf.exists()
