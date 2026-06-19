"""Mobile bridge for the Survey Plot screen. Mirrors app/pages/1_survey_plot.py:
resolve inputs (DXF->CSV or CSV passthrough), validate optional merge, run
draw_survey, return the output PDF path. Lives under android/, never imported by
cave_sketch. Single entrypoint: generate_survey_plot(inputs_json, work_dir)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd

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


def validate_merge(parent_csv: Optional[str], child_csv: Optional[str],
                   parent_station: str, child_station: str) -> Optional[str]:
    """Mirror app/components/merging_controls.py. Return an error message if the
    merge stations are invalid, else None."""
    if not re.fullmatch(r"\d+", parent_station or ""):
        return "Main station ID must be numeric (e.g. '30')."
    if not re.fullmatch(r"\d+", child_station or ""):
        return "Child station ID must be numeric (e.g. '47')."
    if parent_csv:
        df = pd.read_csv(parent_csv)
        if parent_station not in df["Node_Id"].astype(str).values:
            return f"Station '{parent_station}' not found in the main survey."
    if child_csv:
        df = pd.read_csv(child_csv)
        if child_station not in df["Node_Id"].astype(str).values:
            return f"Station '{child_station}' not found in the child survey."
    return None

