from typing import Dict, List, Optional
from folium import Map
import pandas as pd
import numpy as np
import folium
import json

from cave_sketch.style import STYLE_MAP

def draw_map(
    map_path: str, 
    gps_points: List[Dict], 
    output_path: str, 
    map_name: str = "Cave", 
    additional_json_maps: Optional[List[str]] = None
):
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
    html_map = create_html_map(json_maps_to_combine, output_path)
    
    return html_map, json_path



def cartesian_to_latlon(df: pd.DataFrame, points: List[Dict]) -> pd.DataFrame:

    for i, point in enumerate(points):
        Idx = str(point["station"])
        lat_0 = point["lat"]
        lon_0 = point["lon"]
        
        print("IDX", Idx)
        print(df[df['Node_Id'] == Idx])

        df[f"Latitude_{i}"] = [np.nan] * len(df)
        df[f"Longitude_{i}"] = [np.nan] * len(df)
        
        df.loc[0, f"Latitude_{i}"] = lat_0
        df.loc[0, f"Longitude_{i}"] = lon_0
        offset_x = df[df['Node_Id'] == Idx]['X'].values[0]
        offset_y = df[df['Node_Id'] == Idx]['Y'].values[0]

        lat_0_rad = np.radians(lat_0)
    
        # Valid for near Trento
        meters_per_degree_latitude = 111132.92 - 559.82 * np.cos(2 * lat_0_rad) + 1.175 * np.cos(4 * lat_0_rad)
        meters_per_degree_longitude = 111412.84 * np.cos(lat_0_rad) - 93.5 * np.cos(3 * lat_0_rad)

        df[f'Latitude_{i}'] = lat_0 + ((df['Y'] - offset_y) / meters_per_degree_latitude)
        df[f'Longitude_{i}'] = lon_0 + ((df['X'] - offset_x) / meters_per_degree_longitude)

    lat_cols = [col for col in df.columns if col.startswith("Lat")]
    lon_cols = [col for col in df.columns if col.startswith("Lon")]
    df["Latitude"] = df[lat_cols].mean(axis=1)
    df["Longitude"] = df[lon_cols].mean(axis=1)

    return df


def export_map_data(df: pd.DataFrame, map_name: str, output_path: str):
    """Export map data as JSON for later combination"""
    df["Links"].fillna(" ", inplace=True)
    
    # Prepare data structure
    map_data = {
        "name": map_name,
        "center": df[["Latitude", "Longitude"]].mean().to_dict(),
        "nodes": {},
        "lines": []
    }
    
    # Store nodes
    for _, row in df.iterrows():
        map_data["nodes"][row['Node_Id']] = {
            "lat": row['Latitude'],
            "lon": row['Longitude'],
            "type": row["Type"]
        }
    
    # Store lines
    for _, row in df.iterrows():
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
    colors: Optional[List[str]] = None, 
    map: Optional[Map] = None
):
    """Create HTML map from JSON data files"""
    if not colors:
        colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred', 'lightred']
    
    all_data = []
    all_centers = []
    
    # Load all JSON files
    for i, json_path in enumerate(json_paths):
        with open(json_path, 'r') as f:
            data = json.load(f)
            data['color'] = colors[i % len(colors)]  # Assign different colors
            all_data.append(data)
            all_centers.append([data["center"]["Latitude"], data["center"]["Longitude"]])
    
    # Calculate overall center
    overall_center = [
        sum(center[0] for center in all_centers) / len(all_centers),
        sum(center[1] for center in all_centers) / len(all_centers)
    ]
    
    # Create or use existing map
    if map is None:
        map = Map(
            location=overall_center,
            zoom_start=15,
            control_scale=True
        )
        
        # Add satellite view Layer
        folium.TileLayer(
            'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
            attr='Google', 
            name='Google Satellite', 
            overlay=False
        ).add_to(map)
    
    # Add each map as a separate layer
    for map_data in all_data:
        feature_group = folium.FeatureGroup(name=map_data["name"])
        
        # Add lines for this map
        for line in map_data["lines"]:
            line_type = line["type"]
            # Use assigned color or fallback to STYLE_MAP if available
            try:
                color = STYLE_MAP.get(line_type)["color"] if len(all_data) == 1 else map_data['color']
            except (NameError, TypeError, KeyError):
                color = map_data['color']
            
            weight = 2 if line_type == "L_wall" else 1
            
            folium.PolyLine(
                locations=[[line["from"]["lat"], line["from"]["lon"]], 
                          [line["to"]["lat"], line["to"]["lon"]]], 
                color=color, 
                weight=weight,
                popup=f"{map_data['name']}: {line_type}"
            ).add_to(feature_group)
        
        feature_group.add_to(map)
    
    # Add layer control
    folium.LayerControl().add_to(map)
    map.save(output_path)
    
    return map