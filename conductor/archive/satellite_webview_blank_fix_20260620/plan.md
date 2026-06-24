# Plan: Fix Satellite Map WebView Blank White Render

> **TDD Deviation:** WebView rendering of a network-dependent folium map cannot be unit-tested on the JVM. All verification is manual, on-device. No test files are produced by this plan. This deviation is documented in `spec.md`.

## Phase 1: Instrument MapWebView for Observability [checkpoint: becf1a3]

- [x] Task: Instrument MapWebView with diagnostics [f305bd0]
    - [x] Overwrite `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt` with the instrumented version:
        - Add `WebView.setWebContentsDebuggingEnabled(true)` (enables `chrome://inspect`)
        - Add `WebChromeClient.onConsoleMessage` → forward every JS console message to Logcat under tag `MapWebView`
        - Add `WebViewClient.onReceivedError` → log failed main-frame and subresource loads (URL + error code + description)
        - Add `WebViewClient.onReceivedHttpError` → log non-2xx responses for subresources
        - Add `WebViewClient.onPageFinished` → inject JS probe that reports `document.body` size and `.folium-map` computed width/height to Logcat
        - Extract `loadHtml(webView, htmlPath)` private function shared by `factory` and `update` (DRY)
        - Keep same public signature: `MapWebView(htmlPath: String, modifier: Modifier = Modifier)`
    - [x] Build on the device laptop (`./gradlew :app:assembleDebug`); confirm `BUILD SUCCESSFUL`
    - [x] Commit:
        ```
        fix(mobile-app): instrument MapWebView with console/error diagnostics

        Adds WebChromeClient console forwarding, WebViewClient error callbacks, a
        post-load size probe, and chrome://inspect remote debugging so the blank
        satellite preview can be diagnosed on-device. DRYs the load logic into loadHtml().
        ```

- [x] Task: Conductor - User Manual Verification 'Phase 1: Instrument MapWebView for Observability' (Protocol in workflow.md)

## Phase 2: Observe the Real Cause on Device [checkpoint: 24850d1]

> **Note:** This phase produces no code change and no commit. It produces a **diagnosis classification** that drives Phase 3 branch selection.

- [x] Task: Reproduce blank box on device and capture diagnostics [d4cadd8]
    - [x] Install on device: `./gradlew :app:installDebug`
    - [x] On device: ensure online (Wi-Fi/4G), Survey tab → generate a plot, Satellite tab → valid GPS point matching a survey station → **Generate Satellite Map** → reproduce blank box
    - [x] Capture Logcat: `adb logcat -s MapWebView:* chromium:* | tee /tmp/mapwebview.log`
    - [x] Re-trigger generation; read captured lines. Classify:
        - `page finished, probe={..., "mapH":0, ...}` → **`ZERO_HEIGHT`**
        - `load error` / `http error` lines for CDN/tile URLs → **`RESOURCE_FAILURE`**
        - console lines mentioning `SecurityError`, `origin`, `cross-origin`, `blocked` → **`ORIGIN_ERROR`**
        - None of the above but healthy sizes → **`OTHER`** (proceed to Chrome DevTools)
    - [x] Open Chrome → `chrome://inspect` → find the app's WebView → **inspect**
        - Elements tab: confirm `.folium-map` computed height (0px → `ZERO_HEIGHT`)
        - Console tab: read errors directly
        - Network tab: re-trigger, look for failed (red) requests (→ `RESOURCE_FAILURE`)
    - [x] Record the classification and key evidence in `docs/mobile-app/phases/phase-2-satellite-map/to_fix.md`:
        ```
        DIAGNOSIS 2026-06-20: <CLASS> — <key evidence line>.
        ```
    - [x] Commit: `docs(mobile-app): record satellite WebView blank-render diagnosis`

- [x] Task: Conductor - User Manual Verification 'Phase 2: Observe the Real Cause on Device' (Protocol in workflow.md)

## Phase 3: Apply the Targeted Fix (Conditional on Phase 2 Diagnosis) [checkpoint: ae2e73d]

> **Branch selection:** Execute **exactly one** of the branches below based on the Phase 2 classification. If diagnosis was `OTHER`, re-run Phase 2 Chrome DevTools and bring the specific evidence back before editing.

