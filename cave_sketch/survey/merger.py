import math
import re
from enum import Enum
from typing import Dict, Optional, Set, Tuple

import pandas as pd


class SectionProtocol(Enum):
    SIMPLE = "simple"
    MIRROR = "mirror"
    DISPLACEMENT = "displacement"


def _bbox_distance(
    b1: Tuple[float, float, float, float],
    b2: Tuple[float, float, float, float],
) -> float:
    """Compute the minimum Euclidean distance between two 2D axis-aligned bounding boxes."""
    dx = max(0.0, b1[0] - b2[1], b2[0] - b1[1])
    dy = max(0.0, b1[2] - b2[3], b2[2] - b1[3])
    return math.hypot(dx, dy)


def _compute_displacement(
    parent_df: pd.DataFrame,
    child_df: pd.DataFrame,
    anchor_dx: float,
    anchor_dy: float,
) -> Tuple[float, float]:
    """
    Compute total (dx, dy) displacement for child survey relative to parent survey.

    Starts from the Simple alignment (anchor_dx, anchor_dy), tests directions from
    0° (right) to -90° (below) in 5° steps, slides child to clear parent bounding box
    by at least 10% of parent diagonal (floor 1.0 m), and selects the placement
    yielding the smallest combined bounding box area (tie-break: shorter slide distance,
    then angle closer to 0°).
    """
    p_min_x = float(parent_df["X"].min())
    p_max_x = float(parent_df["X"].max())
    p_min_y = float(parent_df["Y"].min())
    p_max_y = float(parent_df["Y"].max())
    p_box = (p_min_x, p_max_x, p_min_y, p_max_y)

    diag = math.hypot(p_max_x - p_min_x, p_max_y - p_min_y)
    padding = max(1.0, 0.10 * diag)

    c_min_x0 = float(child_df["X"].min()) + anchor_dx
    c_max_x0 = float(child_df["X"].max()) + anchor_dx
    c_min_y0 = float(child_df["Y"].min()) + anchor_dy
    c_max_y0 = float(child_df["Y"].max()) + anchor_dy

    # Angles from 0° (right) to -90° (below) in 5° steps (19 candidates)
    angles = [0 - 5 * i for i in range(19)]

    best_key = None
    best_offset: Tuple[float, float] = (anchor_dx, anchor_dy)

    s_max = (
        (p_max_x - p_min_x)
        + (p_max_y - p_min_y)
        + (c_max_x0 - c_min_x0)
        + (c_max_y0 - c_min_y0)
        + 2.0 * padding
        + 10.0
    )

    for deg in angles:
        if deg == 0:
            ux, uy = 1.0, 0.0
        elif deg == -90:
            ux, uy = 0.0, -1.0
        else:
            rad = math.radians(deg)
            ux, uy = math.cos(rad), math.sin(rad)

        def c_box_at(s: float) -> Tuple[float, float, float, float]:
            return (
                c_min_x0 + s * ux,
                c_max_x0 + s * ux,
                c_min_y0 + s * uy,
                c_max_y0 + s * uy,
            )

        if _bbox_distance(p_box, c_box_at(0.0)) >= padding:
            s = 0.0
        else:
            low = 0.0
            high = s_max
            # Binary search to find minimum slide distance clearing padding
            for _ in range(60):
                mid = (low + high) / 2.0
                if _bbox_distance(p_box, c_box_at(mid)) >= padding:
                    high = mid
                else:
                    low = mid
            s = high

        # Combined bounding box
        cb = c_box_at(s)
        comb_min_x = min(p_min_x, cb[0])
        comb_max_x = max(p_max_x, cb[1])
        comb_min_y = min(p_min_y, cb[2])
        comb_max_y = max(p_max_y, cb[3])
        area = (comb_max_x - comb_min_x) * (comb_max_y - comb_min_y)

        # Key for selection: min area, tie-break shorter slide, tie-break angle closer to 0°
        key = (round(area, 6), round(s, 6), abs(deg))
        if best_key is None or key < best_key:
            best_key = key
            best_offset = (anchor_dx + s * ux, anchor_dy + s * uy)

    return best_offset


