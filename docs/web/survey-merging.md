🌍 Available languages: [🇬🇧 English](survey-merging.md) | [🇮🇹 Italiano](survey-merging.it.md)

# Survey Merging — Combining Parent and Child Surveys

## Overview

CaveSketch lets you combine a **parent** survey with one **child** survey — map DXF and/or section DXF — into a single unified PDF plot.

## How It Works

On the **Survey Plot** page, below the main upload buttons, a merge section appears. The workflow is:

1. **Upload the child survey** — a map `.dxf` and/or a section `.dxf`.
2. **Specify matching station IDs** for parent and child (one pair that links the two surveys together).
3. A **single station ID pair** applies to both the map and section DXF, since the same TopoDroid project uses the same numbering.

> **Station ID format:** IDs must be purely numeric (e.g. `30`, `47`). IDs containing letters (e.g. `12P4`) identify wall or line geometry, not survey stations — they are rejected with a clear error message.

### Merging More Than Two Surveys (Iterative Merge)

To merge more than two surveys:
1. Merge Survey 1 (main) and Survey 2 (child) as usual.
2. Underneath the preview, click **📥 Download Map CSV** and/or **📥 Download Section CSV** to save the merged dataset.
3. In a new session or after clearing inputs, upload the downloaded merged CSV files as the new **Main Survey**.
4. Upload Survey 3 as the **Child Survey**, set the matching station IDs, and generate the plot.
5. Repeat iteratively for any number of sub-surveys!

![Merge UI](imgs/merge-ui.png)

## Map View Protocols

When a child map is uploaded, you can select a merging protocol for the plan view:

### Simple Merging (Default)

The child's matching station is aligned to coincide with the parent's matching station. Both surveys are drawn in the same coordinate space.

### Displacement

The child map is automatically shifted to a separate, non-overlapping area outside the parent's bounding box to prevent visual clutter in complex or overlapping passages. A thin connector line links the parent's matching station to the child's displaced matching station.

> **Note on cave metrics & geospatial exports:** The connector line is excluded from total length and depth calculations, keeping cave totals identical to Simple Merging. In addition, Satellite maps and KML/KMZ exports always preserve the true geographic alignment (Simple Merging).

## Section View Protocols

For section view, you select a merging protocol via a radio/select control:

### Simple Merging

The child's matching station is aligned to the parent's matching station. Both surveys are drawn in the same coordinate space.

### Simple Mirror

Same as Simple Merging, but the child is **mirrored across the vertical axis (y-axis)** before placement. This is useful when surveys approach the junction from opposite directions.

![Mirror protocol](imgs/merge-mirror.png)

### Displacement

The child is placed in a **separate, non-overlapping area**. The search direction is: right first, then below. Two thin connector lines are drawn from the parent's matching station to the child's matching station, visually linking the two survey segments.

![Displacement protocol](imgs/merge-displacement.png)

## Settings & Rendering

All settings — rotation, scale, line width, text size, etc. — apply to the **whole merged result**. If the merged output exceeds the PDF page dimensions, it is automatically rescaled to fit.

## Error Handling

If a station ID is invalid (not found in the uploaded DXF), an inline error message is displayed and PDF generation is blocked until the issue is corrected.

---

[Back to Web Documentation](README.md)
