from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from typing import List
import pandas as pd

from cave_sketch.graphics import create_survey

def draw_survey(
    title: str,
    csv_map_path: str,
    csv_section_path: str,
    output_path: str,
    excluded_nodes: List | None = None,
) -> None:
    
    # Load the CSV files
    map_df = pd.read_csv(csv_map_path)
    section_df = pd.read_csv(csv_section_path)

    fig = plt.figure(figsize=(8.27, 11.69))

    # Add title
    fig.suptitle(title, fontsize=16, y=.95)

    # Create 2 subplots
    
    ## 1. Map subplot
    ax1 = plt.subplot(2, 1, 2)
    create_survey(
        map_df,
        rule_flag=True,
        north_flag=True,
        excluded_nodes=excluded_nodes,
        ax=ax1,
        rule_orientation="horizontal"
        )
    ax1.set_title("Pianta")
    
    ## 2. Section Subplot
    ax2 = plt.subplot(2, 1, 1)
    create_survey(
        section_df, 
        rule_flag=True, 
        north_flag=False,
        excluded_nodes=excluded_nodes,
        ax=ax2,
        rule_orientation="vertical"
    )
    ax2.set_title("Sezione")

    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.subplots_adjust(top=.9)

    with PdfPages(output_path) as pdf:
        pdf.savefig(fig)