import json
import sys
from pathlib import Path

# survey_bridge.py lives in the android source tree, outside the importable package.
ANDROID_PY = Path(__file__).resolve().parents[1] / "android/app/src/main/python"
sys.path.insert(0, str(ANDROID_PY))

import survey_bridge  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_resolve_input_returns_none_for_empty():
    assert survey_bridge.resolve_input(None, "/tmp", "map") is None
    assert survey_bridge.resolve_input("", "/tmp", "map") is None


def test_resolve_input_passes_csv_through():
    csv = str(FIXTURES / "test_survey.csv")
    assert survey_bridge.resolve_input(csv, "/tmp", "map") == csv


def test_resolve_input_parses_dxf_to_csv(tmp_path):
    dxf = str(FIXTURES / "sample.dxf")
    out = survey_bridge.resolve_input(dxf, str(tmp_path), "map")
    assert out == str(tmp_path / "map.csv")
    assert Path(out).exists()


def test_validate_merge_rejects_non_numeric():
    csv = str(FIXTURES / "test_survey.csv")
    err = survey_bridge.validate_merge(csv, csv, "12P4", "1")
    assert err is not None and "numeric" in err.lower()


def test_validate_merge_rejects_missing_station():
    csv = str(FIXTURES / "test_survey.csv")  # has Node_Id 1, 2
    err = survey_bridge.validate_merge(csv, csv, "999", "1")
    assert err is not None and "999" in err


def test_validate_merge_accepts_valid():
    csv = str(FIXTURES / "test_survey.csv")
    assert survey_bridge.validate_merge(csv, csv, "1", "2") is None


def _inputs(**kw):
    base = {
        "map_path": str(FIXTURES / "test_survey.csv"),
        "section_path": None, "child_map_path": None, "child_section_path": None,
        "survey_name": "Test Cave", "surveyor_name": "Tester",
        "parent_station": "", "child_station": "", "section_protocol": "simple",
        "settings": {"rule_length": 100, "rotation_deg": 0.0, "show_details": True,
                     "show_grid": True, "marker_zoom": 0.0, "text_zoom": 0.0,
                     "line_width_zoom": 0.0},
    }
    base.update(kw)
    return json.dumps(base)


def test_generate_creates_pdf(tmp_path):
    out = json.loads(survey_bridge.generate_survey_plot(_inputs(), str(tmp_path)))
    assert "pdf_path" in out
    assert Path(out["pdf_path"]).exists()


def test_generate_no_input_returns_error(tmp_path):
    out = json.loads(survey_bridge.generate_survey_plot(
        _inputs(map_path=None, section_path=None), str(tmp_path)))
    assert out["error"] == "no_input"


def test_generate_bad_file_returns_structured_error(tmp_path):
    bad = tmp_path / "broken.csv"
    bad.write_text("not,a,survey\n1,2,3\n")
    out = json.loads(survey_bridge.generate_survey_plot(
        _inputs(map_path=str(bad)), str(tmp_path)))
    assert out["error"] == "render_failed"
    assert "detail" in out


def test_prewarm_does_not_raise():
    survey_bridge.prewarm()