def _get_numeric_ids(df: pd.DataFrame) -> Set[int]:
    """Extract numeric IDs from the Node_Id column."""
    ids = set()
    for nid in df["Node_Id"]:
        if isinstance(nid, str) and re.fullmatch(r"\d+", nid):
            ids.add(int(nid))
        elif isinstance(nid, (int, float)) and not pd.isna(nid):
            ids.add(int(nid))
    return ids

def _get_mixed_prefixes(df: pd.DataFrame) -> Set[int]:
    """Extract numeric prefixes from xxPyy Node_Ids."""
    prefixes = set()
    for nid in df["Node_Id"]:
        if isinstance(nid, str):
            m = re.match(r"(\d+)P(\d+)", nid)
            if m:
                prefixes.add(int(m.group(1)))
    return prefixes

def _merge_single_view(
    parent_df: pd.DataFrame,
    child_df: pd.DataFrame,
    parent_station: str,
    child_station: str,
    is_section: bool = False,
    section_protocol: SectionProtocol = SectionProtocol.SIMPLE
) -> pd.DataFrame:
    """Helper to merge a single view (map or section)."""
    parent_df = parent_df.copy()
    child_df = child_df.copy()

    # Normalize Node_Id as string
    parent_df["Node_Id"] = parent_df["Node_Id"].astype(str)
    child_df["Node_Id"] = child_df["Node_Id"].astype(str)
    parent_station = str(parent_station)
    child_station = str(child_station)

    # 1. Coordinate translation
    p_indices = [i for i, nid in enumerate(parent_df["Node_Id"]) if nid == parent_station]
    c_indices = [i for i, nid in enumerate(child_df["Node_Id"]) if nid == child_station]
    
    if not p_indices:
        raise ValueError(f"Station {parent_station} not found in parent survey.")
    if not c_indices:
        raise ValueError(f"Station {child_station} not found in child survey.")

    p_row = parent_df.iloc[p_indices[0]]
    c_row = child_df.iloc[c_indices[0]]

    # Simple translation: align child_station to parent_station
    delta_x = p_row["X"] - c_row["X"]
    delta_y = p_row["Y"] - c_row["Y"]
    
    # Apply protocol-specific transformations before translation if needed (e.g. MIRROR)
    # MIRROR: "mirror the child sketch across the vertical axis (y-axis) before being placed"
    # Vertical axis (y-axis) means X' = -X.
    if is_section and section_protocol == SectionProtocol.MIRROR:
        # Mirror child across its own vertical axis through child_station
        child_df["X"] = 2 * c_row["X"] - child_df["X"]
        # Recalculate delta_x after mirroring (c_row["X"] stays same, but child_df["X"] changed)
        delta_x = p_row["X"] - c_row["X"]

    if is_section and section_protocol == SectionProtocol.DISPLACEMENT:
        # Displacement algorithm: search right first, then below
        p_max_x = parent_df["X"].max()
        padding = 50.0 # Better padding for displacement
        
        # Start by centering child at parent station
        delta_x = p_row["X"] - c_row["X"]
        delta_y = p_row["Y"] - c_row["Y"]
        
        # Shift child to the right of parent survey
        # child_df["X"] + delta_x is the position if SIMPLE. 
        # We want (child_df["X"] + delta_x).min() > p_max_x + padding
        current_child_min_x = child_df["X"].min() + delta_x
        additional_shift_x = max(0, (p_max_x + padding) - current_child_min_x)
        delta_x += additional_shift_x
        
        # Add connector node to child_df
        # This node is at the parent station's absolute coordinates
        # but relative to the child survey's origin 
        # (so after delta shift it lands on parent station)
        connector_id = "CONN_1"
        connector_node = pd.DataFrame({
            "Node_Id": [connector_id],
            "X": [p_row["X"] - delta_x],
            "Y": [p_row["Y"] - delta_y],
            "Links": [child_station],
            "Type": ["connector"]
        })
        child_df = pd.concat([child_df, connector_node], ignore_index=True)

    child_df["X"] = child_df["X"] + delta_x
    child_df["Y"] = child_df["Y"] + delta_y

    # 2. ID Remapping
    parent_numeric_ids = _get_numeric_ids(parent_df)
    child_numeric_ids = _get_numeric_ids(child_df)
    
    mapping: Dict[str, str] = {child_station: parent_station}
    
    pref_offset = 0
    if child_numeric_ids:
        max_parent = max(parent_numeric_ids) if parent_numeric_ids else 0
        min_child = min(child_numeric_ids)
        offset = max_parent + 1 - min_child
        
        for cid in child_numeric_ids:
            cid_str = str(cid)
            if cid_str != child_station:
                mapping[cid_str] = str(cid + offset)

    # Mixed IDs (xxPyy) remapping
    parent_prefixes = _get_mixed_prefixes(parent_df)
    child_prefixes = _get_mixed_prefixes(child_df)
    
    if child_prefixes:
        max_p_pref = max(parent_prefixes) if parent_prefixes else 0
        min_c_pref = min(child_prefixes)
        pref_offset = max_p_pref + 1 - min_c_pref

    def remap_id(nid) -> str:
        nid_str = str(nid)
        if nid_str.endswith(".0"):
            nid_str = nid_str[:-2]
        if nid_str in mapping:
            return mapping[nid_str]
        m = re.match(r"(\d+)P(\d+)", nid_str)
        if m:
            base, suffix = int(m.group(1)), m.group(2)
            new_base = base + pref_offset
            return f"{new_base}P{suffix}"
        return nid_str

    # Remove coincident node from child AFTER computing mapping/offset
    not_coincident_indices = [
        i for i, nid in enumerate(child_df["Node_Id"]) if str(nid) != child_station
    ]
    child_df = child_df.iloc[not_coincident_indices].reset_index(drop=True)
    
    child_df["Node_Id"] = child_df["Node_Id"].apply(remap_id)
    
    def remap_links(link_val) -> str:
        if pd.isna(link_val) or not link_val or link_val == "-":
            return "-"
        link_str = str(link_val)
        if link_str.endswith(".0"):
            link_str = link_str[:-2]
        return "-".join(remap_id(link) for link in link_str.split("-"))
    
    child_df["Links"] = child_df["Links"].apply(remap_links)

    return pd.concat([parent_df, child_df], ignore_index=True)

