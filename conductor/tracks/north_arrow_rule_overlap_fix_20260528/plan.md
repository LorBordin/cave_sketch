# Implementation Plan: North Arrow and Rule Overlap Fix

## Phase 1: Logic Refinement
- [ ] Task: Update placement logic tests
    - [ ] Task: Add failing tests for vertical stacking (Arrow on top of Rule).
    - [ ] Task: Add failing tests for center alignment.
    - [ ] Task: Add failing tests for 3% padding constraint.
- [ ] Task: Update `cave_sketch/survey/graphics/placement.py`
    - [ ] Task: Refactor `corner_anchor` to return coordinates for both elements or a structured layout object.
    - [ ] Task: Implement 3% padding calculation in corner scoring.
    - [ ] Task: Implement vertical center alignment logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Logic Refinement' (Protocol in workflow.md)

## Phase 2: Integration & Fallback
- [ ] Task: Update survey plot integration
    - [ ] Task: Modify `create_survey` in `cave_sketch/survey/graphics/survey_plot.py` to use the new dual-element coordinates.
    - [ ] Task: Update fallback logic to correctly expand axes based on the combined height of the arrow + rule + padding.
- [ ] Task: Verify PDF output
    - [ ] Task: Generate sample PDFs for various cave shapes (long, wide, dense) and verify no overlap.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Integration & Fallback' (Protocol in workflow.md)
