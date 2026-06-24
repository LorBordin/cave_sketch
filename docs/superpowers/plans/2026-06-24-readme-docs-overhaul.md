# README + Nested Docs Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the outdated documentation with a bilingual (EN+IT) nested doc tree covering the new web features (survey merging, merged/multi-survey satellite maps, KMZ export) and the shipped Android app (user guide + tech stack), and restructure the root READMEs into landing pages.

**Architecture:** Documentation only — no application code changes. Create `docs/web/` and `docs/android/` trees, each doc mirrored in English and Italian with a language-switch header. Root `README.md`/`README.it.md` become landing pages that link into the new trees. `docs/mobile-app/` is left untouched.

**Tech Stack:** Markdown (GitHub-flavored). No build step. Verification is by relative-link existence checks and content review against source specs.

## Global Constraints

- **Fully bilingual:** every nested doc has an English (`*.md`) and Italian (`*.it.md`) counterpart.
- **Language-switch header** at the top of every doc, following the existing root README pattern:
  `🌍 Available languages: [🇬🇧 English](FILE.md) | [🇮🇹 Italiano](FILE.it.md)` (adjust filenames per doc; relative to the doc's own folder).
- **No application code is modified.** `docs/mobile-app/` is NOT modified.
- **New web screenshots** go in `docs/web/imgs/`. Android docs reference existing `docs/mobile-app/screenshots_v1/`. Original DXF-export images stay in `imgs/`.
- **Screenshot placeholder format** (exact): `<!-- SCREENSHOT: <path> — <description> -->`. Maintainer supplies the image and removes the comment later.
- **Authoring order per doc:** write English first, then the Italian mirror.
- **Relative links** only (the repo is browsed on GitHub). Paths relative to the file containing the link.
- **Source of truth** for facts: `conductor/archive/pdf_merging_20260525/spec.md`, `conductor/archive/merged_satellite_map_20260527/spec.md`, `conductor/archive/offline_kmz_export_20260612/spec.md`, `android/DEVLOG.md`, `android/RELEASE.md`, `conductor/tech-stack.md`, `conductor/product.md`. Do not invent facts beyond these.
- Work happens on branch `docs/readme-overhaul` (already created).

---

### Task 1: Web docs index + image folder

**Files:**
- Create: `docs/web/imgs/.gitkeep`
- Create: `docs/web/README.md`
- Create: `docs/web/README.it.md`

**Interfaces:**
- Produces: the `docs/web/` directory and its index, linked from later root README and sibling web docs. Sibling files referenced: `survey-merging.md`, `satellite-maps.md` (created in Tasks 2–3).

- [ ] **Step 1: Create the image folder placeholder**

Create `docs/web/imgs/.gitkeep` (empty file) so the folder is tracked by git.

- [ ] **Step 2: Write `docs/web/README.md` (English)**

Content:
- Language-switch header: `🌍 Available languages: [🇬🇧 English](README.md) | [🇮🇹 Italiano](README.it.md)`
- Title: `# CaveSketch — Web App Documentation`
- One short paragraph: CaveSketch web app is a Streamlit app that turns TopoDroid DXF exports into PDF surveys and georeferenced satellite maps. Live app link: https://cavesketch.streamlit.app/
- A "Guides" list linking:
  - `[Survey Merging](survey-merging.md)` — merge a parent and child survey into one plot.
  - `[Satellite Maps & Export](satellite-maps.md)` — georeference surveys on satellite imagery and export HTML / KML / KMZ.
- A line linking back: `See the [project README](../../README.md) for installation and the TopoDroid DXF export steps.`

- [ ] **Step 3: Write `docs/web/README.it.md` (Italian mirror)**

Same structure, Italian text. Language-switch header points back: `[🇬🇧 English](README.md) | [🇮🇹 Italiano](README.it.md)`. Links use the `.it.md` siblings: `[Unione dei rilievi](survey-merging.it.md)`, `[Mappe satellitari ed esportazione](satellite-maps.it.md)`, and `[README del progetto](../../README.it.md)`.

- [ ] **Step 4: Verify links resolve**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
for f in docs/web/README.md docs/web/README.it.md; do
  echo "== $f =="; grep -oE '\]\(([^)]+)\)' "$f"
done
```
Expected: each listed relative target either exists now or is created in Tasks 2–3 (`survey-merging.md`, `satellite-maps.md` and `.it.md` variants), and `../../README.md` / `../../README.it.md` exist. Note any that don't yet exist (expected for Task 2–3 siblings).

- [ ] **Step 5: Commit**

```bash
git add docs/web/README.md docs/web/README.it.md docs/web/imgs/.gitkeep
git commit -m "docs(web): add web docs index and image folder"
```

---

### Task 2: Survey merging doc (EN + IT)

**Files:**
- Create: `docs/web/survey-merging.md`
- Create: `docs/web/survey-merging.it.md`

**Source:** `conductor/archive/pdf_merging_20260525/spec.md`

**Interfaces:**
- Consumes: linked from `docs/web/README.md` (Task 1) and root README (Task 6).
- Produces: screenshot placeholders under `docs/web/imgs/` for the maintainer.

- [ ] **Step 1: Write `docs/web/survey-merging.md` (English)**

Required content (all facts from the source spec — include each point):
- Language-switch header for this file pair.
- Title `# Survey Merging`.
- **What it does:** combine a *parent* survey and one *child* survey (each uploaded as DXF: map and/or section) into a single unified plot. UI lives on the Survey Plot page, below the two main upload buttons.
- **Station-ID matching:** the child is aligned to the parent by matching one station in each. Enter the parent's matching station ID and the child's matching station ID.
- **Numeric IDs only:** only purely numeric station IDs are valid. IDs containing letters (e.g. `12P4`) identify wall/line geometry, not survey stations, and are rejected with an error.
- **One pair for both views:** a single parent/child station-ID pair applies to both the map DXF and the section DXF (they share TopoDroid numbering).
- **One child per session:** to merge more surveys, download the merged result and upload it as a new parent in a new session.
- **Map (plan) view:** always uses *Simple Merging* — no protocol selector.
- **Section view protocols** (user picks one):
  - *Simple Merging* — child's matching station translated onto the parent's; same coordinate space.
  - *Simple Mirror* — as Simple, but the child sketch is mirrored across the vertical (y) axis before placement.
  - *Displacement* — child is placed in the nearest non-overlapping area (search **right first, then below**); two thin connector lines are drawn from the parent station to the child station to show the topological connection.
- **Settings scope:** rotation, scale, line width, text size apply to the *whole merged result*. Oversized merges auto-rescale to fit the standard PDF page.
- **Errors:** an invalid/not-found station ID shows an inline error and blocks PDF generation until fixed.
- Screenshot placeholders (exact comment syntax):
  - `<!-- SCREENSHOT: imgs/merge-ui.png — merge section: child map/section upload + parent & child station-ID fields + protocol selector -->`
  - `<!-- SCREENSHOT: imgs/merge-mirror.png — section rendered with Simple Mirror protocol -->`
  - `<!-- SCREENSHOT: imgs/merge-displacement.png — section rendered with Displacement protocol showing connector lines -->`
- Footer link: `Back to [Web App Documentation](README.md).`

- [ ] **Step 2: Write `docs/web/survey-merging.it.md` (Italian mirror)**

Same content in Italian. Placeholder paths are identical (`imgs/...`). Footer: `Torna alla [Documentazione Web App](README.it.md).`

- [ ] **Step 3: Verify against source spec and check links/placeholders**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
grep -c "SCREENSHOT" docs/web/survey-merging.md docs/web/survey-merging.it.md
grep -oE '\]\(([^)]+)\)' docs/web/survey-merging.md
```
Expected: 3 placeholders in each file; `README.md` link present and resolves. Re-read `conductor/archive/pdf_merging_20260525/spec.md` and confirm every protocol and the numeric-ID rule are represented.

- [ ] **Step 4: Commit**

```bash
git add docs/web/survey-merging.md docs/web/survey-merging.it.md
git commit -m "docs(web): document survey merging feature (EN+IT)"
```

---

### Task 3: Satellite maps & export doc (EN + IT)

**Files:**
- Create: `docs/web/satellite-maps.md`
- Create: `docs/web/satellite-maps.it.md`

**Sources:** `conductor/archive/merged_satellite_map_20260527/spec.md`, `conductor/archive/offline_kmz_export_20260612/spec.md`, root README ToDo note on the JSON workflow.

**Interfaces:**
- Consumes: linked from `docs/web/README.md` (Task 1) and root README (Task 6).

- [ ] **Step 1: Write `docs/web/satellite-maps.md` (English)**

Required content (facts from the sources — include each point):
- Language-switch header for this file pair.
- Title `# Satellite Maps & Export`.
- **Single-survey overlay:** add known GPS points for survey stations to georeference the map (the more points, the better the fit). Generate the satellite view.
- **Merged-survey rendering:** when a child survey has been merged on the Survey Plot page, the satellite map renders the merged result automatically.
- **Multiple surveys on one view:** export a sketch as JSON, then re-import that JSON alongside new surveys to draw several sketches on the same satellite view.
- **Outputs:** an interactive HTML map; a KML file for 3D viewing in Google Earth; and a **KMZ** map.
- **KMZ for offline apps:** the KMZ is built for offline use in **Locus Map** and **OsmAnd**. Explain the why: the older per-segment KML emitted thousands of placemarks (~6,211 for one survey) and froze Locus; the KMZ chains 2-point segments into a handful of polylines per feature type (down to single/double-digit placemark counts), so it opens quickly. KMZ generation makes zero network calls. The KMZ is built from *all* loaded JSON maps (matching the HTML map's combine behavior).
- **Accepted limitation:** in OsmAnd, water areas may render as outlines rather than filled; Locus renders them filled. The satellite *imagery* itself is provided by the map app's own offline maps — CaveSketch only delivers the cave vectors.
- Screenshot placeholders:
  - `<!-- SCREENSHOT: imgs/satellite-multi-survey.png — satellite view with multiple surveys drawn from JSON re-import -->`
  - `<!-- SCREENSHOT: imgs/kmz-in-locus.png — exported KMZ opened in Locus Map -->`
- Footer link: `Back to [Web App Documentation](README.md).`

- [ ] **Step 2: Write `docs/web/satellite-maps.it.md` (Italian mirror)**

Same content in Italian. Identical placeholder paths. Footer: `Torna alla [Documentazione Web App](README.it.md).`

- [ ] **Step 3: Verify against sources and check links/placeholders**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
grep -c "SCREENSHOT" docs/web/satellite-maps.md docs/web/satellite-maps.it.md
grep -niE "locus|osmand|kmz|json" docs/web/satellite-maps.md | head
```
Expected: 2 placeholders per file; KMZ/Locus/OsmAnd/JSON all mentioned. Confirm the JSON re-import workflow and the KMZ-freeze rationale are present.

- [ ] **Step 4: Commit**

```bash
git add docs/web/satellite-maps.md docs/web/satellite-maps.it.md
git commit -m "docs(web): document satellite maps, multi-survey, and KMZ export (EN+IT)"
```

---

### Task 4: Android user guide (EN + IT)

**Files:**
- Create: `docs/android/README.md`
- Create: `docs/android/README.it.md`

**Sources:** `android/DEVLOG.md`, `android/RELEASE.md`, `conductor/product.md`, `docs/mobile-app/umbrella-spec.md`. Existing screenshots: `docs/mobile-app/screenshots_v1/` (`survey_1.jpg`–`survey_4.jpg`, `satellite_1.jpg`–`satellite_3.jpg`, `about.jpg`).

**Interfaces:**
- Produces: `docs/android/` directory; linked from root README (Task 6) and references `architecture.md` (Task 5).

- [ ] **Step 1: Write `docs/android/README.md` (English)**

Required content:
- Language-switch header for this file pair.
- Title `# CaveSketch for Android`.
- **What it is:** an offline-capable native Android app that runs the same rendering engine as the web app — generate PDF surveys and georeferenced satellite maps on your phone, without a desktop.
- **Install (from GitHub Releases):**
  1. Download `CaveSketch-x.y.z.apk` from the repo's Releases page.
  2. Tap it; when Android asks, allow installs from this source (Settings → Apps → Special access → Install unknown apps).
  3. Tap Install.
  4. **Upgrades:** download a newer `CaveSketch-x.y.z.apk` and install over the top — settings and app data are preserved (same signing key required).
- **The three screens:**
  - *Survey Plot* — upload DXF (map and/or section), adjust settings (scale, rotation, text size, line width…), merge a child survey, generate the PDF preview, and Save/Share. Reference `screenshots_v1/survey_1.jpg`–`survey_4.jpg`.
  - *Satellite Map* — add GPS points to georeference, optional rotation, import additional surveys as JSON, export KMZ + HTML, and preview the map online. Reference `screenshots_v1/satellite_1.jpg`–`satellite_3.jpg`.
  - *About* — app info and a link to the public repository. Reference `screenshots_v1/about.jpg`.
- **Offline behavior:** PDF generation and KMZ export work fully offline; satellite imagery / the HTML map preview require a network connection.
- Image references use relative paths from `docs/android/` to the screenshots, e.g. `![Survey Plot](../mobile-app/screenshots_v1/survey_1.jpg)`.
- Placeholder for any new shot: `<!-- SCREENSHOT: imgs/ (create docs/android/imgs/ if maintainer supplies updated screenshots) -->` — only add this note once, near the screenshots section.
- **For contributors:** link `See [Architecture & Tech Stack](architecture.md) to build or contribute.`
- Footer: `Back to the [project README](../../README.md).`

- [ ] **Step 2: Verify screenshot paths exist**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
ls docs/mobile-app/screenshots_v1/
grep -oE '\]\(([^)]+)\)' docs/android/README.md
```
Expected: every `../mobile-app/screenshots_v1/*.jpg` referenced actually exists in the listing; `architecture.md` link present (created in Task 5).

- [ ] **Step 3: Write `docs/android/README.it.md` (Italian mirror)**

Same content in Italian. Same relative image paths. Contributor link: `Vedi [Architettura e Stack Tecnologico](architecture.it.md)`. Footer: `Torna al [README del progetto](../../README.it.md).`

- [ ] **Step 4: Commit**

```bash
git add docs/android/README.md docs/android/README.it.md
git commit -m "docs(android): add Android user guide (EN+IT)"
```

---

### Task 5: Android architecture / contributor doc (EN + IT)

**Files:**
- Create: `docs/android/architecture.md`
- Create: `docs/android/architecture.it.md`

**Sources:** `conductor/tech-stack.md`, `android/DEVLOG.md`, `android/RELEASE.md`, and the `android/` source tree (`android/app/src/main/java/com/cavesketch/app/...`, `android/app/src/main/python/`).

**Interfaces:**
- Consumes: linked from `docs/android/README.md` (Task 4) and root README (Task 6).

- [ ] **Step 1: Write `docs/android/architecture.md` (English)**

Required content (facts from the sources — include each point):
- Language-switch header for this file pair.
- Title `# Android App — Architecture & Tech Stack`.
- **Stack:** Kotlin; Jetpack Compose (dark Material3 theme); Chaquopy 17 embedding a Python 3.13 interpreter; native Android `PdfRenderer` for displaying generated PDFs; WebView (Leaflet/Folium) for the satellite map preview.
- **Layering (top to bottom):**
  - Compose **screens** (`ui/SurveyPlotScreen.kt`, `ui/SatelliteScreen.kt`, `ui/AboutScreen.kt`) → **ViewModels** (`ui/SurveyPlotViewModel.kt`, `ui/SatelliteViewModel.kt`) → Kotlin **bridges** (`bridge/PythonBridge.kt`, `bridge/SurveyBridge.kt`, `bridge/SatelliteBridge.kt`) → Python **bridge modules** (`android/app/src/main/python/survey_bridge.py`, `satellite_bridge.py`) → the shared **`cave_sketch` core**.
  - The `cave_sketch` core is symlinked into the app (`android/app/src/main/python/cave_sketch`) and kept **Streamlit-free** so it is shared verbatim with the web app.
- **Key constraints & learnings** (from DEVLOG):
  - The core stays untouched and Streamlit-free; the relative symlink avoids the Gradle input/output overlap error and code duplication.
  - **Render-latency optimization:** warm `draw_survey` reduced from ~60.6s to ~3.0s and `parse_dxf` from ~4.5s to ~1.2s on a Samsung S22 — keep this in mind when touching the draw path.
  - **Build requirements:** JDK 17+ (AGP 8.5 / Gradle 9.x); Chaquopy 17.0; ABIs arm64-v8a + x86_64.
  - Imports are pre-warmed at launch and a staged progress indicator manages perceived latency.
- **Build & release:** summarize the steps and link `[android/RELEASE.md](../../android/RELEASE.md)` — keystore setup (`release.jks` + `keystore.properties`, kept out of git), `cd android && ./gradlew assembleRelease` → `android/app/build/outputs/apk/release/app-release.apk`, rename to `CaveSketch-x.y.z.apk`, attach to a GitHub Release tagged `vX.Y.Z`. Bump `versionCode` (must increase) and `versionName` in `android/app/build.gradle` for new versions.
- **Quality gates:** Python — ruff, mypy, pytest; Kotlin — unit tests under `android/app/src/test/...` (ViewModels, utils, UI components).
- Footer: `Back to the [Android user guide](README.md).`

- [ ] **Step 2: Verify referenced source paths and links exist**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
ls android/app/src/main/java/com/cavesketch/app/bridge/ android/app/src/main/python/
test -f android/RELEASE.md && echo "RELEASE.md ok"
grep -oE '\]\(([^)]+)\)' docs/android/architecture.md
```
Expected: the bridge/python files named in the doc exist; `android/RELEASE.md` exists; the `../../android/RELEASE.md` and `README.md` links resolve.

- [ ] **Step 3: Write `docs/android/architecture.it.md` (Italian mirror)**

Same content in Italian. Same code paths and links (link to `../../android/RELEASE.md` and `README.it.md`). Footer: `Torna alla [Guida utente Android](README.it.md).`

- [ ] **Step 4: Commit**

```bash
git add docs/android/architecture.md docs/android/architecture.it.md
git commit -m "docs(android): add architecture & tech-stack contributor doc (EN+IT)"
```

---

### Task 6: Restructure root READMEs as landing pages (EN + IT)

**Files:**
- Modify: `README.md`
- Modify: `README.it.md`

**Interfaces:**
- Consumes: all docs created in Tasks 1–5 (links must resolve).

- [ ] **Step 1: Read the current root READMEs**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
cat README.md README.it.md
```
Note the sections to preserve: title/badges/language switch, value prop, the TopoDroid DXF-export instructions (with `imgs/` screenshots), the developer setup, and the ToDo list.

- [ ] **Step 2: Rewrite `README.md` (English)**

Keep: badges, language-switch line, logo/intro, the **TopoDroid DXF export** how-to section (with its `imgs/*.jpg` images), and the **For Developers** dev-setup section. Restructure the rest to:
- **Two ways to use CaveSketch:**
  - 🌐 **Web app** — live at https://cavesketch.streamlit.app/ . Detailed guides: `[Web App Documentation](docs/web/README.md)`.
  - 📱 **Android app** — install the `.apk` from Releases. See `[CaveSketch for Android](docs/android/README.md)`.
- **Features at a glance** (bulleted, grouped): PDF survey rendering; survey merging (parent+child); satellite maps (single / merged / multiple-via-JSON); KML (Google Earth) + KMZ (Locus Map / OsmAnd) export; offline Android app. Each bullet links to the relevant doc where one exists (`docs/web/survey-merging.md`, `docs/web/satellite-maps.md`, `docs/android/README.md`).
- In **For Developers**, add: `Android contributors: see [Android Architecture & Tech Stack](docs/android/architecture.md).`
- **Trim the ToDo list** — REMOVE the now-shipped items: "Document multi-survey satellite map workflow", "Implement multi-survey merging for PDF surveys", "Add support for .kml export", "Allow adding surveys to an existing .kml file". KEEP: "Add option to color areas, not just draw lines", "Improve satellite HTML map rendering", "Draw and export 3D cave models".

- [ ] **Step 3: Rewrite `README.it.md` (Italian mirror)**

Apply the identical restructure in Italian. Links point to the `.it.md` docs: `docs/web/README.it.md`, `docs/web/survey-merging.it.md`, `docs/web/satellite-maps.it.md`, `docs/android/README.it.md`, `docs/android/architecture.it.md`. Trim the same ToDo items.

- [ ] **Step 4: Verify all root README links resolve**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
for f in README.md README.it.md; do
  echo "== $f =="
  grep -oE '\]\(([^) ]+)\)' "$f" | sed -E 's/^\]\(//; s/\)$//' | while read -r l; do
    case "$l" in http*|\#*) continue;; esac
    [ -e "$l" ] && echo "OK  $l" || echo "MISSING  $l"
  done
done
```
Expected: no `MISSING` lines for local doc/image links (anchors and http links skipped).

- [ ] **Step 5: Commit**

```bash
git add README.md README.it.md
git commit -m "docs: restructure root READMEs as bilingual landing pages"
```

---

### Task 7: Final cross-doc link & placeholder audit

**Files:** none created — verification only.

- [ ] **Step 1: Audit every relative link across all new/changed docs**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
files="README.md README.it.md $(find docs/web docs/android -name '*.md')"
for f in $files; do
  d=$(dirname "$f")
  grep -oE '\]\(([^) ]+)\)' "$f" | sed -E 's/^\]\(//; s/\)$//' | while read -r l; do
    case "$l" in http*|\#*) continue;; esac
    target="$l"; case "$l" in /*) target=".$l";; *) target="$d/$l";; esac
    [ -e "$target" ] && echo "OK  $f -> $l" || echo "MISSING  $f -> $l"
  done
done | grep MISSING || echo "ALL LINKS OK"
```
Expected: `ALL LINKS OK`.

- [ ] **Step 2: Confirm every doc has a language-switch header and bilingual counterpart**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
for f in $(find docs/web docs/android -name '*.md'); do
  head -3 "$f" | grep -q "Available languages\|Available languages\|🇬🇧\|🇮🇹" && echo "HDR OK  $f" || echo "HDR MISSING  $f"
done
```
Expected: every file reports `HDR OK`. Manually confirm each `*.md` has a matching `*.it.md` and vice versa.

- [ ] **Step 3: List remaining screenshot placeholders for the maintainer**

Run:
```bash
cd /Users/bordil/projects/cave_sketch
grep -rn "SCREENSHOT" docs/web docs/android
```
Expected: lists the web merge/satellite placeholders (and any android note). This is the maintainer's checklist of images to supply.

- [ ] **Step 4: Final commit (if the audit prompted any fixes)**

```bash
git add -A
git commit -m "docs: fix cross-doc links and verify bilingual coverage" || echo "nothing to commit"
```

---

## Self-Review

**Spec coverage** (against `docs/superpowers/specs/2026-06-24-readme-docs-update-design.md`):
- Web survey merging → Task 2 ✓
- Merged + multi-survey satellite + KMZ → Task 3 ✓
- Android user guide (3 screens, install, offline) → Task 4 ✓
- Android tech stack/architecture + build/release → Task 5 ✓
- Root READMEs as landing pages + trimmed ToDo → Task 6 ✓
- Bilingual everywhere → enforced per task + Task 7 audit ✓
- New `docs/web/imgs/`, placeholders → Task 1 + Tasks 2–3 ✓
- `docs/mobile-app/` untouched → no task modifies it ✓
- Web docs index → Task 1 ✓

**Placeholder scan:** Screenshot placeholders are intentional (maintainer-supplied images) and use the exact agreed comment syntax; no "TBD"/"TODO"/"implement later" in plan instructions. Content briefs give the actual facts to write, not vague directions.

**Type/path consistency:** Doc filenames are consistent across tasks (`survey-merging.md`, `satellite-maps.md`, `README.md`, `architecture.md` + `.it.md` variants); screenshot paths are relative to each doc's folder (`imgs/...` for web, `../mobile-app/screenshots_v1/...` for android); root README links use folder-relative `docs/web/...` / `docs/android/...` paths.
