# Spec: Documentation Overhaul (README + Nested Docs)

## Overview

The project's documentation has fallen behind the code. The root `README.md` /
`README.it.md` describe only the *original* web workflow (DXF → PDF, basic
single-survey satellite overlay) and still list shipped features as open ToDos.
Several major additions are entirely undocumented:

- **Web — survey merging:** parent + child DXF merging via numeric station-ID
  matching, with three section protocols (Simple / Mirror / Displacement).
- **Web — merged & multi-survey satellite maps:** rendering a merged survey on
  satellite imagery, plus placing *multiple* surveys on one satellite view via a
  JSON export → re-import workflow.
- **Web — offline KMZ export:** segment-chained KMZ for offline use in Locus Map
  and OsmAnd (replacing the old per-segment KML that froze Locus).
- **Android app:** the shipped (v1.0.0) offline-capable native Android app — its
  features, install/usage, and tech stack — currently undocumented for both
  users and potential contributors.

This is a **documentation-only** track. No application code changes.

## Goals

1. Document the new **web** features (merging, merged/multi-survey satellite, KMZ).
2. Document **all features of the Android app** for users.
3. Document the **Android tech stack & architecture** for potential contributors.
4. Restructure docs into a maintainable **nested tree**, fully bilingual (EN+IT).

## Non-Goals

- No changes to application code or behavior.
- No modification of `docs/mobile-app/` (frozen internal planning history).
- The implementer does not produce screenshots; the maintainer supplies new
  web-feature screenshots. Docs leave clearly-labeled placeholders.

## Decisions (locked with maintainer)

| Decision | Choice |
|----------|--------|
| Languages | **Fully bilingual** — every nested doc mirrored EN + IT |
| Location | **New `docs/web/` + `docs/android/` tree**; root READMEs link out |
| Screenshots | Maintainer provides new web screenshots; docs use labeled placeholders |
| Web docs granularity | **Two docs**: `survey-merging` + `satellite-maps` |
| `docs/mobile-app/` | **Left untouched** |
| Root ToDo list | **Trim shipped items**; keep genuinely open ones |
| New web images | New folder `docs/web/imgs/` |

## Functional Requirements

### FR-1: Web docs index and image folder
- Create `docs/web/README.md` (+ `.it.md`): a short index linking the two web
  guides and the live app, with a back-link to the root README.
- Create `docs/web/imgs/` (tracked via `.gitkeep`) for new web screenshots.

### FR-2: Survey merging doc — `docs/web/survey-merging.md` (+ `.it.md`)
Source of truth: `conductor/archive/pdf_merging_20260525/spec.md`. Must cover:
- Combine a parent + one child survey (DXF map and/or section) into one plot.
- Numeric-only station-ID matching; letter IDs (e.g. `12P4`) are wall geometry
  and are rejected.
- One station-ID pair applies to both map and section DXF.
- One child per session; iterate by re-uploading the merged result as a parent.
- Map view always uses Simple Merging (no protocol selector).
- Section protocols: Simple, Simple Mirror (mirror across vertical axis),
  Displacement (nearest non-overlapping placement, right-first then below, with
  two thin connector lines).
- Settings apply to the whole merged result; oversized merges auto-rescale.
- Invalid station ID shows an inline error and blocks generation.

### FR-3: Satellite maps & export doc — `docs/web/satellite-maps.md` (+ `.it.md`)
Sources: `conductor/archive/merged_satellite_map_20260527/spec.md`,
`conductor/archive/offline_kmz_export_20260612/spec.md`. Must cover:
- Single-survey overlay via GPS points (more points = better fit).
- Merged-survey rendering on the satellite map.
- Multiple surveys on one view via JSON export → re-import.
- Outputs: interactive HTML map, KML (Google Earth 3D), KMZ.
- KMZ for offline use in Locus Map / OsmAnd; segment-chaining collapses
  thousands of placemarks into a handful (fixes the Locus freeze); zero network
  calls; built from all loaded JSON maps.
