# Phase 1 — Survey Plot Screen — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the full on-device Survey Plot screen (file inputs, optional merge, all settings, Generate → PDF preview → Save/Share) at parity with the web `app/pages/1_survey_plot.py`, on a clean app foundation that Phase 2 plugs into.

**Architecture:** Compose UI → one `SurveyPlotViewModel` (async state) → a thin `PythonBridge` (Kotlin) → one Python entrypoint `survey_bridge.generate_survey_plot(...)` → the untouched `cave_sketch` core via Chaquopy. The bridge is the mobile analogue of the web page's glue; all business logic stays in `cave_sketch`.

**Tech Stack:** Kotlin + Jetpack Compose, Navigation-Compose, AndroidX Lifecycle ViewModel, Chaquopy 17.0 (CPython 3.13), Python (`numpy`/`pandas`/`matplotlib`/`ezdxf`/`folium`), pytest (laptop, under relaxed mobile pins), Gradle/AGP.

## Global Constraints

(Copied from `spec.md` §11 and `../../umbrella-spec.md` §12 — every task inherits these.)

- `cave_sketch/` stays **untouched** and free of UI/Streamlit/Android imports. Do not edit any file under `cave_sketch/`.
- The Streamlit web app, root `pyproject.toml`, and `uv.lock` are **unchanged**. Relaxed mobile pins live only in `requirements-mobile.txt` / `.venv-mobile`.
- Proven dependency pins (Phase 0): `numpy==1.26.2`, `pandas==2.1.3`, `matplotlib==3.8.4`, `ezdxf==1.4.1`, `folium==0.19.5`; Chaquopy 17.0, Python 3.13, ABIs `arm64-v8a` + `x86_64`.
- **`rule_length` must be a multiple of 5** (web parity; avoids the `cave_sketch/survey/graphics/rule.py:15` assertion).
- Python managed with `uv` (never bare `pip` for the project env).
- Keep the symlink `android/app/src/main/python/cave_sketch` → `../../../../../cave_sketch`.
- Android builds need JVM 17+; prefix Gradle commands with `JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"` (see `android/DEVLOG.md`).
- Mobile-app work logs to `android/DEVLOG.md`, **not** the root `DEVLOG.md`.
- GEMINI.md requires **real-device** verification for UI work (emulator is not sufficient for sign-off).

**Run commands from:** repo root for Python; `android/` for Gradle.

- Python bridge tests (laptop, relaxed pins) run with the mobile venv's interpreter directly (matching `scripts/check_mobile_env.sh`):
  ```bash
  .venv-mobile/bin/python -m pytest tests/test_survey_bridge.py -v
  ```
  If `.venv-mobile` does not exist yet, create it first: `bash scripts/check_mobile_env.sh` (it builds `.venv-mobile` and installs `requirements-mobile.txt` + `cave_sketch` with `--no-deps`).
- Gradle build: `cd android && JAVA_HOME="…" ./gradlew :app:assembleDebug`
- Kotlin unit tests: `cd android && JAVA_HOME="…" ./gradlew :app:testDebugUnitTest`

---

### [x] Task 1: Measurement spike — break down the ~70s cold render · 74c5866

This is **throwaway instrumentation** reusing the Phase 0 spike. Its deliverable is a recorded breakdown + a chosen cold-start strategy, not kept code. It **gates** the rest of the phase (Task 10 uses its decision).

**Files:**
- Modify: `android/app/src/main/python/spike.py`
- Modify: `android/app/src/main/java/com/cavesketch/spike/MainActivity.kt:72-92`
- Modify: `android/DEVLOG.md`

**Interfaces:**
- Produces: a DEVLOG entry with import/parse/draw timings (cold + warm) and a one-line strategy decision consumed narratively by Task 5 (pre-warm) and Task 10 (progress messaging).

- [x] **Step 1: Add per-stage timing to `spike.py`**

Replace `render_sample_pdf` with a timed version that returns the breakdown as a JSON string:

```python
"""Phase 0/1 spike glue — TIMED. Throwaway: deleted in Task 12."""
import json
import time
from pathlib import Path


def render_sample_pdf_timed(dxf_path: str, work_dir: str) -> str:
    """Render the sample DXF, returning JSON timings (ms) for import/parse/draw."""
    work = Path(work_dir)
    csv_path = work / "sample.csv"
    pdf_path = work / "sample.pdf"

    t0 = time.perf_counter()
    from cave_sketch.dxf.parser import parse_dxf
    from cave_sketch.survey.survey import draw_survey
    t1 = time.perf_counter()

    parse_dxf(Path(dxf_path), csv_path)
    t2 = time.perf_counter()

    draw_survey(title="Spike", rule_length=20.0, csv_map_path=str(csv_path),
                output_path=str(pdf_path))
    t3 = time.perf_counter()

    return json.dumps({
        "import_ms": round((t1 - t0) * 1000),
        "parse_ms": round((t2 - t1) * 1000),
        "draw_ms": round((t3 - t2) * 1000),
        "pdf_path": str(pdf_path),
    })
```

- [x] **Step 2: Display the breakdown in `MainActivity.kt`**

In `runSpike()`, call the timed function and surface the JSON. Change the call site to:

```kotlin
val resultJson = py.getModule("spike")
    .callAttr("render_sample_pdf_timed", dxf.absolutePath, filesDir.absolutePath)
    .toString()
android.util.Log.i("SpikeTiming", resultJson)   // visible in `adb logcat -s SpikeTiming`
val pdfPath = org.json.JSONObject(resultJson).getString("pdf_path")
```
Append `resultJson` to the on-screen `status` text so it is readable on-device without a cable.

- [x] **Step 3: Build and install on the real phone**

Run:
```bash
cd android && JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:installDebug
```
Expected: BUILD SUCCESSFUL; app installs on the connected device.

- [x] **Step 4: Measure cold + warm**

Cold: force-stop the app, launch, tap "Run spike" once, record the JSON. Warm: tap "Run spike" a second time in the same session, record again. (Cold = first call after process start; warm = second call.)

- [x] **Step 5: Record findings and decide the strategy**

Add a dated entry to `android/DEVLOG.md` with the cold and warm `import_ms` / `parse_ms` / `draw_ms`, and a one-line decision:
- if `import_ms` (+ first-run draw font-cache) dominates and warm `draw_ms` is small → **strategy: pre-warm imports at launch** (Task 5 already does this; expected outcome);
- if `draw_ms` dominates even when warm → **strategy: also optimize the draw path** — record this as added scope to revisit after Task 10.

- [x] **Step 6: Commit**

```bash
git add android/app/src/main/python/spike.py android/app/src/main/java/com/cavesketch/spike/MainActivity.kt android/DEVLOG.md
git commit -m "chore(mobile-app): instrument cold-start breakdown (Phase 1 measurement)"
```

---

### [x] Task 2: Python bridge — input resolution · 755af5f

