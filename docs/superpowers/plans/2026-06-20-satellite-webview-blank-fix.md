# Satellite Map WebView Blank-Render Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the generated folium satellite map render in the in-app `MapWebView` preview instead of a blank white box, by first making the failure observable on a physical device and then applying the smallest evidence-driven fix.

**Architecture:** Instrument the existing `MapWebView` composable with WebView console + error diagnostics and remote-debugging, observe the real cause on a connected Android device, then apply one of three pre-staged minimal fixes (zero-height container / resource-load failure / origin issue). Keep the inline-preview architecture and the exported folium HTML as the single source of truth for the preview.

**Tech Stack:** Kotlin, Jetpack Compose, `AndroidView` + `android.webkit.WebView`, folium/Leaflet HTML, Gradle, `adb` + Chrome `chrome://inspect`.

## Global Constraints

- **No device/emulator on the authoring machine.** All build/run/observe/verify
  steps execute on a **separate laptop** with a physical Android device attached via
  Android Studio + `adb`. Commands below are run there.
- **minSdk 24, compileSdk 34**, applicationId `com.cavesketch.app`. All WebView APIs
  used here (`onReceivedError`/`onReceivedHttpError` with `WebResourceRequest`,
  `evaluateJavascript`, `ConsoleMessage`) are available at API 24.
- **Do not modify map generation** (Python/folium) — generation already succeeds;
  only the in-app rendering is broken.
- **Preserve existing behavior**: the offline banner and the three Save/Share buttons
  in `SatelliteScreen.kt` must remain functional.
- **Root cause is UNCONFIRMED** — Task 3 is conditional on Task 2's observed evidence.
  Apply only the staged fix that matches what you see; do not apply all three.

---

## File Structure

- `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt`
  — the only production file changed. Task 1 adds diagnostics + DRYs the load logic;
  Task 3 adds the targeted fix.
- No automated test file: WebView rendering of a network-dependent folium map cannot
  be unit-tested on the JVM. Verification is **manual, on-device**, via Logcat and
  `chrome://inspect` (Tasks 2 and 4). This is a deliberate, documented deviation from
  TDD driven by the device-only nature of the bug.

---

### Task 1: Instrument `MapWebView` for observability

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt` (full rewrite of the file, 60 lines)

**Interfaces:**
- Consumes: nothing new. Same public signature.
- Produces: `MapWebView(htmlPath: String, modifier: Modifier = Modifier)` — unchanged
  public composable. Now also emits Logcat under tag `MapWebView`:
  - `console [...]` lines from the page's JS console.
  - `load error ...` / `http error ...` lines for failed resources.
  - `page finished, probe=...` line with a JSON blob reporting body and
    `.folium-map` computed width/height.

- [ ] **Step 1: Replace the file with the instrumented version**

Overwrite `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt` with:

```kotlin
package com.cavesketch.app.ui.components

import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import java.io.File

private const val TAG = "MapWebView"

/** Renders a local folium HTML file (the same artifact exported by Save/Share HTML).
 * Instrumented: forwards JS console + resource-load errors to Logcat and enables
 * remote inspection via chrome://inspect, so blank-render causes are observable. */
