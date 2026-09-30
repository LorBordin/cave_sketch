# DXF Elements Reference

This document catalogues all unique elements found in DXF files across the project and their rendering specifications in `cave_sketch/style.py`.

## Overview

DXF elements are organized into three categories based on their DXF representation:
- **Line Elements** (L_ prefix): Polylines representing walls, passages, and features
- **Area Elements** (A_ prefix): Hatches representing filled regions
- **Block/Feature Elements** (B_ prefix): INSERT blocks representing point features
- **Standard Elements**: Layers and special entities

---

## Line Elements

### L_wall
- **Type**: Line
- **DXF Type**: LWPOLYLINE/POLYLINE with linetype "L_wall"
- **Description**: Main/solid cave wall
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Red
  - Line Style: Solid
  - Weight: 3
- **Files using**: sample.dxf, sample_v14.dxf, sample_v9.dxf, val_cont_06-0p.dxf, val_mul_4-1p.dxf, grotta_mittelbergferner-1p.dxf

### L_wall-presumed
- **Type**: Line
- **DXF Type**: LWPOLYLINE/POLYLINE with linetype "L_wall-presumed"
- **Description**: Presumed/uncertain wall (shown as dashed)
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Red
  - Line Style: Dashed (0, (1, 2))
  - Weight: 1
- **Files using**: sample.dxf, sample_v14.dxf, sample_v9.dxf, val_cont_06-0p.dxf, val_mul_4-1p.dxf, grotta_mittelbergferner-1p.dxf

### L_pit
- **Type**: Line
- **DXF Type**: LWPOLYLINE/POLYLINE with linetype "L_pit"
- **Description**: Pit or vertical drop feature
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Indigo
  - Line Style: Dotted (0, (1, 1))
  - Weight: 1
- **Files using**: sample.dxf, sample_v14.dxf, sample_v9.dxf, val_cont_06-0p.dxf, val_mul_4-1p.dxf, grotta_mittelbergferner-1p.dxf

### L_chimney
- **Type**: Line
- **DXF Type**: LWPOLYLINE/POLYLINE with linetype "L_chimney"
- **Description**: Vertical or near-vertical passage (chimney/pitch)
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Indigo
  - Line Style: Dashed (0, (1, 2))
  - Weight: 1
- **Files using**: sample.dxf, val_mul_4-1p.dxf

### L_water-flow
- **Type**: Line
- **DXF Type**: LWPOLYLINE/POLYLINE with linetype "L_water-flow"
- **Description**: Water flow direction indicator
- **Defined in style.py**: ❌ **Missing** — Not defined in style.py
- **Files using**: val_cont_06-0p.dxf (93 instances)

### L_border
- **Type**: Line
- **DXF Type**: LWPOLYLINE/POLYLINE with linetype "L_border"
- **Description**: Survey area boundary or border
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Green
  - Line Style: Solid
  - Weight: 2
- **Files using**: sample.dxf only

### L_slope
- **Type**: Line
- **DXF Type**: (Inferred from style.py only)
- **Description**: Inclined passage or slope
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Black
  - Line Style: Solid
  - Weight: 2
- **Files using**: Not found in analyzed DXF files (defined in code but unused in data)

---

## Area Elements

### A_water
- **Type**: Area/Hatch
- **DXF Type**: HATCH entity with linetype "A_water"
- **Description**: Water-filled areas (flooded passages, sumps, lakes)
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Blue
  - Alpha: 0.3 (30% transparent)
  - Type: Area fill
- **Files using**: sample_v14.dxf, sample_v9.dxf, val_cont_06-0p.dxf, val_mul_4-1p.dxf, grotta_mittelbergferner-1p.dxf

---

## Block/Feature Elements

### B_ice
- **Type**: Block (INSERT entity)
- **DXF Type**: INSERT block named "B_ice"
- **Description**: Ice formation or icy passage feature
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Deep Sky Blue
  - Marker: Dot (.)
  - Marker Size: 2
  - Type: Point marker
- **Files using**: sample_v14.dxf, sample_v9.dxf, grotta_mittelbergferner-1p.dxf (102 instances)

### B_snow
- **Type**: Block (INSERT entity)
- **DXF Type**: INSERT block named "B_snow"
- **Description**: Snow deposit or snowy area
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Alice Blue
  - Marker: Star (*)
  - Marker Size: 2
  - Type: Point marker
- **Files using**: sample_v14.dxf, sample_v9.dxf, grotta_mittelbergferner-1p.dxf (146 instances)

### B_water-flow
- **Type**: Block (INSERT entity)
- **DXF Type**: INSERT block named "B_water-flow"
- **Description**: Water flow indicator or direction marker
- **Defined in style.py**: ❌ **Missing** — Not defined in style.py
- **Files using**: sample_v14.dxf, sample_v9.dxf, val_mul_4-1p.dxf (6 instances), grotta_mittelbergferner-1p.dxf (20 instances)

### B_blocks
- **Type**: Block (INSERT entity)
- **DXF Type**: INSERT block named "B_blocks"
- **Description**: Rock blocks, breakdown, or debris (generic blocks)
- **Defined in style.py**: ⚠️ Partially — defined as "BLOCK" (different name)
- **Rendering** (via "BLOCK" entry):
  - Color: Saddle Brown
  - Marker: Circle (o)
  - Marker Size: 4
  - Type: Point marker
- **Files using**: sample_v14.dxf, sample_v9.dxf, val_mul_4-1p.dxf (5 instances), grotta_mittelbergferner-1p.dxf (90 instances)
- **Note**: DXF uses "B_blocks" but style.py defines it as "BLOCK"

