from typing import List, Dict, Optional
from folium import Map
import pandas as pd
import numpy as np
import folium
import json
import math

from cave_sketch.features.render_features import extract_features
from cave_sketch.backend_renders import render_to_folium
from cave_sketch.style import STYLE_MAP

# WGS84 constants
_A = 6378137.0
_F = 1.0 / 298.257223563
_E2 = _F * (2 - _F)
_DEG2RAD = np.pi / 180.0

def draw_map(
    map_path: str, 
    gps_points: List[Dict], 
    output_path: str, 
    map_name: str = "Cave", 
    additional_json_maps: Optional[List[str]] = None,
    rotation_angle: float = 0):
    """
    Create cave map from CSV data and optionally combine with additional JSON maps
    
    Args:
        map_path: Path to CSV file with cave data
        gps_points: List of GPS reference points
        output_path: Path for HTML output
        map_name: Name for the current map
        additional_json_maps: List of paths to additional JSON map files to combine
    
    Returns:
        tuple: (html_map, json_path) - The created map and path to JSON export
    """
    # Load and process the main map data
    map_df = pd.read_csv(map_path)
    map_df = cartesian_to_latlon(map_df, gps_points)
    
    # Export current map as JSON (different path to avoid conflicts)
    json_output_path = output_path.replace('.html', '.json')
    json_path = export_map_data(map_df, map_name, json_output_path)
    
    # Prepare list of all JSON maps to combine
    json_maps_to_combine = [json_path]
    if additional_json_maps:
        json_maps_to_combine.extend(additional_json_maps)
    
    # Create HTML map from JSON data
    html_map = create_html_map(json_maps_to_combine, output_path, rotation_angle=rotation_angle)
    
    return html_map, json_path

def _meters_per_degree_wgs84(lat_deg: float):
    """
    Return (meters_per_degree_latitude, meters_per_degree_longitude)
    at given latitude in degrees using WGS84 ellipsoid.
    """
    lat_rad = np.asarray(lat_deg) * _DEG2RAD
    sinlat = np.sin(lat_rad)
    one_minus_e2_sin2 = 1.0 - _E2 * sinlat**2

    # meridional radius of curvature
    M = _A * (1 - _E2) / (one_minus_e2_sin2 ** 1.5)
    # prime vertical radius of curvature
    N = _A / np.sqrt(one_minus_e2_sin2)

    m_per_deg_lat = M * _DEG2RAD
    m_per_deg_lon = N * np.cos(lat_rad) * _DEG2RAD

    return float(m_per_deg_lat), float(m_per_deg_lon)


def cartesian_to_latlon(df: pd.DataFrame, points: List[Dict]) -> pd.DataFrame:
    """
    For each anchor point in `points` (dict with keys 'station', 'lat', 'lon'),
    build a linear local transform around (lat, lon) and produce columns
    Latitude_i, Longitude_i for each anchor. Finally average those columns
    into df['Latitude'] and df['Longitude'].
    Assumes X is Easting (meters), Y is Northing (meters).
    """
    # Make a copy to avoid mutating caller's DF unexpectedly
    df = df.copy()

    for i, point in enumerate(points):
        Idx = str(point["station"])
        lat_0 = float(point["lat"])
        lon_0 = float(point["lon"])

        # prepare columns
        lat_col = f"Latitude_{i}"
        lon_col = f"Longitude_{i}"
        df[lat_col] = np.nan
        df[lon_col] = np.nan

        # find anchor row (where Node_Id equals the station id)
        mask_anchor = df['Node_Id'].astype(str) == Idx
        if not mask_anchor.any():
            # anchor not found: skip this point but keep NaNs
            print(f"[warn] anchor Node_Id {Idx} not found in dataframe — skipping anchor {Idx}")
            continue

        # choose the first matching row as offset origin
        anchor_idx = np.flatnonzero(mask_anchor)[0]
        offset_x = float(df.loc[anchor_idx, 'X'])
        offset_y = float(df.loc[anchor_idx, 'Y'])

        # compute local meters-per-degree at lat_0
        m_per_deg_lat, m_per_deg_lon = _meters_per_degree_wgs84(lat_0)

        # set exact anchor lat/lon for the anchor row (optional, mirrors your old behavior)
        df.loc[anchor_idx, lat_col] = lat_0
        df.loc[anchor_idx, lon_col] = lon_0

        # compute lat/lon for all rows using the linear approx
        # dy = Y - offset_y  (north displacement)
        # dx = X - offset_x  (east displacement)
        dy = df['Y'].to_numpy(dtype=float) - offset_y
        dx = df['X'].to_numpy(dtype=float) - offset_x

        df[lat_col] = lat_0 + (dy / m_per_deg_lat)
        df[lon_col] = lon_0 + (dx / m_per_deg_lon)

    # gather generated columns and average
    lat_cols = [c for c in df.columns if c.startswith("Latitude_")]
    lon_cols = [c for c in df.columns if c.startswith("Longitude_")]

    if lat_cols:
        df["Latitude"] = df[lat_cols].mean(axis=1)
    else:
        df["Latitude"] = np.nan

    if lon_cols:
        df["Longitude"] = df[lon_cols].mean(axis=1)
    else:
        df["Longitude"] = np.nan

    return df


