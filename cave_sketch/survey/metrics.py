import math
import re
from typing import Optional

import pandas as pd


def compute_total_length(df: pd.DataFrame) -> float:
    """
    Compute the total surveyed length from the plan (map) view DataFrame.
    Sum of Euclidean distances between all pairs of directly connected
    numeric-only stations (survey legs).
    """
    if df is None or df.empty:
        return 0.0

    # Pattern for numeric-only stations
    numeric_pattern = re.compile(r"^\d+$")

    # Mapping of numeric station ID to coordinates (X, Y)
    coords = {}
    for _, row in df.iterrows():
        node_id = str(row["Node_Id"])
        if numeric_pattern.match(node_id):
            coords[node_id] = (float(row["X"]), float(row["Y"]))

    # Parse and deduplicate legs
    legs = set()
    for _, row in df.iterrows():
        node_id = str(row["Node_Id"])
        if not numeric_pattern.match(node_id):
            continue

        links_str = row.get("Links")
        if pd.isna(links_str) or not links_str or links_str == "-":
            continue

        # Split and filter to numeric links
        links = [link.strip() for link in str(links_str).split("-") if link.strip()]
        for link in links:
            if numeric_pattern.match(link) and link in coords:
                # Store as a sorted tuple to prevent counting A->B and B->A twice
                leg = tuple(sorted([node_id, link]))
                legs.add(leg)

    # Sum distances
    total_length = 0.0
    for u, v in legs:
        xu, yu = coords[u]
        xv, yv = coords[v]
        total_length += math.sqrt((xu - xv) ** 2 + (yu - yv) ** 2)

    return total_length


def compute_total_depth(df: Optional[pd.DataFrame]) -> Optional[float]:
    """
    Compute the total depth range from the section view DataFrame.
    max(Y) - min(Y) among all numeric-only stations in the section view DataFrame.
    Returns None if the DataFrame is None.
    """
    if df is None:
        return None
    if df.empty:
        return 0.0

    # Pattern for numeric-only stations
    numeric_pattern = re.compile(r"^\d+$")

    # Collect Y coordinates for numeric-only stations
    y_coords = []
    for _, row in df.iterrows():
        node_id = str(row["Node_Id"])
        if numeric_pattern.match(node_id):
            y_coords.append(float(row["Y"]))

    if not y_coords:
        return 0.0

    return max(y_coords) - min(y_coords)