### B_continuation
- **Type**: Block (INSERT entity)
- **DXF Type**: INSERT block named "B_continuation"
- **Description**: Passage continues or survey continuation marker
- **Defined in style.py**: ❌ **Missing** — Not defined in style.py
- **Files using**: val_cont_06-0p.dxf (1 instance)

### B_entrance
- **Type**: Block (INSERT entity)
- **DXF Type**: INSERT block named "B_entrance"
- **Description**: Cave entrance marker
- **Defined in style.py**: ❌ **Missing** — Not defined in style.py
- **Files using**: val_cont_06-0p.dxf

---

## Standard Elements

### station
- **Type**: Special point
- **DXF Type**: TEXT entity on "STATION" layer
- **Description**: Survey station point (topographic datum)
- **Defined in style.py**: ✅ Yes
- **Rendering**:
  - Color: Black
  - Line Style: Solid
  - Weight: 1
  - Type: Line (connection marker)
- **All files**: All DXF files

### LEG
- **Type**: Connection
- **DXF Type**: LINE entity on "LEG" layer
- **Description**: Survey leg connecting two stations
- **Defined in style.py**: ⚠️ Partially — defined as "connector"
- **Rendering** (via "connector" entry):
  - Color: Gray
  - Line Style: Dotted
  - Weight: 0.5
- **All files**: All DXF files

### SPLAY
- **Type**: Layer
- **DXF Type**: Entities on "SPLAY" layer
- **Description**: Splay shot (radiating shot from a station)
- **Defined in style.py**: ❌ **Missing** — Not defined in style.py
- **Files using**: All fixture files (sample.dxf, sample_v14.dxf, sample_v9.dxf)

### SCRAP_0
- **Type**: Layer
- **DXF Type**: Entities on "SCRAP_0" layer
- **Description**: Scrap or auxiliary drawing data (explicitly filtered out in parser)
- **Defined in style.py**: ❌ **Missing** — Not defined in style.py
- **Note**: Filtered during parsing (see `_parse_polylines` in `parse_dxf.py`)
- **Files using**: All files

---

## Summary Table

| Element | Type | In style.py | Status | Count |
|---------|------|-------------|--------|-------|
| L_wall | Line | ✅ | Defined | 6/6 files |
| L_wall-presumed | Line | ✅ | Defined | 6/6 files |
| L_pit | Line | ✅ | Defined | 6/6 files |
| L_chimney | Line | ✅ | Defined | 2/6 files (sample.dxf, val_mul_4-1p.dxf) |
| L_border | Line | ✅ | Defined | 1/6 files |
| L_slope | Line | ✅ | Defined | 0/6 files (code only) |
| L_water-flow | Line | ❌ | **Missing** | 1/6 files (val_cont_06-0p.dxf) |
| A_water | Area | ✅ | Defined | 6/6 files |
| B_ice | Block | ✅ | Defined | 3/6 files (sample_v14.dxf, sample_v9.dxf, grotta_mittelbergferner-1p.dxf) |
| B_snow | Block | ✅ | Defined | 3/6 files (sample_v14.dxf, sample_v9.dxf, grotta_mittelbergferner-1p.dxf) |
| B_blocks | Block | ⚠️ | Partial (named "BLOCK") | 4/6 files (sample_v14.dxf, sample_v9.dxf, val_mul_4-1p.dxf, grotta_mittelbergferner-1p.dxf) |
| B_water-flow | Block | ❌ | **Missing** | 4/6 files (sample_v14.dxf, sample_v9.dxf, val_mul_4-1p.dxf, grotta_mittelbergferner-1p.dxf) |
| B_continuation | Block | ❌ | **Missing** | 1/6 files (val_cont_06-0p.dxf) |
| B_entrance | Block | ❌ | **Missing** | 1/6 files |
| station | Point | ✅ | Defined | 6/6 files |
| LEG | Line | ⚠️ | Partial (as "connector") | 6/6 files |
| SPLAY | Layer | ❌ | **Missing** | 3/6 files |

---

## Missing Definitions in style.py

The following elements exist in DXF files but lack rendering definitions in `style.py`:

1. **L_water-flow** — Water flow direction lines (val_cont_06-0p.dxf: 93 instances)
2. **B_water-flow** — Water flow markers (4 files: sample_v14.dxf, sample_v9.dxf, val_mul_4-1p.dxf, grotta_mittelbergferner-1p.dxf)
3. **B_continuation** — Passage continuation markers (val_cont_06-0p.dxf: 1 instance)
4. **B_entrance** — Entrance markers (1 file)
5. **SPLAY** — Splay shots layer (3 files)

Consider adding style definitions for these elements to enable proper rendering in visualizations.

---

## Notes

- DXF files use TopoDroid convention for element naming
- The parser in `parse_dxf.py` extracts linetype and layer information
- Rendering is controlled by `cave_sketch/style.py` via the `STYLE_MAP` dictionary
- HATCH entities are noted as redundant in comments (boundaries already captured by polylines)
- "SCRAP_0" layer is explicitly filtered during parsing
- **New files scanned**:
  - **grotta_mittelbergferner-1p.dxf**: Large survey with 3067 L_wall, 1574 A_water, 146 B_snow, 102 B_ice, 90 B_blocks, 20 B_water-flow instances
  - **val_cont_06-0p.dxf**: Survey with 608 L_wall, 734 A_water, 102 L_pit, 138 L_wall-presumed, 93 L_water-flow, 1 B_continuation
  - **val_mul_4-1p.dxf**: Survey with 452 L_wall, 285 A_water, 52 L_wall-presumed, 54 L_chimney, 5 B_blocks, 6 B_water-flow
  - No new element types discovered; all elements were previously documented
