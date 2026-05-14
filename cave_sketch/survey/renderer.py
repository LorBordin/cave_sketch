from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from cave_sketch.dxf.models import CaveSurvey
from cave_sketch.survey.config import SurveyConfig
from cave_sketch.survey.graphics.survey_plot import create_survey


def render_survey(
    survey: CaveSurvey,
    config: SurveyConfig,
    section_survey: Optional[CaveSurvey] = None,
    excluded_nodes: Optional[List[str]] = None,
) -> Figure:
    """
    Render a cave survey plot (plan and optionally section) using matplotlib.

    Args:
        survey: The plan view CaveSurvey.
        config: Rendering configuration.
        section_survey: Optional section view CaveSurvey.
        excluded_nodes: List of node IDs to exclude from rendering.

    Returns:
        A matplotlib Figure object.
    """
    # Create Fig
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.subplots_adjust(top=0.88)
    fig.suptitle(survey.name, fontsize=16, y=0.95)

    n_plots = 1 + (1 if section_survey else 0)
    index = 1

    # Convert config dataclass to dict for legacy create_survey
    config_dict = {
        "show_details": config.show_details,
        "marker_zoom": config.marker_zoom,
        "text_zoom": config.text_zoom,
        "line_width_zoom": config.line_width_zoom,
        "rotation_deg": config.rotation_deg,
    }

    # 1. Section Subplot
    if section_survey:
        ax = plt.subplot(n_plots, 1, index)
        section_df = _survey_to_df(section_survey)
        create_survey(
            section_df,
            rule_flag=True,
            rule_length=config.rule_length,
            north_flag=False,
            excluded_nodes=excluded_nodes,
            rule_orientation="vertical",
            config=config_dict,
            ax=ax,
        )
        ax.set_title("Sezione")
        index += 1

    # 2. Map subplot
    ax = plt.subplot(n_plots, 1, index)
    map_df = _survey_to_df(survey)
    create_survey(
        map_df,
        rule_flag=True,
        rule_length=config.rule_length,
        north_flag=True,
        excluded_nodes=excluded_nodes,
        rule_orientation="horizontal",
        rotation_deg=config.rotation_deg,
        config=config_dict,
        ax=ax,
    )
    ax.set_title("Pianta")

    return fig


def _survey_to_df(survey: CaveSurvey) -> pd.DataFrame:
    """Helper to convert CaveSurvey model to DataFrame for legacy rendering."""
    data = []
    for p in survey.points:
        links_str = "-".join(p.links) if p.links else "-"
        data.append([p.id, links_str, p.x, p.y, p.point_type])
    return pd.DataFrame(data, columns=["Node_Id", "Links", "X", "Y", "Type"])
