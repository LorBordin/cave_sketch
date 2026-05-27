# Specification: North Symbol Placement Fix

## Overview
This track addresses a bug in the PDF generation for the survey plot where the North symbol occasionally renders on top of the cave sketch. The fix will ensure the symbol is consistently placed in an empty area.

## Functional Requirements
- **Dynamic Placement:** The system must calculate the bounding box of the rendered cave elements.
- **Corner Search:** The system must dynamically identify the corner (e.g., top-left, top-right, bottom-left, bottom-right) within the plot area that contains the most empty space.
- **Symbol Rendering:** The North symbol must be rendered in the identified empty corner to avoid overlapping with the cave sketch.
- **Fallback Behavior:** In cases where the cave sketch occupies the entire plot area leaving no sufficient empty corner, the North symbol must be drawn outside the defined page margins rather than overlapping the cave drawing.

## Non-Functional Requirements
- The dynamic calculation of empty space should be reasonably fast to not significantly slow down PDF generation.
- The aesthetic quality of the PDF must be maintained.

## Out of Scope
- Changes to the appearance or style of the North symbol itself.
- Changes to the cave rendering logic, other than the placement of the North symbol.