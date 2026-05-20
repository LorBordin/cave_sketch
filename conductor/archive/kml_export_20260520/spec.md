# Specification: KML Export for Google Earth

## Overview
Implement the capability to export georeferenced cave data into KML format for visualization in Google Earth. This feature will bridge the gap between 2D satellite maps and 3D geospatial exploration.

## Functional Requirements
- **KML Generation**: Create a valid KML file containing the cave's centerline and/or walls.
- **Georeferencing**: Use the existing georeferencing logic to translate survey coordinates into WGS84 (Latitude/Longitude/Altitude).
- **Styling**: Apply basic KML styling for line colors and widths to match the app's aesthetic.
- **UI Integration**: Add a "Download KML" button to the relevant Streamlit pages (Satellite Map or a new export component).

## Technical Constraints
- **Library**: Use a lightweight KML library or manual XML generation (given the simple structure).
- **Architecture**: Logic must reside in `cave_sketch/geo/` to maintain the Streamlit-free core.
- **Altitude**: Handle altitude data if available in the DXF/georef, otherwise default to a ground-relative offset.

## Success Criteria
- Valid KML file generated from a sample DXF with georeferencing.
- KML file opens correctly in Google Earth with the cave correctly positioned.
- No regressions in PDF or HTML map generation.
