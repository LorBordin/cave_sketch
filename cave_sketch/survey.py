from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from matplotlib.figure import Figure

from cave_sketch.dxf.models import CaveSurvey, SurveyPoint
from cave_sketch.survey.config import SurveyConfig
from cave_sketch.survey.pdf import export_pdf
from cave_sketch.survey.renderer import render_survey


def draw_survey(
    title: str,
    rule_length: float,
    csv_map_path: Optional[str] = None,
    csv_section_path: Optional[str] = None,
    output_path: Optional[str] = None,
    excluded_nodes: Optional[List] = None,
    config: Dict = {}
) -> Figure:
    """
    Backward-compatible shim for drawing a cave survey.
    """
    survey = None
    if csv_map_path:
        survey = _df_to_survey(pd.read_csv(csv_map_path), title)
    
    section_survey = None
    if csv_section_path:
        section_survey = _df_to_survey(pd.read_csv(csv_section_path), f"{title} Section")
        
    if not survey and not section_survey:
        raise ValueError("At least one survey path (map or section) must be provided.")
        
    # If only section is provided, use it as primary for render_survey for now
    if not survey and section_survey:
        survey = section_survey
        section_survey = None

    render_config = SurveyConfig(
        rule_length=rule_length,
        rotation_deg=config.get("rotation_deg", 0.0),
        show_details=config.get("show_details", True),
        marker_zoom=config.get("marker_zoom", 0.0),
        text_zoom=config.get("text_zoom", 0.0),
        line_width_zoom=config.get("line_width_zoom", 0.0)
    )
    
    fig = render_survey(
        survey=survey,
        config=render_config,
        section_survey=section_survey,
        excluded_nodes=excluded_nodes
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
        survey.points.append(SurveyPoint(
            id=str(row["Node_Id"]),
            x=float(row["X"]),
            y=float(row["Y"]),
            point_type=str(row["Type"]),
            links=links
        ))
    return survey