def export_map_data(df: pd.DataFrame, map_name: str, output_path: str):
    """Export map data as JSON for later combination"""
    df["Links"].fillna(" ", inplace=True)
    
    # Prepare data structure
    map_data = {
        "name": map_name,
        "center": df[["Latitude", "Longitude"]].mean().to_dict(),
        "nodes": {},
        "lines": [],
        "water_polygons": []
    }
    
    # Store nodes
    for _, row in df.iterrows():
        map_data["nodes"][row['Node_Id']] = {
            "lat": row['Latitude'],
            "lon": row['Longitude'],
            "type": row["Type"]
        }
    
    # Separate water areas from regular lines
    water_df = df[df["Type"] == "A_water"].copy()
    non_water_df = df[df["Type"] != "A_water"].copy()
    
    # Process water polygons
    if not water_df.empty:
        # Group by polygon ID (prefix of Node_Id)
        water_df['polygon_id'] = water_df['Node_Id'].str.extract(r'^(\d+)P')
        
        for polygon_id, group in water_df.groupby('polygon_id'):
            # Sort by the numeric part after 'P' to maintain order
            group = group.copy()
            group['sort_key'] = group['Node_Id'].str.extract(r'P(\d+)').astype(int)
            group = group.sort_values('sort_key')
            
            # Extract coordinates in order
            coordinates = []
            for _, row in group.iterrows():
                coordinates.append([row['Latitude'], row['Longitude']])
            
            # Ensure polygon is closed (first point = last point)
            if coordinates and coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            
            if len(coordinates) >= 3:  # Valid polygon needs at least 3 points
                map_data["water_polygons"].append({
                    "coordinates": coordinates,
                    "polygon_id": polygon_id
                })
    
    # Store regular lines (non-water)
    for _, row in non_water_df.iterrows():
        lat, lon = row['Latitude'], row['Longitude']
        for link in row['Links'].split('-'):
            if link and link in map_data["nodes"]:
                map_data["lines"].append({
                    "from": {"lat": lat, "lon": lon, "id": row['Node_Id']},
                    "to": {"lat": map_data["nodes"][link]["lat"], 
                          "lon": map_data["nodes"][link]["lon"], "id": link},
                    "type": row["Type"]
                })
    
    # Save as JSON
    with open(output_path, 'w') as f:
        json.dump(map_data, f, indent=2)
    
    return output_path


def create_html_map(
    json_paths: List[str],
    output_path: str,
    rotation_angle: float = 0
):
    """Create a Folium HTML map by combining multiple survey JSONs."""
    all_data = []
    centers = []

    for p in json_paths:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        all_data.append(d)
        centers.append([d["center"]["Latitude"], d["center"]["Longitude"]])

    overall_center = [
        sum(c[0] for c in centers) / len(centers),
        sum(c[1] for c in centers) / len(centers)
    ]

    fmap = Map(location=overall_center, zoom_start=15, control_scale=True)
    folium.TileLayer(
        'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google', name='Google Satellite', overlay=False
    ).add_to(fmap)

    for d in all_data:
        features = extract_features(d, rotation_angle)
        render_to_folium(features, fmap, d["name"])

    folium.LayerControl().add_to(fmap)
    fmap.save(output_path)
    return fmap


# Standalone function for combining existing JSON maps (keeping for backward compatibility)
def combine_maps_from_json(json_paths: List[str], output_path: str):
    """Combine multiple JSON map exports into single HTML map"""
    return create_html_map(json_paths, output_path)