Start the real bridge module. `resolve_input` turns a picked path into a CSV path: DXF → parsed CSV, CSV → passthrough, empty → None. Pure logic, TDD on the laptop.

**Files:**
- Create: `android/app/src/main/python/survey_bridge.py`
- Create: `tests/test_survey_bridge.py`

**Interfaces:**
- Consumes: `cave_sketch.dxf.parser.parse_dxf(input_path: Path, output_path: Optional[Path]) -> CaveSurvey`.
- Produces: `resolve_input(input_path: Optional[str], work_dir: str, stem: str) -> Optional[str]`.

- [x] **Step 1: Write the failing tests**

Create `tests/test_survey_bridge.py`:

```python
import json
import sys
from pathlib import Path

import pytest

# survey_bridge.py lives in the android source tree, outside the importable package.
ANDROID_PY = Path(__file__).resolve().parents[1] / "android/app/src/main/python"
sys.path.insert(0, str(ANDROID_PY))

import survey_bridge  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_resolve_input_returns_none_for_empty():
    assert survey_bridge.resolve_input(None, "/tmp", "map") is None
    assert survey_bridge.resolve_input("", "/tmp", "map") is None


def test_resolve_input_passes_csv_through():
    csv = str(FIXTURES / "test_survey.csv")
    assert survey_bridge.resolve_input(csv, "/tmp", "map") == csv


def test_resolve_input_parses_dxf_to_csv(tmp_path):
    dxf = str(FIXTURES / "sample.dxf")
    out = survey_bridge.resolve_input(dxf, str(tmp_path), "map")
    assert out == str(tmp_path / "map.csv")
    assert Path(out).exists()
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv-mobile/bin/python -m pytest tests/test_survey_bridge.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'survey_bridge'`.

- [x] **Step 3: Write the minimal implementation**

Create `android/app/src/main/python/survey_bridge.py`:

```python
"""Mobile bridge for the Survey Plot screen. Mirrors app/pages/1_survey_plot.py:
resolve inputs (DXF->CSV or CSV passthrough), validate optional merge, run
draw_survey, return the output PDF path. Lives under android/, never imported by
cave_sketch. Single entrypoint: generate_survey_plot(inputs_json, work_dir)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from cave_sketch.dxf.parser import parse_dxf


def resolve_input(input_path: Optional[str], work_dir: str, stem: str) -> Optional[str]:
    """Return a CSV path for an input. DXF inputs are parsed to <work_dir>/<stem>.csv;
    CSV inputs are returned unchanged; None/empty returns None."""
    if not input_path:
        return None
    src = Path(input_path)
    if src.suffix.lower() == ".dxf":
        csv_path = Path(work_dir) / f"{stem}.csv"
        parse_dxf(src, csv_path)
        return str(csv_path)
    return str(src)
```

- [x] **Step 4: Run tests to verify they pass**

Run: `.venv-mobile/bin/python -m pytest tests/test_survey_bridge.py -v`
Expected: 3 passed.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/python/survey_bridge.py tests/test_survey_bridge.py
git commit -m "feat(mobile-app): survey_bridge input resolution (dxf->csv / csv passthrough)"
```

---

### [x] Task 3: Python bridge — merge validation · 66e10f4

Mirror the web's merge validation (`app/components/merging_controls.py`): station IDs must be numeric and exist in the referenced survey. Returns an error message or `None`.

**Files:**
- Modify: `android/app/src/main/python/survey_bridge.py`
- Modify: `tests/test_survey_bridge.py`

**Interfaces:**
- Produces: `validate_merge(parent_csv: Optional[str], child_csv: Optional[str], parent_station: str, child_station: str) -> Optional[str]` (error message or None).

- [x] **Step 1: Write the failing tests**

Append to `tests/test_survey_bridge.py`:

```python
def test_validate_merge_rejects_non_numeric():
    csv = str(FIXTURES / "test_survey.csv")
    err = survey_bridge.validate_merge(csv, csv, "12P4", "1")
    assert err is not None and "numeric" in err.lower()


def test_validate_merge_rejects_missing_station():
    csv = str(FIXTURES / "test_survey.csv")  # has Node_Id 1, 2
    err = survey_bridge.validate_merge(csv, csv, "999", "1")
    assert err is not None and "999" in err


def test_validate_merge_accepts_valid():
    csv = str(FIXTURES / "test_survey.csv")
    assert survey_bridge.validate_merge(csv, csv, "1", "2") is None
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv-mobile/bin/python -m pytest tests/test_survey_bridge.py -k validate_merge -v`
Expected: FAIL — `AttributeError: module 'survey_bridge' has no attribute 'validate_merge'`.

- [x] **Step 3: Write the minimal implementation**

Add to `survey_bridge.py` (add `import re` and `import pandas as pd` to the imports):

```python
import re

import pandas as pd


def validate_merge(parent_csv: Optional[str], child_csv: Optional[str],
                   parent_station: str, child_station: str) -> Optional[str]:
    """Mirror app/components/merging_controls.py. Return an error message if the
    merge stations are invalid, else None."""
    if not re.fullmatch(r"\d+", parent_station or ""):
        return "Main station ID must be numeric (e.g. '30')."
    if not re.fullmatch(r"\d+", child_station or ""):
        return "Child station ID must be numeric (e.g. '47')."
    if parent_csv:
        df = pd.read_csv(parent_csv)
        if parent_station not in df["Node_Id"].astype(str).values:
            return f"Station '{parent_station}' not found in the main survey."
    if child_csv:
        df = pd.read_csv(child_csv)
        if child_station not in df["Node_Id"].astype(str).values:
            return f"Station '{child_station}' not found in the child survey."
    return None
```

- [x] **Step 4: Run tests to verify they pass**

Run: `.venv-mobile/bin/python -m pytest tests/test_survey_bridge.py -v`
Expected: 6 passed.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/python/survey_bridge.py tests/test_survey_bridge.py
git commit -m "feat(mobile-app): survey_bridge merge validation (web parity)"
```

---

### [x] Task 4: Python bridge — `generate_survey_plot` entrypoint + `prewarm` · 9c904a2

Tie resolution + validation + `draw_survey` together behind one JSON-in / JSON-out call, with all failures converted to structured errors. Add `prewarm()` for the cold-start strategy.

**Files:**
- Modify: `android/app/src/main/python/survey_bridge.py`
- Modify: `tests/test_survey_bridge.py`