@Composable
fun MapWebView(htmlPath: String, modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            // Enables chrome://inspect for this app's WebViews. Diagnostic; harmless
            // to leave on, but guard behind a debug flag before a production release.
            WebView.setWebContentsDebuggingEnabled(true)
            WebView(ctx).apply {
                @Suppress("SetJavaScriptEnabled")
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true

                webChromeClient = object : WebChromeClient() {
                    override fun onConsoleMessage(msg: ConsoleMessage): Boolean {
                        Log.d(
                            TAG,
                            "console [${msg.messageLevel()}] ${msg.message()} " +
                                "@ ${msg.sourceId()}:${msg.lineNumber()}",
                        )
                        return true
                    }
                }
                webViewClient = object : WebViewClient() {
                    override fun onReceivedError(
                        view: WebView,
                        request: WebResourceRequest,
                        error: WebResourceError,
                    ) {
                        Log.e(
                            TAG,
                            "load error ${error.errorCode} ${error.description} " +
                                "for ${request.url} (mainFrame=${request.isForMainFrame})",
                        )
                    }

                    override fun onReceivedHttpError(
                        view: WebView,
                        request: WebResourceRequest,
                        response: WebResourceResponse,
                    ) {
                        Log.e(TAG, "http error ${response.statusCode} for ${request.url}")
                    }

                    override fun onPageFinished(view: WebView, url: String?) {
                        view.evaluateJavascript(
                            """(function(){
                                var b=document.body, m=document.querySelector('.folium-map');
                                return JSON.stringify({
                                  bodyW: b?b.clientWidth:-1, bodyH: b?b.clientHeight:-1,
                                  mapFound: !!m,
                                  mapW: m?m.clientWidth:-1, mapH: m?m.clientHeight:-1
                                });
                            })();""".trimIndent(),
                        ) { result -> Log.d(TAG, "page finished, probe=$result") }
                    }
                }
                loadHtml(this, htmlPath)
            }
        },
        update = { webView -> loadHtml(webView, htmlPath) },
    )
}

/** Loads the folium HTML, reusing the existing loadDataWithBaseURL strategy.
 * Extracted so factory and update share one implementation (DRY). */
private fun loadHtml(webView: WebView, htmlPath: String) {
    try {
        val file = File(htmlPath)
        if (file.exists()) {
            webView.loadDataWithBaseURL(
                "https://appassets.androidplatform.net/",
                file.readText(),
                "text/html",
                "UTF-8",
                null,
            )
        } else {
            webView.loadData("Map file not found.", "text/html", "UTF-8")
        }
    } catch (e: Exception) {
        webView.loadData("Error loading map: ${e.message}", "text/html", "UTF-8")
    }
}
```

- [ ] **Step 2: Build on the device laptop**

Run (from the repo's `android/` directory on the laptop with the device):
```bash
./gradlew :app:assembleDebug
```
Expected: `BUILD SUCCESSFUL`. If it fails to compile, fix the reported error before
continuing (most likely a missing import from the list above).

- [ ] **Step 3: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt
git commit -m "fix(mobile-app): instrument MapWebView with console/error diagnostics

Adds WebChromeClient console forwarding, WebViewClient error callbacks, a
post-load size probe, and chrome://inspect remote debugging so the blank
satellite preview can be diagnosed on-device. DRYs the load logic into loadHtml().

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Observe the real cause on the device

**Files:** none (manual diagnostic procedure; no code change, no commit).

**Interfaces:**
- Consumes: the instrumented `MapWebView` from Task 1.
- Produces: a **classification** of the cause — one of `ZERO_HEIGHT`,
  `RESOURCE_FAILURE`, `ORIGIN_ERROR`, or `OTHER` — that selects the Task 3 branch.

- [ ] **Step 1: Install and launch on the device**

```bash
./gradlew :app:installDebug
```
On the device: open the app, ensure it's **online** (Wi-Fi/4G), go to the Survey tab
and generate a plot so a map exists, then go to the Satellite tab, enter a valid GPS
point whose station matches a survey station, and tap **Generate Satellite Map**.
Reproduce the blank box.

- [ ] **Step 2: Capture Logcat for the WebView**

In a terminal on the laptop:
```bash
adb logcat -s MapWebView:* chromium:* | tee /tmp/mapwebview.log
```
Re-trigger generation. Read the captured lines. Interpret:
- `page finished, probe={"bodyW":...,"bodyH":...,"mapH":0,...}` → **`mapH` (or
  `bodyH`) is 0 or tiny** ⇒ classify **`ZERO_HEIGHT`**.
- `load error ...` or `http error ...` lines for `cdn.jsdelivr.net`, `unpkg`,
  `mt1.google.com`, or other resources ⇒ classify **`RESOURCE_FAILURE`**.
- `console [...]` lines mentioning `SecurityError`, `origin`, `cross-origin`,
  `blocked`, or mixed content ⇒ classify **`ORIGIN_ERROR`** (note: if it mentions
  http/https mixed content specifically, `RESOURCE_FAILURE` fix C2 also applies).
- None of the above, page reports healthy sizes but still blank ⇒ classify **`OTHER`**
  and go to Step 3 for deeper inspection.

- [ ] **Step 3: Inspect live via Chrome DevTools**

On the laptop, open Chrome → `chrome://inspect` → under **Remote Target** find the
app's WebView → **inspect**. Then:
- **Elements** tab: confirm `<div class="folium-map">` exists and check its computed
  height. A `0px` height confirms **`ZERO_HEIGHT`**.
