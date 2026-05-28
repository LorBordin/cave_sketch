# Specification: North Symbol Placement Fix

## Overview
This track addresses a bug in the PDF generation for the survey plot where the North symbol occasionally renders on top of the cave sketch. The fix will ensure the symbol is consistently placed in an empty area.

## Functional Requirements
- **Dynamic Placement:** The system must calculate the bounding box of the rendered cave elements using the (post-rotation) survey data coordinates available in `create_survey` (`df["X"]`, `df["Y"]` after any rotation is applied).
- **Corner Zone Definition:** Each corner zone is defined as a **20% × 20% region** of the total data bounding box, anchored at each of the four corners (top-left, top-right, bottom-left, bottom-right).
- **Empty Space Measurement:** A corner's "free space" score is defined as the fraction of that corner zone that contains **no survey data points**. Specifically, count the number of data points (stations and intermediate points) that fall inside the corner zone and normalize by the zone area; the corner with the lowest point density wins.
- **Corner Search:** The system must dynamically select the corner with the highest free space score. In case of a tie, prefer bottom-left, then bottom-right, then top-left, then top-right (to preserve visual convention).
- **Symbol Rendering:** The North symbol must be rendered in the identified empty corner to avoid overlapping with the cave sketch. The symbol's anchor coordinate is placed at 10% inset from the chosen corner (i.e., 2% of the bounding box width/height inward from the edge).
- **Scale Rule Co-location:** The scale rule (`_add_rule`) must be placed in the same corner as the North symbol. The two elements must be arranged side-by-side within the corner zone without overlapping each other.
- **Fallback Behavior:** If all four corner zones each contain more than **50%** of the maximum corner point density (i.e., no corner is clearly free), the North symbol and scale rule must be placed **outside the axes bounds** by extending the axes limits by `arrow_len` on the side with more empty space (prefer the bottom edge, then left edge). This avoids overlapping the cave drawing by expanding the view rather than using separate figure coordinates.

## Non-Functional Requirements
- The dynamic calculation of empty space should be reasonably fast to not significantly slow down PDF generation.
- The aesthetic quality of the PDF must be maintained.

## Out of Scope
- Changes to the appearance or style of the North symbol itself.
- Changes to the cave rendering logic, other than the placement of the North symbol.