**Interfaces:**
- Consumes: `resolve_input`, `validate_merge` (Tasks 2–3); `cave_sketch.survey.survey.draw_survey(...)`; `cave_sketch.survey.merger.SectionProtocol`.
- Produces:
  - `generate_survey_plot(inputs_json: str, work_dir: str) -> str` — returns JSON `{"pdf_path": ...}` or `{"error": <type>, "detail": <msg>}`. `inputs_json` keys: `map_path`, `section_path`, `child_map_path`, `child_section_path` (str|null), `survey_name`, `surveyor_name` (str), `parent_station`, `child_station` (str), `section_protocol` ("simple"|"mirror"|"displacement"), `settings` (object: `rule_length`, `rotation_deg`, `show_details`, `show_grid`, `marker_zoom`, `text_zoom`, `line_width_zoom`).
  - `prewarm() -> None` — pays the one-time import + matplotlib font-cache cost.

- [x] **Step 1: Write the failing tests**

Append to `tests/test_survey_bridge.py`:

```python
def _inputs(**kw):
    base = {
        "map_path": str(FIXTURES / "test_survey.csv"),
        "section_path": None, "child_map_path": None, "child_section_path": None,
        "survey_name": "Test Cave", "surveyor_name": "Tester",
        "parent_station": "", "child_station": "", "section_protocol": "simple",
        "settings": {"rule_length": 100, "rotation_deg": 0.0, "show_details": True,
                     "show_grid": True, "marker_zoom": 0.0, "text_zoom": 0.0,
                     "line_width_zoom": 0.0},
    }
    base.update(kw)
    return json.dumps(base)


def test_generate_creates_pdf(tmp_path):
    out = json.loads(survey_bridge.generate_survey_plot(_inputs(), str(tmp_path)))
    assert "pdf_path" in out
    assert Path(out["pdf_path"]).exists()


def test_generate_no_input_returns_error(tmp_path):
    out = json.loads(survey_bridge.generate_survey_plot(
        _inputs(map_path=None, section_path=None), str(tmp_path)))
    assert out["error"] == "no_input"


def test_generate_bad_file_returns_structured_error(tmp_path):
    bad = tmp_path / "broken.csv"
    bad.write_text("not,a,survey\n1,2,3\n")
    out = json.loads(survey_bridge.generate_survey_plot(
        _inputs(map_path=str(bad)), str(tmp_path)))
    assert out["error"] == "render_failed"
    assert "detail" in out


def test_prewarm_does_not_raise():
    survey_bridge.prewarm()
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.venv-mobile/bin/python -m pytest tests/test_survey_bridge.py -k "generate or prewarm" -v`
Expected: FAIL — `AttributeError: module 'survey_bridge' has no attribute 'generate_survey_plot'`.

- [x] **Step 3: Write the minimal implementation**

Add to `survey_bridge.py` (add `import json` to imports):

```python
import json

from cave_sketch.survey.merger import SectionProtocol
from cave_sketch.survey.survey import draw_survey


def generate_survey_plot(inputs_json: str, work_dir: str) -> str:
    """Entrypoint mirroring app/pages/1_survey_plot.py. See module/Interfaces for
    the inputs_json shape. Returns JSON {"pdf_path": ...} or {"error", "detail"}."""
    try:
        data = json.loads(inputs_json)
        settings = data.get("settings", {})

        map_csv = resolve_input(data.get("map_path"), work_dir, "map")
        section_csv = resolve_input(data.get("section_path"), work_dir, "section")
        child_map_csv = resolve_input(data.get("child_map_path"), work_dir, "child_map")
        child_section_csv = resolve_input(data.get("child_section_path"), work_dir, "child_section")

        if not map_csv and not section_csv:
            return json.dumps({"error": "no_input",
                               "detail": "Select at least one map or section file."})

        parent_station = data.get("parent_station") or ""
        child_station = data.get("child_station") or ""
        has_child = bool(child_map_csv or child_section_csv)
        if has_child and parent_station and child_station:
            err = validate_merge(map_csv or section_csv,
                                 child_map_csv or child_section_csv,
                                 parent_station, child_station)
            if err:
                return json.dumps({"error": "merge_invalid", "detail": err})

        pdf_path = str(Path(work_dir) / "survey.pdf")
        fig = draw_survey(
            title=data.get("survey_name", ""),
            rule_length=float(settings.get("rule_length", 100)),
            csv_map_path=map_csv,
            csv_section_path=section_csv,
            child_csv_map_path=child_map_csv,
            child_csv_section_path=child_section_csv,
            parent_station=parent_station or None,
            child_station=child_station or None,
            section_protocol=SectionProtocol(data.get("section_protocol", "simple")),
            output_path=pdf_path,
            surveyor_name=data.get("surveyor_name", ""),
            config={
                "rotation_deg": settings.get("rotation_deg", 0.0),
                "show_details": settings.get("show_details", True),
                "show_grid": settings.get("show_grid", True),
                "marker_zoom": settings.get("marker_zoom", 0.0),
                "text_zoom": settings.get("text_zoom", 0.0),
                "line_width_zoom": settings.get("line_width_zoom", 0.0),
            },
        )
        import matplotlib.pyplot as plt
        plt.close(fig)  # release the figure; mobile renders the PDF, not the figure
        return json.dumps({"pdf_path": pdf_path})
    except Exception as e:  # noqa: BLE001 — the bridge converts all failures to structured errors
        return json.dumps({"error": "render_failed", "detail": str(e)})


def prewarm() -> None:
    """Pay the one-time import + matplotlib font-cache cost off the critical path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure()
    fig.text(0.5, 0.5, "warm")  # forces the font manager to initialise
    plt.close(fig)
```

- [x] **Step 4: Run the full bridge suite to verify it passes**

Run: `.venv-mobile/bin/python -m pytest tests/test_survey_bridge.py -v`
Expected: 10 passed.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/python/survey_bridge.py tests/test_survey_bridge.py
git commit -m "feat(mobile-app): survey_bridge generate_survey_plot entrypoint + prewarm"
```

---

### [x] Task 5: App foundation — Gradle namespace, Application (Python + pre-warm), FileProvider · 02a6347

Create the real app package alongside the dormant spike. Switch the manifest to a new Application + Activity, start Python and kick off pre-warm at launch, and register a `FileProvider` for sharing.

**Files:**
- Modify: `android/app/build.gradle:8,12,16,48-56`
- Modify: `android/app/src/main/AndroidManifest.xml`
- Create: `android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`
- Create: `android/app/src/main/res/xml/file_paths.xml`

**Interfaces:**
- Produces: a launching app with package `com.cavesketch.app`, Python started + `survey_bridge.prewarm()` running on a background thread at startup, and a `FileProvider` authority `com.cavesketch.app.fileprovider`.

- [x] **Step 1: Update `build.gradle`**

Set `namespace` and `applicationId` to `com.cavesketch.app`, bump `versionName` to `0.2-phase1`, and add the navigation + lifecycle + coroutines-test dependencies. Replace the `namespace`/`applicationId`/`versionName` lines and the `dependencies { }` block:

```gradle
    namespace "com.cavesketch.app"
```
```gradle
        applicationId "com.cavesketch.app"
        versionName "0.2-phase1"
