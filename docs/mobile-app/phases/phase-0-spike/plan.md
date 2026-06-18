# Phase 0 — Spike (De-risk) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the CaveSketch Python scientific stack runs under Chaquopy on a real Android phone and produces a correct survey PDF, and record the numbers (working dep versions, render time, APK size) that decide how hard Phases 1–3 will be.

**Architecture:** Two sequential gates. **Gate A** (laptop): an isolated Python 3.13 env with Chaquopy-compatible relaxed pins (`numpy==1.26.2`, `pandas==2.1.3`, `matplotlib==3.8.4`) must pass the existing `pytest` suite — retiring the dependency-downgrade risk where debugging is cheap. **Gate B** (device): a minimal Jetpack Compose app embeds CPython via Chaquopy, calls the untouched `cave_sketch` core through a thin `spike.py`, renders `tests/fixtures/sample.dxf` to a PDF, and displays page 1 on a real arm64 phone.

**Tech Stack:** Python 3.13 + uv (Gate A); Kotlin + Jetpack Compose + Chaquopy 17.0 + Android Gradle Plugin + Android `PdfRenderer` (Gate B). Spec: `docs/mobile-app/phases/phase-0-spike/spec.md`.

**TDD note:** Gate A is verification-driven by the existing test suite. Gate B is a throwaway spike whose only honest verification is "the APK builds" + "the PDF renders correctly on the real phone" (GEMINI.md requires real-device, not emulator). Gate B tasks therefore use build/manual-verification checkpoints, not a write-failing-test-first loop. This is the correct call for throwaway packaging + UI code, not a shortcut.

**Hard constraints (umbrella §12 — hold for every task):**
- `cave_sketch/` stays untouched and free of UI/Streamlit/Android imports.
- The web app's `pyproject.toml` and `uv.lock` (numpy 2.2.5 etc.) are NOT modified.
- Mobile work logs to `android/DEVLOG.md`, never the root `DEVLOG.md`.
- The Android project lives under a new top-level `android/` directory.

---

## File Structure

**Gate A (repo root):**
- Create: `requirements-mobile.txt` — the relaxed, Chaquopy-compatible pins. The "lock" for the mobile env.
- Create: `scripts/check_mobile_env.sh` — builds the isolated venv and runs the existing suite under the relaxed pins. Reusable when Phase 1+ bumps pins.

**Gate B (`android/`):**
- Create: `android/settings.gradle` — Gradle project + plugin management.
- Create: `android/build.gradle` — top-level plugin versions.
- Create: `android/gradle.properties` — AndroidX + JVM flags.
- Create: `android/app/build.gradle` — Android + **Chaquopy** config (Python 3.13, `pip install` relaxed pins, `abiFilters`, `python.srcDir` pointing at the untouched repo-root `cave_sketch`).
- Create: `android/app/src/main/AndroidManifest.xml`.
- Create: `android/app/src/main/python/spike.py` — thin glue: `parse_dxf` → `draw_survey` → PDF path. Imports `cave_sketch`; contains no business logic.
- Create: `android/app/src/main/assets/sample.dxf` — copy of `tests/fixtures/sample.dxf` (build input, not core source).
- Create: `android/app/src/main/java/com/cavesketch/spike/SpikeApplication.kt` — starts the Python runtime.
- Create: `android/app/src/main/java/com/cavesketch/spike/MainActivity.kt` — one-button Compose UI → bridge → `PdfRenderer` → `Image`.
- Create: `android/DEVLOG.md` — first mobile-app DEVLOG entry + findings.
- Modify: `docs/mobile-app/README.md` — flip the Phase 0 status row.

---

# GATE A — Desktop relaxed-pin proof

### Task A1: Pin the Chaquopy-compatible mobile dependency set [8a43188]

**Files:**
- Create: `requirements-mobile.txt`
- Create: `scripts/check_mobile_env.sh`

- [x] **Step 1: Write the relaxed-pins requirements file**

Create `requirements-mobile.txt`:

```text
# Chaquopy 17.0 (pypi-13.1) ceilings for the native scientific stack.
# These are the versions the Android app will bundle; proven here on the
# laptop before any device work. The web app keeps numpy 2.2.5 etc. via the
# untouched pyproject.toml / uv.lock — do NOT edit those.
numpy==1.26.2
pandas==2.1.3
matplotlib==3.8.4
# pure-Python, identical to the web app pins:
ezdxf==1.4.1
folium==0.19.5
# test runner:
pytest>=8
```

- [x] **Step 2: Write the env-check script**

Create `scripts/check_mobile_env.sh`:

```bash
#!/usr/bin/env bash
# Gate A: prove the existing test suite is green under Chaquopy-compatible
# relaxed pins, in an isolated Python 3.13 venv. Leaves the project env and
# uv.lock untouched.
set -euo pipefail
cd "$(dirname "$0")/.."

VENV=".venv-mobile"
echo ">> Creating isolated mobile env ($VENV, Python 3.13)"
uv venv "$VENV" --python 3.13

echo ">> Installing relaxed pins"
uv pip install --python "$VENV" -r requirements-mobile.txt

echo ">> Installing cave_sketch WITHOUT its deps (use the relaxed pins above)"
uv pip install --python "$VENV" --no-deps -e .

echo ">> Running the existing test suite under the relaxed pins"
"$VENV/bin/python" -m pytest -q

echo ">> Recording resolved versions"
"$VENV/bin/python" -c "import numpy, pandas, matplotlib, ezdxf, folium, sys; \
print('python', sys.version.split()[0]); \
print('numpy', numpy.__version__); print('pandas', pandas.__version__); \
print('matplotlib', matplotlib.__version__); print('ezdxf', ezdxf.__version__); \
print('folium', folium.__version__)"
```

- [x] **Step 3: Make the script executable**

Run: `chmod +x scripts/check_mobile_env.sh`
Expected: no output, exit 0.

- [x] **Step 4: Add `.venv-mobile` to .gitignore**

Append `.venv-mobile/` to the repo `.gitignore` (the venv is a build artifact, not source).
Run: `grep -q '.venv-mobile' .gitignore && echo OK`
Expected: `OK`

- [x] **Step 5: Commit**

```bash
git add requirements-mobile.txt scripts/check_mobile_env.sh .gitignore
git commit -m "feat(mobile): add Gate A relaxed-pin env + check script"
```

### Task A2: Run the existing suite under the relaxed pins (the Gate A test) [a962935]

**Files:**
- Test: the existing `tests/` suite (no new tests — this gate verifies the unchanged core under downgraded deps).

- [x] **Step 1: Run the Gate A check**

Run: `./scripts/check_mobile_env.sh`
Expected: pytest summary ends in `passed` with **0 failed**, then a version block printing `numpy 1.26.2`, `pandas 2.1.3`, `matplotlib 3.8.4`, Python `3.13.x`.

- [x] **Step 2: If any test fails, diagnose before proceeding**

If the run is NOT green, do NOT start Gate B. For each failure, decide whether it is:
  - a deps-version behaviour change (record it; if a fix is needed in `cave_sketch`, the fix MUST stay Streamlit/Android-free AND keep the web-app env green — re-run `uv run pytest` on the main env to confirm), or
  - environment noise (e.g. a missing matplotlib font/backend) — set `MPLBACKEND=Agg` and re-run.
