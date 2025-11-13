#!/usr/bin/env python3
"""
Utility script to merge two cave surveys.

Each dataframe (CSV) must contain:
    - Node_Id: unique identifier (numeric or alphanumeric like "12P4")
    - Links:  connected nodes, separated by "-"
    - X, Y:   coordinates
    - Type:   node type (station, L_wall, etc.)

The script merges two graphs, aligning the coincident nodes and
updating IDs, links, and coordinates accordingly.

Usage (from terminal):
-----------------------
python merge_cave_graphs.py df1.csv df2.csv node_id_df1 node_id_df2 merged.csv

Example:
--------
python merge_cave_graphs.py monte.csv intermezzo.csv 30 47 merged.csv

Author: Lorenzo + ChatGPT
Date: October 2025
"""

import pandas as pd
import re
import sys

sys.path.append("../")
from cave_sketch import parse_dxf

def merge_cave_graphs(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    node_id_df1: int | str,
    node_id_df2: int | str,
    output_csv: str | None = None
) -> pd.DataFrame:
    """
    Merge two cave-graph dataframes (df1 and df2) with possibly overlapping Node_Ids.

    Parameters
    ----------
    df1 : pd.DataFrame
        First dataframe (base).
    df2 : pd.DataFrame
        Second dataframe to merge into df1.
    node_id_df1 : int | str
        ID of the coincident node in df1 (must be numeric for offset calculation).
    node_id_df2 : int | str
        ID of the coincident node in df2.
    output_csv : str | None, optional
        If provided, export the merged dataframe to this path.

    Returns
    -------
    pd.DataFrame
        The merged dataframe with updated Node_Id, Links, and coordinates.
    """

    df1 = df1.copy()
    df2 = df2.copy()

    # Normalize Node_Id as string for both dfs
    df1["Node_Id"] = df1["Node_Id"].astype(str)
    df2["Node_Id"] = df2["Node_Id"].astype(str)
    node_id_df1 = str(node_id_df1)
    node_id_df2 = str(node_id_df2)

    # --- Step 1. Remove coincident node from df2
    coincident_node = df2[df2["Node_Id"] == node_id_df2]
    df2 = df2[df2["Node_Id"] != node_id_df2].reset_index(drop=True)

    # --- Step 2. Compute numeric offset for renaming
    numeric_ids_df1 = [int(x) for x in df1["Node_Id"] if re.fullmatch(r"\d+", x)]
    numeric_ids_df2 = [int(x) for x in df2["Node_Id"] if re.fullmatch(r"\d+", x)]
    if not numeric_ids_df2:
        raise ValueError("df2 has no numeric node IDs, cannot compute offset.")
    min_numeric_df2 = min(numeric_ids_df2)

    if not re.fullmatch(r"\d+", node_id_df1):
        raise ValueError(f"node_id_df1 must be numeric for offset calculation, got '{node_id_df1}'")

    offset = max(numeric_ids_df1) + 1 - min_numeric_df2
    numeric_mapping = {nid: nid + offset for nid in numeric_ids_df2}

    # Also map the coincident df2 node to df1 node
    if re.fullmatch(r"\d+", node_id_df2):
        numeric_mapping[int(node_id_df2)] = int(node_id_df1)

    # --- Step 3. Update Node_Id in df2

    # 3A. Build numeric mapping (as before)
    def update_node_id(node_id: str) -> str:
        # Numeric nodes
        if re.fullmatch(r"\d+", node_id):
            return str(numeric_mapping.get(int(node_id), node_id))
        # Mixed nodes (xxPyy)
        m = re.match(r"(\d+)P(\d+)", node_id)
        if m:
            base, suffix = int(m.group(1)), int(m.group(2))
            # We’ll fix these later with a separate mapping
            return f"{base}P{suffix}"
        return node_id

    df2["Node_Id"] = df2["Node_Id"].apply(update_node_id)

    # 3B. Handle mixed IDs (xxPyy) separately
    def get_mixed_prefixes(df):
        """Extract list of numeric prefixes from xxPyy Node_Ids."""
        return sorted({int(m.group(1)) for nid in df["Node_Id"]
                       if (m := re.match(r"(\d+)P\d+", nid))})

    prefixes_df1 = get_mixed_prefixes(df1)
    prefixes_df2 = get_mixed_prefixes(df2)

    if prefixes_df1 and prefixes_df2:
        max_pref_df1 = max(prefixes_df1)
        min_pref_df2 = min(prefixes_df2)

        # Compute offset for mixed prefixes
        offset_mixed = max_pref_df1 + 1 - min_pref_df2
        mixed_mapping = {p: p + offset_mixed for p in prefixes_df2}

        def relabel_mixed(node_id: str) -> str:
            m = re.match(r"(\d+)P(\d+)", node_id)
            if m:
                base, suffix = int(m.group(1)), m.group(2)
                if base in mixed_mapping:
                    return f"{mixed_mapping[base]}P{suffix}"
            return node_id

        df2["Node_Id"] = df2["Node_Id"].apply(relabel_mixed)
        df2["Links"] = df2["Links"].apply(
            lambda s: "-".join(relabel_mixed(l) for l in s.split("-"))
        )

    # --- Step 4. Update Links
    def update_links(link_str: str) -> str:
        return "-".join(update_node_id(l) for l in link_str.split("-"))

    df2["Links"] = df2["Links"].apply(update_links)

    # --- Step 5. Update coordinates (translation)
    if node_id_df1 not in df1["Node_Id"].values:
        raise ValueError(f"Node {node_id_df1} not found in df1['Node_Id'].")

    delta_X = df1.loc[df1["Node_Id"] == node_id_df1, "X"].values[0] - coincident_node["X"].values[0]
    delta_Y = df1.loc[df1["Node_Id"] == node_id_df1, "Y"].values[0] - coincident_node["Y"].values[0]
    df2["X"] = df2["X"] + delta_X
    df2["Y"] = df2["Y"] + delta_Y

    # --- Step 6. Merge and return
    merged = pd.concat([df1, df2], ignore_index=True)

    if output_csv:
        merged.to_csv(output_csv, index=False)

    return merged