```
```gradle
dependencies {
    implementation "androidx.core:core-ktx:1.13.1"
    implementation "androidx.activity:activity-compose:1.9.0"
    implementation "androidx.lifecycle:lifecycle-viewmodel-compose:2.8.3"
    implementation "androidx.navigation:navigation-compose:2.7.7"
    implementation platform("androidx.compose:compose-bom:2024.06.00")
    implementation "androidx.compose.ui:ui"
    implementation "androidx.compose.material3:material3"
    implementation "androidx.compose.material:material-icons-extended"
    implementation "androidx.compose.ui:ui-tooling-preview"
    debugImplementation "androidx.compose.ui:ui-tooling"

    testImplementation "junit:junit:4.13.2"
    testImplementation "org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.1"
}
```

- [x] **Step 2: Create `CaveSketchApplication.kt`**

```kotlin
package com.cavesketch.app

import android.app.Application
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class CaveSketchApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        // Pre-warm: pay the one-time heavy import + matplotlib font-cache cost off
        // the critical path (Phase 1 measurement strategy). Harmless if cheap.
        Thread {
            try {
                Python.getInstance().getModule("survey_bridge").callAttr("prewarm")
            } catch (_: Throwable) { /* best-effort warm-up */ }
        }.start()
    }
}
```

- [x] **Step 3: Create a minimal `MainActivity.kt`**

(The nav host is added in Task 6; for now show a placeholder so the app launches.)

```kotlin
package com.cavesketch.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { App() } }
    }
}

@Composable
fun App() {
    Surface { Text("CaveSketch — foundation OK") }
}
```

- [x] **Step 4: Create `res/xml/file_paths.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<paths>
    <files-path name="outputs" path="." />
    <cache-path name="cache" path="." />
</paths>
```

- [x] **Step 5: Update `AndroidManifest.xml`**

Point the application at the new components and register the FileProvider:

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:name=".CaveSketchApplication"
        android:label="CaveSketch"
        android:theme="@android:style/Theme.Material.Light.NoActionBar">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
    </application>
</manifest>
```

- [x] **Step 6: Build and launch on the real phone**

Run:
```bash
cd android && JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:installDebug
```
Expected: BUILD SUCCESSFUL. Launch the app: it shows "CaveSketch — foundation OK". In `adb logcat`, confirm no crash and that the Python runtime started.

- [x] **Step 7: Commit**

```bash
git add android/app/build.gradle android/app/src/main/AndroidManifest.xml android/app/src/main/java/com/cavesketch/app android/app/src/main/res/xml/file_paths.xml
git commit -m "feat(mobile-app): app foundation — com.cavesketch.app, Python prewarm, FileProvider"
```

---

### [x] Task 6: Navigation skeleton + Satellite stub · fdd35fd

Add a two-destination nav graph so Phase 2 adds a screen rather than restructuring. Survey Plot is the start destination; Satellite is a stub.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/SatelliteStubScreen.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt` (placeholder body; filled in Tasks 8–11)
- Modify: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`

**Interfaces:**
- Consumes: `App()` composable entrypoint (Task 5).
- Produces: `AppNavHost()` composable; routes `"survey_plot"` and `"satellite"`; `SurveyPlotScreen()` and `SatelliteStubScreen()` composables.

- [x] **Step 1: Create `SatelliteStubScreen.kt`**

```kotlin
package com.cavesketch.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SatelliteStubScreen() {
    Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
        Text("Satellite Map — coming in Phase 2")
    }
}
```

- [x] **Step 2: Create a placeholder `SurveyPlotScreen.kt`**

```kotlin
package com.cavesketch.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SurveyPlotScreen() {
    Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
        Text("Survey Plot")
    }
}
```

- [x] **Step 3: Create `AppNavHost.kt`**

```kotlin
package com.cavesketch.app.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.Terrain
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController

@Composable
fun AppNavHost() {
    val nav = rememberNavController()
    val current = nav.currentBackStackEntryAsState().value?.destination?.route
    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = current == "survey_plot",
                    onClick = { nav.navigate("survey_plot") { launchSingleTop = true } },
                    icon = { Icon(Icons.Filled.Terrain, null) },
                    label = { Text("Survey") },
                )
                NavigationBarItem(
                    selected = current == "satellite",
                    onClick = { nav.navigate("satellite") { launchSingleTop = true } },
                    icon = { Icon(Icons.Filled.Map, null) },
                    label = { Text("Satellite") },
                )
            }
        }
    ) { padding ->
        NavHost(nav, startDestination = "survey_plot", modifier = Modifier.padding(padding)) {
            composable("survey_plot") { SurveyPlotScreen() }
            composable("satellite") { SatelliteStubScreen() }
        }
    }
}
```

- [x] **Step 4: Wire `App()` to the nav host**

In `MainActivity.kt`, replace the `App()` body:

```kotlin
@Composable
fun App() {
    com.cavesketch.app.ui.AppNavHost()
}
```

- [x] **Step 5: Build and verify on the real phone**

Run: `cd android && JAVA_HOME="…" ./gradlew :app:installDebug`
Expected: BUILD SUCCESSFUL. On-device: bottom bar with "Survey" and "Satellite"; tapping switches between the "Survey Plot" placeholder and the "coming in Phase 2" stub.

- [x] **Step 6: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app
git commit -m "feat(mobile-app): navigation skeleton + Satellite stub"
```

---

### [x] Task 7: `PythonBridge` + `SurveyPlotViewModel` (+ JVM unit test) · 65c6577

Add the Kotlin↔Python wrapper behind an interface (so it can be faked), and the ViewModel that owns UI state + the async Generate. Unit-test the state machine on the JVM.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/bridge/SurveyBridge.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/bridge/PythonBridge.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt`
- Create: `android/app/src/test/java/com/cavesketch/app/SurveyPlotViewModelTest.kt`

**Interfaces:**
- Consumes: `survey_bridge.generate_survey_plot(inputs_json, work_dir)` (Task 4) via Chaquopy.
- Produces:
  - `interface SurveyBridge { suspend fun generate(inputsJson: String, workDir: String): String }`
  - `class PythonBridge(io: CoroutineDispatcher) : SurveyBridge`
  - `data class SurveyInputs(...)` and its `toJson(): String`.
  - `sealed interface PlotState { Idle; Generating(phase: String); Success(pdfPath: String); Error(message: String) }`
  - `class SurveyPlotViewModel(bridge: SurveyBridge, workDir: String, io: CoroutineDispatcher) { val state: StateFlow<PlotState>; fun generate(inputs: SurveyInputs) }`

- [x] **Step 1: Write the failing ViewModel test**

Create `android/app/src/test/java/com/cavesketch/app/SurveyPlotViewModelTest.kt`:

