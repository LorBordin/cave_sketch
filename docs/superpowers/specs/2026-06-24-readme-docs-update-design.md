# Design: Documentation Overhaul (README + Nested Docs)

**Date:** 2026-06-24
**Status:** Approved (design); pending implementation plan

## Problem

The project's documentation has fallen well behind the code. The root
`README.md` / `README.it.md` describe only the *original* web workflow
(DXF → PDF, basic single-survey satellite overlay) and still list shipped
features as open ToDos. Several major additions are entirely undocumented:

- **Web — survey merging:** parent + child DXF merging via numeric station-ID
  matching, with three section protocols (Simple / Mirror / Displacement).
- **Web — merged & multi-survey satellite maps:** rendering a merged survey on
  satellite imagery, plus placing *multiple* surveys on one satellite view via a
  JSON export → re-import workflow.
- **Web — offline KMZ export:** segment-chained KMZ for offline use in Locus Map
  and OsmAnd (replacing the old per-segment KML that froze Locus).
- **Android app:** a full, shipped (v1.0.0) offline-capable native Android app —
  its features, install/usage, and tech stack — currently undocumented for both
  users and potential contributors.

Additionally, `docs/mobile-app/README.md` is stale (its status table says
Phases 1–4 are "Not started" although the app is shipped), but per the decision
below it is left untouched as frozen internal planning history.

## Goals

1. Document the new **web** features (merging, merged/multi-survey satellite,
   KMZ export).
2. Document **all features of the Android app** for users.
3. Document the **Android tech stack & architecture** for potential
   contributors.
4. Restructure docs into a maintainable **nested tree**, fully bilingual
   (English + Italian).

## Non-Goals

- No changes to application code or behavior — documentation only.
- No modification of `docs/mobile-app/` (frozen internal planning history).
- No new screenshots produced by the implementer; the maintainer will supply
  new web-feature screenshots. Docs leave clearly-labeled placeholders.

## Decisions (locked with maintainer)

| Decision | Choice |
|----------|--------|
| Languages | **Fully bilingual** — every nested doc mirrored EN + IT |
| Location | **New `docs/web/` + `docs/android/` tree**; root READMEs link out |
| Screenshots | Maintainer provides new web screenshots; docs use labeled placeholders |
| Web docs granularity | **Two docs**: `survey-merging` + `satellite-maps` |
| `docs/mobile-app/` | **Left untouched** |
| Root ToDo list | **Trim shipped items** (merging, KMZ, multi-survey docs); keep open ones |
| New web images | New folder `docs/web/imgs/` |

## File Tree (target)

```
README.md / README.it.md          ← landing pages (restructured)

docs/
  web/
    README.md      / README.it.md      ← web app docs index
    survey-merging.md / .it.md         ← parent+child DXF merging
    satellite-maps.md / .it.md         ← satellite + multi-survey + KMZ/KML
    imgs/                              ← new web-feature screenshots (maintainer-supplied)
  android/
    README.md      / README.it.md      ← Android user guide
    architecture.md / .it.md           ← Android contributor / tech-stack doc

docs/mobile-app/   ← UNCHANGED (internal dev planning history)
```

Total new/changed content: 2 root READMEs + 6 content docs × 2 languages = 14
markdown files, plus a new `docs/web/imgs/` directory.

## Content Specification

### Root `README.md` / `README.it.md` (landing pages)

Restructured, preserving valuable existing content:

- **Intro + value prop** (kept, lightly updated).
- **Two ways to use CaveSketch**: 🌐 Web app (live Streamlit link) and
  📱 Android app (APK from GitHub Releases) — short pitch + link to each detailed
  doc set.
- **Features at a glance** — bulleted, grouped: PDF survey · survey merging ·
  satellite maps (single/merged/multi-survey) · KML/KMZ export · Android offline
  app.
- **Prerequisite: exporting DXF from TopoDroid** — kept as-is (shared by both web
  and app); retains existing screenshots from `imgs/`.
- **For developers** — existing dev setup (uv sync, pre-commit, run streamlit)
  kept; add a pointer to `docs/android/architecture.md` for Android contributors.
- **ToDo list** — remove now-shipped items (multi-survey satellite docs,
  multi-survey PDF merging, .kml export, merge-into-existing-kml); keep genuinely
  open ones (area coloring, satellite HTML rendering improvements, 3D models).
- Links into `docs/web/` and `docs/android/`.
- Bilingual language-switch line at top (existing pattern).

### `docs/web/README.md` (+ `.it.md`)

Index of web app documentation: one-paragraph overview of the web app and links
to `survey-merging.md` and `satellite-maps.md`. Bilingual switch line.

### `docs/web/survey-merging.md` (+ `.it.md`)

Source of truth: `conductor/archive/pdf_merging_20260525/spec.md`.

- What merging does (combine a parent + one child survey into one PDF).
- **Numeric station-ID matching** rule; why letter IDs (e.g. `12P4`) are invalid
  (they identify wall/line geometry, not stations).
- A single parent/child station-ID pair applies to **both** map and section DXF.
- **One child per session**; iterate by downloading the merged result and
  re-uploading it as a new parent.
- **Map view always uses Simple Merging** (no protocol selector).
- **Section protocols** with when-to-use guidance:
  - *Simple Merging* — child translated onto parent station, same space.
  - *Simple Mirror* — as Simple but child mirrored across the vertical axis.
  - *Displacement* — child placed in a non-overlapping area (right-first, then
    below) with two thin connector lines to indicate topological connection.
