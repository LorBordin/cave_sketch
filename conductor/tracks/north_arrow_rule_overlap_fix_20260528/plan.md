# Implementation Plan: North Arrow and Rule Overlap Fix

## Phase 1: Logic Refinement [checkpoint: 44920a7]
- [x] Task: Update placement logic tests
    - [x] Task: Add failing tests for vertical stacking (Arrow on top of Rule).
    - [x] Task: Add failing tests for center alignment.
    - [x] Task: Add failing tests for 3% padding constraint.
- [x] Task: Update `cave_sketch/survey/graphics/placement.py`
    - [x] Task: Refactor `corner_anchor` to return coordinates for both elements or a structured layout object.
    - [x] Task: Implement 3% padding calculation in corner scoring.
    - [x] Task: Implement vertical center alignment logic.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Logic Refinement' (Protocol in workflow.md)

## Phase 2: Integration & Fallback
- [ ] Task: Update survey plot integration
    - [ ] Task: Modify `create_survey` in `cave_sketch/survey/graphics/survey_plot.py` to use the new dual-element coordinates.
    - [ ] Task: Update fallback logic to correctly expand axes based on the combined height of the arrow + rule + padding.
- [ ] Task: Verify PDF output
    - [ ] Task: Generate sample PDFs for various cave shapes (long, wide, dense) and verify no overlap.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Integration & Fallback' (Protocol in workflow.md)