```kotlin
package com.cavesketch.app

import com.cavesketch.app.bridge.SurveyBridge
import com.cavesketch.app.ui.PlotState
import com.cavesketch.app.ui.SurveyInputs
import com.cavesketch.app.ui.SurveyPlotViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class SurveyPlotViewModelTest {
    private fun vm(bridge: SurveyBridge) =
        SurveyPlotViewModel(bridge, "/tmp", StandardTestDispatcher())

    private val inputs = SurveyInputs(mapPath = "/tmp/map.csv")

    @Test
    fun success_path_emits_success_with_pdf_path() = runTest {
        val model = vm(object : SurveyBridge {
            override suspend fun generate(inputsJson: String, workDir: String) =
                """{"pdf_path":"/tmp/survey.pdf"}"""
        })
        model.generate(inputs)
        advanceUntilIdle()
        assertEquals(PlotState.Success("/tmp/survey.pdf"), model.state.value)
    }

    @Test
    fun error_path_emits_error_with_detail() = runTest {
        val model = vm(object : SurveyBridge {
            override suspend fun generate(inputsJson: String, workDir: String) =
                """{"error":"render_failed","detail":"boom"}"""
        })
        model.generate(inputs)
        advanceUntilIdle()
        assertTrue((model.state.value as PlotState.Error).message.contains("boom"))
    }
}
```

- [x] **Step 2: Run the test to verify it fails**

Run: `cd android && JAVA_HOME="…" ./gradlew :app:testDebugUnitTest`
Expected: compilation failure — `SurveyBridge` / `SurveyPlotViewModel` unresolved.

- [x] **Step 3: Create the bridge interface and inputs**

`android/app/src/main/java/com/cavesketch/app/bridge/SurveyBridge.kt`:

```kotlin
package com.cavesketch.app.bridge

interface SurveyBridge {
    /** Calls survey_bridge.generate_survey_plot; returns its JSON result string. */
    suspend fun generate(inputsJson: String, workDir: String): String
}
```

`android/app/src/main/java/com/cavesketch/app/bridge/PythonBridge.kt`:

```kotlin
package com.cavesketch.app.bridge

import com.chaquo.python.Python
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext

class PythonBridge(private val io: CoroutineDispatcher) : SurveyBridge {
    override suspend fun generate(inputsJson: String, workDir: String): String =
        withContext(io) {
            Python.getInstance()
                .getModule("survey_bridge")
                .callAttr("generate_survey_plot", inputsJson, workDir)
                .toString()
        }
}
```

- [x] **Step 4: Create the ViewModel, state, and inputs→JSON**

`android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt`:

```kotlin
package com.cavesketch.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cavesketch.app.bridge.SurveyBridge
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.json.JSONObject

sealed interface PlotState {
    data object Idle : PlotState
    data class Generating(val phase: String) : PlotState
    data class Success(val pdfPath: String) : PlotState
    data class Error(val message: String) : PlotState
}

data class SurveyInputs(
    val mapPath: String? = null,
    val sectionPath: String? = null,
    val childMapPath: String? = null,
    val childSectionPath: String? = null,
    val surveyName: String = "",
    val surveyorName: String = "",
    val parentStation: String = "",
    val childStation: String = "",
    val sectionProtocol: String = "simple",
    val ruleLength: Int = 100,
    val rotationDeg: Int = 0,
    val showDetails: Boolean = true,
    val showGrid: Boolean = true,
    val markerZoom: Double = 0.0,
    val textZoom: Double = 0.0,
    val lineWidthZoom: Double = 0.0,
) {
    fun toJson(): String {
        val settings = JSONObject()
            .put("rule_length", ruleLength)
            .put("rotation_deg", rotationDeg)
            .put("show_details", showDetails)
            .put("show_grid", showGrid)
            .put("marker_zoom", markerZoom)
            .put("text_zoom", textZoom)
            .put("line_width_zoom", lineWidthZoom)
        return JSONObject()
            .put("map_path", mapPath ?: JSONObject.NULL)
            .put("section_path", sectionPath ?: JSONObject.NULL)
            .put("child_map_path", childMapPath ?: JSONObject.NULL)
            .put("child_section_path", childSectionPath ?: JSONObject.NULL)
            .put("survey_name", surveyName)
            .put("surveyor_name", surveyorName)
            .put("parent_station", parentStation)
            .put("child_station", childStation)
            .put("section_protocol", sectionProtocol)
            .put("settings", settings)
            .toString()
    }
}

class SurveyPlotViewModel(
    private val bridge: SurveyBridge,
    private val workDir: String,
    private val io: CoroutineDispatcher,
) : ViewModel() {
    private val _state = MutableStateFlow<PlotState>(PlotState.Idle)
    val state: StateFlow<PlotState> = _state.asStateFlow()

    fun generate(inputs: SurveyInputs) {
        _state.value = PlotState.Generating("Starting engine…")
        viewModelScope.launch {
            try {
                val resultJson = bridge.generate(inputs.toJson(), workDir)
                val obj = JSONObject(resultJson)
                _state.value = if (obj.has("pdf_path")) {
                    PlotState.Success(obj.getString("pdf_path"))
                } else {
                    PlotState.Error(obj.optString("detail", obj.optString("error", "Unknown error")))
                }
            } catch (e: Throwable) {
                _state.value = PlotState.Error(e.message ?: "Generation failed")
            }
        }
    }
}
```

Note: `viewModelScope` uses `Dispatchers.Main` by default; the test injects `StandardTestDispatcher` via `Dispatchers.setMain` is avoided by keeping the bridge call suspend and the test using `runTest`. If `viewModelScope` causes a "Main dispatcher not set" error in the test, add to the test class:

```kotlin
@org.junit.Before fun setUp() = kotlinx.coroutines.Dispatchers.setMain(StandardTestDispatcher())
@org.junit.After fun tearDown() = kotlinx.coroutines.Dispatchers.resetMain()
```

- [x] **Step 5: Run the test to verify it passes**

Run: `cd android && JAVA_HOME="…" ./gradlew :app:testDebugUnitTest`
Expected: 2 tests pass. (If you hit the Main-dispatcher error, apply the `setUp`/`tearDown` from Step 4, then re-run.)

- [x] **Step 6: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/bridge android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt android/app/src/test
git commit -m "feat(mobile-app): PythonBridge + SurveyPlotViewModel with unit tests"
```

---

### [x] Task 8: Survey Plot screen — file pickers, settings form, name fields · f069f4c

Build the real input UI: SAF pickers for main map/section, the settings form at web-parity ranges, and the name fields, all bound to a `SurveyInputs` held in screen state.

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/FilePickerRow.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/SettingsForm.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/util/FileCopy.kt`

**Interfaces:**
- Consumes: `SurveyInputs` (Task 7).
- Produces:
  - `copyUriToDir(context, uri, dir, fileName): String` — copies a picked `content://` file into app storage, returns the absolute path.
  - `FilePickerRow(label, fileName, onPick)` composable using `ActivityResultContracts.OpenDocument`.
  - `SettingsForm(inputs, onChange)` composable.
  - `SurveyPlotScreen` holding `SurveyInputs` state and rendering pickers + settings + names.

