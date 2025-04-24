from typing import List, Dict, Tuple
import pandas as pd
import ezdxf

def parse_dxf(input_dxf_path: str, out_file_path: str | None = None):
    
    all_polylines = parse_polylines(
        input_dxf_path,
        filter_layers=['SCRAP_0']  # or None to grab everything
    )
    stations = get_stations(input_dxf_path)
    offset_x, offset_y = get_offset(input_dxf_path, offset_idx=0)
    df = resample_and_index(
        stations=stations,
        polylines=all_polylines,
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


def parse_polylines(
    input_dxf_file: str,
    filter_layers: List[str] = None
) -> List[Dict[str, object]]:
    """
    Read all POLYLINE entities in the DXF (optionally limited to certain layers)
    and return their vertex coordinates *plus* their DXF styling attributes.
    
    Returns
    -------
    polylines : list of dicts
        Each dict has:
          - 'points': List[Tuple[float, float]]     # the polyline vertices
          - 'color': int                            # DXF color index (0 = BYLAYER)
          - 'linetype': str                         # e.g. 'CONTINUOUS', 'DASHED'
          - 'lineweight': int                       # in 1/100 mm (0 = BYLAYER)
          - 'layer': str                            # layer name
    """
    doc = ezdxf.readfile(input_dxf_file)
    msp = doc.modelspace()
    result = []

    for entity in msp.query('POLYLINE'):
        layer = entity.dxf.layer
        if filter_layers and layer not in filter_layers:
            continue

        # extract raw points
        pts = [(pt[0], pt[1]) for pt in entity.points()]

        # extract style attributes
        color      = entity.dxf.color        # integer index, 0=BYLAYER
        linetype   = entity.dxf.linetype     # e.g. 'CONTINUOUS', 'HIDDEN'
        lineweight = entity.dxf.lineweight    # 0 = BYLAYER, else in 1/100 mm

        result.append({
            'points': pts,
            'color': color,
            'linetype': linetype,
            'lineweight': lineweight,
            'layer': layer,
        })

    return result



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
        p_type = "station"
        data.append([idx, links, x - x_off, y - y_off, p_type])
    
    for i, polyline in enumerate(polylines):
        
        p_type = polyline['linetype']

        if resample_step:
            points = polyline['points'][::resample_step]
        else:
            points = polyline['points']
        
        for j, (x, y) in enumerate(points):
            node_id = f"{i}P{j}"
            links = []
            if j > 0:
                links.append(f"{i}P{j-1}")
            if j < len(polyline) - 1:
                links.append(f"{i}P{j+1}")
            link_str = "-".join(links)
            data.append([node_id, link_str, x - x_off, y - y_off, p_type])

    df = pd.DataFrame(data, columns=["Node_Id", "Links", "X", "Y", "Type"])
    df["Links"] = df["Links"].fillna("-")
    return df