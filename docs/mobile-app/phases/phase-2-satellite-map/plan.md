# Phase 2 — Satellite Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Android Satellite Map screen at full parity with the web `2_satellite_map.py` page — GPS-point georeferencing → HTML/JSON/KMZ outputs, with online preview and graceful-offline KMZ/JSON export.

**Architecture:** A new `satellite_bridge.py` calls the untouched core `draw_map`. The cave-map CSV is handed from the Survey Plot screen to the Satellite screen through an app-scoped reactive `SurveyResultStore` (the Phase 1 survey bridge is extended, additively, to surface the effective map CSV path). A `SatelliteViewModel` drives a state machine consumed by a Compose `SatelliteScreen` that replaces the Phase 1 stub.

**Tech Stack:** Kotlin + Jetpack Compose, Chaquopy (CPython 3.13), Python core (`cave_sketch`), folium/pandas, JUnit + kotlinx-coroutines-test, pytest.

## Global Constraints

- `cave_sketch/` stays **untouched and Streamlit-free**; all new logic lives under `android/`. (verbatim: umbrella §12)
- The Streamlit web app behaviour is **unchanged**.
- Python managed with **`uv`** (never bare `pip`); commit `uv.lock` if it changes.
- Verification gates before "done": `uv run ruff check .`, `uv run mypy cave_sketch/`, `uv run pytest` all pass.
- No new Chaquopy pip pins (folium 0.19.5, pandas 2.1.3, numpy 1.26.2 already in `android/app/build.gradle`).
- Mobile work logs to `android/DEVLOG.md` (Phase 1 entry format).
- Bridge modules live under `android/app/src/main/python/` and are **never imported by `cave_sketch`**.
- GPS coordinates are parsed via the core `cave_sketch.geo.coordinates.parse_coordinate` (decimal, `.` or `,` separator).

---

### Task 1: `satellite_bridge.py` — Python bridge for the Satellite screen

**Files:**
- Create: `android/app/src/main/python/satellite_bridge.py`
- Test: `tests/test_satellite_bridge.py`

**Interfaces:**
- Consumes: core `cave_sketch.satellite_view.draw_map(map_path, gps_points, output_path, map_name, additional_json_maps, rotation_angle) -> (html, json_path, kmz_path)`; core `cave_sketch.geo.coordinates.parse_coordinate(str) -> float | None`.
- Produces: `generate_satellite_map(inputs_json: str, work_dir: str) -> str` returning JSON `{"html_path","json_path","kmz_path"}` on success or `{"error","detail"}` on failure. Input JSON shape: `{"map_path": str, "gps_points": [{"station","lat","lon"}], "survey_name": str, "rotation_angle": number, "additional_json_maps": [str]}` where `lat`/`lon` are raw strings.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_satellite_bridge.py`:

```python
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

# Load the bridge module (lives under android/, not a package).
_BRIDGE_PATH = (
    Path(__file__).parent.parent
    / "android/app/src/main/python/satellite_bridge.py"
)
_spec = importlib.util.spec_from_file_location("satellite_bridge", _BRIDGE_PATH)
satellite_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(satellite_bridge)


@pytest.fixture
def map_csv(tmp_path):
    df = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "X": [0.0, 10.0],
        "Y": [0.0, 0.0],
        "Links": ["st2", "st1"],
        "Type": ["station", "station"],
    })
    path = tmp_path / "map.csv"
    df.to_csv(path, index=False)
    return str(path)


def _inputs(map_path, points, **kw):
    base = {
        "map_path": map_path,
        "gps_points": points,
        "survey_name": "Test",
        "rotation_angle": 0,
        "additional_json_maps": [],
    }
    base.update(kw)
    return json.dumps(base)


def test_success_writes_three_outputs(map_csv, tmp_path):
    points = [{"station": "st1", "lat": "45.0", "lon": "7.0"}]
    out = json.loads(satellite_bridge.generate_satellite_map(_inputs(map_csv, points), str(tmp_path)))
    assert "error" not in out
    assert Path(out["html_path"]).exists()
    assert Path(out["json_path"]).exists()
    assert Path(out["kmz_path"]).exists()


def test_no_map_path_errors(tmp_path):
    out = json.loads(satellite_bridge.generate_satellite_map(_inputs("", []), str(tmp_path)))
    assert out["error"] == "no_map"


def test_empty_points_errors(map_csv, tmp_path):
    out = json.loads(satellite_bridge.generate_satellite_map(_inputs(map_csv, []), str(tmp_path)))
    assert out["error"] == "invalid_points"


def test_invalid_coordinate_errors(map_csv, tmp_path):
    points = [{"station": "st1", "lat": "abc", "lon": "7.0"}]
    out = json.loads(satellite_bridge.generate_satellite_map(_inputs(map_csv, points), str(tmp_path)))
    assert out["error"] == "invalid_points"


