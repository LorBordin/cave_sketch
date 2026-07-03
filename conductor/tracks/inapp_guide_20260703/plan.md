# Plan: In-App Offline User Guide (Android)

## Phase 1: Bundle Guide Assets [checkpoint: 2ab8a7a]

- [x] Task: Prepare guide Markdown files for in-app use [1a30d3b]
    - [x] Create `assets/guide/` directory structure (`assets/guide/screenshots/`, `assets/guide/`)
    - [x] Copy screenshot JPEGs from `docs/mobile-app/screenshots_v1/` into `assets/guide/screenshots/`
    - [x] Adapt `docs/android/README.md` → `assets/guide/guide_en.md`: strip Installation, For Contributors, external-only links; rewrite image paths to `screenshots/...`
    - [x] Adapt `docs/android/README.it.md` → `assets/guide/guide_it.md`: same adaptations for Italian
    - [x] Create `assets/guide/guide.css` with Material 3 dark-theme-compatible styling for the rendered HTML

- [x] Task: Create Markdown-to-HTML conversion utility [2ad5ed7]
    - [x] Write tests for a `GuideRenderer` utility that loads a Markdown asset file and produces a complete HTML string with embedded CSS link and correct base URL for images
    - [x] Implement `GuideRenderer` in `util/GuideRenderer.kt` that reads the Markdown asset, converts to HTML (using a lightweight library or simple regex-based conversion), and wraps with the CSS stylesheet reference

- [x] Task: Conductor - User Manual Verification 'Phase 1: Bundle Guide Assets' (Protocol in workflow.md)

## Phase 2: WebView Guide Component [checkpoint: 0e36290]

- [x] Task: Create GuideWebView composable component [8c8de28]
    - [x] Write tests for the composable: verifies WebView is created with correct settings (JavaScript disabled, no external loads), and that `loadDataWithBaseURL` is called with the rendered HTML
    - [x] Implement `GuideWebView` composable in `ui/components/GuideWebView.kt` that accepts an HTML string, renders it in an Android `WebView`, intercepts external URL clicks to open in system browser, and configures offline-only operation

- [x] Task: Conductor - User Manual Verification 'Phase 2: WebView Guide Component' (Protocol in workflow.md)

## Phase 3: About Screen Integration [checkpoint: 0d6597d]

- [x] Task: Add language toggle and accordion UI to AboutScreen [9b78b73]
    - [x] Write tests for the updated AboutScreen: verify the User Guide accordion header is displayed, expand/collapse toggles content visibility, and language toggle switches between EN/IT
    - [x] Update `AboutScreen.kt` to add a "User Guide" expandable accordion section below existing content, with a 🇬🇧/🇮🇹 language toggle in the header and animated expand/collapse
    - [x] Integrate `GuideRenderer` and `GuideWebView` inside the accordion body: load the selected language's Markdown, render to HTML, and display in the WebView
    - [x] Handle nested scrolling: configure the WebView with a fixed or adaptive height to avoid scroll conflicts with the parent Column

- [x] Task: Conductor - User Manual Verification 'Phase 3: About Screen Integration' (Protocol in workflow.md)

## Phase 4: Polish & Final Verification

- [ ] Task: End-to-end polish and edge cases
    - [ ] Verify all 8 screenshots render inline in airplane mode
    - [ ] Test language toggle does not reset scroll position unexpectedly
    - [ ] Ensure external links (GitHub) open in system browser, not inside the WebView
    - [ ] Review CSS styling for readability (font sizes, spacing, image sizing) on various screen sizes
    - [ ] Run full test suite and verify >80% coverage for new code

- [ ] Task: Conductor - User Manual Verification 'Phase 4: Polish & Final Verification' (Protocol in workflow.md)
