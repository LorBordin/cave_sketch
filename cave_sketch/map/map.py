from typing import Dict, List, Optional
from folium import Map
import pandas as pd
import numpy as np
import folium

from cave_sketch.style import STYLE_MAP

def draw_map(map_path: str, gps_points: List[Dict], output_path: str):
    map_df = pd.read_csv(map_path)
    map_df = cartesian_to_latlon(map_df, gps_points)
    html_map = create_html_map(map_df, output_path)

    return html_map


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

def create_html_map(df: pd.DataFrame, output_path: str, map: Optional[Map] = None):
    df["Links"].fillna(" ", inplace=True)
    if map is None:
        map = Map(
            location=df[["Latitude", "Longitude"]].mean().values,
            zoom_start=15,
            control_scale=True
        )

        # Add satelite view Layer
        folium.TileLayer(
            'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
                attr='Google', 
                name='Google Satellite', 
                overlay=False
        ).add_to(map)
    
    node_dict = {
            row['Node_Id']: (row['Latitude'], row['Longitude'])  
                for _, row in df.iterrows()
            }
    for _, row in df.iterrows():
        lat, lon = row['Latitude'], row['Longitude']
        for link in row['Links'].split('-'):
            if link:  
                lat_link, lon_link = node_dict.get(link, (False, False))
                if not lat_link:
                    continue
                
                line_type = row["Type"]
                color = STYLE_MAP[line_type]["color"]
                weight = 1 if line_type == "L_wall" else .5
                folium.PolyLine(
                    locations=[[lat_link, lon_link],[lat, lon]], 
                    color=color, 
                    weight=weight
                ).add_to(map)
    
    folium.LayerControl().add_to(map)
    map.save(output_path)
    
    return map