from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from cave_sketch.dxf.models import CaveSurvey
from cave_sketch.survey.config import SurveyConfig, TitleBlockInfo
from cave_sketch.survey.graphics.survey_plot import create_survey
from cave_sketch.survey.graphics.title_block import (
    build_title_rows,
    draw_cave_name,
    draw_title_block,
)


def render_survey(
    survey: CaveSurvey,
    config: SurveyConfig,
    section_survey: Optional[CaveSurvey] = None,
    excluded_nodes: Optional[List[str]] = None,
    total_length: float = 0.0,
    total_depth: Optional[float] = None,
    title_block: Optional[TitleBlockInfo] = None,
    magnetic_variation_deg: float = 0.0,
) -> Figure:
    """
    Render a cave survey plot (plan and optionally section) using matplotlib.

    Args:
        survey: The plan view CaveSurvey.
        config: Rendering configuration.
        section_survey: Optional section view CaveSurvey.
        excluded_nodes: List of node IDs to exclude from rendering.
        total_length: Total length of the cave survey in meters.
        total_depth: Total depth range in meters, or None.
        title_block: Metadata shown in the title block.
        magnetic_variation_deg: Variation applied to the map, printed when non-zero.

    Returns:
        A matplotlib Figure object.
    """
    # Create Fig
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.subplots_adjust(top=0.86)
    name_text = draw_cave_name(fig, survey.name)

    n_plots = 1 + (1 if section_survey else 0)
    index = 1

    # Convert config dataclass to dict for legacy create_survey
    config_dict = {
        "show_details": config.show_details,
        "marker_zoom": config.marker_zoom,
        "text_zoom": config.text_zoom,
        "line_width_zoom": config.line_width_zoom,
        "rotation_deg": config.rotation_deg,
        "show_grid": config.show_grid,
        "show_centerline": config.show_centerline,
    }

    section_ax = None
    # 1. Section Subplot
    if section_survey:
        section_ax = plt.subplot(n_plots, 1, index)
        section_df = _survey_to_df(section_survey)
        create_survey(
            section_df,
            rule_flag=True,
            rule_length=config.rule_length,
            north_flag=False,
            excluded_nodes=excluded_nodes,
            rule_orientation="vertical",
            config=config_dict,
            ax=section_ax,
        )
        section_ax.set_title("Sezione")
        index += 1

    # 2. Map subplot
    map_ax = plt.subplot(n_plots, 1, index)
    map_df = _survey_to_df(survey)
    create_survey(
        map_df,
        rule_flag=True,
        rule_length=config.rule_length,
        north_flag=config.show_north,
        excluded_nodes=excluded_nodes,
        rule_orientation="horizontal",
        rotation_deg=config.rotation_deg,
        config=config_dict,
        ax=map_ax,
    )
    title = "Pianta" if config.show_north or section_survey is not None else "Sezione"
    map_ax.set_title(title)

    # The plan view gets first pick of free corners for the title block.
    plot_axes = [map_ax] + ([section_ax] if section_ax is not None else [])
    rows = build_title_rows(
        title_block or TitleBlockInfo(), magnetic_variation_deg, total_length, total_depth
    )
    draw_title_block(fig, name_text, rows, plot_axes)

    return fig


def _survey_to_df(survey: CaveSurvey) -> pd.DataFrame:
    """Helper to convert CaveSurvey model to DataFrame for legacy rendering."""
    data = []
    for p in survey.points:
        links_str = "-".join(p.links) if p.links else "-"
        data.append([p.id, links_str, p.x, p.y, p.point_type, p.rotation])
    return pd.DataFrame(data, columns=["Node_Id", "Links", "X", "Y", "Type", "Rotation"])