Record the failure and resolution verbatim for the DEVLOG (Task B8). Expected (per the spec's API grep): **green with no code changes.**

- [x] **Step 3: Confirm the web-app env is untouched**

Run: `git status --porcelain pyproject.toml uv.lock`
Expected: **no output** (the web app's pins are unchanged).

- [x] **Step 4: Capture the version block for the DEVLOG**

Copy the printed version block from Step 1 into a scratch note; it becomes part of the Gate A findings in Task B8.

**GATE A EXIT:** existing suite green under the relaxed pins, web-app env unchanged. Only now proceed to Gate B.

---

# GATE B — On-device proof (real arm64 phone)

### Task B1: Install and verify the Android toolchain [3bf0478]

**Files:** none (local toolchain).

- [x] **Step 1: Install Android Studio + SDK + JDK 17**

Install Android Studio (bundles the SDK and a compatible JDK). On macOS: `brew install --cask android-studio`, then launch once and complete the SDK setup wizard (install "Android SDK Platform 34" and "Android SDK Build-Tools").

- [x] **Step 2: Verify the SDK command-line tools are on PATH**

Run: `sdkmanager --version` (or `~/Library/Android/sdk/cmdline-tools/latest/bin/sdkmanager --version`)
Expected: a version number prints (e.g. `12.0` or similar), exit 0.

- [x] **Step 3: Enable USB debugging on the phone and connect it**

On the phone: Settings → About → tap Build Number 7× → Developer options → enable "USB debugging". Connect via USB and accept the RSA prompt.

- [x] **Step 4: Verify the real device is visible to adb**

Run: `adb devices`
Expected: the phone's serial listed with status `device` (not `unauthorized`/`offline`). This is the device Gate B must run on — emulator does not count.

### Task B2: Scaffold the `android/` Gradle project with Chaquopy [9cd5f60]

**Files:**
- Create: `android/settings.gradle`
- Create: `android/build.gradle`
- Create: `android/gradle.properties`
- Create: `android/app/build.gradle`

> Reference scaffold: the official `chaquo/chaquopy-matplotlib` example
> (https://github.com/chaquo/chaquopy-matplotlib). The files below are the
> minimal, self-contained equivalent. If a Chaquopy 17.0 DSL detail differs,
> the official example for the installed Chaquopy version wins — record any
> deviation in the DEVLOG.

- [x] **Step 1: Write `android/settings.gradle`**

```groovy
pluginManagement {
    repositories {
        gradlePluginPortal()
        google()
        mavenCentral()
    }
}
dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "CaveSketchSpike"
include ":app"
```

- [x] **Step 2: Write `android/build.gradle` (top-level)**

```groovy
plugins {
    id "com.android.application" version "8.5.0" apply false
    id "org.jetbrains.kotlin.android" version "1.9.24" apply false
    id "com.chaquo.python" version "17.0.0" apply false
}
```

- [x] **Step 3: Write `android/gradle.properties`**

```properties
org.gradle.jvmargs=-Xmx2048m
android.useAndroidX=true
kotlin.code.style=official
```

- [x] **Step 4: Write `android/app/build.gradle`**

```groovy
plugins {
    id "com.android.application"
    id "org.jetbrains.kotlin.android"
    id "com.chaquo.python"
}

android {
    namespace "com.cavesketch.spike"
    compileSdk 34

    defaultConfig {
        applicationId "com.cavesketch.spike"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "0.1-spike"

        // arm64-v8a = the real phone; x86_64 = emulator fallback.
        ndk {
            abiFilters "arm64-v8a", "x86_64"
        }

        python {
            version "3.13"
            pip {
                install "numpy==1.26.2"
                install "pandas==2.1.3"
                install "matplotlib==3.8.4"
                install "ezdxf==1.4.1"
                install "folium==0.19.5"
            }
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    buildFeatures { compose true }
    composeOptions { kotlinCompilerExtensionVersion "1.5.14" }
}

// Make the UNTOUCHED repo-root cave_sketch importable from Python.
// srcDir points at the repo root (../../ from android/app); cave_sketch is
// imported at runtime. No copy, no duplication of the core.
chaquopy {
    sourceSets {
        getByName("main") {
            srcDir "../.."
        }
    }
}

dependencies {
    implementation "androidx.core:core-ktx:1.13.1"
    implementation "androidx.activity:activity-compose:1.9.0"
    implementation platform("androidx.compose:compose-bom:2024.06.00")
    implementation "androidx.compose.ui:ui"
    implementation "androidx.compose.material3:material3"
    implementation "androidx.compose.ui:ui-tooling-preview"
    debugImplementation "androidx.compose.ui:ui-tooling"
}
```

- [x] **Step 5: Commit the scaffold**

```bash
git add android/settings.gradle android/build.gradle android/gradle.properties android/app/build.gradle
git commit -m "feat(android): scaffold Chaquopy spike Gradle project"
```

### Task B3: Add the Python glue and the sample input [2ce9c14]

**Files:**
- Create: `android/app/src/main/python/spike.py`
- Create: `android/app/src/main/assets/sample.dxf`

- [x] **Step 1: Write `spike.py` (thin glue, no business logic)**

```python
"""Phase 0 spike glue. Calls the UNTOUCHED cave_sketch core, mirroring the web
Survey Plot flow: parse_dxf (DXF->CSV) then draw_survey (CSV->PDF)."""
from pathlib import Path

from cave_sketch.dxf.parser import parse_dxf
from cave_sketch.survey.survey import draw_survey


def render_sample_pdf(dxf_path: str, work_dir: str) -> str:
    """Render the sample DXF to a PDF and return its absolute path."""
    work = Path(work_dir)
    csv_path = work / "sample.csv"
    pdf_path = work / "sample.pdf"

    # DXF -> CSV (writes csv_path, returns CaveSurvey)
    parse_dxf(Path(dxf_path), csv_path)

    # CSV -> PDF (rule_length is a sample value; spike only proves rendering)
    draw_survey(
        title="Phase 0 Spike",
        rule_length=1.0,
        csv_map_path=str(csv_path),
        output_path=str(pdf_path),
    )
    return str(pdf_path)
```

- [x] **Step 2: Copy the fixture DXF into the app assets**

Run: `mkdir -p android/app/src/main/assets && cp tests/fixtures/sample.dxf android/app/src/main/assets/sample.dxf`
Expected: `android/app/src/main/assets/sample.dxf` exists.

Verify: `test -s android/app/src/main/assets/sample.dxf && echo OK`
Expected: `OK`

- [x] **Step 3: Commit**

```bash
git add android/app/src/main/python/spike.py android/app/src/main/assets/sample.dxf
git commit -m "feat(android): add spike.py glue + sample.dxf asset"
```

### Task B4: Manifest + Python runtime startup [4bbd172]

**Files:**
- Create: `android/app/src/main/AndroidManifest.xml`
- Create: `android/app/src/main/java/com/cavesketch/spike/SpikeApplication.kt`

- [x] **Step 1: Write the manifest**

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:name=".SpikeApplication"
        android:label="CaveSketch Spike"
        android:theme="@android:style/Theme.Material.Light.NoActionBar">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

- [x] **Step 2: Write the Application that starts Python**

```kotlin
package com.cavesketch.spike

import android.app.Application
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class SpikeApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
    }
}
```

- [x] **Step 3: Commit**

```bash
git add android/app/src/main/AndroidManifest.xml android/app/src/main/java/com/cavesketch/spike/SpikeApplication.kt
git commit -m "feat(android): manifest + Python runtime startup"
```

### Task B5: The Compose screen — button → bridge → PDF → on-screen image [f238b48]

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/spike/MainActivity.kt`

- [x] **Step 1: Write `MainActivity.kt`**

```kotlin
package com.cavesketch.spike

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.pdf.PdfRenderer
import android.os.Bundle
import android.os.ParcelFileDescriptor
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.dp
import com.chaquo.python.Python
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { SpikeScreen() } }
    }

    @Composable
    fun SpikeScreen() {
        val scope = rememberCoroutineScope()
        var status by remember { mutableStateOf("Tap to run the spike") }
        var bitmap by remember { mutableStateOf<Bitmap?>(null) }
        var running by remember { mutableStateOf(false) }

        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Button(
                enabled = !running,
                onClick = {
                    running = true
                    status = "Running…"
                    bitmap = null
                    scope.launch {
                        try {
                            val result = withContext(Dispatchers.IO) { runSpike() }
                            bitmap = result.first
                            status = "OK — rendered in ${result.second} ms"
                        } catch (e: Throwable) {
                            status = "FAILED: ${e.message}"
                        } finally {
                            running = false
                        }
                    }
                }
            ) { Text("Run spike") }

            Spacer(Modifier.height(12.dp))
            Text(status)
            Spacer(Modifier.height(12.dp))
            bitmap?.let { Image(it.asImageBitmap(), contentDescription = "Survey PDF page 1") }
        }
    }

    /** Copies the sample DXF out of assets, calls Python to make the PDF,
     *  renders page 1 to a Bitmap. Returns (bitmap, elapsedMillis). */
    private fun runSpike(): Pair<Bitmap, Long> {
        val dxf = File(filesDir, "sample.dxf")
        assets.open("sample.dxf").use { input -> dxf.outputStream().use { input.copyTo(it) } }

        val start = System.nanoTime()
        val py = Python.getInstance()
        val pdfPath = py.getModule("spike")
            .callAttr("render_sample_pdf", dxf.absolutePath, filesDir.absolutePath)
            .toString()
        val elapsedMs = (System.nanoTime() - start) / 1_000_000

        val pfd = ParcelFileDescriptor.open(File(pdfPath), ParcelFileDescriptor.MODE_READ_ONLY)
        PdfRenderer(pfd).use { renderer ->
            renderer.openPage(0).use { page ->
                val bmp = Bitmap.createBitmap(page.width * 2, page.height * 2, Bitmap.Config.ARGB_8888)
                bmp.eraseColor(Color.WHITE)
                page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                return Pair(bmp, elapsedMs)
            }
        }
    }
}
```

- [x] **Step 2: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/spike/MainActivity.kt
git commit -m "feat(android): Compose UI + bridge + PdfRenderer on-screen preview"
```

