
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


def test_merge_surveys_displacement_station_handling():
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

    _, merged = merge_surveys(
        parent_map=None,
        parent_section=parent_section,
        child_map=None,
        child_section=child_section,
        parent_station="2",
        child_station="1",
        section_protocol=SectionProtocol.DISPLACEMENT
    )

    assert merged is not None
    node_ids = merged["Node_Id"].tolist()

    # Child matching station (1) is NOT deleted; remapped to "3" with offset
    assert "1" in node_ids
    assert "2" in node_ids
    assert "3" in node_ids
    assert "4" in node_ids

    # Displaced child matching station 3 coordinates are displaced
    # (not coincident with parent station 2)
    row_parent_2 = merged[merged["Node_Id"] == "2"].iloc[0]
    row_child_3 = merged[merged["Node_Id"] == "3"].iloc[0]
    assert (row_child_3["X"], row_child_3["Y"]) != (row_parent_2["X"], row_parent_2["Y"])

    # Displaced child station 4 links to displaced child station 3 (NOT to parent station 2)
    row_child_4 = merged[merged["Node_Id"] == "4"].iloc[0]
    assert row_child_4["Links"] == "3"

    # No child station links to parent station 2
    child_rows = merged[merged["Node_Id"].isin(["3", "4"])]
    for _, crow in child_rows.iterrows():
        links = [lk.strip() for lk in str(crow["Links"]).split("-") if lk.strip()]
        assert "2" not in links

    # Exactly one connector row links parent station 2 to displaced child station 3
    connectors = merged[merged["Type"] == "connector"]
    assert len(connectors) == 1
    conn = connectors.iloc[0]
    # Connector coordinates at parent station 2, linked to child station 3
    assert conn["X"] == row_parent_2["X"]
    assert conn["Y"] == row_parent_2["Y"]
    assert conn["Links"] == "3"


def test_map_protocol_enum_and_merge_surveys_displacement():
    from cave_sketch.survey.merger import MapProtocol

    assert MapProtocol.SIMPLE.value == "simple"
    assert MapProtocol.DISPLACEMENT.value == "displacement"

    parent_map = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 20.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    child_map = pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    })

    # Default is SIMPLE: child matching station is coincident with parent station 2
    merged_def, _ = merge_surveys(
        parent_map=parent_map,
        parent_section=None,
        child_map=child_map,
        child_section=None,
        parent_station="2",
        child_station="1",
    )
    assert merged_def is not None
    # In SIMPLE: child 1 is merged with parent 2; child 2 is remapped to 4 at (30.0, 0.0)
    assert "3" not in merged_def["Node_Id"].tolist()
    row_4_def = merged_def[merged_def["Node_Id"] == "4"].iloc[0]
    assert row_4_def["X"] == 30.0
    assert len(merged_def[merged_def["Type"] == "connector"]) == 0

    # DISPLACEMENT: child map is displaced
    merged_disp, _ = merge_surveys(
        parent_map=parent_map,
        parent_section=None,
        child_map=child_map,
        child_section=None,
        parent_station="2",
        child_station="1",
        map_protocol=MapProtocol.DISPLACEMENT,
    )
    assert merged_disp is not None
    node_ids = merged_disp["Node_Id"].tolist()
    assert "1" in node_ids
    assert "2" in node_ids
    assert "3" in node_ids
    assert "4" in node_ids

    # Connector row exists in map
    connectors = merged_disp[merged_disp["Type"] == "connector"]
    assert len(connectors) == 1
    assert connectors.iloc[0]["Links"] == "3"


def test_draw_survey_forwards_map_protocol(tmp_path):
    from cave_sketch.survey.merger import MapProtocol

    parent_map = tmp_path / "parent_map.csv"
    child_map = tmp_path / "child_map.csv"

    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 20.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    }).to_csv(parent_map, index=False)

    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    }).to_csv(child_map, index=False)

    fig = draw_survey(
        title="Displacement Map Cave",
        rule_length=10.0,
        csv_map_path=str(parent_map),
        csv_section_path=None,
        child_csv_map_path=str(child_map),
        child_csv_section_path=None,
        parent_station="2",
        child_station="1",
        map_protocol=MapProtocol.DISPLACEMENT,
    )
    assert fig is not None


