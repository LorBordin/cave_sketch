from dataclasses import dataclass
from typing import Optional


@dataclass
class SurveyConfig:
    """Configuration options for rendering a cave survey plot."""

    rule_length: float = 100.0
    rotation_deg: float = 0.0
    show_details: bool = True
    marker_zoom: float = 0.0
    text_zoom: float = 0.0
    line_width_zoom: float = 0.0
    show_north: bool = True
    show_grid: bool = True
    surveyor_name: str = ""
    show_centerline: bool = True


@dataclass
class TitleBlockInfo:
    """Optional survey metadata printed in the PDF title block (cartiglio).

    This is the validation boundary for both the webapp and the Android bridge.
    """

    surveyor_name: str = ""
    drawer_name: str = ""
    municipality: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None

    def __post_init__(self) -> None:
        self.surveyor_name = self.surveyor_name.strip()
        self.drawer_name = self.drawer_name.strip()
        self.municipality = self.municipality.strip()
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be entered together.")
        # `not a <= x <= b` is also True for NaN, so NaN is rejected too.
        if self.latitude is not None and not -90.0 <= self.latitude <= 90.0:
            raise ValueError("Latitude must be between -90 and 90.")
        if self.longitude is not None and not -180.0 <= self.longitude <= 180.0:
            raise ValueError("Longitude must be between -180 and 180.")

