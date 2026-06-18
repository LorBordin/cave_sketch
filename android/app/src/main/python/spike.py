"""Phase 0 spike glue. Calls the UNTOUCHED cave_sketch core, mirroring the web
Survey Plot flow: parse_dxf (DXF->CSV) then draw_survey (CSV->PDF)."""
from pathlib import Path

from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.survey.survey import draw_survey


def render_sample_pdf(dxf_path: str, work_dir: str) -> str:
    """Render the sample DXF to a PDF and return its absolute path."""
    work = Path(work_dir)
    csv_path = work / "sample.csv"
    pdf_path = work / "sample.pdf"

    # DXF -> CSV (writes csv_path, returns CaveSurvey)
    parse_dxf(Path(dxf_path), csv_path)

    # CSV -> PDF (rule_length is a sample value; spike only proves rendering)
    draw_survey(
        title="Phase 0 Spike",
        rule_length=20.0,
        csv_map_path=str(csv_path),
        output_path=str(pdf_path),
    )
    return str(pdf_path)
