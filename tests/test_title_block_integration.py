import pandas as pd

from cave_sketch.survey import draw_survey


def test_draw_survey_with_map_and_section_shows_title_block(tmp_path):
    map_csv = tmp_path / "map.csv"
    section_csv = tmp_path / "section.csv"

    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    }).to_csv(map_csv, index=False)

    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, -5.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"]
    }).to_csv(section_csv, index=False)

    fig = draw_survey(
        title="Integration Cave",
        rule_length=10.0,
        csv_map_path=str(map_csv),
        csv_section_path=str(section_csv),
        surveyor_name="Alice Smith",
    )

    # Find the title block Axes
    title_ax = None
    for ax in fig.axes:
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None
    texts = " ".join([t.get_text() for t in title_ax.texts])

    assert "Integration Cave" in texts
    assert "Alice Smith" in texts
    assert "10.0 m" in texts  # Length
    assert "5.0 m" in texts   # Depth (max(Y)-min(Y) = 0 - (-5) = 5.0)


def test_draw_survey_without_section_omits_depth(tmp_path):
    map_csv = tmp_path / "map.csv"

    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    }).to_csv(map_csv, index=False)

    fig = draw_survey(
        title="Plan Only Cave",
        rule_length=10.0,
        csv_map_path=str(map_csv),
        csv_section_path=None,
        surveyor_name="Bob Jones",
    )

    title_ax = None
    for ax in fig.axes:
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None
    texts = " ".join([t.get_text() for t in title_ax.texts])

    assert "Plan Only Cave" in texts
    assert "Bob Jones" in texts
    assert "10.0 m" in texts
    assert "Dislivello" not in texts
    assert "Depth" not in texts


def test_draw_survey_with_merged_surveys_computes_merged_metrics(tmp_path):
    parent_map = tmp_path / "parent_map.csv"
    parent_section = tmp_path / "parent_section.csv"
    child_map = tmp_path / "child_map.csv"
    child_section = tmp_path / "child_section.csv"

    # Parent length: 1-2 is 10m
    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    }).to_csv(parent_map, index=False)

    # Parent depth: Y range is 5m (0 to -5)
    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 10.0],
        "Y": [0.0, -5.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"]
    }).to_csv(parent_section, index=False)

    # Child length: 1-2 is 5m
    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 5.0],
        "Y": [0.0, 0.0],
        "Links": ["2", "1"],
        "Type": ["station", "station"]
    }).to_csv(child_map, index=False)

    # Child depth: Y range is 3m (0 to -3)
    pd.DataFrame({
        "Node_Id": ["1", "2"],
        "X": [0.0, 5.0],
        "Y": [0.0, -3.0],
        "Links": ["-", "-"],
        "Type": ["station", "station"]
    }).to_csv(child_section, index=False)

    # Merging at Parent:2 and Child:1
    # Remapped Child 2 Node_Id will be 4
    # Child will translate by X offset = 10, Y offset = 0
    # Remapped child map: Node_Id 4 is at (15, 0), linked to 2
    # Total merged length: Parent 1-2 (10m) + Child 2-4 (5m) = 15m
    # Remapped child section: Node_Id 4 is at (15, -3 - 5) = (15, -8) (if simple protocol)
    # Total merged depth: max Y is 0 (station 1), min Y is -8 (station 4). Depth = 8m

    fig = draw_survey(
        title="Merged Cave",
        rule_length=10.0,
        csv_map_path=str(parent_map),
        csv_section_path=str(parent_section),
        child_csv_map_path=str(child_map),
        child_csv_section_path=str(child_section),
        parent_station="2",
        child_station="1",
        surveyor_name="Charlie Brown",
    )

    title_ax = None
    for ax in fig.axes:
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None
    texts = " ".join([t.get_text() for t in title_ax.texts])

    assert "Merged Cave" in texts
    assert "Charlie Brown" in texts
    assert "15.0 m" in texts  # Merged length
    assert "8.0 m" in texts   # Merged depth
