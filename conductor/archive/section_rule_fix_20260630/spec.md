# Specification: Prevent Scale Bar (Rule) Intersection in Section Plot

## Overview
There is a bug where the scale bar (rule) drawn on the section plot sometimes overlaps with the main survey drawing (the cave draw itself). This track implements a fix to ensure the scale bar is positioned such that it never overlaps with the main survey elements, utilizing an approach similar to what was previously implemented for the map scale.

## Functional Requirements
- Detect potential intersections or overlaps between the scale bar geometry/bounding box and the section drawing.
- Automatically reposition or adjust the placement of the scale bar in the section plot to avoid the drawing.
- Reuse or adapt the existing intersection-prevention/padding algorithm that was previously developed for the map.

## Non-Functional Requirements
- The change must be covered by a unit test using the specific problematic DXF and settings provided by the user.
- The rendering should not have significant latency increases.

## Acceptance Criteria
- Unit tests verify that the scale bar does not intersect with the main draw in the section plot, using the provided sample survey.
- Manual verification confirms visually that the PDF generated from the sample DXF is correct and the scale bar is clear of the drawing.

## Out of Scope
- Modifying the visual style of the scale bar.
- Refactoring the entire PDF rendering pipeline.
