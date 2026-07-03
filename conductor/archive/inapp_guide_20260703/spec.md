# Spec: In-App Offline User Guide (Android)

## Overview

Embed the existing CaveSketch Android user guide directly into the app so that users can consult it offline at any time. The guide will be accessible from the **About** screen as an expandable accordion section, rendered from bundled Markdown files via a WebView. Both English and Italian versions of the guide will be included, with a language toggle that the user can switch between.

## Functional Requirements

### FR-1: Bundled Guide Content

- The guide content (currently `docs/android/README.md` and `docs/android/README.it.md`) is adapted into **self-contained Markdown files** bundled in the APK's `assets/` directory.
- All referenced screenshot images (survey_1–4.jpg, satellite_1–3.jpg, about.jpg from `docs/mobile-app/screenshots_v1/`) are **copied into `assets/`** and image paths in the Markdown files are rewritten to reference them locally (e.g., `file:///android_asset/guide/screenshots/survey_1.jpg`).
- The guide Markdown files must **strip sections not relevant to end-users** (e.g., "For Contributors", "Installation" from APK, external links that won't work offline) and may lightly reword content to fit the in-app context.

### FR-2: About Screen Integration (Accordion)

- The existing **About screen** retains its current layout (logo, app name, subtitle, version chip, GitHub button).
- A new **"User Guide" expandable section** is added below the existing content. When collapsed, it shows a header row (e.g., 📖 icon + "User Guide" text + expand/collapse chevron). When expanded, it reveals a WebView rendering the guide Markdown.
- The accordion expands/collapses with a smooth animation.

### FR-3: Markdown Rendering via WebView

- The bundled Markdown file is **converted to HTML at render time** (or pre-converted to HTML at build time) and displayed in an Android `WebView`.
- The WebView uses a **local CSS stylesheet** (also bundled in `assets/`) to style the guide consistently with the app's Material 3 dark theme.
- The WebView is configured for **offline-only operation**: no external network requests, JavaScript disabled (unless needed for rendering), and no navigation to external URLs — external links open in the system browser via `shouldOverrideUrlLoading`.
- Images referenced in the Markdown are served from `assets/` and displayed inline.

### FR-4: Language Toggle

- A language toggle (e.g., a segmented button or icon-based selector showing 🇬🇧/🇮🇹 flags) is displayed **within the User Guide section header** or at the top of the expanded guide area.
- Toggling the language **reloads the WebView** with the corresponding Markdown/HTML file (English or Italian).
- The selected language preference is **not persisted** across app restarts (defaults to English each time, keeping it simple).

### FR-5: Scrollable Guide

- The rendered guide content is scrollable within the WebView.
- The About screen itself remains scrollable, with the WebView taking a fixed or adaptive height within the accordion to avoid nested scroll conflicts.

## Non-Functional Requirements

### NFR-1: APK Size Impact

- The 8 bundled JPEG screenshots are ~500 KB total. Combined with the Markdown/HTML and CSS, the total guide asset footprint should be **under 1 MB**.

### NFR-2: Offline-First

- The entire guide, including images, must be fully functional with **no network connectivity**.

### NFR-3: Maintainability

- The guide content is authored in Markdown, making it easy to update alongside the existing `docs/android/` files. A build-time or manual copy step should keep the bundled assets in sync.

## Acceptance Criteria

1. The About screen shows a "User Guide" accordion section below the existing content.
2. Expanding the section displays the full user guide with inline screenshots, rendered in a WebView.
3. The 🇬🇧/🇮🇹 language toggle switches between English and Italian guide content.
4. The guide is fully readable and all images load when the device is in airplane mode.
5. External links (e.g., GitHub repo) in the guide open in the system browser.
6. The accordion expands and collapses with a smooth animation.
7. The guide content is scrollable without conflicting with the parent screen scroll.

## Out of Scope

- Search functionality within the guide.
- Automatic sync of guide content from the `docs/` directory (manual copy step is acceptable).
- Persisting the user's language preference across sessions.
- Deep-linking to specific guide sections from other parts of the app.