- [x] **Step 1: Create `FileCopy.kt`**

```kotlin
package com.cavesketch.app.util

import android.content.Context
import android.net.Uri
import java.io.File

/** Copies a picked content:// document into [dir] as [fileName]; returns its path. */
fun copyUriToDir(context: Context, uri: Uri, dir: File, fileName: String): String {
    val out = File(dir, fileName)
    context.contentResolver.openInputStream(uri).use { input ->
        requireNotNull(input) { "Cannot open $uri" }
        out.outputStream().use { input.copyTo(it) }
    }
    return out.absolutePath
}

/** Best-effort display name → extension (".dxf"/".csv"); defaults to the uri path. */
fun extensionOf(context: Context, uri: Uri): String {
    val name = context.contentResolver.query(uri, null, null, null, null)?.use { c ->
        val idx = c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
        if (idx >= 0 && c.moveToFirst()) c.getString(idx) else null
    } ?: uri.lastPathSegment ?: ""
    return if (name.lowercase().endsWith(".dxf")) ".dxf" else ".csv"
}
```

- [x] **Step 2: Create `FilePickerRow.kt`**

```kotlin
package com.cavesketch.app.ui.components

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

@Composable
fun FilePickerRow(label: String, fileName: String?, onPick: (Uri) -> Unit) {
    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri -> if (uri != null) onPick(uri) }
    Column(Modifier.fillMaxWidth()) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Button(onClick = { launcher.launch(arrayOf("*/*")) }) { Text(label) }
            Text(fileName ?: "none")
        }
    }
}
```

(Note: TopoDroid DXF/CSV often report generic MIME types, so the picker filter is `*/*`; the extension is resolved from the display name in `extensionOf`.)

- [x] **Step 3: Create `SettingsForm.kt` (web-parity ranges)**

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import com.cavesketch.app.ui.SurveyInputs

@Composable
fun SettingsForm(inputs: SurveyInputs, onChange: (SurveyInputs) -> Unit) {
    Text("Survey settings")

    // Rule length: 5..1000, step 5 (multiple-of-5 constraint).
    Text("Rule length (m): ${inputs.ruleLength}")
    Slider(
        value = inputs.ruleLength.toFloat(),
        onValueChange = { onChange(inputs.copy(ruleLength = (Math.round(it / 5f) * 5))) },
        valueRange = 5f..1000f,
    )

    // Map rotation: -180..180, step 1.
    Text("Map rotation (°): ${inputs.rotationDeg}")
    Slider(
        value = inputs.rotationDeg.toFloat(),
        onValueChange = { onChange(inputs.copy(rotationDeg = Math.round(it))) },
        valueRange = -180f..180f,
    )

    ZoomSlider("Marker zoom", inputs.markerZoom) { onChange(inputs.copy(markerZoom = it)) }
    ZoomSlider("Text zoom", inputs.textZoom) { onChange(inputs.copy(textZoom = it)) }
    ZoomSlider("Line width zoom", inputs.lineWidthZoom) { onChange(inputs.copy(lineWidthZoom = it)) }

    Row(Modifier.fillMaxWidth()) {
        Checkbox(inputs.showDetails, { onChange(inputs.copy(showDetails = it)) })
        Text("Show station markers")
    }
    Row(Modifier.fillMaxWidth()) {
        Checkbox(inputs.showGrid, { onChange(inputs.copy(showGrid = it)) })
        Text("Show grid")
    }
}

@Composable
private fun ZoomSlider(label: String, value: Double, onChange: (Double) -> Unit) {
    Text("$label [-1, 1]: ${"%.1f".format(value)}")
    Slider(
        value = value.toFloat(),
        onValueChange = { onChange((Math.round(it * 10f) / 10f).toDouble()) },
        valueRange = -1f..1f,
    )
}
```

- [x] **Step 4: Build the `SurveyPlotScreen` body**

Replace `SurveyPlotScreen.kt`:

```kotlin
package com.cavesketch.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.components.FilePickerRow
import com.cavesketch.app.ui.components.SettingsForm
import com.cavesketch.app.util.copyUriToDir
import com.cavesketch.app.util.extensionOf

@Composable
fun SurveyPlotScreen() {
    val context = LocalContext.current
    var inputs by remember { mutableStateOf(SurveyInputs()) }

    Column(Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())) {
        Text("Survey Plot")

        FilePickerRow("Pick Cave Map", inputs.mapPath?.let { "map" + extOf(it) }) { uri ->
            val path = copyUriToDir(context, uri, context.filesDir, "map" + extensionOf(context, uri))
            inputs = inputs.copy(mapPath = path)
        }
        FilePickerRow("Pick Cave Section", inputs.sectionPath?.let { "section" + extOf(it) }) { uri ->
            val path = copyUriToDir(context, uri, context.filesDir, "section" + extensionOf(context, uri))
            inputs = inputs.copy(sectionPath = path)
        }

        OutlinedTextField(
            value = inputs.surveyName,
            onValueChange = { inputs = inputs.copy(surveyName = it) },
            label = { Text("Survey name") },
        )
        OutlinedTextField(
            value = inputs.surveyorName,
            onValueChange = { inputs = inputs.copy(surveyorName = it) },
            label = { Text("Surveyor name") },
        )

        SettingsForm(inputs) { inputs = it }
    }
}

private fun extOf(path: String) = if (path.lowercase().endsWith(".dxf")) ".dxf" else ".csv"
```

- [x] **Step 5: Build and verify on the real phone**

Run: `cd android && JAVA_HOME="…" ./gradlew :app:installDebug`
Expected: BUILD SUCCESSFUL. On-device: the Survey screen scrolls; tapping "Pick Cave Map"/"Pick Cave Section" opens the system file picker and the chosen file name appears; name fields accept text; sliders/checkboxes move and rule-length snaps to multiples of 5.

- [x] **Step 6: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui android/app/src/main/java/com/cavesketch/app/util
git commit -m "feat(mobile-app): Survey Plot inputs — file pickers, settings form, names"
```

---

### Task 9: Merge controls UI

Add the optional child-survey pickers, the station-ID fields, and the section-protocol selector — shown only when a child file is present, mirroring the web's conditional reveal.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt`

**Interfaces:**
- Consumes: `SurveyInputs` (Task 7), `FilePickerRow` (Task 8).
- Produces: `MergeControls(inputs, context, onChange)` composable.

- [ ] **Step 1: Create `MergeControls.kt`**