def test_no_anchor_match_errors(map_csv, tmp_path):
    points = [{"station": "nope", "lat": "45.0", "lon": "7.0"}]
    out = json.loads(satellite_bridge.generate_satellite_map(_inputs(map_csv, points), str(tmp_path)))
    assert out["error"] == "no_anchor_match"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_satellite_bridge.py -v`
Expected: FAIL — `FileNotFoundError` / module load error (bridge file does not exist yet).

- [ ] **Step 3: Write the bridge implementation**

Create `android/app/src/main/python/satellite_bridge.py`:

```python
"""Mobile bridge for the Satellite Map screen. Mirrors app/pages/2_satellite_map.py:
validate GPS points, run draw_map, return output paths. Lives under android/, never
imported by cave_sketch. Single entrypoint: generate_satellite_map(inputs_json, work_dir)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cave_sketch.geo.coordinates import parse_coordinate
from cave_sketch.satellite_view import draw_map


def _validate_points(gps_points) -> str | None:
    """Validate and normalise GPS points in place (lat/lon strings -> floats).
    Mirror app/components/gps_points.py:validate_known_points. Return an error
    message, or None when all points are valid."""
    if not gps_points:
        return "Add at least one GPS point."
    for pt in gps_points:
        if not str(pt.get("station", "")).strip():
            return "Every GPS point needs a station ID."
        lat = parse_coordinate(str(pt.get("lat", "")))
        lon = parse_coordinate(str(pt.get("lon", "")))
        if lat is None or lon is None:
            return "Every GPS point needs a valid latitude and longitude."
        pt["lat"], pt["lon"] = lat, lon
    return None


def generate_satellite_map(inputs_json: str, work_dir: str) -> str:
    """Entrypoint mirroring app/pages/2_satellite_map.py. Returns JSON
    {"html_path","json_path","kmz_path"} or {"error","detail"}."""
    try:
        data = json.loads(inputs_json)

        map_path = data.get("map_path")
        if not map_path:
            return json.dumps({"error": "no_map",
                               "detail": "Generate a survey plot first."})

        gps_points = data.get("gps_points") or []
        err = _validate_points(gps_points)
        if err:
            return json.dumps({"error": "invalid_points", "detail": err})

        # Guard: at least one anchor station must exist in the map CSV, else
        # draw_map yields all-NaN coordinates (a broken map).
        node_ids = set(pd.read_csv(map_path)["Node_Id"].astype(str))
        if not any(str(p["station"]) in node_ids for p in gps_points):
            return json.dumps({"error": "no_anchor_match",
                               "detail": "None of the GPS stations match a station "
                                         "in the survey."})

        html_path = str(Path(work_dir) / "survey.html")
        _, json_path, kmz_path = draw_map(
            map_path=map_path,
            gps_points=gps_points,
            output_path=html_path,
            map_name=data.get("survey_name") or "Cave",
            additional_json_maps=data.get("additional_json_maps") or [],
            rotation_angle=float(data.get("rotation_angle", 0) or 0),
        )
        return json.dumps({"html_path": html_path,
                           "json_path": json_path, "kmz_path": kmz_path})
    except Exception as e:  # noqa: BLE001 — the bridge converts all failures to structured errors
        return json.dumps({"error": "render_failed", "detail": str(e)})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_satellite_bridge.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Run lint + full suite**

Run: `uv run ruff check . && uv run pytest -q`
Expected: ruff clean; whole suite passes (core untouched).

- [ ] **Step 6: Commit**

```bash
git add android/app/src/main/python/satellite_bridge.py tests/test_satellite_bridge.py
git commit -m "feat(mobile-app): satellite_bridge — GPS validation + draw_map + structured errors"
```

---

### Task 2: Survey bridge surfaces the effective map CSV

**Files:**
- Modify: `android/app/src/main/python/survey_bridge.py`
- Test: `tests/test_survey_bridge.py`

**Interfaces:**
- Consumes: core `merge_surveys(...)`, `SectionProtocol` (already imported in `survey_bridge.py`).
- Produces: new helper `effective_map_csv(map_csv, child_map_csv, parent_station, child_station, section_protocol, work_dir) -> str | None`. `generate_survey_plot` return JSON gains an optional `"map_csv_path"` key (present when a map was generated; the merged CSV path when a valid merge ran, else the parsed map CSV).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_survey_bridge.py`:

```python
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from cave_sketch.survey.merger import SectionProtocol

_BRIDGE_PATH = (
    Path(__file__).parent.parent
    / "android/app/src/main/python/survey_bridge.py"
)
_spec = importlib.util.spec_from_file_location("survey_bridge", _BRIDGE_PATH)
survey_bridge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(survey_bridge)


@pytest.fixture
def two_csvs(tmp_path):
    parent = pd.DataFrame({
        "Node_Id": ["st1", "st2"], "X": [0.0, 10.0], "Y": [0.0, 0.0],
        "Links": ["st2", "st1"], "Type": ["station", "station"],
    })
    child = pd.DataFrame({
        "Node_Id": ["st1", "st2"], "X": [0.0, 5.0], "Y": [0.0, 0.0],
        "Links": ["st2", "st1"], "Type": ["station", "station"],
    })
    p = tmp_path / "map.csv"
    c = tmp_path / "child_map.csv"
    parent.to_csv(p, index=False)
    child.to_csv(c, index=False)
    return str(p), str(c), tmp_path


def test_no_merge_returns_parsed_map_csv(two_csvs, tmp_path):
    map_csv, _, _ = two_csvs
    out = survey_bridge.effective_map_csv(
        map_csv, None, "", "", SectionProtocol.SIMPLE, str(tmp_path)
    )
    assert out == map_csv


def test_no_map_returns_none(tmp_path):
    out = survey_bridge.effective_map_csv(
        None, None, "", "", SectionProtocol.SIMPLE, str(tmp_path)
    )
    assert out is None


def test_merge_writes_and_returns_merged_csv(two_csvs):
    map_csv, child_csv, work_dir = two_csvs
    out = survey_bridge.effective_map_csv(
        map_csv, child_csv, "st2", "st1", SectionProtocol.SIMPLE, str(work_dir)
    )
    assert out == str(work_dir / "merged_map.csv")
    assert Path(out).exists()
    assert len(pd.read_csv(out)) > len(pd.read_csv(map_csv))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_survey_bridge.py -v`
Expected: FAIL — `AttributeError: module 'survey_bridge' has no attribute 'effective_map_csv'`.

- [ ] **Step 3: Add the helper and extend the return value**

In `android/app/src/main/python/survey_bridge.py`, add this helper after `validate_merge` (the `Path`, `Optional`, `pd`, `merge_surveys`, `SectionProtocol` imports already exist):

```python
def effective_map_csv(map_csv: Optional[str], child_map_csv: Optional[str],
                      parent_station: str, child_station: str,
                      section_protocol: SectionProtocol,
                      work_dir: str) -> Optional[str]:
    """Return the map CSV the Satellite view should use: the merged CSV when a
    valid merge was requested (mirrors app/pages/1_survey_plot.py glue), else the
    parsed map CSV, or None when no map was provided."""
    if not map_csv:
        return None
    if child_map_csv and parent_station and child_station:
        from cave_sketch.survey.merger import merge_surveys
        merged_df, _ = merge_surveys(
            parent_map=pd.read_csv(map_csv),
            parent_section=None,
            child_map=pd.read_csv(child_map_csv),
            child_section=None,
            parent_station=parent_station,
            child_station=child_station,
            section_protocol=section_protocol,
        )
        if merged_df is not None:
            merged_path = Path(work_dir) / "merged_map.csv"
            merged_df.to_csv(merged_path, index=False)
            return str(merged_path)
    return map_csv
```

Then in `generate_survey_plot`, replace the final success return:

```python
        import matplotlib.pyplot as plt
        plt.close(fig)  # release the figure; mobile renders the PDF, not the figure
        return json.dumps({"pdf_path": pdf_path})
```

with:

```python
        import matplotlib.pyplot as plt
        plt.close(fig)  # release the figure; mobile renders the PDF, not the figure
        result = {"pdf_path": pdf_path}
        eff_map_csv = effective_map_csv(
            map_csv, child_map_csv, parent_station or "", child_station or "",
            SectionProtocol(data.get("section_protocol", "simple")), work_dir,
        )
        if eff_map_csv:
            result["map_csv_path"] = eff_map_csv
        return json.dumps(result)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_survey_bridge.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Lint + full suite**

Run: `uv run ruff check . && uv run mypy cave_sketch/ && uv run pytest -q`
Expected: all clean (mypy unaffected; core untouched).

- [ ] **Step 6: Commit**

```bash
git add android/app/src/main/python/survey_bridge.py tests/test_survey_bridge.py
git commit -m "feat(mobile-app): survey_bridge surfaces effective map CSV (merged or parsed)"
```

---

### Task 3: `SurveyResultStore` + Survey ViewModel publishes to it

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/data/SurveyResultStore.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`
- Test: `android/app/src/test/java/com/cavesketch/app/SurveyPlotViewModelTest.kt`

**Interfaces:**
- Produces: `data class SurveyResult(val mapCsvPath: String, val surveyName: String)`; `class SurveyResultStore { val result: StateFlow<SurveyResult?>; fun publish(result: SurveyResult) }`.
- Consumes: existing `PlotState`, `SurveyInputs`, `SurveyBridge`.
- Changes: `SurveyPlotViewModel` constructor gains a 4th param `store: SurveyResultStore`. On a success response containing `map_csv_path`, it publishes `SurveyResult(mapCsvPath, inputs.surveyName)`.

- [ ] **Step 1: Create the store**

Create `android/app/src/main/java/com/cavesketch/app/data/SurveyResultStore.kt`:

```kotlin
package com.cavesketch.app.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** The effective cave-map CSV produced by the Survey Plot screen, shared with the
 * Satellite Map screen (the reactive analog of the web app's session map_csv). */
data class SurveyResult(val mapCsvPath: String, val surveyName: String)

class SurveyResultStore {
    private val _result = MutableStateFlow<SurveyResult?>(null)
    val result: StateFlow<SurveyResult?> = _result.asStateFlow()

    fun publish(result: SurveyResult) {
        _result.value = result
    }
}
```

- [ ] **Step 2: Write the failing test**

In `SurveyPlotViewModelTest.kt`, update the `vm()` helper to inject a store and add a publish test. Replace the helper and add the new test:

```kotlin
    private val store = com.cavesketch.app.data.SurveyResultStore()

    private fun vm(bridge: SurveyBridge) =
        SurveyPlotViewModel(bridge, "/tmp", testDispatcher, store)
```

```kotlin
    @Test
    fun success_with_map_csv_publishes_to_store() = runTest(testDispatcher) {
        val model = vm(object : SurveyBridge {
            override suspend fun generate(inputsJson: String, workDir: String) =
                """{"pdf_path":"/tmp/survey.pdf","map_csv_path":"/tmp/map.csv"}"""
        })
        model.generate(SurveyInputs(mapPath = "/tmp/map.csv", surveyName = "Cave"))
        advanceUntilIdle()
        assertEquals(
            com.cavesketch.app.data.SurveyResult("/tmp/map.csv", "Cave"),
            store.result.value,
        )
    }
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.SurveyPlotViewModelTest"`
Expected: FAIL — constructor arity mismatch (no 4th param) / `store` unresolved.

- [ ] **Step 4: Wire the store into the ViewModel**

In `SurveyPlotViewModel.kt`, add the import and constructor param, and publish on success. Change the constructor:

```kotlin
class SurveyPlotViewModel(
    private val bridge: SurveyBridge,
    private val workDir: String,
    private val io: CoroutineDispatcher,
    private val store: com.cavesketch.app.data.SurveyResultStore,
) : ViewModel() {
```

In `generate(inputs)`, replace the success branch:

```kotlin
                _state.value = if (obj.has("pdf_path")) {
                    PlotState.Success(obj.getString("pdf_path"))
                } else {
                    PlotState.Error(obj.optString("detail", obj.optString("error", "Unknown error")))
                }
```

with:

```kotlin
                _state.value = if (obj.has("pdf_path")) {
                    if (obj.has("map_csv_path")) {
                        store.publish(
                            com.cavesketch.app.data.SurveyResult(
                                obj.getString("map_csv_path"), inputs.surveyName
                            )
                        )
                    }
                    PlotState.Success(obj.getString("pdf_path"))
                } else {
                    PlotState.Error(obj.optString("detail", obj.optString("error", "Unknown error")))
                }
```

- [ ] **Step 5: Keep `MainActivity` compiling (pass a store to the 4-arg ctor)**

The constructor now needs a store, so `MainActivity.App()` won't compile until it supplies one. In `MainActivity.kt`, change the `App()` body to create a store and pass it (the full two-ViewModel wiring lands in Task 7):

```kotlin
@Composable
fun App() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val store = androidx.compose.runtime.remember { com.cavesketch.app.data.SurveyResultStore() }
    val viewModel = androidx.lifecycle.viewmodel.compose.viewModel<com.cavesketch.app.ui.SurveyPlotViewModel>(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T =
                com.cavesketch.app.ui.SurveyPlotViewModel(
                    com.cavesketch.app.bridge.PythonBridge(kotlinx.coroutines.Dispatchers.IO),
                    context.filesDir.absolutePath,
                    kotlinx.coroutines.Dispatchers.IO,
                    store,
                ) as T
        }
    )
    com.cavesketch.app.ui.AppNavHost(viewModel)
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.SurveyPlotViewModelTest"`
Expected: PASS (all 3 tests, including the existing two whose `{"pdf_path":...}`-only responses leave the store null).

- [ ] **Step 7: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/data/SurveyResultStore.kt \
        android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt \
        android/app/src/main/java/com/cavesketch/app/MainActivity.kt \
        android/app/src/test/java/com/cavesketch/app/SurveyPlotViewModelTest.kt
git commit -m "feat(mobile-app): SurveyResultStore + survey VM publishes effective map CSV"
```

---

### Task 4: `SatelliteBridge` interface + `SatelliteViewModel`

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/bridge/SatelliteBridge.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/bridge/PythonBridge.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/SatelliteViewModel.kt`
- Test: `android/app/src/test/java/com/cavesketch/app/SatelliteViewModelTest.kt`

**Interfaces:**
- Produces: `interface SatelliteBridge { suspend fun generateSatellite(inputsJson: String, workDir: String): String }`; `data class GpsPoint(station, lat, lon)`; `sealed interface SatelliteState { Idle; NoMap; Generating(phase); Success(htmlPath, jsonPath, kmzPath, online); Error(message) }`; `class SatelliteViewModel(bridge: SatelliteBridge, store: SurveyResultStore, workDir: String, io: CoroutineDispatcher, isOnline: () -> Boolean)`.
- Consumes: `SurveyResultStore.result` (Task 3) for map availability + survey-name suggestion.

- [ ] **Step 1: Create the bridge interface + extend PythonBridge**

Create `android/app/src/main/java/com/cavesketch/app/bridge/SatelliteBridge.kt`:

```kotlin
package com.cavesketch.app.bridge

interface SatelliteBridge {
    /** Calls satellite_bridge.generate_satellite_map; returns its JSON result string. */
    suspend fun generateSatellite(inputsJson: String, workDir: String): String
}
```

Replace `PythonBridge.kt` with (implements both bridge interfaces):

```kotlin
package com.cavesketch.app.bridge

import com.chaquo.python.Python
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext

class PythonBridge(private val io: CoroutineDispatcher) : SurveyBridge, SatelliteBridge {
    override suspend fun generate(inputsJson: String, workDir: String): String =
        withContext(io) {
            Python.getInstance()
                .getModule("survey_bridge")
                .callAttr("generate_survey_plot", inputsJson, workDir)
                .toString()
        }

    override suspend fun generateSatellite(inputsJson: String, workDir: String): String =
        withContext(io) {
            Python.getInstance()
                .getModule("satellite_bridge")
                .callAttr("generate_satellite_map", inputsJson, workDir)
                .toString()
        }
}
```

- [ ] **Step 2: Write the failing test**

Create `android/app/src/test/java/com/cavesketch/app/SatelliteViewModelTest.kt`:

```kotlin
package com.cavesketch.app

import com.cavesketch.app.bridge.SatelliteBridge
import com.cavesketch.app.data.SurveyResult
import com.cavesketch.app.data.SurveyResultStore
import com.cavesketch.app.ui.GpsPoint
import com.cavesketch.app.ui.SatelliteState
import com.cavesketch.app.ui.SatelliteViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class SatelliteViewModelTest {
    private val testDispatcher = StandardTestDispatcher()

    @Before fun setUp() = Dispatchers.setMain(testDispatcher)
    @After fun tearDown() = Dispatchers.resetMain()

    private fun vm(
        store: SurveyResultStore,
        online: Boolean = true,
        bridge: SatelliteBridge = SatelliteBridge { _, _ -> "{}" },
    ) = SatelliteViewModel(bridge, store, "/tmp", testDispatcher) { online }

    @Test
    fun empty_store_is_no_map() = runTest(testDispatcher) {
        val model = vm(SurveyResultStore())
        advanceUntilIdle()
        assertEquals(SatelliteState.NoMap, model.state.value)
    }

    @Test
    fun publishing_map_makes_it_idle() = runTest(testDispatcher) {
        val store = SurveyResultStore()
        val model = vm(store)
        advanceUntilIdle()
        store.publish(SurveyResult("/tmp/map.csv", "Cave"))
        advanceUntilIdle()
        assertEquals(SatelliteState.Idle, model.state.value)
    }

    @Test
    fun generate_success_emits_success_with_online_flag() = runTest(testDispatcher) {
        val store = SurveyResultStore().apply { publish(SurveyResult("/tmp/map.csv", "Cave")) }
        val model = vm(store, online = false, bridge = { _, _ ->
            """{"html_path":"/tmp/survey.html","json_path":"/tmp/survey.json","kmz_path":"/tmp/survey.kmz"}"""
        })
        advanceUntilIdle()
        model.addPoint()
        model.updatePoint(0, GpsPoint("st1", "45.0", "7.0"))
        model.generate("Cave")
        advanceUntilIdle()
        val s = model.state.value as SatelliteState.Success
        assertEquals("/tmp/survey.kmz", s.kmzPath)
        assertEquals(false, s.online)
    }

    @Test
    fun generate_error_emits_error_with_detail() = runTest(testDispatcher) {
        val store = SurveyResultStore().apply { publish(SurveyResult("/tmp/map.csv", "Cave")) }
        val model = vm(store, bridge = { _, _ ->
            """{"error":"no_anchor_match","detail":"no match"}"""
        })
        advanceUntilIdle()
        model.generate("Cave")
        advanceUntilIdle()
        assertTrue((model.state.value as SatelliteState.Error).message.contains("no match"))
    }

    @Test
    fun add_and_remove_points() = runTest(testDispatcher) {
        val model = vm(SurveyResultStore())
        advanceUntilIdle()
        assertEquals(1, model.points.value.size)
        model.addPoint()
        assertEquals(2, model.points.value.size)
        model.removeLastPoint()
        assertEquals(1, model.points.value.size)
        model.removeLastPoint() // never drops below one row
        assertEquals(1, model.points.value.size)
    }
}
```

Note: the `SatelliteBridge { _, _ -> ... }` SAM-lambda form requires `SatelliteBridge` to be a `fun interface`. It is declared as a plain interface in Step 1 — update Step 1's file to `fun interface SatelliteBridge` so the test fakes compile.

- [ ] **Step 3: Run test to verify it fails**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.SatelliteViewModelTest"`
Expected: FAIL — `SatelliteViewModel` / `SatelliteState` / `GpsPoint` unresolved.

- [ ] **Step 4: Implement the ViewModel**

First make the bridge a `fun interface` in `SatelliteBridge.kt`:

```kotlin
fun interface SatelliteBridge {
    suspend fun generateSatellite(inputsJson: String, workDir: String): String
}
```

Create `android/app/src/main/java/com/cavesketch/app/ui/SatelliteViewModel.kt`:

```kotlin
package com.cavesketch.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cavesketch.app.bridge.SatelliteBridge
import com.cavesketch.app.data.SurveyResultStore
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

sealed interface SatelliteState {
    data object Idle : SatelliteState
    data object NoMap : SatelliteState
    data class Generating(val phase: String) : SatelliteState
    data class Success(
        val htmlPath: String,
        val jsonPath: String,
        val kmzPath: String,
        val online: Boolean,
    ) : SatelliteState
    data class Error(val message: String) : SatelliteState
}

data class GpsPoint(val station: String = "", val lat: String = "", val lon: String = "")

class SatelliteViewModel(
    private val bridge: SatelliteBridge,
    private val store: SurveyResultStore,
    private val workDir: String,
    private val io: CoroutineDispatcher,
    private val isOnline: () -> Boolean,
) : ViewModel() {
    private val _state = MutableStateFlow<SatelliteState>(SatelliteState.NoMap)
    val state: StateFlow<SatelliteState> = _state.asStateFlow()

    private val _points = MutableStateFlow(listOf(GpsPoint()))
    val points: StateFlow<List<GpsPoint>> = _points.asStateFlow()

    private val _rotation = MutableStateFlow(0.0)
    val rotation: StateFlow<Double> = _rotation.asStateFlow()

    private val _jsonMaps = MutableStateFlow<List<String>>(emptyList())
    val jsonMaps: StateFlow<List<String>> = _jsonMaps.asStateFlow()

    init {
        viewModelScope.launch {
            store.result.collect { result ->
                // Only the gating states reflect map availability; never clobber a
                // Generating/Success/Error result.
                if (_state.value is SatelliteState.Idle || _state.value is SatelliteState.NoMap) {
                    _state.value = if (result == null) SatelliteState.NoMap else SatelliteState.Idle
                }
            }
        }
    }

    fun suggestedSurveyName(): String = store.result.value?.surveyName ?: "MySurvey"

    fun addPoint() { _points.value = _points.value + GpsPoint() }
    fun removeLastPoint() {
        if (_points.value.size > 1) _points.value = _points.value.dropLast(1)
    }
    fun updatePoint(index: Int, point: GpsPoint) {
        _points.value = _points.value.toMutableList().also { it[index] = point }
    }
    fun setRotation(value: Double) { _rotation.value = value }
    fun addJsonMap(path: String) { _jsonMaps.value = _jsonMaps.value + path }

    fun generate(surveyName: String) {
        val map = store.result.value ?: run { _state.value = SatelliteState.NoMap; return }
        _state.value = SatelliteState.Generating("Building map…")
        viewModelScope.launch {
            try {
                val resultJson = bridge.generateSatellite(buildJson(map.mapCsvPath, surveyName), workDir)
                val obj = JSONObject(resultJson)
                _state.value = if (obj.has("html_path")) {
                    SatelliteState.Success(
                        obj.getString("html_path"),
                        obj.getString("json_path"),
                        obj.getString("kmz_path"),
                        isOnline(),
                    )
                } else {
                    SatelliteState.Error(obj.optString("detail", obj.optString("error", "Unknown error")))
                }
            } catch (e: Throwable) {
                _state.value = SatelliteState.Error(e.message ?: "Generation failed")
            }
        }
    }

    private fun buildJson(mapCsvPath: String, surveyName: String): String {
        val pts = JSONArray()
        _points.value.forEach { p ->
            pts.put(JSONObject().put("station", p.station).put("lat", p.lat).put("lon", p.lon))
        }
        val maps = JSONArray()
        _jsonMaps.value.forEach { maps.put(it) }
        return JSONObject()
            .put("map_path", mapCsvPath)
            .put("gps_points", pts)
            .put("survey_name", surveyName)
            .put("rotation_angle", _rotation.value)
            .put("additional_json_maps", maps)
            .toString()
    }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.SatelliteViewModelTest"`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/bridge/SatelliteBridge.kt \
        android/app/src/main/java/com/cavesketch/app/bridge/PythonBridge.kt \
        android/app/src/main/java/com/cavesketch/app/ui/SatelliteViewModel.kt \
        android/app/src/test/java/com/cavesketch/app/SatelliteViewModelTest.kt
git commit -m "feat(mobile-app): SatelliteBridge + SatelliteViewModel state machine"
```

---

### Task 5: Generalize sharing, add connectivity helper, declare network permissions

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/util/Share.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/util/Connectivity.kt`
- Modify: `android/app/src/main/AndroidManifest.xml`

**Interfaces:**
- Produces: `fun shareFile(context, path, mimeType, displayName)`; `fun sharePdf(...)` now delegates to it; `fun isOnline(context): Boolean`.

- [ ] **Step 1: Generalize `Share.kt`**

Replace `Share.kt` with:

```kotlin
package com.cavesketch.app.util

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

/** Launches the Android share sheet for [path] with the given [mimeType], via the
 * app's FileProvider. */
fun shareFile(context: Context, path: String, mimeType: String, displayName: String) {
    val file = File(path)
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = mimeType
        putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_TITLE, displayName)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "Share $displayName"))
}

/** Backwards-compatible PDF share (Phase 1 call sites). */
fun sharePdf(context: Context, pdfPath: String, displayName: String) =
    shareFile(context, pdfPath, "application/pdf", displayName)
```

- [ ] **Step 2: Add the connectivity helper**

Create `android/app/src/main/java/com/cavesketch/app/util/Connectivity.kt`:

```kotlin
package com.cavesketch.app.util

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities

/** True when the device has a network with validated internet capability. */
fun isOnline(context: Context): Boolean {
    val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
        ?: return false
    val network = cm.activeNetwork ?: return false
    val caps = cm.getNetworkCapabilities(network) ?: return false
    return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
}
```

- [ ] **Step 3: Declare permissions**

In `AndroidManifest.xml`, add these two lines immediately after the `<manifest ...>` opening tag (before `<application>`):

```xml
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

- [ ] **Step 4: Verify it compiles**

Run: `cd android && ./gradlew :app:compileDebugKotlin`
Expected: BUILD SUCCESSFUL (existing `sharePdf` call site in `SurveyPlotScreen.kt` still resolves).

- [ ] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/util/Share.kt \
        android/app/src/main/java/com/cavesketch/app/util/Connectivity.kt \
        android/app/src/main/AndroidManifest.xml
git commit -m "feat(mobile-app): generalize shareFile, add isOnline, declare network perms"
```

---

### Task 6: Satellite screen UI — `GpsPointsEditor`, `MapWebView`, `SatelliteScreen`

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt`

**Interfaces:**
- Consumes: `SatelliteViewModel` (state, points, rotation, jsonMaps, `suggestedSurveyName`, `addPoint`, `removeLastPoint`, `updatePoint`, `setRotation`, `addJsonMap`, `generate`); `GpsPoint`; `shareFile`; `copyUriToDir`.
- Produces: composables `GpsPointsEditor`, `MapWebView`, `SatelliteScreen(viewModel: SatelliteViewModel)`.

- [ ] **Step 1: GPS points editor (with inline coordinate validation)**

Create `android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt`:

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.GpsPoint

/** Mirror of cave_sketch.geo.coordinates.parse_coordinate (decimal, '.'/',' separator). */
fun parsesAsCoordinate(value: String): Boolean =
    value.trim().replace(",", ".").toDoubleOrNull() != null

@Composable
fun GpsPointsEditor(
    points: List<GpsPoint>,
    onUpdate: (Int, GpsPoint) -> Unit,
    onAdd: () -> Unit,
    onRemove: () -> Unit,
) {
    Column(Modifier.fillMaxWidth()) {
        Text("📍 Known GPS Points")
        points.forEachIndexed { i, p ->
            Row(Modifier.fillMaxWidth().padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = p.station,
                    onValueChange = { onUpdate(i, p.copy(station = it)) },
                    label = { Text("Station") },
                    modifier = Modifier.weight(1f),
                )
                OutlinedTextField(
                    value = p.lat,
                    onValueChange = { onUpdate(i, p.copy(lat = it)) },
                    label = { Text("Lat") },
                    isError = p.lat.isNotBlank() && !parsesAsCoordinate(p.lat),
                    modifier = Modifier.weight(1f),
                )
                OutlinedTextField(
                    value = p.lon,
                    onValueChange = { onUpdate(i, p.copy(lon = it)) },
                    label = { Text("Lon") },
                    isError = p.lon.isNotBlank() && !parsesAsCoordinate(p.lon),
                    modifier = Modifier.weight(1f),
                )
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = onAdd) { Text("➕ Add point") }
            Button(onClick = onRemove) { Text("➖ Remove last") }
        }
    }
}
```

- [ ] **Step 2: WebView preview composable**

Create `android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt`:

```kotlin
package com.cavesketch.app.ui.components

import android.webkit.WebView
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView

/** Renders a local folium HTML file. Requires connectivity to fetch satellite tiles;
 * the caller decides whether to show this (online) or the offline banner. */
@Composable
fun MapWebView(htmlPath: String, modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            WebView(ctx).apply {
                settings.javaScriptEnabled = true
                @Suppress("SetJavaScriptEnabled")
                settings.allowFileAccess = true
                loadUrl("file://$htmlPath")
            }
        },
        update = { it.loadUrl("file://$htmlPath") },
    )
}
```

- [ ] **Step 3: The screen**

Create `android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt`:

```kotlin
package com.cavesketch.app.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.components.GpsPointsEditor
import com.cavesketch.app.ui.components.MapWebView
import com.cavesketch.app.ui.components.parsesAsCoordinate
import com.cavesketch.app.util.copyUriToDir
import com.cavesketch.app.util.shareFile

@Composable
fun SatelliteScreen(viewModel: SatelliteViewModel) {
    val context = LocalContext.current
    val state by viewModel.state.collectAsState()
    val points by viewModel.points.collectAsState()
    val rotation by viewModel.rotation.collectAsState()
    val jsonMaps by viewModel.jsonMaps.collectAsState()

    var surveyName by remember { mutableStateOf(viewModel.suggestedSurveyName()) }
    var rotationText by remember { mutableStateOf("0") }

    val jsonPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris ->
        uris.forEachIndexed { idx, uri ->
            val path = copyUriToDir(context, uri, context.filesDir, "additional_${jsonMaps.size + idx}.json")
            viewModel.addJsonMap(path)
        }
    }

    if (state is SatelliteState.NoMap) {
        Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
            Text("Generate a survey plot first — the Satellite Map needs a cave map.")
        }
        return
    }

    val pointsValid = points.all {
        it.station.isNotBlank() && parsesAsCoordinate(it.lat) && parsesAsCoordinate(it.lon)
    }

    Column(Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())) {
        Text("🌍 Satellite Map")

        GpsPointsEditor(
            points = points,
            onUpdate = viewModel::updatePoint,
            onAdd = viewModel::addPoint,
            onRemove = viewModel::removeLastPoint,
        )

        OutlinedTextField(
            value = surveyName,
            onValueChange = { surveyName = it },
            label = { Text("Survey name") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = rotationText,
            onValueChange = {
                rotationText = it
                it.trim().replace(",", ".").toDoubleOrNull()?.let(viewModel::setRotation)
            },
            label = { Text("Map rotation angle (°)") },
            isError = rotationText.isNotBlank() && rotationText.trim().replace(",", ".").toDoubleOrNull() == null,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(Modifier.height(8.dp))
        Button(onClick = { jsonPicker.launch(arrayOf("application/json", "*/*")) }) {
            Text("📁 Import JSON maps (${jsonMaps.size})")
        }

        Spacer(Modifier.height(16.dp))
        Button(
            enabled = pointsValid && state !is SatelliteState.Generating,
            onClick = { viewModel.generate(surveyName) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Generate Satellite Map") }

        Spacer(Modifier.height(16.dp))

        when (val s = state) {
            is SatelliteState.Generating -> {
                Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(8.dp))
                    Text(s.phase)
                }
            }
            is SatelliteState.Error -> {
                Text("⚠️ ${s.message}", color = MaterialTheme.colorScheme.error)
            }
            is SatelliteState.Success -> {
                if (s.online) {
                    MapWebView(s.htmlPath, Modifier.fillMaxWidth().height(360.dp))
                } else {
                    Text(
                        "No connection — satellite preview unavailable. " +
                            "KMZ & JSON are ready to save/share.",
                        color = MaterialTheme.colorScheme.error,
                    )
                }
                Spacer(Modifier.height(8.dp))
                val name = surveyName.ifBlank { "survey" }
                Button(
                    onClick = { shareFile(context, s.htmlPath, "text/html", "$name.html") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share HTML") }
                Button(
                    onClick = { shareFile(context, s.jsonPath, "application/json", "$name.json") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share JSON") }
                Button(
                    onClick = { shareFile(context, s.kmzPath, "application/vnd.google-earth.kmz", "$name.kmz") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share KMZ") }
            }
            else -> {}
        }
    }
}
```

- [ ] **Step 4: Verify it compiles**

Run: `cd android && ./gradlew :app:compileDebugKotlin`
Expected: BUILD SUCCESSFUL.

- [ ] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt \
        android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt \
        android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt
git commit -m "feat(mobile-app): SatelliteScreen + GpsPointsEditor + MapWebView"
```

---

### Task 7: Wire the screen in — navigation, DI, session cleanup; remove the stub

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt`
- Delete: `android/app/src/main/java/com/cavesketch/app/ui/SatelliteStubScreen.kt`

**Interfaces:**
- Consumes: `SurveyResultStore` (Task 3), `SurveyPlotViewModel` (4-arg ctor, Task 3), `SatelliteViewModel` (Task 4), `SatelliteScreen` (Task 6), `PythonBridge` (both bridges, Task 4), `isOnline` (Task 5).

- [ ] **Step 1: Accept both ViewModels in `AppNavHost`**

Replace `AppNavHost.kt`'s signature and the satellite `composable`:

```kotlin
@Composable
fun AppNavHost(surveyViewModel: SurveyPlotViewModel, satelliteViewModel: SatelliteViewModel) {
```

and inside `NavHost`:

```kotlin
            composable("survey_plot") { SurveyPlotScreen(surveyViewModel) }
            composable("satellite") { SatelliteScreen(satelliteViewModel) }
```

(The two `NavigationBarItem`s and the rest of the file are unchanged.)

- [ ] **Step 2: Build the store + both ViewModels in `MainActivity`**

Replace the `App()` composable in `MainActivity.kt`:

```kotlin
@Composable
fun App() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val store = androidx.compose.runtime.remember { com.cavesketch.app.data.SurveyResultStore() }
    val bridge = androidx.compose.runtime.remember {
        com.cavesketch.app.bridge.PythonBridge(kotlinx.coroutines.Dispatchers.IO)
    }
    val filesDir = context.filesDir.absolutePath

    val surveyViewModel = androidx.lifecycle.viewmodel.compose.viewModel<com.cavesketch.app.ui.SurveyPlotViewModel>(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T =
                com.cavesketch.app.ui.SurveyPlotViewModel(
                    bridge, filesDir, kotlinx.coroutines.Dispatchers.IO, store,
                ) as T
        }
    )
    val satelliteViewModel = androidx.lifecycle.viewmodel.compose.viewModel<com.cavesketch.app.ui.SatelliteViewModel>(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T =
                com.cavesketch.app.ui.SatelliteViewModel(
                    bridge, store, filesDir, kotlinx.coroutines.Dispatchers.IO,
                ) { com.cavesketch.app.util.isOnline(context) } as T
        }
    )
    com.cavesketch.app.ui.AppNavHost(surveyViewModel, satelliteViewModel)
}
```

- [ ] **Step 3: Extend session cleanup**

In `CaveSketchApplication.kt`, replace the cleanup block:

```kotlin
        // Per-session cleanup: remove last run's intermediate CSVs + PDF.
        listOf("map.csv", "section.csv", "child_map.csv", "child_section.csv", "survey.pdf")
            .forEach { java.io.File(filesDir, it).delete() }
```

with:

```kotlin
        // Per-session cleanup: remove last run's intermediate + output files.
        listOf(
            "map.csv", "section.csv", "child_map.csv", "child_section.csv",
            "merged_map.csv", "survey.pdf", "survey.html", "survey.json", "survey.kmz",
        ).forEach { java.io.File(filesDir, it).delete() }
        // Imported JSON maps from the previous session.
        filesDir.listFiles { f -> f.name.startsWith("additional_") }?.forEach { it.delete() }
```

- [ ] **Step 4: Delete the stub**

```bash
git rm android/app/src/main/java/com/cavesketch/app/ui/SatelliteStubScreen.kt
```

- [ ] **Step 5: Build the debug APK + run unit tests**

Run: `cd android && ./gradlew :app:assembleDebug :app:testDebugUnitTest`
Expected: BUILD SUCCESSFUL; all unit tests pass (`SurveyPlotViewModelTest`, `SatelliteViewModelTest`).

- [ ] **Step 6: Manual device verification**

Install on a real device and confirm:
1. Generate a survey plot (Survey tab) → switch to Satellite tab → the "Generate a survey plot first" guidance is gone and the editor is enabled, survey name prefilled.
2. Enter a GPS point whose station matches a survey station → **Generate** → online: the folium map renders in the WebView; all three Save/Share buttons open the share sheet.
3. Confirm the **KMZ** opens correctly in Locus Map (or Google Earth).
4. Enable airplane mode → Generate → the offline banner appears and KMZ/JSON Save/Share still work.

- [ ] **Step 7: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt \
        android/app/src/main/java/com/cavesketch/app/MainActivity.kt \
        android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt
git commit -m "feat(mobile-app): wire Satellite screen into navigation + session cleanup; remove stub"
```

---

### Task 8: Final verification gates + DEVLOG

**Files:**
- Modify: `android/DEVLOG.md`

- [ ] **Step 1: Run the full project gates**

Run: `uv run ruff check . && uv run mypy cave_sketch/ && uv run pytest -q`
Expected: all clean (core untouched; bridge tests pass).

- [ ] **Step 2: Run the Android unit tests + build**

Run: `cd android && ./gradlew :app:testDebugUnitTest :app:assembleDebug`
Expected: BUILD SUCCESSFUL; tests green.

- [ ] **Step 3: Append the Phase 2 DEVLOG entry**

Add an entry to `android/DEVLOG.md` (Phase 1 format) summarising: the Satellite Map screen, `satellite_bridge.py`, the `SurveyResultStore` cross-screen hand-off, the survey-bridge `map_csv_path` extension, graceful-offline preview, and outputs (HTML/JSON/KMZ). Record any device-render timings observed.

- [ ] **Step 4: Commit**

```bash
git add android/DEVLOG.md
git commit -m "docs(mobile-app): Phase 2 Satellite Map DEVLOG entry"
```

---

## Notes / out of scope

- The deferred ~60s `draw_survey` rendering optimization (Phase 1 review §F) is a **separate track** — not addressed here.
- No offline satellite-tile bundling/caching (umbrella §6: graceful degrade only).
- No changes to `cave_sketch/` or the Streamlit web app.