# ------------------ CLI Interface ------------------

if __name__ == "__main__":
    #if len(sys.argv) < 6:
    #    print("Usage: python merge_cave_graphs.py df1.csv df2.csv node_id_df1 node_id_df2 merged.csv")
    #    sys.exit(1)

    #df1_path, df2_path, node_id_df1, node_id_df2, output_path = sys.argv[1:6]
    
    section = True
    suffix = 's' if section else 'p'
    out_suffix = 'sezione' if section else 'pianta'

    #df1_path = f"/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/surveys/monte_05_25/grotta_mittelbergferner-1{suffix}.dxf"
    #df2_path = f"/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/surveys/intermezzo_monte_10_25/grotta_mittelbergferner-2-1{suffix}.dxf"
    #node_id_df1 = 30
    #node_id_df2 = 47
    #output_path = f"/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/surveys/monte_10_25/monte_10_25_{out_suffix}.csv"

    df1_path = f"/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/surveys/monte_10_25/monte_10_25_{out_suffix}.csv"
    df2_path = f"/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/surveys/valle_10_25/grotta_mittelbergferner-3-1{suffix}.dxf"
    node_id_df1 = 31
    node_id_df2 = 54
    output_path = f"/Users/bordil/projects/cave_survey/un_altro_buco_nell_acqua/surveys/full_10_25_{out_suffix}.csv"

    print(f"\n📂 Loading dataframes:\n - {df1_path}\n - {df2_path}\n")
    if df1_path.endswith('.dxf'):
        df1 = parse_dxf(df1_path)
    else:
        df1 = pd.read_csv(df1_path)
    df2 = parse_dxf(df2_path)

    print(f"🔗 Merging at df1:{node_id_df1}  ↔  df2:{node_id_df2}")
    merged = merge_cave_graphs(df1, df2, node_id_df1, node_id_df2, output_csv=output_path)

    print(f"\n✅ Merge completed! Saved to {output_path}")
