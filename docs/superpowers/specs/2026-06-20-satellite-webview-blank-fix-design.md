# Fix: Satellite Map WebView renders blank white

**Date:** 2026-06-20
**Status:** Design approved
**Branch:** `android/phase-2-satellite-map`

## Problem

On the Satellite tab, after **Generate Satellite Map** succeeds, the inline map
preview area shows only a blank white box (see `to_fix.md`). All other satellite
features work — generation completes, and Save/Share HTML/JSON/KMZ function. Only
the in-app preview fails to render.

Several fixes have already been attempted blindly (switching from `loadUrl("file://…")`
to `loadDataWithBaseURL`, enabling `domStorage` and file access). None worked,
and — critically — **none could be verified**, because the current `MapWebView`
has no diagnostics: no `WebChromeClient`, no `WebViewClient` error callbacks, and
no remote-debugging hook. Every attempt has been a guess.

## Root-cause status: UNCONFIRMED

We are deliberately **not** committing to a single root cause. The likely
candidates, given the code:

- **Leaflet container collapses to zero height.** Folium's map `<div>` uses
  `height: 100%`, which requires an unbroken `height: 100%` chain from
  `html`/`body`. Inside a WebView this can collapse to 0 → blank.
- **External resources silently fail.** The folium HTML pulls Leaflet JS/CSS from
  CDNs and Google satellite tiles from `https://mt1.google.com`. All are https and
  `INTERNET` permission is present, so mixed-content/cleartext is *unlikely* — but
  unverified.
- **`loadDataWithBaseURL` origin behavior.** The current fake base
  `https://appassets.androidplatform.net/` is the `WebViewAssetLoader` authority
  but is used here without an actual asset loader; its effect on resource loading
  is unverified.

The plan's first job is to make the real cause **observable on a physical device**,
then apply the smallest fix the evidence supports.

## Constraints

- **No device on this machine.** The build/run/verify loop happens on a *separate*
  laptop with a physical Android device attached via Android Studio. The deliverable
  must be self-sufficient to carry over and execute there.
- Keep the existing architecture (inline preview in `SatelliteScreen`) unless the
  evidence forces a change.
- Preserve current behavior of the offline banner and the Save/Share buttons.

## Approach: Instrument first, then minimal targeted fix

### Phase A — Instrumentation (observability)

Modify `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt`:

1. **`WebView.setWebContentsDebuggingEnabled(true)`** (guarded to debug builds) so
   the WebView is inspectable from the laptop via `chrome://inspect`, exposing the
   live DOM, console, and network tabs for the loaded page.
2. **`WebChromeClient.onConsoleMessage`** — forward every JS console message
   (level, message, source, line) to Logcat under a stable tag (e.g. `MapWebView`).
3. **`WebViewClient`** with:
   - `onReceivedError` — log failed main-frame and subresource loads (URL + error).
   - `onReceivedHttpError` — log non-2xx responses for subresources (e.g. CDN/tiles).
   - `onPageFinished` — log completion and inject a probe that reports
     `document.body` size and the Leaflet container's computed height, so a
     zero-height container is immediately visible in Logcat.

No behavioral change yet — this phase only adds visibility.

### Phase B — Observe on device

On the device laptop:
1. Build, run, reproduce the blank box.
2. Read Logcat (`MapWebView` tag) and open `chrome://inspect` against the WebView.
3. Classify the cause from evidence into one of the pre-staged fixes below.

### Phase C — Apply the minimal fix the evidence points to

Pre-staged fixes, to apply *only* the one(s) matching the observed cause:

- **C1 — Zero-height container** (if the height probe reports ~0, or DOM shows a
  collapsed map div): inject a small CSS/JS shim after load (or wrap the HTML) to
  force `html, body, .folium-map` to `height: 100%` / explicit pixel height, and
  call Leaflet's `map.invalidateSize()` once laid out. Confirm the WebView itself
  has a real height inside the `verticalScroll` Column (the fixed `360.dp` should
  suffice, but verify).
- **C2 — Resource load failure** (if `onReceivedError`/`onReceivedHttpError` fire
  for CDN/tiles, or console shows blocked requests): address the specific failure —
  e.g. set `mixedContentMode` if any subresource is http, or correct the load
  strategy/base URL so external https resources resolve.
- **C3 — Origin/load-strategy issue** (if console shows security/origin errors):
  fall back to the simplest strategy that works — `loadUrl("file://…")` with
  `allowFileAccess = true`, or escalate to `WebViewAssetLoader` (deferred Approach 2)
  if a proper secure origin is required.

### Phase D — Verify on device

- Re-run on the device; confirm the satellite imagery + cave overlay render in the
  preview.
- Confirm offline path still shows the banner and Save/Share buttons still work.
- Once confirmed, remove or quiet any temporary probe logging that isn't worth
  keeping; keep the error/console callbacks (they're cheap and useful).

## Out of scope

- Re-architecting the preview into a full-screen route (Approach 3) — only if C1–C3
  fail to produce a working inline preview.
- Adopting `WebViewAssetLoader` wholesale (Approach 2) — only as the C3 escalation.
- Any change to map *generation* (Python/folium) — generation already succeeds.

## Files touched

- `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt`
  (instrumentation in Phase A; targeted fix in Phase C).
- Possibly `SatelliteScreen.kt` only if Phase C reveals a container-height issue
  originating in the Compose layout.

## Success criteria

- The generated folium map (satellite tiles + cave overlay) is visible in the inline
  preview on a physical device when online.
- The offline banner and all three Save/Share buttons remain functional.
- `MapWebView` retains durable diagnostics (console + error callbacks) so any future
  regression is observable rather than a blank guess.