- [x] Task: Apply fix branch C1 — `ZERO_HEIGHT`: force container height and reflow Leaflet [9bedac9]
    - **Condition:** Apply only if Phase 2 classified `ZERO_HEIGHT`
    - [x] In `MapWebView.kt`, replace the `onPageFinished` body with:
        1. A `evaluateJavascript` call that injects CSS (`html,body{height:100%;margin:0;padding:0;}` + `.folium-map{position:absolute;top:0;bottom:0;left:0;right:0;height:100%!important;width:100%!important;}`) and dispatches `window.resize`
        2. A second `evaluateJavascript` re-probe that logs `post-fix probe=` with corrected sizes
    - [x] Rebuild and reinstall: `./gradlew :app:installDebug`
    - [x] Re-trigger generation; confirm Logcat shows `post-fix probe={"bodyH":<positive>,"mapH":<positive>}` and map renders
    - [x] Commit:
        ```
        fix(mobile-app): force folium container height + Leaflet reflow in WebView

        Injects a height:100% chain and dispatches a resize event after load so the
        Leaflet map, initialized in a 0px container, recalculates and renders.
        ```

- [ ] Task: Apply fix branch C2 — `RESOURCE_FAILURE`: fix blocked subresource loads
    - **Condition:** Apply only if Phase 2 classified `RESOURCE_FAILURE`
    - [ ] Confirm the failing URL is `http` (mixed content on https-origin page); if `https` fails, verify device connectivity and `INTERNET` permission — no code change applies; stop and report
    - [ ] In `MapWebView.kt`, add `import android.webkit.WebSettings` and inside `WebView(ctx).apply { ... }` after `settings.domStorageEnabled = true`:
        ```kotlin
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
        ```
    - [ ] Rebuild and reinstall: `./gradlew :app:installDebug`
    - [ ] Re-trigger; confirm the previously failing resource now loads (no error line in Logcat) and map renders
    - [ ] Commit:
        ```
        fix(mobile-app): allow mixed-content compatibility for folium WebView assets
        ```

- [ ] Task: Apply fix branch C3 — `ORIGIN_ERROR`: switch to a clean local origin
    - **Condition:** Apply only if Phase 2 classified `ORIGIN_ERROR`
    - [ ] In `MapWebView.kt`, add `settings.allowFileAccess = true` after `settings.domStorageEnabled = true`
    - [ ] Replace the `loadHtml` body to use `webView.loadUrl("file://$htmlPath")` instead of `loadDataWithBaseURL`
    - [ ] Rebuild and reinstall: `./gradlew :app:installDebug`
    - [ ] Re-trigger; if still failing with origin/security errors, escalate to `WebViewAssetLoader`:
        - Add `implementation "androidx.webkit:webkit:1.11.0"` to `android/app/build.gradle`
        - Build an `WebViewAssetLoader` in the `factory`, add `shouldInterceptRequest` override to the `webViewClient`, load via `https://appassets.androidplatform.net/files/<filename>` URL
        - Rebuild and reinstall
    - [ ] Commit:
        ```
        fix(mobile-app): load folium HTML from a clean local origin in WebView
        ```

- [x] Task: Conductor - User Manual Verification 'Phase 3: Apply the Targeted Fix' (Protocol in workflow.md)

## Phase 4: Verify End-to-End and Clean Up Temporary Probes [checkpoint: e3ea355]

- [x] Task: Full manual verification and probe cleanup [af1eabf, 91d1065]
    - [x] On device, online: Survey → generate plot → Satellite → valid GPS point → **Generate Satellite Map**. Confirm:
        - Satellite imagery **and** the cave overlay render in the inline preview
        - Pan/zoom works
        - **Save / Share HTML**, **Save / Share JSON**, **Save / Share KMZ** each open the share sheet
    - [x] Turn off Wi-Fi/data, generate again. Confirm the offline banner shows and Save/Share buttons still work
    - [x] In `MapWebView.kt`, delete the temporary size-probe `evaluateJavascript` block(s) from `onPageFinished`:
        - Keep `onConsoleMessage`, `onReceivedError`, `onReceivedHttpError` (durable diagnostics)
        - If C1 applied: keep the CSS-inject + `resize` dispatch (that is the fix)
        - Keep `setWebContentsDebuggingEnabled(true)` but add `// TODO: guard behind debug build`
    - [x] Rebuild and reinstall: `./gradlew :app:installDebug`. Re-trigger; confirm map still renders (probe removal must not regress the fix)
    - [x] Commit:
        ```
        chore(mobile-app): remove temporary WebView size probe; keep diagnostics
        ```
    - [x] Update `docs/mobile-app/phases/phase-2-satellite-map/to_fix.md`:
        ```
        RESOLVED 2026-06-20: <branch C1/C2/C3> — <one-line root cause>. Preview renders on device.
        ```
    - [x] Commit: `docs(mobile-app): mark satellite WebView blank-render fixed`

- [x] Task: Conductor - User Manual Verification 'Phase 4: Verify End-to-End and Clean Up Temporary Probes' (Protocol in workflow.md)