### Task B6: Build the debug APK (build-success checkpoint) [14ef731]

**Files:** none (build).

- [x] **Step 1: Assemble the debug APK**

Run (from `android/`): `./gradlew :app:assembleDebug`
Expected: `BUILD SUCCESSFUL`. The first run downloads Chaquopy's native wheels for `numpy`/`pandas`/`matplotlib` (arm64-v8a + x86_64) — slow the first time.

- [x] **Step 2: If the build fails on a dependency, record and adjust**

If Chaquopy reports a package/ABI it cannot satisfy at the pinned version, note the exact message in the DEVLOG, then pick the nearest available version from `https://chaquo.com/pypi-13.1/<pkg>/` and re-run. Re-run Gate A (`./scripts/check_mobile_env.sh` with the adjusted pin) before accepting any changed pin, so the laptop proof stays honest.

- [x] **Step 3: Note the APK size (a findings metric)**

Run: `ls -lh android/app/build/outputs/apk/debug/app-debug.apk`
Expected: a file in the tens-of-MB range. Record the size for Task B8.

### Task B7: Run on the real phone and verify the PDF (manual device verification) [e19eed0]

**Files:** none (on-device).

- [x] **Step 1: Install and launch on the connected phone**

Run (from `android/`): `./gradlew :app:installDebug`
Then launch "CaveSketch Spike" from the phone's app drawer (or `adb shell monkey -p com.cavesketch.spike 1`).
Expected: app opens showing the "Run spike" button.

