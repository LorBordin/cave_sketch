"""Mobile bridge for the Satellite Map screen. Mirrors app/pages/2_satellite_map.py:
validate GPS points, run draw_map, return output paths. Lives under android/, never
imported by cave_sketch. Single entrypoint: generate_satellite_map(inputs_json, work_dir)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cave_sketch.geo.coordinates import parse_coordinate
from cave_sketch.satellite_view import draw_map


def _validate_points(gps_points) -> str | None:
    """Validate and normalise GPS points in place (lat/lon strings -> floats).
    Mirror app/components/gps_points.py:validate_known_points. Return an error
    message, or None when all points are valid."""
    if not gps_points:
        return "Add at least one GPS point."
    for pt in gps_points:
        if not str(pt.get("station", "")).strip():
            return "Every GPS point needs a station ID."
        lat = parse_coordinate(str(pt.get("lat", "")))
        lon = parse_coordinate(str(pt.get("lon", "")))
        if lat is None or lon is None:
            return "Every GPS point needs a valid latitude and longitude."
        pt["lat"], pt["lon"] = lat, lon
    return None


def generate_satellite_map(inputs_json: str, work_dir: str) -> str:
    """Entrypoint mirroring app/pages/2_satellite_map.py. Returns JSON
    {"html_path","json_path","kmz_path"} or {"error","detail"}."""
    try:
        data = json.loads(inputs_json)

        map_path = data.get("map_path")
        if not map_path:
            return json.dumps({"error": "no_map",
                               "detail": "Generate a survey plot first."})

        gps_points = data.get("gps_points") or []
        err = _validate_points(gps_points)
        if err:
            return json.dumps({"error": "invalid_points", "detail": err})

        # Guard: at least one anchor station must exist in the map CSV, else
        # draw_map yields all-NaN coordinates (a broken map).
        node_ids = set(pd.read_csv(map_path)["Node_Id"].astype(str))
        if not any(str(p["station"]) in node_ids for p in gps_points):
            return json.dumps({"error": "no_anchor_match",
                               "detail": "None of the GPS stations match a station "
                                         "in the survey."})

        html_path = str(Path(work_dir) / "survey.html")
        _, json_path, kmz_path = draw_map(
            map_path=map_path,
            gps_points=gps_points,
            output_path=html_path,
            map_name=data.get("survey_name") or "Cave",
            additional_json_maps=data.get("additional_json_maps") or [],
            rotation_angle=float(data.get("rotation_angle", 0) or 0),
        )
        return json.dumps({"html_path": html_path,
                           "json_path": json_path, "kmz_path": kmz_path})
    except Exception as e:  # noqa: BLE001 — the bridge converts all failures to structured errors
        return json.dumps({"error": "render_failed", "detail": str(e)})
