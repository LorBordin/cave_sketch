# Specification: North Symbol Visibility for Section Renders

## Overview
This track addresses an issue in the PDF survey generation where the north symbol is incorrectly drawn when only the cave's cross-section is rendered. Since a section view represents a vertical slice, a top-down north indicator is not physically meaningful and should be omitted.

## Functional Requirements
1. **Conditional North Symbol Rendering:** The rendering engine must evaluate the selected views before drawing the north symbol.
2. **Section-Only Exclusion:** If the rendering configuration specifies *only* the Section view (i.e., the Plan view is omitted/disabled), the north symbol must not be drawn on the resulting PDF.
3. **Plan View Inclusion:** If the Plan view is included in the rendering configuration (either alone or alongside the Section view), the north symbol drawing logic should proceed as normally configured.
4. **Backend Enforcement:** This conditional logic must be implemented in the backend rendering module. The user interface (UI) will remain unchanged; any toggle for the north symbol will simply be ignored by the backend if a section-only render is requested.

## Non-Functional Requirements
- **Performance:** The check for view types should not noticeably impact rendering time.

## Acceptance Criteria
- [ ] Generating a PDF with only the Section view selected produces a plot *without* a north symbol.
- [ ] Generating a PDF with only the Plan view selected produces a plot *with* a north symbol (if enabled).
- [ ] Generating a PDF with both Plan and Section views selected produces a plot *with* a north symbol (if enabled).
- [ ] The user interface for the north symbol toggle remains visible and interactive regardless of the view selection.

## Out of Scope
- Modifying the UI to disable or hide the north symbol toggle based on view selection.
- Changes to the north symbol's design, position, or scale.
- Alterations to the KML or satellite map export logic.