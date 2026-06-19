import json
import sys
from pathlib import Path

import pytest

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