```kotlin
package com.cavesketch.app.ui.components

import android.content.Context
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.selection.selectable
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import com.cavesketch.app.ui.SurveyInputs
import com.cavesketch.app.util.copyUriToDir
import com.cavesketch.app.util.extensionOf

@Composable
fun MergeControls(inputs: SurveyInputs, context: Context, onChange: (SurveyInputs) -> Unit) {
    Text("Merge another survey (optional)")

    FilePickerRow("Pick Child Map", inputs.childMapPath?.let { "child_map" }) { uri ->
        val p = copyUriToDir(context, uri, context.filesDir, "child_map" + extensionOf(context, uri))
        onChange(inputs.copy(childMapPath = p))
    }
    FilePickerRow("Pick Child Section", inputs.childSectionPath?.let { "child_section" }) { uri ->
        val p = copyUriToDir(context, uri, context.filesDir, "child_section" + extensionOf(context, uri))
        onChange(inputs.copy(childSectionPath = p))
    }

    val hasChild = inputs.childMapPath != null || inputs.childSectionPath != null
    if (hasChild) {
        OutlinedTextField(
            value = inputs.parentStation,
            onValueChange = { onChange(inputs.copy(parentStation = it)) },
            label = { Text("Main station ID (e.g. 30)") },
        )
        OutlinedTextField(
            value = inputs.childStation,
            onValueChange = { onChange(inputs.copy(childStation = it)) },
            label = { Text("Child station ID (e.g. 47)") },
        )
        if (inputs.childSectionPath != null) {
            Text("Section merge protocol")
            listOf("simple", "mirror", "displacement").forEach { proto ->
                Row(Modifier.selectable(
                    selected = inputs.sectionProtocol == proto,
                    onClick = { onChange(inputs.copy(sectionProtocol = proto)) },
                )) {
                    RadioButton(inputs.sectionProtocol == proto, null)
                    Text(proto.replaceFirstChar { it.uppercase() })
                }
            }
        }
    }
}
```

(Add the missing import `import androidx.compose.ui.Modifier` to the file.)

- [ ] **Step 2: Insert `MergeControls` into `SurveyPlotScreen`**

In `SurveyPlotScreen.kt`, after the section picker and before the name fields, add:

```kotlin
        com.cavesketch.app.ui.components.MergeControls(inputs, context) { inputs = it }
```

- [ ] **Step 3: Build and verify on the real phone**

Run: `cd android && JAVA_HOME="…" ./gradlew :app:installDebug`
Expected: BUILD SUCCESSFUL. On-device: child pickers appear; after picking a child file, the station-ID fields appear; picking a child *section* additionally reveals the Simple/Mirror/Displacement selector.

- [ ] **Step 4: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui
git commit -m "feat(mobile-app): merge controls UI (child pickers, stations, protocol)"
```

---

### Task 10: Generate → staged progress → static PDF preview

Wire the screen to the ViewModel: a Generate button that runs async with staged progress, and a static fit-to-width PDF preview rendered from the result via `PdfRenderer`. Apply the cold-start strategy decided in Task 1.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/PdfPreview.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt` (provide the ViewModel)

**Interfaces:**
- Consumes: `SurveyPlotViewModel`, `PlotState`, `SurveyInputs` (Task 7); `PythonBridge` (Task 7).
- Produces: `renderPdfFirstPage(pdfPath: String): Bitmap`; `PdfPreview(pdfPath)` composable; a Generate button bound to `viewModel.generate(inputs)`.

- [ ] **Step 1: Create `PdfPreview.kt`**

```kotlin
package com.cavesketch.app.ui

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import java.io.File

/** Renders page 1 of [pdfPath] to a fit-to-width bitmap (2× for legibility). */
fun renderPdfFirstPage(pdfPath: String): Bitmap {
    val pfd = ParcelFileDescriptor.open(File(pdfPath), ParcelFileDescriptor.MODE_READ_ONLY)
    PdfRenderer(pfd).use { renderer ->
        renderer.openPage(0).use { page ->
            val bmp = Bitmap.createBitmap(page.width * 2, page.height * 2, Bitmap.Config.ARGB_8888)
            bmp.eraseColor(Color.WHITE)
            page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            return bmp
        }
    }
}

@Composable
fun PdfPreview(pdfPath: String) {
    val bitmap = remember(pdfPath) { renderPdfFirstPage(pdfPath) }
    Image(bitmap.asImageBitmap(), contentDescription = "Survey plot preview",
        modifier = Modifier.fillMaxWidth())
}
```

- [ ] **Step 2: Provide the ViewModel from `MainActivity`**

Replace `App()` in `MainActivity.kt` to build the bridge + ViewModel and pass it down:

```kotlin
@Composable
fun App() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val viewModel = androidx.lifecycle.viewmodel.compose.viewModel<com.cavesketch.app.ui.SurveyPlotViewModel>(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T =
                com.cavesketch.app.ui.SurveyPlotViewModel(
                    com.cavesketch.app.bridge.PythonBridge(kotlinx.coroutines.Dispatchers.IO),
                    context.filesDir.absolutePath,
                    kotlinx.coroutines.Dispatchers.IO,
                ) as T
        }
    )
    com.cavesketch.app.ui.AppNavHost(viewModel)
}
```

Update `AppNavHost` (Task 6) to take the ViewModel and pass it to `SurveyPlotScreen`:

```kotlin
@Composable
fun AppNavHost(viewModel: SurveyPlotViewModel) {
    // …unchanged scaffold…
    composable("survey_plot") { SurveyPlotScreen(viewModel) }
    composable("satellite") { SatelliteStubScreen() }
}
```

- [ ] **Step 3: Add Generate + progress + preview to `SurveyPlotScreen`**

Change the signature to `SurveyPlotScreen(viewModel: SurveyPlotViewModel)`, collect state, and append below `SettingsForm`:

```kotlin
        val state by viewModel.state.collectAsState()
        val canGenerate = inputs.mapPath != null || inputs.sectionPath != null

        Button(enabled = canGenerate && state !is PlotState.Generating,
            onClick = { viewModel.generate(inputs) }) { Text("Generate Survey Plot") }

        when (val s = state) {
            is PlotState.Generating -> {
                CircularProgressIndicator()
                Text(s.phase)
            }
            is PlotState.Error -> Text("⚠️ ${s.message}")
            is PlotState.Success -> PdfPreview(s.pdfPath)
            PlotState.Idle -> {}
        }
```

Add imports: `androidx.compose.material3.Button`, `androidx.compose.material3.CircularProgressIndicator`, `androidx.compose.runtime.collectAsState`, `androidx.compose.runtime.getValue`.

- [ ] **Step 4: Apply the Task 1 cold-start strategy**

Pre-warm is already wired in `CaveSketchApplication` (Task 5). Stage the progress label so the wait is legible: in `SurveyPlotViewModel.generate`, the initial label is "Starting engine…"; immediately before calling the bridge, set `_state.value = PlotState.Generating("Rendering survey…")`. If Task 1 found `draw_ms` dominates even warm, also record the optimisation follow-up in `android/DEVLOG.md` (added scope), but still ship this UI.

