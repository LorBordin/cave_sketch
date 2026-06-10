# Specification: Ensure Station ID Visibility in PDF Survey Plots

## 1. Overview
In the generated PDF survey plots, station IDs (numbers) are sometimes partially hidden by station markers, survey lines, or cave walls. This track addresses the issue by ensuring that station IDs are always fully visible and readable to the user.

## 2. Functional Requirements
- **Z-Order adjustment:** Station IDs must be rendered last, ensuring they are placed on the topmost visual layer (highest z-order). They must not be obscured by survey lines, wall lines, or other sketch features. A `zorder` value of 10 (or higher) must be set on station ID text artists, above the station marker scatter (`zorder=5`).
- **Fixed offset placement:** Labels must be rendered with a small fixed offset from the station marker coordinates, using matplotlib's `xytext` / `annotate` or an explicit data-unit offset in `ax.text()`, so they do not sit directly on top of the marker dot. No third-party collision-avoidance library is required.

## 3. Non-Functional Requirements
- **Performance:** The offset approach must add negligible overhead — no iterative collision loop. PDF generation performance must be unchanged for surveys with hundreds of stations.

## 4. Acceptance Criteria
- [ ] Generate a PDF for a survey with dense stations and crossing lines.
- [ ] Verify visually that all station IDs are drawn on top of all lines and markers.
- [ ] Verify visually that station IDs are offset from their corresponding station markers and do not sit directly on top of the marker dot.

## 5. Out of Scope
- Adding background bounding boxes or halos to the text.
- Changes to the HTML/Folium satellite map export.