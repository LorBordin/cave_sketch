"""Vector shapes for DXF point symbols, drawn as plain line strokes.

Every shape lives in a unit box: centered on (0, 0), largest side 1.0, and
the icon's "up" pointing to +Y. Rotation 0 therefore means "up = north",
the same convention as the TopoDroid DXF block definitions, whose INSERT
rotation (degrees, counter-clockwise) can be applied directly.
"""

import math
from typing import Dict, List, Tuple

Point = Tuple[float, float]
Stroke = List[Point]

ICON_SHAPES: Dict[str, List[Stroke]] = {
    # Rock block: outline plus two inner fracture lines (TopoDroid B_blocks).
    "blocks": [
        [(-0.5, -0.267), (0.367, -0.4), (0.5, -0.333), (0.433, 0.333), (-0.367, 0.4),
         (-0.5, 0.267), (-0.5, -0.267), (0.1, 0.067), (0.5, -0.333)],
        [(-0.5, 0.267), (0.1, 0.067), (0.433, 0.333)],
    ],
    # Entrance: closed triangle pointing up (TopoDroid B_entrance).
    "entrance": [
        [(0.0, 0.5), (-0.333, -0.5), (0.333, -0.5), (0.0, 0.5)],
    ],
    # Continuation: a question mark "?" -- hook + stem, then the dot (TopoDroid B_continuation).
    "continuation": [
        [(0.031, -0.192), (0.031, 0.038), (0.031, 0.069), (0.046, 0.1), (0.062, 0.131),
         (0.077, 0.162), (0.108, 0.177), (0.123, 0.208), (0.154, 0.238), (0.185, 0.269),
         (0.2, 0.3), (0.2, 0.331), (0.185, 0.377), (0.169, 0.408), (0.138, 0.454),
         (0.092, 0.469), (0.062, 0.5), (0.031, 0.5), (0.0, 0.485), (-0.031, 0.469),
         (-0.077, 0.438), (-0.108, 0.392), (-0.154, 0.362), (-0.169, 0.331), (-0.2, 0.331),
         (-0.2, 0.346)],
        [(0.031, -0.5), (0.031, -0.346)],
    ],
    # Water flow: S-shaped wiggle with an arrowhead on top; the arrow points
    # downstream (+Y at rotation 0).
    "water_flow": [
        [(0.0, -0.5), (-0.1, -0.438), (-0.173, -0.375), (-0.2, -0.312), (-0.173, -0.25),
         (-0.1, -0.188), (0.0, -0.125), (0.1, -0.062), (0.173, 0.0), (0.2, 0.062),
         (0.173, 0.125), (0.1, 0.188), (0.0, 0.25), (0.0, 0.5)],
        [(-0.2, 0.28), (0.0, 0.5), (0.2, 0.28)],
    ],
    # Chevron placed on each L_water-flow segment, apex pointing downstream.
    "water_flow_chevron": [
        [(-0.5, -0.25), (0.0, 0.25), (0.5, -0.25)],
    ],
}


def icon_strokes(
    name: str, x: float, y: float, size_m: float, rotation_deg: float = 0.0
) -> List[Stroke]:
    """Place icon ``name`` in local metric coordinates (X east, Y north).

    The unit shape is scaled so its largest side is ``size_m`` meters,
    rotated ``rotation_deg`` degrees counter-clockwise, and centered on
    ``(x, y)``. Returns one open polyline per stroke. Raises ``KeyError``
    for an unknown icon name.
    """
    theta = math.radians(rotation_deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    return [
        [
            (x + size_m * (u * cos_t - v * sin_t), y + size_m * (u * sin_t + v * cos_t))
            for u, v in stroke
        ]
        for stroke in ICON_SHAPES[name]
    ]
