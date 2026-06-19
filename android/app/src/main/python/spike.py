"""Phase 0 spike glue. Calls the UNTOUCHED cave_sketch core, mirroring the web
Survey Plot flow: parse_dxf (DXF->CSV) then draw_survey (CSV->PDF)."""
from pathlib import Path


def render_sample_pdf_timed(dxf_path: str, work_dir: str) -> str:
    """Render the sample DXF, returning JSON timings (ms) for import/parse/draw."""
    import json
    import time
    from pathlib import Path

    work = Path(work_dir)
    csv_path = work / "sample.csv"
    pdf_path = work / "sample.pdf"

    t0 = time.perf_counter()
    from cave_sketch.dxf.parser import parse_dxf
    from cave_sketch.survey.survey import draw_survey
    t1 = time.perf_counter()

    parse_dxf(Path(dxf_path), csv_path)
    t2 = time.perf_counter()

    draw_survey(title="Spike", rule_length=20.0, csv_map_path=str(csv_path),
                output_path=str(pdf_path))
    t3 = time.perf_counter()

    return json.dumps({
        "import_ms": round((t1 - t0) * 1000),
        "parse_ms": round((t2 - t1) * 1000),
        "draw_ms": round((t3 - t2) * 1000),
        "pdf_path": str(pdf_path),
    })