- [x] **Step 2: Run the spike on-device**

Tap **Run spike**. Expected: status changes to `OK — rendered in <N> ms` and a survey plot image appears below the button.

- [x] **Step 3: Verify correctness against the desktop output**

Generate the desktop reference from the Gate A env for the same fixture:

```bash
.venv-mobile/bin/python -c "from pathlib import Path; from cave_sketch.dxf.parser import parse_dxf; from cave_sketch.survey.survey import draw_survey; parse_dxf(Path('tests/fixtures/sample.dxf'), Path('/tmp/spike.csv')); draw_survey(title='Phase 0 Spike', rule_length=1.0, csv_map_path='/tmp/spike.csv', output_path='/tmp/spike_desktop.pdf')"
```

Open `/tmp/spike_desktop.pdf` and eyeball-compare it to the on-phone image: same survey geometry, stations, and layout. Expected: **visually equivalent** (minor font/anti-aliasing differences are acceptable; the plot must be the same survey).

- [x] **Step 4: Record the on-device render time**

From the status line in Step 2, record the elapsed milliseconds. If it varies, run 3× and record the range. This is the §6 render-time metric.

- [x] **Step 5: If it fails on-device, capture logs**

Run: `adb logcat -d | grep -iE "python|chaquopy|AndroidRuntime" | tail -50`
Record any Python traceback in the DEVLOG before attempting a fix.

