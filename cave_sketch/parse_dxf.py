from typing import Dict, List, Tuple
import pandas as pd
import ezdxf

def parse_dxf(input_dxf_path: str, out_file_path: str | None = None):
    
    all_points = get_polylines(input_dxf_path)
    stations = get_stations(input_dxf_path)
    offset_x, offset_y = get_offset(input_dxf_path, offset_idx=0)
    df = resample_and_index(
        stations=stations,
        polylines=all_points,
        x_off=offset_x,
        y_off=offset_y
    )

    if out_file_path:
        df.to_csv(out_file_path)
    
    return df


def get_stations(input_dxf_file: str) -> Dict:
    """
    Read the .dxf file and return all stations (caposaldi) as a dict object.
    
    Schema
    ------
    station_id: str[int]: {
        point: Tuple[float, float]  -> coordinates of the station
        links: str                  -> linked stations (separated by '-')
    }
    """
    doc = ezdxf.readfile(input_dxf_file)
    msp = doc.modelspace()
    idxs, coords, legs = [], [], []
    for entity in msp:
        if entity.dxf.layer == "STATION":
            if entity.dxftype() == "TEXT":
                station_idx = entity.dxf.text 
                idxs.append(station_idx)
            elif entity.dxftype() == "LINE":
                start = entity.dxf.start
                coords.append((start.x, start.y))
        elif entity.dxf.layer == "LEG":
            assert entity.dxftype() == "LINE", "Invalid type."
            start = entity.dxf.start
            end = entity.dxf.end
            legs.append({'start': (start.x, start.y), 'end': (end.x, end.y)})
    
    stations = {idx: {'point': coord} for idx, coord in zip(idxs, coords)}

    for leg in legs:
        station_1, station_2 = None, None
        for station, item in stations.items():
            coord = item['point']
            if leg['start'] == coord:
                station_1 = station
            elif leg['end'] == coord:
                station_2 = station
        if station_1 and station_2:
            if stations[station_1].get('links', False):
                stations[station_1]['links'] += f'-{station_2}'
            else:
                stations[station_1]['links'] = station_2
            if stations[station_2].get('links', False):
                stations[station_2]['links'] += f'-{station_1}'
            else:
                stations[station_2]['links'] = station_1
        
    return stations


def get_polylines(
        input_dxf_file: str, 
        target_layer: str = 'SCRAP_0'
    ) -> List[List[Tuple]]:
    """
    Load all the polygonals lines drawn by the user. 

    Returns
    -------
    all_points: list
        The point coordinates of all the lines.
    """
    # Load the DXF file
    doc = ezdxf.readfile(input_dxf_file)
    msp = doc.modelspace()
    all_points = []

    # Iterate through the entities in the DXF file and filter by layer
    for entity in msp:
        if entity.dxf.layer == target_layer:
            if entity.dxftype() == 'POLYLINE':
                points = [(point[0], point[1]) for point in entity.points()]
                all_points.append(points)

    return all_points


def get_offset(input_dxf_file: str, offset_idx: int) -> Tuple[int, int]:
    """Offset the survey placing the station 'offset_idx' at the origin."""
    doc = ezdxf.readfile(input_dxf_file)
    msp = doc.modelspace()

    offset_flag = False
    for entity in msp:
        if entity.dxf.layer == "STATION":
            if entity.dxftype() == "TEXT":
                text = entity.dxf.text 
                if text == str(offset_idx):
                    offset_flag = True
            elif entity.dxftype() == "LINE" and offset_flag:
                start = entity.dxf.start
                return start.x, start.y


def resample_and_index(
        stations, 
        polylines, 
        x_off=0, 
        y_off=0, 
        resample_step: int | None = None
    ) -> pd.DataFrame:
    """
    Merge together stations and drawn lines (polylines), saves all points in a 
    csv file.
    
    Schema
    ------
    Node_id: str
        Id of the current node. Conventions:
        - integer for stations
        - alphanumeric for polylines: [line_id]P[point_id]
    Links: str
        Node Ids connected to the current node (separated by '-')
    X: float
        X coordinate
    y: float
        Y coordinate
    """
    data = []
    
    for idx, item in stations.items():
        links = item['links']
        x, y = item['point']
        data.append([idx, links, x - x_off, y - y_off])
    
    for i, polyline in enumerate(polylines):
        
        if resample_step:
            polyline = polyline[::resample_step]
        
        for j, (x, y) in enumerate(polyline):
            node_id = f"{i}P{j}"
            links = []
            if j > 0:
                links.append(f"{i}P{j-1}")
            if j < len(polyline) - 1:
                links.append(f"{i}P{j+1}")
            link_str = "-".join(links)
            data.append([node_id, link_str, x - x_off, y - y_off])

    df = pd.DataFrame(data, columns=["Node_Id", "Links", "X", "Y"])
    df["Links"] = df["Links"].fillna("-")
    return df