from matplotlib.axes._axes import Axes
import matplotlib.pyplot as plt
from typing import List
import pandas as pd

from cave_sketch.graphics.utils import _is_integer_node
from cave_sketch.graphics.north import _add_north_arrow
from cave_sketch.graphics.rule import _add_rule

def create_survey(
    df: pd.DataFrame,
    rule_flag: bool,
    north_flag: bool,
    rule_orientation: str = "horizontal",
    excluded_nodes: List | None = None,
    ax: Axes| None = None
):
    if ax is None:
        ax = plt.gca()

    if excluded_nodes is None:
        excluded_nodes = []

    # Draw points and links
    for _, row in df.iterrows():
        node_id = row["Node_Id"]
        x, y = row["X"], row["Y"]
        links = row["Links"]

        if node_id in excluded_nodes:
            continue

        if _is_integer_node(node_id):
            ax.scatter(x, y, s=1, color="red")
            ax.text(
                x, y, node_id,
                fontsize=5, ha="right", va="bottom", color="black"
            )
        
        if pd.notna(links):
            linked_nodes = links.split("-")
            for link in linked_nodes:
                second_node_id = link.strip()

                if second_node_id in excluded_nodes:
                    continue

                linked_row = df[df["Node_Id"] ==  second_node_id]
                if not linked_row.empty:
                    x2, y2 = linked_row.iloc[0]['X'], linked_row.iloc[0]['Y']
                    line_color = 'gray' if _is_integer_node(node_id) else 'black'
                    line_width = .5 if line_color == "gray" else 1
                    ax.plot([x, x2], [y, y2], color=line_color, linewidth=line_width)
                
    # Add scale rule
    if rule_flag:
        if rule_orientation == "horizontal":
            scale_x_start, scale_y_start = min(df['X']), min(df['Y']) - 6
        else: 
            scale_x_start, scale_y_start = min(df['X']) - 6, min(df['Y'])
        _add_rule(ax, scale_x_start, scale_y_start, orientation=rule_orientation)

    # Add North
    if north_flag:
        arrow_x = scale_x_start + 14
        arrow_y = scale_y_start + 5
        arrow_len = 5
        _add_north_arrow(ax, arrow_x, arrow_y, arrow_len)

    # Remove axes
    ax.axis('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
