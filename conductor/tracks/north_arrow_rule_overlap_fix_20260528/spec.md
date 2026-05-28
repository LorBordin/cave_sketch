# Specification: North Arrow and Rule Overlap Fix

## Overview
This track fixes a layout bug where the North arrow and the scale rule can overlap with each other or with the cave sketch. It refines the placement logic to ensure a clear, professional survey plot.

## Functional Requirements
- **Vertical Stack & Center Alignment:** The scale rule must be placed below the North arrow. The North arrow must be horizontally centered relative to the width of the scale rule.
- **Mutual Exclusivity:** Ensure the bounding boxes of the North arrow and the scale rule do not overlap.
- **Sketch Avoidance:** Maintain a minimum padding of **3% of the total axes range** between the layout elements (arrow/rule) and any cave sketch data points.
- **Dynamic Placement:** Leverage the existing corner-scoring logic to find the best empty corner, but with the updated vertical stacking and alignment constraints.
- **Fallback Behavior:** If all corners are too crowded to honor the 3% padding, expand the axes limits on the bottom or side to create dedicated whitespace for the arrow and rule.

## Non-Functional Requirements
- Maintain rendering performance for large surveys.
- Consistent visual style across all PDF exports.

## Acceptance Criteria
- [x] North arrow and scale rule are vertically stacked (Arrow on top).
- [x] North arrow is horizontally centered relative to the scale rule.
- [x] No overlap between North arrow, scale rule, and cave sketch.
- [x] 3% padding is visible in the generated PDF.
- [x] Fallback axes expansion works when the sketch is large.

## Out of Scope
- Changing the graphical design of the North symbol or scale rule.
- Adding other annotations (text, legends) beyond these two.