- **Console** tab: read errors directly.
- **Network** tab: re-trigger; look for failed (red) requests to CDNs/tiles —
  confirms **`RESOURCE_FAILURE`** and shows exactly which URL/status.

- [ ] **Step 4: Record the classification**

Write the classification and the key evidence line(s) into the to_fix log so Task 3
applies the right branch:
```bash
# append the finding (replace with your actual classification + evidence)
printf '\nDIAGNOSIS 2026-06-20: ZERO_HEIGHT — probe mapH=0; folium-map computed height 0px.\n' \
  >> docs/mobile-app/phases/phase-2-satellite-map/to_fix.md
git add docs/mobile-app/phases/phase-2-satellite-map/to_fix.md
git commit -m "docs(mobile-app): record satellite WebView blank-render diagnosis"
```

---

### Task 3: Apply the staged fix matching the diagnosis

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt`

**Interfaces:**
- Consumes: the classification from Task 2.
- Produces: `MapWebView` unchanged public signature; the relevant branch's behavior
  applied. Apply **only** the branch matching the diagnosis.

> **Branch selection:** Do exactly one of C1 / C2 / C3 below based on Task 2. If the
> diagnosis was `OTHER`, re-run Task 2 Step 3 and bring the specific console/network
> evidence back for a tailored fix before editing.

#### Branch C1 — `ZERO_HEIGHT`: force container height and reflow Leaflet

- [ ] **Step C1.1: Extend `onPageFinished` to inject CSS and trigger a Leaflet reflow**

In `MapWebView.kt`, replace the body of `onPageFinished` (currently just the size
probe) with a version that first forces the height chain, then re-probes:

```kotlin
override fun onPageFinished(view: WebView, url: String?) {
    // Force a full height chain and reflow Leaflet. Leaflet recalculates its
    // size on a window 'resize' event, which fixes maps initialized in a
    // container that measured 0px at init time.
    view.evaluateJavascript(
        """(function(){
            var s=document.createElement('style');
            s.innerHTML='html,body{height:100%;margin:0;padding:0;}'+
                        '.folium-map{position:absolute;top:0;bottom:0;left:0;right:0;'+
                        'height:100%!important;width:100%!important;}';
            document.head.appendChild(s);
            window.dispatchEvent(new Event('resize'));
        })();""".trimIndent(),
        null,
    )
    // Re-probe so the log shows the corrected sizes.
    view.evaluateJavascript(
        """(function(){
            var b=document.body, m=document.querySelector('.folium-map');
            return JSON.stringify({
              bodyH: b?b.clientHeight:-1, mapH: m?m.clientHeight:-1
            });
        })();""".trimIndent(),
    ) { result -> Log.d(TAG, "post-fix probe=$result") }
}
```

- [ ] **Step C1.2: Rebuild, reinstall, verify on device**

```bash
./gradlew :app:installDebug
```
Re-trigger generation. Expected Logcat: `post-fix probe={"bodyH":<positive>,"mapH":<positive>}`
and satellite tiles + cave overlay visible in the preview. If `mapH` is now positive
but tiles are gray, that's a separate tile-load issue → re-diagnose as `RESOURCE_FAILURE`.

- [ ] **Step C1.3: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt
git commit -m "fix(mobile-app): force folium container height + Leaflet reflow in WebView

Injects a height:100% chain and dispatches a resize event after load so the
Leaflet map, initialized in a 0px container, recalculates and renders.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

#### Branch C2 — `RESOURCE_FAILURE`: fix blocked subresource loads

- [ ] **Step C2.1: Identify the failure mode from Task 2 evidence**

- If the failing URL is **http** (mixed content on an https-origin page) → apply the
  `mixedContentMode` fix in Step C2.2.
- If the failing URL is **https** but errors (DNS/timeout/blocked) → the cause is not
  the WebView config; verify device connectivity and that `INTERNET` permission is
  present (it is, in `AndroidManifest.xml`). Re-test on a different network. No code
  change applies; stop and report.

- [ ] **Step C2.2: Allow mixed content (only if a subresource is http)**

In `MapWebView.kt`, add the import and the setting inside `WebView(ctx).apply { ... }`,
right after `settings.domStorageEnabled = true`:

```kotlin
import android.webkit.WebSettings
```
```kotlin
// folium/Leaflet assets are https, but allow compatibility mode in case a
// subresource resolves over http on an https-origin page.
settings.mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
```

- [ ] **Step C2.3: Rebuild, reinstall, verify on device**

```bash
./gradlew :app:installDebug
```
Re-trigger. Expected: the previously failing resource now loads (no `http error` /
`load error` line for it in Logcat) and the map renders.

- [ ] **Step C2.4: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt
git commit -m "fix(mobile-app): allow mixed-content compatibility for folium WebView assets

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

#### Branch C3 — `ORIGIN_ERROR`: switch to a clean local origin

- [ ] **Step C3.1: Fall back to `file://` load with file access enabled**

