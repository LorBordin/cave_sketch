import datetime

from cave_sketch.survey.config import TitleBlockInfo
from cave_sketch.survey.graphics.title_block import build_title_rows

DAY = datetime.date(2026, 1, 2)


def test_required_rows_only():
    rows = build_title_rows(TitleBlockInfo(), 0.0, 154.34, None, today=DAY)
    assert rows == ["Rilevatore: -", "Data: 02/01/2026", "Sviluppo: 154.3 m"]


def test_all_rows_in_order():
    info = TitleBlockInfo(
        surveyor_name="Alice",
        drawer_name="Bob",
        municipality="Genga",
        latitude=43.40123456,
        longitude=12.96543219,
        elevation_m=1249.6,
    )
    rows = build_title_rows(info, 2.54, 154.3, 45.2, today=DAY)
    assert rows == [
        "Rilevatore: Alice",
        "Disegnatore: Bob",
        "Data: 02/01/2026",
        "Comune: Genga",
        "Coordinate: 43.40123° N, 12.96543° E",
        "Quota slm: 1250 m",
        "Declinazione: 2.5° E",
        "Sviluppo: 154.3 m",
        "Dislivello: 45.2 m",
    ]


def test_zero_values_are_printed():
    info = TitleBlockInfo(latitude=0.0, longitude=0.0, elevation_m=0.0)
    rows = build_title_rows(info, 0.0, 1.0, None, today=DAY)
    assert "Coordinate: 0.00000° N, 0.00000° E" in rows
    assert "Quota slm: 0 m" in rows


def test_southern_western_hemisphere_and_west_variation():
    info = TitleBlockInfo(latitude=-33.5, longitude=-70.25)
    rows = build_title_rows(info, -1.25, 1.0, None, today=DAY)
    assert "Coordinate: 33.50000° S, 70.25000° W" in rows
    assert "Declinazione: 1.2° W" in rows


def test_zero_variation_is_omitted():
    rows = build_title_rows(TitleBlockInfo(), 0.0, 1.0, None, today=DAY)
    assert not any(r.startswith("Declinazione") for r in rows)


def test_long_values_are_truncated_to_30_chars():
    long_name = "Comunità Montana dell'Alta Valle dell'Esino"
    rows = build_title_rows(TitleBlockInfo(municipality=long_name), 0.0, 1.0, None, today=DAY)
    value = next(r for r in rows if r.startswith("Comune: ")).removeprefix("Comune: ")
    assert len(value) == 30
    assert value.endswith("…")


def test_today_defaults_to_current_date():
    rows = build_title_rows(TitleBlockInfo(), 0.0, 1.0, None)
    assert rows[1] == f"Data: {datetime.date.today().strftime('%d/%m/%Y')}"