- Accepted limitation: OsmAnd may render water areas as outlines, not filled.

### FR-4: Android user guide — `docs/android/README.md` (+ `.it.md`)
Sources: `android/DEVLOG.md`, `android/RELEASE.md`, `conductor/product.md`,
`docs/mobile-app/umbrella-spec.md`. Must cover:
- What the app is: offline-capable native Android app, same engine as the web app.
- Install from GitHub Releases (allow unknown sources; upgrade-over-top behavior).
- The three screens: Survey Plot (DXF→PDF, settings, merging, save/share),
  Satellite Map (GPS georeferencing, JSON import, KMZ/HTML export, online
  preview), About.
- Offline behavior: PDF + KMZ work offline; satellite tiles / HTML preview need
  network.
- Reuse existing screenshots in `docs/mobile-app/screenshots_v1/`.

### FR-5: Android architecture doc — `docs/android/architecture.md` (+ `.it.md`)
Sources: `conductor/tech-stack.md`, `android/DEVLOG.md`, `android/RELEASE.md`,
`android/` source tree. Must cover:
- Stack: Kotlin, Jetpack Compose (dark Material3), Chaquopy 17 embedding Python
  3.13, native `PdfRenderer`, WebView (Leaflet/Folium).
- Layering: Compose screens → ViewModels → Kotlin bridges → Python bridge
  modules → shared `cave_sketch` core (symlinked, Streamlit-free).
- Key learnings: symlink trick; render-latency optimization (warm `draw_survey`
  ~60.6s → ~3.0s, `parse_dxf` ~4.5s → ~1.2s); JDK 17+/Chaquopy/AGP build needs.
- Build & release: link `android/RELEASE.md` (keystore, `assembleRelease`,
  publishing).
- Quality gates: ruff/mypy/pytest + Kotlin unit tests.

### FR-6: Restructure root READMEs as landing pages
- Keep: badges, language switch, intro, TopoDroid DXF export how-to (with `imgs/`
  images), developer setup.
- Add: "Two ways to use CaveSketch" (web + Android) and a "Features at a glance"
  section linking the new docs.
- Trim shipped ToDo items (multi-survey satellite docs, multi-survey PDF merging,
  .kml export, merge-into-existing-kml); keep area coloring, satellite HTML
  rendering improvements, 3D models.

### FR-7: Conventions
- Language-switch header on every doc:
  `🌍 Available languages: [🇬🇧 English](FILE.md) | [🇮🇹 Italiano](FILE.it.md)`.
- Screenshot placeholder syntax: `<!-- SCREENSHOT: <path> — <description> -->`.
- New web images in `docs/web/imgs/`; android docs reference
  `docs/mobile-app/screenshots_v1/`; original DXF images stay in `imgs/`.
- Authoring order per doc: English first, then Italian mirror.
- Relative links only; facts only from the cited sources.

## Acceptance Criteria

1. Root `README.md` and `README.it.md` are landing pages with both-platform entry
   points, a features-at-a-glance section, preserved DXF-export prerequisite and
   dev setup, a trimmed ToDo list, and links into `docs/web/` and `docs/android/`.
2. `docs/web/` contains `README`, `survey-merging`, `satellite-maps` (EN+IT),
   accurate per the source specs.
3. `docs/android/` contains `README` (user guide) and `architecture` (contributor
   doc), EN+IT, covering install/usage, the three screens, offline behavior, the
   full tech stack/layering, and build/release.
4. Every nested doc has a working EN↔IT language-switch link.
5. Screenshot placeholders are present and clearly labeled; existing images use
   correct relative paths.
6. `docs/mobile-app/` is unchanged.
7. No application code is modified.

## Out of Scope

- Producing the new web-feature screenshots (maintainer task — see
  `screenshots-needed.md`).
- Translating or restructuring `docs/mobile-app/` internal planning docs.
- Any change to application behavior.
