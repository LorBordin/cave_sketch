# Implementation Plan: Single Child Survey Merging for PDF Surveys

## Phase 1: Core Merging Logic [checkpoint: 1f6b497]
- [x] Task: Create a new `cave_sketch/survey/merger.py` module implementing the merging logic for a single parent + single child survey. `merge_surveys.py` (root-level utility) may serve as inspiration for the ID remapping approach but is not to be refactored — the new module must handle both map and section DataFrames simultaneously, accept a section protocol parameter, and be designed as a library (no CLI, no `sys.path` manipulation). (5a7fc60)
- [x] Task: Write failing unit tests for the new merger module — numeric ID offset remapping, Links column remapping, coordinate translation via station matching, and correct handling of non-numeric Node IDs (wall geometry: excluded from offset computation, but their Links references are still remapped). (7251785)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Core Merging Logic' (Protocol in workflow.md) (2e83140)

## Phase 2: UI Implementation in Survey Plot Page
- [~] Task: Update `1_survey_plot.py` to include a child survey upload section (child map DXF and child section DXF), mirroring the existing parent upload structure.
- [ ] Task: Add two plain-text numeric inputs for the matching station IDs (parent station, child station). Validate on submit: reject non-numeric input immediately; if the ID is numeric but not present in the parsed DXF, display `st.error` below the inputs and block PDF generation until resolved.
- [ ] Task: Add a Section View protocol selector (Simple, Mirror, Displacement) that appears only when a child section DXF is uploaded. Do NOT show a protocol selector for the map view.
- [ ] Task: Wire session state to store child CSV paths, station ID pair, and selected section protocol.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: UI Implementation in Survey Plot Page' (Protocol in workflow.md)

## Phase 3: Section View Merging Protocols & Pipeline Integration
- [ ] Task: Implement drawing logic for the "Simple Mirror" protocol: mirror the child DataFrame coordinates across the y-axis before applying the translation.
- [ ] Task: Implement drawing logic for the "Displacement" protocol: search rightward then downward from the parent matching station for the nearest non-overlapping placement (no intersection between child bounding box + padding and any parent line segment), then draw two thin connector lines between the matched stations.
- [ ] Task: Update the map view rendering path to always apply Simple Merging (translate + concatenate) when a child map DXF is present.
- [ ] Task: Update the main PDF rendering pipeline (`draw_survey` / `render_survey`) to: (1) accept the merged DataFrames and the selected section protocol, (2) apply all user settings (rotation, scale, line width, etc.) to the fully merged result — not per-survey — and (3) auto-rescale the sketch if the merged bounding box exceeds the PDF page dimensions.
- [ ] Task: Add tests confirming that the single-survey workflow (no child uploaded) produces correct output — verifying the new code path does not break the existing flow.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Section View Merging Protocols & Pipeline Integration' (Protocol in workflow.md)
