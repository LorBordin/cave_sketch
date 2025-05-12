from matplotlib.backends.backend_pdf import PdfPages
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import pandas as pd

from cave_sketch.survey.graphics import create_survey

def draw_survey(
    title: str,
    rule_length: float,
    csv_map_path: Optional[str] = None,
    csv_section_path: Optional[str] = None,
    output_path: Optional[str] = None,
    excluded_nodes: Optional[List] = None,
    config: Dict = {} 
) -> None:
    # Load the CSV files
    map_df, section_df = None, None

    if csv_map_path is not None:
        map_df = pd.read_csv(csv_map_path)
    if csv_section_path is not None:
        section_df = pd.read_csv(csv_section_path)

    # Create Fig
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.subplots_adjust(top=0.88)  # Leave more space for title
    fig.suptitle(title, fontsize=16, y=0.95)

    n_plots = int(map_df is not None) + int(section_df is not None)
    rotation_deg = config["rotation_deg"]
    index = 1


    ## 1. Section Subplot
    if section_df is not None:
        ax = plt.subplot(n_plots, 1, index)
        create_survey(
            section_df, 
            rule_flag=True, 
            rule_length=rule_length,
            north_flag=False,
            excluded_nodes=excluded_nodes,
            rule_orientation="vertical",
            config=config, 
            ax=ax
        )
        ax.set_title("Sezione")
        index += 1

    ## 2. Map subplot
    if map_df is not None:
        ax = plt.subplot(2, 1, index)
        create_survey(
            map_df,
            rule_flag=True,
            rule_length=rule_length,
            north_flag=True,
            excluded_nodes=excluded_nodes,
            rule_orientation="horizontal", 
            rotation_deg=rotation_deg,
            config=config,
            ax=ax,
            )
        ax.set_title("Pianta")

    # Adjust layout to prevent overlap
    #plt.tight_layout()
    #plt.subplots_adjust(top=.9)

    with PdfPages(output_path) as pdf:
        pdf.savefig(fig)

    return fig