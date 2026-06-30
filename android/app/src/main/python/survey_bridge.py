"""Mobile bridge for the Survey Plot screen. Mirrors app/pages/1_survey_plot.py:
resolve inputs (DXF->CSV or CSV passthrough), validate optional merge, run
draw_survey, return the output PDF path. Lives under android/, never imported by
cave_sketch. Single entrypoint: generate_survey_plot(inputs_json, work_dir)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.survey.merger import SectionProtocol
from cave_sketch.survey.survey import draw_survey


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


def effective_map_csv(map_csv: Optional[str], child_map_csv: Optional[str],
                      parent_station: str, child_station: str,
                      section_protocol: SectionProtocol,
                      work_dir: str) -> Optional[str]:
    """Return the map CSV the Satellite view should use: the merged CSV when a
    valid merge was requested (mirrors app/pages/1_survey_plot.py glue), else the
    parsed map CSV, or None when no map was provided."""
    if not map_csv:
        return None
    if child_map_csv and parent_station and child_station:
        from cave_sketch.survey.merger import merge_surveys
        merged_df, _ = merge_surveys(
            parent_map=pd.read_csv(map_csv),
            parent_section=None,
            child_map=pd.read_csv(child_map_csv),
            child_section=None,
            parent_station=parent_station,
            child_station=child_station,
            section_protocol=section_protocol,
        )
        if merged_df is not None:
            merged_path = Path(work_dir) / "merged_map.csv"
            merged_df.to_csv(merged_path, index=False)
            return str(merged_path)
    return map_csv


def generate_survey_plot(inputs_json: str, work_dir: str) -> str:
    """Entrypoint mirroring app/pages/1_survey_plot.py. See module/Interfaces for
    the inputs_json shape. Returns JSON {"pdf_path": ...} or {"error", "detail"}."""
    try:
        data = json.loads(inputs_json)
        settings = data.get("settings", {})

        map_csv = resolve_input(data.get("map_path"), work_dir, "map")
        section_csv = resolve_input(data.get("section_path"), work_dir, "section")
        child_map_csv = resolve_input(data.get("child_map_path"), work_dir, "child_map")
        child_section_csv = resolve_input(data.get("child_section_path"), work_dir, "child_section")

        if not map_csv and not section_csv:
            return json.dumps({"error": "no_input",
                               "detail": "Select at least one map or section file."})

        parent_station = data.get("parent_station") or ""
        child_station = data.get("child_station") or ""
        has_child = bool(child_map_csv or child_section_csv)
        if has_child and parent_station and child_station:
            err = validate_merge(map_csv or section_csv,
                                 child_map_csv or child_section_csv,
                                 parent_station, child_station)
            if err:
                return json.dumps({"error": "merge_invalid", "detail": err})

        pdf_path = str(Path(work_dir) / "survey.pdf")
        fig = draw_survey(
            title=data.get("survey_name", ""),
            rule_length=float(settings.get("rule_length", 100)),
            csv_map_path=map_csv,
            csv_section_path=section_csv,
            child_csv_map_path=child_map_csv,
            child_csv_section_path=child_section_csv,
            parent_station=parent_station or None,
            child_station=child_station or None,
            section_protocol=SectionProtocol(data.get("section_protocol", "simple")),
            output_path=pdf_path,
            surveyor_name=data.get("surveyor_name", ""),
            config={
                "rotation_deg": settings.get("rotation_deg", 0.0),
                "show_details": settings.get("show_details", True),
                "show_grid": settings.get("show_grid", True),
                "marker_zoom": settings.get("marker_zoom", 0.0),
                "text_zoom": settings.get("text_zoom", 0.0),
                "line_width_zoom": settings.get("line_width_zoom", 0.0),
                "show_centerline": settings.get("show_centerline", True),
            },
        )
        import matplotlib.pyplot as plt
        plt.close(fig)  # release the figure; mobile renders the PDF, not the figure
        result = {"pdf_path": pdf_path}
        eff_map_csv = effective_map_csv(
            map_csv, child_map_csv, parent_station or "", child_station or "",
            SectionProtocol(data.get("section_protocol", "simple")), work_dir,
        )
        if eff_map_csv:
            result["map_csv_path"] = eff_map_csv
        return json.dumps(result)
    except Exception as e:  # noqa: BLE001 — the bridge converts all failures to structured errors
        return json.dumps({"error": "render_failed", "detail": str(e)})


def prewarm() -> None:
    """Pay the one-time import + matplotlib font-cache cost off the critical path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure()
    fig.text(0.5, 0.5, "warm")  # forces the font manager to initialise
    plt.close(fig)