```kotlin
    fun generate(inputs: SurveyInputs) {
        _state.value = PlotState.Generating("Starting engine…")
        viewModelScope.launch {
            try {
                _state.value = PlotState.Generating("Rendering survey…")
                val resultJson = bridge.generate(inputs.toJson(), workDir)
                // …unchanged parsing…
```

- [ ] **Step 5: Build, install, and verify on the real phone**

Run: `cd android && JAVA_HOME="…" ./gradlew :app:installDebug`
Expected: BUILD SUCCESSFUL. On-device: pick `sample.dxf` (push it with `adb push tests/fixtures/sample.dxf /sdcard/Download/`), tap Generate → progress shows, then a survey plot preview appears. **Eyeball-compare** it to the web output for the same file (run the Streamlit app on the laptop). Record the cold + warm render times in `android/DEVLOG.md`.

- [ ] **Step 6: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app android/DEVLOG.md
git commit -m "feat(mobile-app): Generate flow — progress + static PDF preview"
```

---

### Task 11: Save / Share via FileProvider

Replace the web download with an Android share sheet (and "Open with"), so the PDF can go to Files, Drive, or a PDF viewer.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/util/Share.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt`

**Interfaces:**
- Consumes: the `FileProvider` authority `com.cavesketch.app.fileprovider` (Task 5); `PlotState.Success.pdfPath` (Task 7).
- Produces: `sharePdf(context, pdfPath, displayName)`.

- [ ] **Step 1: Create `Share.kt`**

```kotlin
package com.cavesketch.app.util

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

/** Launches the Android share sheet for [pdfPath] via the app's FileProvider. */
fun sharePdf(context: Context, pdfPath: String, displayName: String) {
    val file = File(pdfPath)
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "application/pdf"
        putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_TITLE, displayName)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "Share survey PDF"))
}
```

- [ ] **Step 2: Add a Share button to the Success state**

In `SurveyPlotScreen.kt`, change the `PlotState.Success` branch:

```kotlin
            is PlotState.Success -> {
                PdfPreview(s.pdfPath)
                Button(onClick = {
                    val name = inputs.surveyName.ifBlank { "survey" } + ".pdf"
                    com.cavesketch.app.util.sharePdf(context, s.pdfPath, name)
                }) { Text("Save / Share PDF") }
            }
```

- [ ] **Step 3: Build, install, and verify on the real phone**

Run: `cd android && JAVA_HOME="…" ./gradlew :app:installDebug`
Expected: BUILD SUCCESSFUL. On-device: after generating, tap "Save / Share PDF" → the system share sheet opens; share to a PDF viewer / Files and confirm the PDF opens correctly. (This also covers "Save to device" via the sheet's "Save to Files".)

- [ ] **Step 4: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/util/Share.kt android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt
git commit -m "feat(mobile-app): save/share PDF via FileProvider share sheet"
```

---

### Task 12: Session cleanup, delete spike, verification gates, DEVLOG

Finalise: clean per-session temp files, delete the throwaway spike, run all gates, do the on-device parity sweep, and log the phase.

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt`
- Delete: `android/app/src/main/java/com/cavesketch/spike/MainActivity.kt`, `android/app/src/main/java/com/cavesketch/spike/SpikeApplication.kt`, `android/app/src/main/python/spike.py`
- Modify: `android/DEVLOG.md`

**Interfaces:**
- Consumes: everything above.
- Produces: a clean, parity-complete app; no `com.cavesketch.spike` code remains.

- [ ] **Step 1: Clear stale outputs at launch**

In `CaveSketchApplication.onCreate`, before starting the pre-warm thread, delete previous-session artefacts so a fresh run never shows a stale PDF:

```kotlin
        // Per-session cleanup: remove last run's intermediate CSVs + PDF.
        listOf("map.csv", "section.csv", "child_map.csv", "child_section.csv", "survey.pdf")
            .forEach { java.io.File(filesDir, it).delete() }
```

- [ ] **Step 2: Delete the throwaway spike**

Run:
```bash
git rm android/app/src/main/java/com/cavesketch/spike/MainActivity.kt \
       android/app/src/main/java/com/cavesketch/spike/SpikeApplication.kt \
       android/app/src/main/python/spike.py
```

- [ ] **Step 3: Run the Python gates**

Run:
```bash
uv run ruff check .
uv run mypy cave_sketch/
uv run pytest -q
.venv-mobile/bin/python -m pytest tests/test_survey_bridge.py -v
```
Expected: ruff clean, mypy clean, the web/core pytest suite green, and the 10 bridge tests pass. (`survey_bridge.py` is excluded from `mypy cave_sketch/` since it lives under `android/`; if `ruff` flags it, it follows the same E/F/I rules — fix any findings.)

- [ ] **Step 4: Run the Kotlin gate and build**

Run:
```bash
cd android && JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest :app:assembleDebug
```
Expected: unit tests pass; BUILD SUCCESSFUL; no references to `com.cavesketch.spike` remain (the build would fail otherwise).

- [ ] **Step 5: On-device parity sweep**

Install (`./gradlew :app:installDebug`) and verify against the web Survey Plot page:
1. Single map DXF → Generate → preview matches web; share works.
2. Map + section → both views render.
3. Merge: main + child map with valid stations → merged plot; invalid/missing station → inline error, no crash.
4. Settings: change rule length, rotation, zooms, toggles → reflected in the output.
Record pass/fail for each.

- [ ] **Step 6: Update `android/DEVLOG.md`**

Add a dated Phase 1 entry: the cold-start breakdown + chosen strategy (from Task 1), final cold/warm render times, the parity-sweep results, and any surprises.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(mobile-app): Phase 1 complete — session cleanup, remove spike, DEVLOG"
```

---

## Self-Review Notes

- **Spec coverage:** measurement-first (Task 1 / spec §3 Step 1); foundation + nav skeleton + Satellite stub (Tasks 5–6 / §3 Step 2); file pickers, settings parity, merge, generate, static preview (Tasks 8–10 / §3 Steps 3); save/share (Task 11 / §3 Step 4); bridge contract + single entrypoint (Tasks 2–4 / §5); error handling incl. no-input, merge validation, structured render errors, multiple-of-5 rule length (Tasks 3,4,8,10 / §6); offline (no network introduced anywhere / §7); testing — bridge pytest under relaxed pins, ViewModel JVM tests, on-device manual (Tasks 2–4,7,12 / §8); exit criteria + gates + DEVLOG + spike deletion (Task 12 / §9). Non-goals (satellite/KMZ, icon, pinch-zoom, release build) are untouched.
- **Type consistency:** `SurveyInputs`/`PlotState`/`SurveyBridge`/`generate`/`generate_survey_plot`/`resolve_input`/`validate_merge`/`prewarm` names are used identically across tasks; the bridge JSON keys in `SurveyInputs.toJson()` (Task 7) match the keys read by `generate_survey_plot` (Task 4).
