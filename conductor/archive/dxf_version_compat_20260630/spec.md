# Spec: DXF Version Compatibility (R9, R12, R14/R2000)

## Overview

The CaveSketch DXF parser currently only handles `POLYLINE` entities, which are used in DXF versions R9/R12 (AC1009). TopoDroid can also export DXF in version R14/R2000 (AC1015), which uses `LWPOLYLINE` (Lightweight Polyline) instead. This causes **all polyline-based survey features** (walls, slopes, pits, water areas, etc.) to be completely missing from the rendered output when a v14 DXF is loaded.

Additionally, DXF R2000 represents filled areas (like `A_water`) as `HATCH` entities rather than closed polylines, which may need to be handled for full parity.

The parser must auto-detect the DXF version and handle both entity types transparently, so that the same survey produces identical `CaveSurvey` output regardless of which DXF version was used for export.

## Functional Requirements

1. **FR-1: LWPOLYLINE Support** — The `_parse_polylines()` function in `parser.py` must query both `POLYLINE` and `LWPOLYLINE` entities from the modelspace. `LWPOLYLINE` entities store vertices differently (flat list via `.get_points()`) and must be normalized to the same `(x, y)` point tuple format.

2. **FR-2: Automatic Version Detection** — No user intervention is required. The parser should transparently handle any DXF version that `ezdxf` can read. The version is detected automatically by `ezdxf.readfile()`.

3. **FR-3: Identical Output** — Parsing `sample_v9.dxf` and `sample_v14.dxf` (same survey, different DXF versions) must produce `CaveSurvey` objects with **identical** points, lines, and line types. This is the primary acceptance criterion.

4. **FR-4: HATCH Entity Handling** — DXF R2000 uses `HATCH` entities for area fills (e.g., `A_water`). Investigate whether these should be parsed as area polygons. If the existing `A_water` polyline data already provides equivalent coverage, HATCH entities can be safely ignored.

5. **FR-5: Backward Compatibility** — All existing DXF files (including the original `sample.dxf` fixture) must continue to parse correctly with no regressions.

## Non-Functional Requirements

- **NFR-1:** No new dependencies. The `ezdxf` library already supports both entity types.
- **NFR-2:** All changes confined to `cave_sketch/dxf/parser.py` (and tests). No changes to the rendering pipeline or style system.

## Acceptance Criteria

- [ ] `parse_dxf("sample_v9.dxf")` and `parse_dxf("sample_v14.dxf")` produce `CaveSurvey` objects with the same number of points, lines, and identical line type distributions.
- [ ] The existing `sample.dxf` test continues to pass unchanged.
- [ ] `uv run ruff check .`, `uv run mypy cave_sketch/`, and `uv run pytest` all pass.

## Out of Scope

- Support for DXF versions beyond R2000 (e.g., R2004, R2007, R2010) — can be added later.
- Changes to the rendering pipeline (`survey/`, `features/`, `backend_renders/`).
- Changes to the Streamlit UI.
- Handling of `MTEXT` entities (not present in these TopoDroid exports).
