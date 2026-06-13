from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from matplotlib.figure import Figure

from cave_sketch.dxf.models import CaveSurvey, SurveyPoint
from cave_sketch.survey.config import SurveyConfig
from cave_sketch.survey.merger import SectionProtocol, merge_surveys
from cave_sketch.survey.metrics import compute_total_depth, compute_total_length
from cave_sketch.survey.pdf import export_pdf
from cave_sketch.survey.renderer import render_survey


def draw_survey(
    title: str,
    rule_length: float,
    csv_map_path: Optional[str] = None,
    csv_section_path: Optional[str] = None,
    child_csv_map_path: Optional[str] = None,
    child_csv_section_path: Optional[str] = None,
    parent_station: Optional[str] = None,
    child_station: Optional[str] = None,
    section_protocol: SectionProtocol = SectionProtocol.SIMPLE,
    output_path: Optional[str] = None,
    excluded_nodes: Optional[List] = None,
    surveyor_name: str = "",
    config: Dict = {},
) -> Figure:
    """
    Draw a cave survey, optionally merging a child survey.
    """
    parent_map = pd.read_csv(csv_map_path) if csv_map_path else None
    parent_section = pd.read_csv(csv_section_path) if csv_section_path else None
    child_map = pd.read_csv(child_csv_map_path) if child_csv_map_path else None
    child_section = pd.read_csv(child_csv_section_path) if child_csv_section_path else None

    if (child_map is not None or child_section is not None) and parent_station and child_station:
        merged_map, merged_section = merge_surveys(
            parent_map=parent_map,
            parent_section=parent_section,
            child_map=child_map,
            child_section=child_section,
            parent_station=parent_station,
            child_station=child_station,
            section_protocol=section_protocol
        )
    else:
        merged_map, merged_section = parent_map, parent_section

    # Compute metrics after merge
    total_length = compute_total_length(merged_map)
    total_depth = compute_total_depth(merged_section)

    survey = None
    if merged_map is not None:
        survey = _df_to_survey(merged_map, title)

    section_survey = None
    if merged_section is not None:
        section_survey = _df_to_survey(merged_section, f"{title} Section")

    if not survey and not section_survey:
        raise ValueError("At least one survey path (map or section) must be provided.")

    # If only section is provided, use it as primary for render_survey
    show_north = config.get("show_north", True)
    if not survey and section_survey:
        survey = section_survey
        section_survey = None
        show_north = False

    assert survey is not None

    render_config = SurveyConfig(
        rule_length=rule_length,
        rotation_deg=config.get("rotation_deg", 0.0),
        show_details=config.get("show_details", True),
        marker_zoom=config.get("marker_zoom", 0.0),
        text_zoom=config.get("text_zoom", 0.0),
        line_width_zoom=config.get("line_width_zoom", 0.0),
        show_north=show_north,
        show_grid=config.get("show_grid", True),
        surveyor_name=surveyor_name,
    )

    fig = render_survey(
        survey=survey,
        config=render_config,
        section_survey=section_survey,
        excluded_nodes=excluded_nodes,
        total_length=total_length,
        total_depth=total_depth,
    )

    if output_path:
        export_pdf(fig, Path(output_path))

    return fig


def _df_to_survey(df: pd.DataFrame, name: str) -> CaveSurvey:
    """Helper to convert a survey DataFrame back to a CaveSurvey model."""
    survey = CaveSurvey(name=name)
    for _, row in df.iterrows():
        links_str = row["Links"]
        links = [link.strip() for link in str(links_str).split("-") if link.strip() and link != "-"]
        survey.points.append(
            SurveyPoint(
                id=str(row["Node_Id"]),
                x=float(row["X"]),
                y=float(row["Y"]),
                point_type=str(row["Type"]),
                links=links,
            )
        )
    return survey
