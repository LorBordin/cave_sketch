from pathlib import Path
from typing import Dict, List, Optional, Tuple

import ezdxf
import pandas as pd

from cave_sketch.dxf.models import CaveSurvey, SurveyLine, SurveyPoint


def parse_dxf(input_path: Path, output_path: Optional[Path] = None) -> CaveSurvey:
    """
    Parse a TopoDroid DXF file into a CaveSurvey dataclass.
    
    Args:
        input_path: Path to the .dxf file.
        output_path: Optional path to save a CSV representation of the parsed data.
        
    Returns:
        A CaveSurvey object containing points and lines.
    """
    input_str = str(input_path)
    
    stations = _get_stations(input_str)
    all_polylines = _parse_polylines(input_str, filter_layers=['SCRAP_0'])
    offset_x, offset_y = _get_offset(input_str, offset_idx=0)
    blocks = _get_features(input_str)

    survey = CaveSurvey(name=input_path.stem)
    
    # Process stations
    for idx, item in stations.items():
        links_str = item.get('links', '')
        links = [
            link.strip() for link in links_str.split('-') if link.strip()
        ] if links_str else []
        x, y = item['point']
        survey.points.append(SurveyPoint(
            id=str(idx),
            x=x - offset_x,
            y=y - offset_y,
            point_type="station",
            links=links
        ))
        
        # Create lines from station links
        # To avoid double-counting lines (A-B and B-A), we could sort the IDs,
        # but let's stick to the behavior of the original code which just listed them in 'Links'
        for link in links:
            survey.lines.append(SurveyLine(from_id=str(idx), to_id=link, line_type="station_leg"))

    # Process polylines
    for i, polyline in enumerate(all_polylines):
        p_type = polyline['linetype']
        pts = polyline['points']
        
        poly_points = []
        for j, (x, y) in enumerate(pts):
            node_id = f"{i}P{j}"
            links = []
            if j > 0:
                links.append(f"{i}P{j-1}")
            if j < len(pts) - 1:
                links.append(f"{i}P{j+1}")
            
            p = SurveyPoint(
                id=node_id,
                x=x - offset_x,
                y=y - offset_y,
                point_type=p_type,
                links=links
            )
            survey.points.append(p)
            poly_points.append(p)
            
            if j > 0:
                line = SurveyLine(from_id=f"{i}P{j-1}", to_id=node_id, line_type=p_type)
                survey.lines.append(line)

    # Process blocks
    for i, block in enumerate(blocks):
        survey.points.append(SurveyPoint(
            id=block["Node_Id"],
            x=block["X"] - offset_x,
            y=block["Y"] - offset_y,
            point_type=block["Type"],
            links=[]
        ))

    if output_path:
        _export_to_csv(survey, output_path)
        
    return survey

def _get_stations(input_dxf_file: str) -> Dict:
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
            if entity.dxftype() == "LINE":
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

def _parse_polylines(input_dxf_file: str, filter_layers: List[str] = None) -> List[Dict]:
    doc = ezdxf.readfile(input_dxf_file)
    msp = doc.modelspace()
    result = []
    for entity in msp.query('POLYLINE'):
        layer = entity.dxf.layer
        if filter_layers and layer not in filter_layers:
            continue
        pts = [(pt[0], pt[1]) for pt in entity.points()]
        result.append({
            'points': pts,
            'color': entity.dxf.color,
            'linetype': entity.dxf.linetype,
            'lineweight': entity.dxf.lineweight,
            'layer': layer,
        })
    return result

def _get_offset(input_dxf_file: str, offset_idx: int) -> Tuple[float, float]:
    doc = ezdxf.readfile(input_dxf_file)
    msp = doc.modelspace()
    offset_flag = False
    for entity in msp:
        if entity.dxf.layer == "STATION":
            if entity.dxftype() == "TEXT" and entity.dxf.text == str(offset_idx):
                offset_flag = True
            elif entity.dxftype() == "LINE" and offset_flag:
                return entity.dxf.start.x, entity.dxf.start.y
    return 0.0, 0.0

def _get_features(input_dxf_file: str) -> List[Dict]:
    doc = ezdxf.readfile(input_dxf_file)
    msp = doc.modelspace()
    valid_block_names = {"B_ice", "BLOCK", 'B_snow'}
    blocks = []
    for entity in msp.query('INSERT'):
        if entity.dxf.name in valid_block_names:
            blocks.append({
                "Node_Id": f"{entity.dxf.name}_{len(blocks)}",
                "Links": "-",
                "X": entity.dxf.insert.x,
                "Y": entity.dxf.insert.y,
                "Type": entity.dxf.name,
            })
    return blocks

def _export_to_csv(survey: CaveSurvey, output_path: Path):
    data = []
    for p in survey.points:
        links_str = "-".join(p.links) if p.links else "-"
        data.append([p.id, links_str, p.x, p.y, p.point_type])
    df = pd.DataFrame(data, columns=["Node_Id", "Links", "X", "Y", "Type"])
    df.to_csv(output_path, index=False)
