# Specification: North Symbol Visibility for Section Renders

## Overview
This track addresses an issue in the PDF survey generation where the north symbol is incorrectly drawn when only the cave's cross-section is rendered. Since a section view represents a vertical slice, a top-down north indicator is not physically meaningful and should be omitted.

## Functional Requirements
1. **Conditional North Symbol Rendering:** The rendering engine must evaluate the selected views before drawing the north symbol.
2. **Section-Only Exclusion:** If the rendering configuration specifies *only* the Section view (i.e., `csv_map_path` is `None` and only `csv_section_path` is provided to `draw_survey()`), the north symbol must not be drawn on the resulting PDF.
3. **Plan View Inclusion:** If the Plan view is included in the rendering configuration (either alone or alongside the Section view), the north symbol drawing logic should proceed as normally configured.
4. **Section-Only Subplot Title:** When rendering section-only, the subplot title must be `"Sezione"` (not `"Pianta"`, which is the plan view title).
5. **Backend Enforcement:** This conditional logic must be implemented in the backend rendering module via a new `show_north: bool = True` field on `SurveyConfig`. The user interface (UI) will remain unchanged; any toggle for the north symbol will simply be ignored by the backend if a section-only render is requested.

## Non-Functional Requirements
- **Performance:** The check for view types should not noticeably impact rendering time.

## Root Cause

In `cave_sketch/survey/survey.py`, when only section data is provided, the code reassigns it to the plan slot and loses the "section-only" context:
```python
if not survey and section_survey:
    survey = section_survey   # section data placed in plan slot
    section_survey = None     # context lost
```
`render_survey()` then renders one subplot with hardcoded `north_flag=True`, causing the north symbol to appear on section data rendered under the title `"Pianta"`.

## Acceptance Criteria
- [ ] Generating a PDF with only the Section view (`csv_map_path=None`, `csv_section_path` provided) produces a plot *without* a north symbol and with subplot title `"Sezione"`.
- [ ] Generating a PDF with only the Plan view produces a plot *with* a north symbol (if enabled) and subplot title `"Pianta"`.
- [ ] Generating a PDF with both Plan and Section views produces a plot *with* a north symbol on the plan subplot (if enabled).
- [ ] The user interface for the north symbol toggle remains visible and interactive regardless of the view selection.

## Out of Scope
- Modifying the UI to disable or hide the north symbol toggle based on view selection.
- Changes to the north symbol's design, position, or scale.
- Alterations to the KML or satellite map export logic.