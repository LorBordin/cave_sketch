# Specification: Implement single child survey merging for PDF surveys

## Overview
This feature enables the CaveSketch application to merge two cave surveys (a parent and one child, each uploaded as DXF files) and generate a single, unified PDF survey plot.

## Functional Requirements

### Data Input & UI
- On the existing Survey Plot page (`1_survey_plot.py`), add a new UI section below the two main upload buttons.
- This new section allows uploading one additional (`child`) survey: a map `.dxf` and/or a section `.dxf`, mirroring the existing parent upload structure.
- After at least one child DXF is uploaded, UI controls must appear for the user to specify:
  - The matching station ID in the `parent` survey (plain text, numeric only — e.g. `30`).
  - The matching station ID in the `child` survey (plain text, numeric only — e.g. `47`).
  - The desired merging protocol for the Section View (see Section View Specifics below).
- **Station ID constraint:** Only purely numeric station IDs are valid matching inputs. IDs containing letters (e.g. `12P4`) identify wall/line geometry, not survey stations, and must not be used for merging. The UI should reject non-numeric input with a clear error message.
- **Shared station pair:** A single parent/child station ID pair applies to both the map DXF and the section DXF. This is valid because the map and section DXF files originate from the same TopoDroid project and share the same station numbering.
- **One child survey per session:** Only one child survey can be merged at a time. To merge additional surveys, the user can download the merged result and upload it as a new parent in a subsequent session.

### Alignment
The merging process aligns the child survey to the parent using **station matching**: the child's coordinate system is translated so that the child's matching station coincides with the parent's matching station.

### Data Structure Merging
- Create a single merged Pandas DataFrame for the map view and, independently, a single merged DataFrame for the section view.
- Remap all numeric Node IDs in the child DataFrame by applying an integer offset equal to `max(parent_ids) + 1 - min(child_ids)`, ensuring no ID collision.
- Remap all ID references in the child's `Links` column using the same offset.
- Translate the child's `X` and `Y` coordinates so the child's matching station aligns with the parent's matching station.

### Views Supported
- Map (Plan) View
- Section View

### Map View Merging
Map view always uses **Simple Merging**: once matching stations are provided, the child drawing is translated so its matching station coincides with the parent's matching station, and the DataFrames are concatenated. No protocol selection is exposed in the UI for the map view.

### Section View Merging Protocols
The user selects one of three protocols via a radio button or select box:

1. **Simple Merging:** The child's matching station is translated onto the parent's matching station and everything is drawn in the same coordinate space.
2. **Simple Mirror:** Same as Simple Merging, but the child sketch is mirrored across the vertical axis (y-axis) before being placed.
3. **Displacement:** The child sketch is drawn in a separate area where it does not visually overlap any lines from the parent sketch. Placement algorithm:
   - Starting from the parent's matching station, search for the nearest position where the child's bounding box (with a small padding) does not intersect any line segment of the parent sketch.
   - Search direction preference: **right first, then below** (i.e., scan rightward from the parent station along the x-axis; if no non-overlapping position is found within a reasonable range, scan downward along the y-axis).
   - Once placed, draw two thin connector lines from the parent's matching station to the child's matching station to indicate their topological connection.

### Settings & Rendering Workflow
All existing per-survey settings (rotation, scale, line width, text size, etc.) apply to the **whole merged result**, not per-survey. The rendering pipeline follows this order:
1. Parse and load the parent DXF(s).
2. If a child survey is present: parse the child DXF(s) and merge into the parent DataFrames.
3. Apply user settings (rotation, scale, etc.) to the merged DataFrames and render the final sketch.

### Error Handling
- **Invalid station ID (not found in DXF):** Display an inline error message (Streamlit `st.error`) below the station ID input fields, clearly stating which ID was not found. Prevent PDF generation until the error is resolved.
- **Coordinate system incompatibility:** Not possible — all surveys use Cartesian coordinates; only the origin differs. No handling required.
- **Merged sketch too large for the page:** Automatically rescale the entire merged sketch (map and/or section) so that it fits within the standard PDF page dimensions. No user intervention needed.

## Non-Functional Requirements
- **Integration:** The feature must seamlessly integrate into the existing `1_survey_plot.py` page without breaking the current single-file workflow.
- **Performance:** Merging must complete within Streamlit's default request timeout (30 seconds) for surveys of typical cave size.
- **Robustness:** The merging logic must correctly handle ID remapping and coordinate translation to avoid data corruption in the plots.

## Acceptance Criteria
- Users can upload one child survey (map and/or section DXF) in a new section on the Survey Plot page.
- Non-numeric station IDs are rejected with a clear error message.
- A single numeric station ID pair (parent station, child station) is used for both the map and section merge.
- The internal Pandas DataFrames correctly remap IDs and translate coordinates for the child survey.
- Map view always applies Simple Merging; no protocol selector is shown for the map.
- The user can select from the three section merging protocols (Simple, Mirror, Displacement) when a child section DXF is uploaded.
- For Displacement, the child sketch is placed in a non-overlapping area (right or below preference) with two thin connector lines drawn.
- The user can generate and download a single PDF containing the merged Map (Plan) view.
- The user can generate and download a single PDF containing the merged Section view.
- The single-survey PDF generation (no child uploaded) remains fully functional with no regressions.

## Out of Scope
- Merging more than one child survey in a single session (users iterate the process for additional children).
- Merging based on georeferencing for the PDF plots (this relies on station matching).
- Uploading JSON survey exports for PDF merging (restricted to DXF files for now).
- Creation of a new, dedicated UI page for merging.
