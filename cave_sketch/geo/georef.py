from typing import List

import numpy as np

from cave_sketch.dxf.models import CaveSurvey
from cave_sketch.geo.models import GeoPoint, GpsRef

# WGS84 constants
_A = 6378137.0
_F = 1.0 / 298.257223563
_E2 = _F * (2 - _F)
_DEG2RAD = np.pi / 180.0


def _meters_per_degree_wgs84(lat_deg: float):
    """
    Return (meters_per_degree_latitude, meters_per_degree_longitude)
    at given latitude in degrees using WGS84 ellipsoid.
    """
    lat_rad = np.asarray(lat_deg) * _DEG2RAD
    sinlat = np.sin(lat_rad)
    one_minus_e2_sin2 = 1.0 - _E2 * sinlat**2

    # meridional radius of curvature
    M = _A * (1 - _E2) / (one_minus_e2_sin2**1.5)
    # prime vertical radius of curvature
    N = _A / np.sqrt(one_minus_e2_sin2)

    m_per_deg_lat = M * _DEG2RAD
    m_per_deg_lon = N * np.cos(lat_rad) * _DEG2RAD

    return float(m_per_deg_lat), float(m_per_deg_lon)


def georeference(survey: CaveSurvey, gps_refs: List[GpsRef]) -> List[GeoPoint]:
    """
    Georeference a CaveSurvey using one or more GPS reference points.

    If multiple references are provided, the resulting coordinates are averaged.

    Args:
        survey: The CaveSurvey object to georeference.
        gps_refs: A list of GpsRef objects.

    Returns:
        A list of GeoPoint objects.

    Raises:
        ValueError: If fewer than 2 reference points are provided (as per spec,
                   though the logic could work with 1).
    """
    if len(gps_refs) < 2:
        raise ValueError("At least 2 reference points are required for georeferencing.")

    geo_points: List[GeoPoint] = []

    # Pre-calculate transforms for each reference point
    transforms = []
    for ref in gps_refs:
        # Find the station in the survey
        anchor = next((p for p in survey.points if p.id == ref.station_id), None)
        if anchor is None:
            continue

        m_per_deg_lat, m_per_deg_lon = _meters_per_degree_wgs84(ref.lat)
        transforms.append(
            {
                "ref": ref,
                "anchor_x": anchor.x,
                "anchor_y": anchor.y,
                "m_per_deg_lat": m_per_deg_lat,
                "m_per_deg_lon": m_per_deg_lon,
            }
        )

    if not transforms:
        return []

    # Apply averaged transforms to all survey points
    for p in survey.points:
        lats = []
        lons = []
        for t in transforms:
            dy = p.y - t["anchor_y"]
            dx = p.x - t["anchor_x"]

            lats.append(t["ref"].lat + (dy / t["m_per_deg_lat"]))
            lons.append(t["ref"].lon + (dx / t["m_per_deg_lon"]))

        geo_points.append(
            GeoPoint(
                station_id=p.id, lat=float(np.mean(lats)), lon=float(np.mean(lons)), x=p.x, y=p.y
            )
        )

    return geo_points