- Settings (rotation, scale, line width, text size) apply to the **whole merged
  result**; oversized merges auto-rescale to fit the page.
- Placeholders: merge UI (child upload + station-ID fields), Mirror example,
  Displacement example.

### `docs/web/satellite-maps.md` (+ `.it.md`)

Sources: `conductor/archive/merged_satellite_map_20260527/spec.md`,
`conductor/archive/offline_kmz_export_20260612/spec.md`, root README ToDo note on
the JSON workflow.

- **Single-survey overlay**: add known GPS points for stations to georeference
  (the more the better); generate the satellite view.
- **Merged-survey rendering**: when a child survey is merged on the Survey Plot
  page, the satellite map renders the merged result.
- **Multiple surveys on one view**: export a sketch as JSON, then re-import it
  alongside new surveys to draw several sketches on the same satellite view.
- **Outputs**: interactive HTML map, KML (Google Earth 3D), and **KMZ**.
- **KMZ for offline apps**: explain it targets **Locus Map** and **OsmAnd**;
  segment-chaining collapses thousands of placemarks into a handful (fixes the
  Locus freeze); KMZ generation makes zero network calls; note the accepted
  OsmAnd polygon-fill limitation (water may render as outline, not filled).
- Placeholders: multi-survey satellite view, KMZ loaded in Locus Map.

### `docs/android/README.md` (+ `.it.md`) — user guide

Sources: `android/DEVLOG.md`, `android/RELEASE.md`, `conductor/product.md`,
`docs/mobile-app/umbrella-spec.md`.

- What the app is: offline-capable native Android app, same rendering engine as
  the web app.
- **Install**: download `CaveSketch-x.y.z.apk` from GitHub Releases; allow
  installs from unknown sources; install; upgrade behavior (install over the top,
  settings preserved, same signing key required).
- **The three screens**:
  - *Survey Plot* — DXF → PDF, settings form, survey merging controls,
    save/share.
  - *Satellite Map* — GPS-point georeferencing, optional rotation, additional
    JSON map import, KMZ + HTML export, online map preview (WebView).
  - *About* — app info, link to the public repo.
- **Offline behavior**: PDF generation and KMZ export work offline; satellite
  tiles / HTML preview need a network connection.
- Visuals: reuse `docs/mobile-app/screenshots_v1/` (survey_1–4, satellite_1–3,
  about); placeholders for any new shots the maintainer supplies.

### `docs/android/architecture.md` (+ `.it.md`) — contributor doc

Sources: `conductor/tech-stack.md`, `android/DEVLOG.md`, `android/RELEASE.md`,
the `android/` source tree.

- **Stack**: Kotlin · Jetpack Compose (dark Material3 theme) · Chaquopy 17
  embedding Python 3.13 · native Android `PdfRenderer` · WebView (Leaflet/Folium
  for the satellite preview).
- **Layering**: Compose screens → ViewModels (`SurveyPlotViewModel`,
  `SatelliteViewModel`) → Kotlin bridges (`PythonBridge`, `SurveyBridge`,
  `SatelliteBridge`) → Python bridge modules (`survey_bridge.py`,
  `satellite_bridge.py`) → shared `cave_sketch` core (symlinked into the app, kept
  Streamlit-free).
- **Key constraints / learnings** (from DEVLOG): the `cave_sketch` core stays
  untouched and Streamlit-free; the relative-symlink trick that avoids the Gradle
  input/output overlap and code duplication; render-latency optimization
  (warm `draw_survey` ~60.6s → ~3.0s, `parse_dxf` ~4.5s → ~1.2s); JDK 17+ /
  Chaquopy / AGP build requirements.
- **Build & release**: summarize and link `android/RELEASE.md` (signing keystore,
  `./gradlew assembleRelease`, publishing to GitHub Releases).
- **Quality gates**: ruff + mypy + pytest for Python; Kotlin unit tests
  (ViewModel/util/components).

## Conventions

- **Screenshot placeholders** use an HTML comment naming the target path and
  intended content, e.g.:
  ```
  <!-- SCREENSHOT: docs/web/imgs/merge-ui.png — merging UI with child upload + station IDs -->
  ```
  The maintainer drops the image in and removes the comment.
- **New web images** live in `docs/web/imgs/`. Android docs reuse
  `docs/mobile-app/screenshots_v1/`. The original DXF-export images stay in
  `imgs/`.
- **Bilingual cross-links**: every doc starts with the 🇬🇧/🇮🇹 language-switch
  line used by the current root READMEs, pointing at its EN/IT counterpart.
- Authoring order per doc: **English first, then the Italian mirror.**

## Acceptance Criteria

1. Root `README.md` and `README.it.md` are restructured as landing pages with a
   features-at-a-glance section, both-platforms entry points, preserved TopoDroid
   DXF-export prerequisite and dev setup, a trimmed ToDo list, and links into
   `docs/web/` and `docs/android/`.
2. `docs/web/` contains `README`, `survey-merging`, and `satellite-maps` (EN+IT),
   covering merging protocols, merged/multi-survey satellite rendering, and
   KML/KMZ export accurately per the source specs.
3. `docs/android/` contains `README` (user guide) and `architecture`
   (contributor doc), EN+IT, covering install/usage, the three screens, offline
   behavior, the full tech stack/layering, and the build/release process.
4. Every nested doc has a working EN↔IT language-switch link.
5. Screenshot placeholders are present and clearly labeled where new images are
   needed; existing images are referenced with correct relative paths.
6. `docs/mobile-app/` is unchanged.
7. No application code is modified.
