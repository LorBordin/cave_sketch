# Spec: B_snow icon (bug)

## Overview
`B_snow` point blocks are rendered in the KML but omitted from the KMZ (`google_earth.py` suppresses `B_snow`/`B_ice`/`B_blocks` point placemarks; only icon-type features are drawn as LineStrings). Add a `snow` icon — a white "*" like TopoDroid's — so snow appears in the KMZ.

## Functional Requirements
1. Define a `snow` icon geometry (6-armed asterisk, stroked line segments) alongside existing icons (blocks, entrance, ...).
2. Change `B_snow` in `style.py` to `type: "icon"`, `icon: "snow"`, `color: "white"`, `size_m: 1.5` in all backends (matplotlib, folium, KMZ).
3. KMZ emits a `#icon_B_snow` style and a LineString placemark per B_snow point.
4. `B_ice` remains unchanged (still suppressed in KMZ).

## Acceptance Criteria
- KMZ from a DXF containing B_snow includes B_snow icon LineStrings.
- Existing KMZ test asserting B_snow suppression is updated to assert presence.
- `ruff`, `mypy`, `pytest` pass.

## Out of Scope
B_ice icon; changes to other icons.

## Open note
White on a white PDF background is invisible; verify PDF/folium legibility (e.g. thin outline or light-grey fallback) during implementation.
