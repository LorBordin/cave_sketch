# Implementation Plan: North Symbol Placement Fix

## Phase 1: Bounding Box and Corner Analysis
- [ ] Task: Add failing tests for corner analysis
    - [ ] Sub-task: Test identifying the corner with maximum free space given a set of cave geometries.
    - [ ] Sub-task: Test identifying when fallback (outside margins) is required.
- [ ] Task: Implement corner analysis logic
    - [ ] Sub-task: Add utility to calculate aggregated bounding box of cave elements.
    - [ ] Sub-task: Implement algorithm to evaluate free space in the four corners of the plot.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Bounding Box and Corner Analysis' (Protocol in workflow.md)

## Phase 2: North Symbol Integration
- [ ] Task: Add failing tests for North symbol placement
    - [ ] Sub-task: Test that `cave_sketch/survey/graphics/north.py` (or PDF renderer) utilizes the new corner analysis.
- [ ] Task: Integrate dynamic placement in PDF rendering
    - [ ] Sub-task: Update PDF generation routine (`cave_sketch/survey/pdf.py` or similar) to call the corner analysis.
    - [ ] Sub-task: Apply the calculated coordinates to the North symbol rendering function.
    - [ ] Sub-task: Ensure fallback logic correctly positions the symbol outside the main axes if needed.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: North Symbol Integration' (Protocol in workflow.md)