# Plan: DXF Version Compatibility (R9, R12, R14/R2000)

## Phase 1: Test Infrastructure & LWPOLYLINE Support

- [ ] Task: Write failing tests for DXF v14 parsing parity
    - [ ] Add test `test_parse_v14_produces_same_survey_as_v9` that loads both `sample_v9.dxf` and `sample_v14.dxf`, parses them, and asserts the resulting `CaveSurvey` objects have identical point counts, line counts, and line-type distributions.
    - [ ] Add test `test_parse_v14_polyline_linetypes` that verifies all expected line types (`L_wall`, `L_wall-presumed`, `L_pit`, `A_water`) are present in the v14 parse result.
    - [ ] Add test `test_parse_v9_backward_compat` that ensures parsing `sample_v9.dxf` produces the same result as the existing `sample.dxf` baseline (if they represent the same survey) or at minimum has stations and polylines.
    - [ ] Run tests and confirm they fail (Red phase).

- [ ] Task: Implement LWPOLYLINE support in `_parse_polylines()`
    - [ ] Modify `_parse_polylines()` in `cave_sketch/dxf/parser.py` to query both `POLYLINE` and `LWPOLYLINE` entity types.
    - [ ] Normalize `LWPOLYLINE` vertex access (uses `.get_points(format='xy')` or similar) to the same `(x, y)` tuple format as `POLYLINE`.
    - [ ] Ensure linetype, color, lineweight, and layer attributes are read correctly from `LWPOLYLINE` entities.
    - [ ] Run tests and confirm all pass (Green phase).

- [ ] Task: Investigate HATCH entities for area parity
    - [ ] Write a small investigation to compare `A_water` area data parsed from v9 polylines vs. v14 (which has both LWPOLYLINE with `A_water` linetype AND `HATCH` entities).
    - [ ] If the `A_water` LWPOLYLINE data already produces equivalent area polygons, document that HATCH entities are redundant and can be ignored.
    - [ ] If HATCH entities are needed, add parsing support. Otherwise, add a code comment explaining the decision.

- [ ] Task: Verify backward compatibility with existing `sample.dxf`
    - [ ] Run the existing `test_parse_valid_dxf` test to confirm no regression.
    - [ ] Confirm the parse output (stations, polylines, blocks) matches the pre-change baseline.

- [ ] Task: Conductor - User Manual Verification 'Phase 1: Test Infrastructure & LWPOLYLINE Support' (Protocol in workflow.md)
