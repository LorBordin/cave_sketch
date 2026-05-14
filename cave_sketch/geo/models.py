from dataclasses import dataclass


@dataclass
class GpsRef:
    """A known reference point linking a survey station ID to GPS coordinates."""

    station_id: str
    lat: float
    lon: float


@dataclass
class GeoPoint:
    """A survey point that has been georeferenced to GPS coordinates."""

    station_id: str
    lat: float
    lon: float
    x: float
    y: float
