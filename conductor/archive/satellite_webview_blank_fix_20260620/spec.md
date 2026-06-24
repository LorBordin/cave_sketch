# Spec: Fix Satellite Map WebView Blank White Render

**Date:** 2026-06-20
**Branch:** `android/phase-2-satellite-map`

## Problem

On the Satellite tab, after **Generate Satellite Map** succeeds, the inline map preview area shows only a blank white box. All other satellite features work — generation completes, and Save/Share HTML/JSON/KMZ function. Only the in-app preview fails to render.

Several fixes were attempted blindly (`loadDataWithBaseURL`, `domStorage`, file access flags). None worked and none could be verified because `MapWebView` has no diagnostics: no `WebChromeClient`, no `WebViewClient` error callbacks, no remote-debugging hook. Every attempt has been a guess.

## Root-Cause Status: UNCONFIRMED

Likely candidates:

- **Leaflet container collapses to zero height.** Folium's map `<div>` uses `height: 100%`, which requires an unbroken `height: 100%` chain from `html`/`body`. Inside a WebView this can collapse to 0.
- **External resources silently fail.** The folium HTML pulls Leaflet JS/CSS from CDNs and Google satellite tiles from `https://mt1.google.com`. All are https and `INTERNET` permission is present, but unverified.
- **`loadDataWithBaseURL` origin behavior.** The fake base `https://appassets.androidplatform.net/` is used without an actual asset loader; its effect on resource loading is unverified.

## Constraints

- **No device on the authoring machine.** The build/run/verify loop happens on a *separate* laptop with a physical Android device attached via Android Studio. The deliverable must be self-sufficient to carry over and execute there.
- Keep the existing inline-preview architecture in `SatelliteScreen` unless evidence forces a change.
- Preserve current behavior of the offline banner and the Save/Share buttons.
- **minSdk 24, compileSdk 34** — all WebView APIs used are available at API 24.
- **Do not modify map generation** (Python/folium) — generation already succeeds.

## Approach: Instrument First, Then Minimal Targeted Fix

### Phase A — Instrumentation

Modify `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt`:

1. `WebView.setWebContentsDebuggingEnabled(true)` (debug builds) — enables `chrome://inspect`.
2. `WebChromeClient.onConsoleMessage` — forward every JS console message to Logcat under tag `MapWebView`.
3. `WebViewClient` with:
   - `onReceivedError` — log failed main-frame and subresource loads.
   - `onReceivedHttpError` — log non-2xx responses for subresources.
   - `onPageFinished` — log completion and inject a JS probe reporting `document.body` size and the Leaflet container's computed height.

No behavioral change — this phase only adds visibility.

### Phase B — Observe on Device

On the device laptop:
1. Build, run, reproduce the blank box.
2. Read Logcat (`MapWebView` tag) and open `chrome://inspect` against the WebView.
3. Classify the cause into one of: `ZERO_HEIGHT`, `RESOURCE_FAILURE`, `ORIGIN_ERROR`, `OTHER`.

### Phase C — Apply the Minimal Fix

Apply **only** the branch matching the observed cause:

- **C1 — `ZERO_HEIGHT`:** Inject CSS height chain + dispatch `resize` event so Leaflet recalculates its size. Keep CSS-inject + resize in the final code (it is the fix, not a probe).
- **C2 — `RESOURCE_FAILURE`:** Set `mixedContentMode = MIXED_CONTENT_COMPATIBILITY_MODE` if a subresource fails over http on an https-origin page.
- **C3 — `ORIGIN_ERROR`:** Fall back to `file://` URL with `allowFileAccess = true`. Escalate to `WebViewAssetLoader` only if `file://` also fails.

### Phase D — Verify on Device

- Re-run on device; confirm satellite imagery + cave overlay render in the preview.
- Confirm offline path still shows the banner and Save/Share buttons still work.
- Remove the temporary size-probe; retain the error/console callbacks.

## TDD Deviation

WebView rendering of a network-dependent folium map cannot be unit-tested on the JVM. Verification is **manual, on-device**, via Logcat and `chrome://inspect`. This is a deliberate, documented deviation from TDD driven by the device-only nature of the bug.

## Files Touched

- `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt` (instrumentation in Phase A; targeted fix in Phase C).
- Possibly `SatelliteScreen.kt` only if Phase C reveals a container-height issue in the Compose layout.
- `android/app/build.gradle` only if C3 escalation to `WebViewAssetLoader` is needed.

## Acceptance Criteria

- The generated folium map (satellite tiles + cave overlay) is visible in the inline preview on a physical device when online.
- The offline banner and all three Save/Share buttons remain functional.
- `MapWebView` retains durable diagnostics (console + error callbacks) so any future regression is observable.