The fake `https://appassets.androidplatform.net/` base gives the page an https origin
without a server behind it, which can trigger security errors. Switch the loader to a
real `file://` URL. In `MapWebView.kt`, add the file-access setting after
`settings.domStorageEnabled = true`:

```kotlin
settings.allowFileAccess = true
```
and replace the `loadHtml` body with:

```kotlin
private fun loadHtml(webView: WebView, htmlPath: String) {
    val file = File(htmlPath)
    if (file.exists()) {
        webView.loadUrl("file://$htmlPath")
    } else {
        webView.loadData("Map file not found.", "text/html", "UTF-8")
    }
}
```

- [ ] **Step C3.2: Rebuild, reinstall, verify on device**

```bash
./gradlew :app:installDebug
```
Re-trigger. Expected: no `SecurityError`/origin console messages; map renders.

- [ ] **Step C3.3: If `file://` still fails, escalate to `WebViewAssetLoader`**

Only if Step C3.2 still shows origin/security errors. Add the dependency in
`android/app/build.gradle` dependencies block:
```groovy
implementation "androidx.webkit:webkit:1.11.0"
```
Then serve `filesDir` through the asset loader so the page gets a genuine secure
origin. Replace the `WebViewClient`/load wiring in `MapWebView.kt` so the factory
builds the loader and intercepts requests:

```kotlin
import androidx.webkit.WebViewAssetLoader
import java.io.File

// inside factory, before setting webViewClient:
val assetLoader = WebViewAssetLoader.Builder()
    .addPathHandler(
        "/files/",
        WebViewAssetLoader.InternalStoragePathHandler(ctx, File(ctx.filesDir, "")),
    )
    .build()
```
Add to the existing `webViewClient` object:
```kotlin
override fun shouldInterceptRequest(
    view: WebView,
    request: WebResourceRequest,
): WebResourceResponse? = assetLoader.shouldInterceptRequest(request.url)
```
And load via the asset-loader URL (the file under `filesDir` mapped to `/files/`):
```kotlin
// htmlPath is an absolute path under filesDir; map its filename into /files/
private fun assetUrlFor(htmlPath: String): String =
    "https://appassets.androidplatform.net/files/" + File(htmlPath).name
```
then `webView.loadUrl(assetUrlFor(htmlPath))` in `loadHtml`. Rebuild, reinstall, verify.

