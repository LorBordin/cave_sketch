from dataclasses import dataclass


@dataclass
class SurveyConfig:
    """Configuration options for rendering a cave survey plot."""

    rule_length: float = 100.0
    rotation_deg: float = 0.0
    show_details: bool = True
    marker_zoom: float = 0.0
    text_zoom: float = 0.0
    line_width_zoom: float = 0.0
