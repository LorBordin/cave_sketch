from dataclasses import dataclass, field
from typing import List


@dataclass
class SurveyPoint:
    """Represents a single point in the cave survey, such as a station or a detail point."""

    id: str
    x: float
    y: float
    z: float = 0.0
    point_type: str = "station"
    links: List[str] = field(default_factory=list)


@dataclass
class SurveyLine:
    """Represents a connection between two survey points with a specific line style."""

    from_id: str
    to_id: str
    line_type: str = "L_wall"


@dataclass
class CaveSurvey:
    """Root container for a complete cave survey dataset."""

    name: str
    points: List[SurveyPoint] = field(default_factory=list)
    lines: List[SurveyLine] = field(default_factory=list)