- [ ] **Step C3.4: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt android/app/build.gradle
git commit -m "fix(mobile-app): load folium HTML from a clean local origin in WebView

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Verify end-to-end on device and quiet temporary logging

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt`

**Interfaces:**
- Consumes: the working fix from Task 3.
- Produces: final `MapWebView` with durable error/console diagnostics retained and
  the temporary size-probe logging removed.

- [ ] **Step 1: Full manual verification on device (online)**

On the device, online: Survey → generate plot → Satellite → valid GPS point →
**Generate Satellite Map**. Confirm:
- Satellite imagery **and** the cave overlay render in the inline preview.
- Pan/zoom works.
- **Save / Share HTML**, **Save / Share JSON**, **Save / Share KMZ** each open the
  share sheet.

- [ ] **Step 2: Verify offline behavior unchanged**

Turn off Wi-Fi/data, generate again. Confirm the offline banner
("No connection — satellite preview unavailable…") shows instead of the WebView, and
the three Save/Share buttons still work.

- [ ] **Step 3: Remove the temporary size-probe, keep durable diagnostics**

In `MapWebView.kt`, delete the size-probe `evaluateJavascript` block(s) from
`onPageFinished` (and the `post-fix probe` block if C1 was applied). Keep the
`onConsoleMessage`, `onReceivedError`, and `onReceivedHttpError` callbacks — they're
cheap and make future regressions observable. If C1 was applied, **keep** the CSS-inject
+ `resize` dispatch (that is the fix, not a probe). Leave
`setWebContentsDebuggingEnabled(true)` but add a `// TODO: guard behind debug build`
comment.

- [ ] **Step 4: Rebuild and re-verify it still renders**

```bash
./gradlew :app:installDebug
```
Re-trigger generation; confirm the map still renders (removing the probe must not
regress the fix).

- [ ] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt
git commit -m "chore(mobile-app): remove temporary WebView size probe; keep diagnostics

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 6: Update to_fix.md / DEVLOG**

Mark the issue resolved with the confirmed root cause and the branch applied:
```bash
printf '\nRESOLVED 2026-06-20: <branch C1/C2/C3> — <one-line root cause>. Preview renders on device.\n' \
  >> docs/mobile-app/phases/phase-2-satellite-map/to_fix.md
git add docs/mobile-app/phases/phase-2-satellite-map/to_fix.md
git commit -m "docs(mobile-app): mark satellite WebView blank-render fixed"
```

---

## Self-Review

**Spec coverage:**
- Phase A (instrumentation) → Task 1. ✓
- Phase B (observe on device) → Task 2. ✓
- Phase C (staged minimal fix C1/C2/C3) → Task 3 branches, mapped to the spec's
  C1/C2/C3. ✓
- Phase D (verify + quiet temporary logging) → Task 4. ✓
- Constraint "preserve offline banner + Save/Share" → Task 4 Steps 1–2. ✓
- Constraint "device-only verification loop" → all build/run steps run on the device
  laptop; no automated test claimed. ✓
- Out-of-scope items (full-screen route, blanket WebViewAssetLoader) → only the C3
  escalation touches WebViewAssetLoader, and only conditionally. ✓

**Placeholder scan:** No "TBD/TODO-implement-later". The one `// TODO: guard behind
debug build` is an intentional, specific code comment, not a plan gap. The `<branch>`
/ `<one-line root cause>` tokens in Task 4 Step 6 and Task 2 Step 4 are runtime values
the engineer fills from observed evidence, not undefined work.

**Type consistency:** `MapWebView(htmlPath: String, modifier: Modifier)` signature is
stable across all tasks. `loadHtml(webView: WebView, htmlPath: String)` defined in
Task 1 and re-edited consistently in C3. `onPageFinished`, `onReceivedError`,
`onReceivedHttpError`, `onConsoleMessage` signatures match the `WebViewClient`/
`WebChromeClient` API at minSdk 24. ✓
