# Specification: Ensure Station ID Visibility in PDF Survey Plots

## 1. Overview
In the generated PDF survey plots, station IDs (numbers) are sometimes partially hidden by station markers, survey lines, or cave walls. This track addresses the issue by ensuring that station IDs are always fully visible and readable to the user.

## 2. Functional Requirements
- **Z-Order adjustment:** Station IDs must be rendered last, ensuring they are placed on the topmost visual layer (highest z-order). They must not be obscured by survey lines, wall lines, or other sketch features.
- **Auto-Placement:** The rendering engine (matplotlib) should utilize an auto-placement or collision-avoidance strategy (e.g., via the `adjustText` library or built-in matplotlib label placement) to ensure labels do not directly overlap with the station marker dots themselves or with each other.

## 3. Non-Functional Requirements
- **Performance:** Auto-placement algorithms should not unreasonably degrade the performance of PDF generation, especially for large surveys with many stations.

## 4. Acceptance Criteria
- [ ] Generate a PDF for a survey with dense stations and crossing lines.
- [ ] Verify visually that all station IDs are drawn on top of all lines and markers.
- [ ] Verify visually that station IDs do not perfectly overlap their corresponding station markers, utilizing auto-placement to remain legible.

## 5. Out of Scope
- Adding background bounding boxes or halos to the text.
- Changes to the HTML/Folium satellite map export.