def merge_surveys(
    parent_map: Optional[pd.DataFrame],
    parent_section: Optional[pd.DataFrame],
    child_map: Optional[pd.DataFrame],
    child_section: Optional[pd.DataFrame],
    parent_station: str,
    child_station: str,
    section_protocol: SectionProtocol = SectionProtocol.SIMPLE
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Merge two cave surveys (parent and child) into a single survey.
    
    Args:
        parent_map: DataFrame for parent map view
        parent_section: DataFrame for parent section view
        child_map: DataFrame for child map view
        child_section: DataFrame for child section view
        parent_station: Station ID in parent survey to match
        child_station: Station ID in child survey to match
        section_protocol: Protocol to use for merging section view
        
    Returns:
        Tuple of (merged_map, merged_section) DataFrames
    """
    merged_map = None
    if parent_map is not None and child_map is not None:
        merged_map = _merge_single_view(
            parent_map, child_map, parent_station, child_station
        )
    elif parent_map is not None:
        merged_map = parent_map.copy()
    elif child_map is not None:
        # If only child is present, it's not really a merge, 
        # but for consistency we might want to just return it.
        # However, the UI ensures both are uploaded.
        merged_map = child_map.copy()

    merged_section = None
    if parent_section is not None and child_section is not None:
        merged_section = _merge_single_view(
            parent_section, child_section, parent_station, child_station,
            is_section=True, section_protocol=section_protocol
        )
    elif parent_section is not None:
        merged_section = parent_section.copy()
    elif child_section is not None:
        merged_section = child_section.copy()
        
    return merged_map, merged_section
