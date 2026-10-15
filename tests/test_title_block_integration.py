import pandas as pd

from cave_sketch.survey import draw_survey
from cave_sketch.survey.config import TitleBlockInfo


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
        title_block=TitleBlockInfo(surveyor_name="Alice Smith"),
    )

    # Find the title block Axes
    title_ax = None
    for ax in fig.axes:
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None
    texts = " ".join([t.get_text() for t in title_ax.texts] + [t.get_text() for t in fig.texts])

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
        title_block=TitleBlockInfo(surveyor_name="Bob Jones"),
    )

    title_ax = None
    for ax in fig.axes:
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None
    texts = " ".join([t.get_text() for t in title_ax.texts] + [t.get_text() for t in fig.texts])

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

    fig = draw_survey(
        title="Merged Cave",
        rule_length=10.0,
        csv_map_path=str(parent_map),
        csv_section_path=str(parent_section),
        child_csv_map_path=str(child_map),
        child_csv_section_path=str(child_section),
        parent_station="2",
        child_station="1",
        title_block=TitleBlockInfo(surveyor_name="Charlie Brown"),
    )

    title_ax = None
    for ax in fig.axes:
        bbox = ax.get_position()
        if bbox.y0 >= 0.8:
            title_ax = ax
            break

    assert title_ax is not None
    texts = " ".join([t.get_text() for t in title_ax.texts] + [t.get_text() for t in fig.texts])

    assert "Merged Cave" in texts
    assert "Charlie Brown" in texts
    assert "15.0 m" in texts  # Merged length
    assert "8.0 m" in texts   # Merged depth


def _write_csvs(tmp_path):
    map_csv = tmp_path / "map.csv"
    section_csv = tmp_path / "section.csv"
    pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 10.0], "Y": [0.0, 0.0],
        "Links": ["2", "1"], "Type": ["station", "station"],
    }).to_csv(map_csv, index=False)
    pd.DataFrame({
        "Node_Id": ["1", "2"], "X": [0.0, 10.0], "Y": [0.0, -5.0],
        "Links": ["-", "-"], "Type": ["station", "station"],
    }).to_csv(section_csv, index=False)
    return str(map_csv), str(section_csv)


def _title_texts(fig):
    return [t.get_text() for t in fig.axes[-1].texts]


def test_draw_survey_full_metadata_prints_all_rows(tmp_path):
    map_csv, section_csv = _write_csvs(tmp_path)
    fig = draw_survey(
        title="Full Cave",
        rule_length=10.0,
        csv_map_path=map_csv,
        csv_section_path=section_csv,
        magnetic_variation_deg=2.5,
        title_block=TitleBlockInfo(
            surveyor_name="Alice", drawer_name="Bob", municipality="Genga",
            latitude=43.4, longitude=12.9, elevation_m=320,
        ),
    )
    labels = [t.split(":")[0] for t in _title_texts(fig)]
    assert labels == [
        "Rilevatore", "Disegnatore", "Data", "Comune", "Coordinate",
        "Quota slm", "Declinazione", "Sviluppo", "Dislivello",
    ]


def test_section_only_survey_does_not_print_variation(tmp_path):
    _, section_csv = _write_csvs(tmp_path)
    fig = draw_survey(
        title="Section Only",
        rule_length=10.0,
        csv_section_path=section_csv,
        magnetic_variation_deg=2.5,
    )
    assert not any(t.startswith("Declinazione") for t in _title_texts(fig))
