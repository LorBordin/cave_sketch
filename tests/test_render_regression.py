import os
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.survey import draw_survey


class MockDate:
    @classmethod
    def today(cls):
        return date(2026, 1, 1)

@pytest.fixture(autouse=True)
def fixed_date(monkeypatch):
    monkeypatch.setattr("cave_sketch.survey.graphics.title_block.datetime.date", MockDate)

@pytest.fixture(scope="module")
def parsed_csv_paths(tmp_path_factory):
    dxf_path = Path("tests/fixtures/sample.dxf")
    temp_dir = tmp_path_factory.mktemp("regression_data")
    csv_path = temp_dir / "sample.csv"
    parse_dxf(dxf_path, output_path=csv_path)
    return csv_path

@pytest.mark.parametrize("scenario", ["plan_only", "dual"])
def test_render_regression(scenario, parsed_csv_paths, tmp_path):
    baselines_dir = Path("tests/fixtures/render_baselines")
    baseline_png = baselines_dir / f"{scenario}.png"
    
    csv_path_str = str(parsed_csv_paths)
    if scenario == "plan_only":
        fig = draw_survey(
            title="Sample Survey Plan",
            rule_length=20.0,
            csv_map_path=csv_path_str,
            csv_section_path=None,
            surveyor_name="Test Surveyor"
        )
    else:  # dual
        fig = draw_survey(
            title="Sample Survey Dual",
            rule_length=20.0,
            csv_map_path=csv_path_str,
            csv_section_path=csv_path_str,
            surveyor_name="Test Surveyor"
        )
    
    baselines_dir.mkdir(parents=True, exist_ok=True)
    
    output_png = tmp_path / f"{scenario}.png"
    fig.savefig(output_png, dpi=100)
    plt.close(fig)
    
    if os.environ.get("CAVE_SKETCH_GENERATE_BASELINES") == "1":
        import shutil
        shutil.copy(output_png, baseline_png)
        pytest.skip(f"Generated baseline for {scenario} and skipping comparison.")
        
    assert baseline_png.exists(), f"Baseline image not found: {baseline_png}"
    
    from matplotlib.testing.compare import compare_images
    result = compare_images(str(baseline_png), str(output_png), tol=1.0)
    assert result is None, f"Image mismatch in {scenario}: {result}"
