# Plan: Documentation Overhaul (README + Nested Docs)

> Source of truth for this track. Status markers: `[ ]` todo, `[~]` in progress,
> `[x]` done (append the 7-char commit SHA when complete). This is a
> documentation-only track: the workflow's TDD/coverage gates do not apply to
> `.md`/`.json` files (excluded per `workflow.md`); each task's verification is a
> relative-link / placeholder / content check against the cited source specs.

## Global Constraints

- Fully bilingual: every nested doc has `*.md` (EN) and `*.it.md` (IT) counterparts.
- Language-switch header on every doc:
  `🌍 Available languages: [🇬🇧 English](FILE.md) | [🇮🇹 Italiano](FILE.it.md)`.
- No application code modified. `docs/mobile-app/` NOT modified.
- New web screenshots → `docs/web/imgs/`. Android docs reference existing
  `docs/mobile-app/screenshots_v1/`. Original DXF images stay in `imgs/`.
- Screenshot placeholder syntax: `<!-- SCREENSHOT: <path> — <description> -->`.
- Authoring order per doc: English first, then Italian mirror.
- Facts only from: `conductor/archive/pdf_merging_20260525/spec.md`,
  `conductor/archive/merged_satellite_map_20260527/spec.md`,
  `conductor/archive/offline_kmz_export_20260612/spec.md`, `android/DEVLOG.md`,
  `android/RELEASE.md`, `conductor/tech-stack.md`, `conductor/product.md`.

---

## Phase 1: Web Documentation [checkpoint: 3388355]

- [x] Task: Web docs index + image folder dd292b0
    - [ ] Create `docs/web/imgs/.gitkeep` (empty, to track the folder)
    - [ ] Create `docs/web/README.md` (EN): language-switch header; title
      `# CaveSketch — Web App Documentation`; one-paragraph overview + live link
      https://cavesketch.streamlit.app/ ; "Guides" list linking
      `survey-merging.md` and `satellite-maps.md`; back-link to `../../README.md`
    - [ ] Create `docs/web/README.it.md` (IT mirror): links use `.it.md` siblings
      and `../../README.it.md`
    - [ ] Verify: `grep -oE '\]\(([^)]+)\)' docs/web/README.md` — listed targets
      exist or are created in this phase
    - [ ] Commit: `docs(web): add web docs index and image folder`

- [x] Task: Survey merging doc (EN + IT) 37627ee
    - [ ] Create `docs/web/survey-merging.md` (EN) per spec FR-2 — cover: what
      merging does; numeric-only station IDs (letter IDs rejected); one ID pair
      for both views; one child per session; map = Simple Merging; section
      protocols Simple / Mirror / Displacement (right-first-then-below, connector
      lines); whole-result settings + auto-rescale; inline error on bad ID
    - [ ] Add 3 screenshot placeholders: `imgs/merge-ui.png`,
      `imgs/merge-mirror.png`, `imgs/merge-displacement.png`
    - [ ] Create `docs/web/survey-merging.it.md` (IT mirror), identical
      placeholder paths
    - [ ] Verify: 3 `SCREENSHOT` comments per file; `README.md` back-link
      resolves; re-read `conductor/archive/pdf_merging_20260525/spec.md` and
      confirm all protocols + the numeric-ID rule are represented
    - [ ] Commit: `docs(web): document survey merging feature (EN+IT)`

- [x] Task: Satellite maps & export doc (EN + IT) d36a9df
    - [ ] Create `docs/web/satellite-maps.md` (EN) per spec FR-3 — cover:
      single-survey overlay via GPS points; merged-survey rendering; multiple
      surveys via JSON export → re-import; outputs HTML + KML + KMZ; KMZ for
      Locus Map / OsmAnd with the segment-chaining freeze-fix rationale, zero
      network calls, built from all loaded JSON maps; OsmAnd polygon-fill caveat
    - [ ] Add 2 screenshot placeholders: `imgs/satellite-multi-survey.png`,
      `imgs/kmz-in-locus.png`
    - [ ] Create `docs/web/satellite-maps.it.md` (IT mirror)
    - [ ] Verify: 2 placeholders per file; KMZ/Locus/OsmAnd/JSON all mentioned;
      JSON re-import workflow + KMZ rationale present
    - [ ] Commit: `docs(web): document satellite maps, multi-survey, and KMZ export (EN+IT)`

