"""Mobile bridge for the Survey Plot screen. Mirrors app/pages/1_survey_plot.py:
resolve inputs (DXF->CSV or CSV passthrough), validate optional merge, run
draw_survey, return the output PDF path. Lives under android/, never imported by
cave_sketch. Single entrypoint: generate_survey_plot(inputs_json, work_dir)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cave_sketch.dxf.parser import parse_dxf


def resolve_input(input_path: Optional[str], work_dir: str, stem: str) -> Optional[str]:
    """Return a CSV path for an input. DXF inputs are parsed to <work_dir>/<stem>.csv;
    CSV inputs are returned unchanged; None/empty returns None."""
    if not input_path:
        return None
    src = Path(input_path)
    if src.suffix.lower() == ".dxf":
        csv_path = Path(work_dir) / f"{stem}.csv"
        parse_dxf(src, csv_path)
        return str(csv_path)
    return str(src)