### Task B8: Record findings, difficulty verdict, and flip status

**Files:**
- Create: `android/DEVLOG.md`
- Modify: `docs/mobile-app/README.md`

- [ ] **Step 1: Write the first `android/DEVLOG.md` entry**

Create `android/DEVLOG.md` with the findings (fill the bracketed values from the run):

```markdown
# CaveSketch Mobile App — DEVLOG

(Mobile-app history. Root `DEVLOG.md` covers the Python project / web app.)

## 2026-06-16 — Phase 0 spike complete

**Gate A (desktop relaxed pins):** existing pytest suite [PASSED/FAILED] under
Python [3.13.x], numpy 1.26.2, pandas 2.1.3, matplotlib 3.8.4, ezdxf 1.4.1,
folium 0.19.5. Code changes to cave_sketch required: [none / describe]. Web-app
`pyproject.toml`/`uv.lock` unchanged: [confirmed].

**Gate B (on-device):** Chaquopy 17.0, AGP [8.5.0], Python 3.13, ABIs
arm64-v8a (+x86_64). Built APK size: [N] MB. Device: [phone model / Android N].
PDF render time for sample.dxf: [N] ms ([range if measured]). On-screen PDF
visually matches desktop output: [yes/no].

**Surprises / deviations:** [e.g. DSL tweaks vs the official example, pin bumps].

**Difficulty verdict for Phases 1–3:** [GREEN/YELLOW/RED] — [one-paragraph
justification grounded in the above: e.g. "GREEN: stack runs unchanged, render
time acceptable at N ms, no pin surprises; remaining work is UI wiring."].
```

- [ ] **Step 2: Flip the Phase 0 status in the initiative README**

In `docs/mobile-app/README.md`, change the Phase 0 row from `⬜ Not started` to `✅ Done` (and the Gate-A/Gate-B outcome if you wish to note it).

Verify: `grep -A1 "Phase 0" docs/mobile-app/README.md`
Expected: shows the updated status.

- [ ] **Step 3: Commit the findings**

```bash
git add android/DEVLOG.md docs/mobile-app/README.md
git commit -m "docs(mobile-app): record Phase 0 spike findings + difficulty verdict"
```

**GATE B EXIT (and Phase 0 complete):** APK runs on the real phone, PDF matches
desktop, and `android/DEVLOG.md` records working versions, render time, APK size,
and a green/yellow/red verdict that feeds the Phase 1 spec.

---

## Self-Review (completed by plan author)

**Spec coverage:**
- Spec §2 relaxed-pins finding → Task A1 (`requirements-mobile.txt`).
- Spec §3 architecture (spike.py glue, PdfRenderer display, untouched core via srcDir) → Tasks B3, B5, B2 Step 4.
- Spec §4 Gate A (separate env, run existing pytest, don't touch web pins) → Tasks A1–A2.
- Spec §5 Gate B (toolchain setup, Chaquopy pip + ABIs + bundling, Compose+bridge, real-device deploy) → Tasks B1–B7.
- Spec §6 exit criteria (Gate A green, APK matches desktop, recorded versions/render-time/APK-size, difficulty verdict, android/DEVLOG.md created) → Task A2 + Tasks B6–B8.
- Spec §7 non-goals → honored: no file picker/settings/merge/map/share/icon; hardcoded sample.
- Spec §8 hard constraints → cave_sketch untouched (imported via srcDir, not copied/edited); web pyproject/uv.lock untouched (A2 Step 3); mobile logs to android/DEVLOG.md (B8); android/ top-level dir.

**Placeholder scan:** the only bracketed `[…]` values are the measured findings in the DEVLOG template (render time, APK size, device model) — these are runtime measurements, not unfilled plan content. All code/config steps contain complete content.

**Type/name consistency:** `render_sample_pdf(dxf_path, work_dir)` defined in `spike.py` (B3) is called with exactly those args in `MainActivity.runSpike()` (B5). `applicationId`/`namespace` `com.cavesketch.spike` consistent across `build.gradle`, manifest, `SpikeApplication`, `MainActivity`. Python version `3.13` consistent across Gate A (A1) and Chaquopy config (B2).