- [x] Task: Conductor - User Manual Verification 'Web Documentation' (Protocol in workflow.md) 3388355

## Phase 2: Android Documentation [checkpoint: 3388355]

- [x] Task: Android user guide (EN + IT) c622157
    - [ ] Create `docs/android/README.md` (EN) per spec FR-4 — cover: what the app
      is (offline native, same engine); install from Releases (allow unknown
      sources; upgrade-over-top, settings preserved, same signing key); the three
      screens (Survey Plot, Satellite Map, About); offline behavior (PDF + KMZ
      offline, satellite/HTML preview need network)
    - [ ] Reference existing screenshots via `../mobile-app/screenshots_v1/`
      (`survey_1..4.jpg`, `satellite_1..3.jpg`, `about.jpg`); link
      `architecture.md`; back-link `../../README.md`
    - [ ] Verify: `ls docs/mobile-app/screenshots_v1/` — every referenced jpg
      exists; `architecture.md` link present
    - [ ] Create `docs/android/README.it.md` (IT mirror), same image paths
    - [ ] Commit: `docs(android): add Android user guide (EN+IT)`

- [x] Task: Android architecture / contributor doc (EN + IT) c2aec70
    - [ ] Create `docs/android/architecture.md` (EN) per spec FR-5 — cover: stack
      (Kotlin, Compose dark Material3, Chaquopy 17 + Python 3.13, native
      PdfRenderer, WebView); layering (screens → ViewModels → bridges → python
      bridge modules → symlinked Streamlit-free `cave_sketch` core); learnings
      (symlink trick; latency ~60.6s→~3.0s draw, ~4.5s→~1.2s parse; JDK 17+ /
      Chaquopy 17 / ABIs arm64-v8a + x86_64); build & release linking
      `../../android/RELEASE.md`; quality gates (ruff/mypy/pytest + Kotlin tests)
    - [ ] Verify: `ls android/app/src/main/java/com/cavesketch/app/bridge/` and
      `android/app/src/main/python/` — named files exist; `android/RELEASE.md`
      exists; links resolve
    - [ ] Create `docs/android/architecture.it.md` (IT mirror), same paths/links
    - [ ] Commit: `docs(android): add architecture & tech-stack contributor doc (EN+IT)`

- [x] Task: Conductor - User Manual Verification 'Android Documentation' (Protocol in workflow.md) 3388355

## Phase 3: Root READMEs + Final Audit [checkpoint: 3388355]

- [x] Task: Restructure root READMEs as landing pages (EN + IT) fed260e
    - [ ] Read current `README.md` / `README.it.md`; note sections to preserve
      (badges, language switch, intro, TopoDroid DXF export how-to with `imgs/`,
      dev setup, ToDo list)
    - [ ] Rewrite `README.md` per spec FR-6: keep preserved sections; add "Two
      ways to use CaveSketch" (🌐 web live link + `docs/web/README.md`; 📱 Android
      + `docs/android/README.md`); add "Features at a glance" linking
      `docs/web/survey-merging.md`, `docs/web/satellite-maps.md`,
      `docs/android/README.md`; add Android-contributors pointer to
      `docs/android/architecture.md`; trim shipped ToDo items (multi-survey
      satellite docs, multi-survey PDF merging, .kml export, merge-into-existing
      -kml); keep area coloring, satellite HTML rendering, 3D models
    - [ ] Rewrite `README.it.md` (IT mirror), links to `.it.md` docs, same trim
    - [ ] Verify: all local links in both READMEs resolve (skip http/# anchors)
    - [ ] Commit: `docs: restructure root READMEs as bilingual landing pages`

- [x] Task: Final cross-doc link & placeholder audit fed260e
    - [ ] Audit every relative link across `README*.md`, `docs/web/**`,
      `docs/android/**` — expect no missing local targets
    - [ ] Confirm every nested doc has a language-switch header and a matching
      EN/IT counterpart
    - [ ] List remaining screenshot placeholders: `grep -rn "SCREENSHOT" docs/web
      docs/android` — reconcile against `screenshots-needed.md`
    - [ ] Commit any audit fixes: `docs: fix cross-doc links and verify bilingual coverage`

- [x] Task: Conductor - User Manual Verification 'Root READMEs + Final Audit' (Protocol in workflow.md) 3388355
