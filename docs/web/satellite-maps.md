🌍 Available languages: [🇬🇧 English](satellite-maps.md) | [🇮🇹 Italiano](satellite-maps.it.md)

# Satellite Maps, Multi-Survey Views & Offline KMZ Export

CaveSketch can overlay your cave survey on satellite imagery, combine multiple surveys into a single geographic view, and export offline-ready map files for field use.

## Single-Survey Overlay

Place a cave map on satellite imagery by providing GPS coordinates for known survey stations. CaveSketch computes an affine transform to align the cave geometry with real-world geography.

> [!TIP]
> The more GPS-referenced stations you provide, the better the affine transform fit. Two points is the minimum, but three or more will significantly improve accuracy.

## Merged Survey Rendering

When surveys are merged on the **Survey Plot** page, the merged map is automatically used for the satellite view. There is no extra step — if your surveys are merged, the satellite overlay reflects the combined result.

## Multiple Surveys on One Map

You can display several independent surveys together on a single satellite view:

1. Generate a satellite map for your first survey.
2. **Export** that survey as JSON from the satellite page.
3. When generating a satellite map for a second survey, **import** the previously exported JSON.
4. Both surveys are drawn on one view. Repeat to add more surveys.

![Multiple surveys on satellite map](imgs/satellite-multi-survey.png)

## Output Formats

CaveSketch produces three output formats from the satellite page:

| Format | Use Case |
|--------|----------|
| **Interactive HTML** | Folium-based map for browsing in any web browser. Pan, zoom, toggle layers. |
| **KML** | Import into Google Earth for 3D visualization with terrain. |
| **KMZ** | Self-contained archive for offline use in mobile apps like **Locus Map** or **OsmAnd**. |

## KMZ for Offline Use — The Freeze-Fix Story

The KMZ export was redesigned to solve a critical performance problem with mobile map apps.

### The Problem

The original KML export produced approximately **6,211 Placemarks** — one per two-point line segment, with many reverse duplicates. Loading this file in Locus Map caused the app to freeze.

### The Solution

The new KMZ export applies several optimizations:

- **Segment chaining** — Thousands of short segments are collapsed into approximately **5–7 long polylines**, drastically reducing the Placemark count.
- **Shared styles** — One `<Style>` definition per feature type, instead of inline styles on every element.
- **MultiGeometry grouping** — One Placemark with a `<MultiGeometry>` block per line type, instead of thousands of individual Placemarks.
- **Water polygons** — Rendered as individual `<Polygon>` placemarks for correct fill display.
- **Point-type nodes** — Survey stations and other point features exported as `<Point>` placemarks.
- **Zero network calls** — The KMZ is fully self-contained and works completely offline.
- **All loaded maps** — The export is built from all loaded JSON maps, not just the current survey.

![KMZ in Locus Map](imgs/kmz-in-locus.png)

## Known Limitations

> [!NOTE]
> **OsmAnd** may render water areas as outlines only, without filled polygons. **Locus Map** renders them correctly with full polygon fills.

---

[Back to Web Documentation](README.md)
