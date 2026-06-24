# CaveSketch Mobile App — DEVLOG

(Mobile-app history. Root `DEVLOG.md` covers the Python project / web app.)

## 2026-06-18 — Phase 0 spike complete

**Gate A (desktop relaxed pins):** existing pytest suite PASSED under Python 3.12.1, numpy 1.26.2, pandas 2.1.3, matplotlib 3.8.4, ezdxf 1.4.1, folium 0.19.5 (with Streamlit app tests deselected). Code changes to cave_sketch required: none. Web-app `pyproject.toml`/`uv.lock` unchanged: confirmed.

**Gate B (on-device):** Chaquopy 17.0, AGP 8.5.0, Python 3.13, ABIs arm64-v8a + x86_64. Built APK size: 104 MB. Device: SM-S901B. PDF render time for sample.dxf: 70670 ms. On-screen PDF visually matches desktop output: yes.

**Surprises / deviations:**
- Had to run Gate A under Python 3.12 on the laptop to avoid compile-from-source issues with matplotlib 3.8.4 and numpy 1.26.2 (pre-built wheels are not available for cp313 on macOS).
- Encountered a Gradle input/output overlap error when specifying `srcDir "../.."` in `build.gradle` (since it contains `android/app/build/` output). Resolved this by creating a relative symlink `android/app/src/main/python/cave_sketch` pointing to the core directory, keeping the codebase untouched and avoiding duplication.
- Build host Java was version 15, but Gradle 9.5.1 / AGP 8.5 require Java 17+. Solved by pointing `JAVA_HOME` to Android Studio's bundled JDK 21.
- Had to change `rule_length` from `1.0` to `20.0` to prevent an assertion error in `_add_rule` (Scale_length must be evenly divisible by segment_length).

**Difficulty verdict for Phases 1–3:** YELLOW
Grounded in the findings: The Python scientific stack runs and packages successfully on the device, producing a visually correct PDF with zero core library changes required. However, the first-run/cold render time of 70.6 seconds is high. We will need to investigate preloading imports, keeping the runtime warm, and/or providing progress feedback to the user in the upcoming UI integration phases.

## [2026-06-19 14:18] Phase 1 — Measurement spike complete
**Files:**
- android/app/src/main/python/spike.py
- android/app/src/main/java/com/cavesketch/spike/MainActivity.kt
- android/DEVLOG.md

**Deviations from spec:**
None.

**Assumptions:**
None.

**Next session notes:**
Timings measured on SM-S901B:
- Cold: import_ms=3250, parse_ms=4215, draw_ms=60406
- Warm: import_ms=0, parse_ms=4529, draw_ms=60624
Decision: draw_survey compute dominates the runtime even when warm (taking ~60 seconds).
Strategy: pre-warm imports at launch (reloading the cache), and manage user expectations with a staged progress indicator ("Starting engine..." -> "Rendering survey..."). We will investigate draw path optimizations after Task 10.

## [2026-06-19 14:35] Phase 1 — Implementation complete
**Files:**
- android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt
- android/app/src/main/java/com/cavesketch/app/MainActivity.kt
- android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt
- android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt
- android/app/src/main/java/com/cavesketch/app/ui/PdfPreview.kt
- android/app/src/main/java/com/cavesketch/app/util/Share.kt
- android/DEVLOG.md
- android/app/src/main/java/com/cavesketch/spike/MainActivity.kt (deleted)
- android/app/src/main/java/com/cavesketch/spike/SpikeApplication.kt (deleted)
- android/app/src/main/python/spike.py (deleted)

**Deviations from spec:**
None.

**Assumptions:**
None.

**Next session notes:**
Phase 1 complete. Staged progress, PDF generation preview, and Save/Share sheet all implemented and verified. All unit/bridge tests passing, ruff and mypy passing. Ready for Phase 2.


## [2026-06-19 14:56] Phase 1 — Create review & findings doc
**Files:**
- docs/mobile-app/phases/phase-1-survey-plot/review.md
- android/DEVLOG.md

**Deviations from spec:**
None

**Assumptions:**
None

**Next session notes:**
Added docs/mobile-app/phases/phase-1-survey-plot/review.md detailing Phase 1 review, latency metrics, deferred optimizations, and recommendations/scope for Phase 2.

## [2026-06-20 11:25] Phase 2 — Implementation complete
**Files:**
- android/app/src/main/python/satellite_bridge.py
- tests/test_satellite_bridge.py
- android/app/src/main/python/survey_bridge.py
- tests/test_survey_bridge.py
- android/app/src/main/java/com/cavesketch/app/data/SurveyResultStore.kt
- android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt
- android/app/src/main/java/com/cavesketch/app/MainActivity.kt
- android/app/src/test/java/com/cavesketch/app/SurveyPlotViewModelTest.kt
- android/app/src/main/java/com/cavesketch/app/bridge/SatelliteBridge.kt
- android/app/src/main/java/com/cavesketch/app/bridge/PythonBridge.kt
- android/app/src/main/java/com/cavesketch/app/ui/SatelliteViewModel.kt
- android/app/src/test/java/com/cavesketch/app/SatelliteViewModelTest.kt
- android/app/src/main/java/com/cavesketch/app/util/Share.kt
- android/app/src/main/java/com/cavesketch/app/util/Connectivity.kt
- android/app/src/main/AndroidManifest.xml
- android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt
- android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt
- android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt
- android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt
- android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt
- android/app/src/main/java/com/cavesketch/app/ui/SatelliteStubScreen.kt (deleted)
- android/DEVLOG.md
- .gitignore

**Deviations from spec:**
- Had to enable `domStorageEnabled`, `allowFileAccessFromFileURLs`, and `allowUniversalAccessFromFileURLs` in WebView configuration to allow Leaflet/Folium scripts to render and access tiles successfully.

**Assumptions:**
None.

**Next session notes:**
Phase 2 complete. The Satellite Map screen is fully implemented with GPS point georeferencing, optional rotation, additional JSON map imports, offline-ready KMZ + JSON generation, and online HTML WebView preview. All Python checks, Kotlin unit tests, and compilation steps are passing cleanly.

## [2026-06-23 09:52] Phase 3 & 4 — Satellite WebView Blank-Render Bugfix
**Files:**
- android/app/src/main/java/com/cavesketch/app/ui/components/MapWebView.kt
- docs/mobile-app/phases/phase-2-satellite-map/to_fix.md

**Deviations from spec:** None

**Assumptions:** None

**Next session notes:** None

## [2026-06-23 12:20] Phase 3 & 4 — Survey Plot Rendering Latency Optimizations
**Files:**
- cave_sketch/dxf/parser.py
- cave_sketch/features/render_features.py
- cave_sketch/backend_renders/matplotlib.py
- cave_sketch/survey/graphics/survey_plot.py
- tests/test_render_regression.py
- tests/test_render_features.py

**Deviations from spec:** None

**Assumptions:** None

**Next session notes:** Latency optimizations successfully reduced the warm draw_survey time on Samsung S22 from ~60.6s to ~3.0s, and parse_dxf time from ~4.5s to ~1.2s. The PDF render on-screen continues to display pixel-identically and correctly.


## [2026-06-23] Survey Settings UI Refinement — Implementation Complete
**Files:**
- android/app/build.gradle
- android/app/src/main/AndroidManifest.xml
- android/app/src/main/java/com/cavesketch/app/ui/components/SettingsForm.kt
- android/app/src/test/java/com/cavesketch/app/ui/components/SettingsFormTest.kt
**Deviations from spec:** None
**Assumptions:** None
**Next session notes:** None

## [2026-06-24] Phase 3 — Polish & Release
**Files:**
- android/app/build.gradle
- android/app/src/main/AndroidManifest.xml
- android/app/src/main/java/com/cavesketch/app/AppInitState.kt
- android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt
- android/app/src/main/java/com/cavesketch/app/MainActivity.kt
- android/app/src/main/java/com/cavesketch/app/ui/AboutScreen.kt
- android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt
- android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt
- android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt
- android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt
- android/app/src/main/java/com/cavesketch/app/ui/theme/Color.kt
- android/app/src/main/java/com/cavesketch/app/ui/theme/Theme.kt
- android/app/src/main/res/drawable/splash_icon.xml
- android/app/src/main/res/values/colors.xml
- android/app/src/main/res/values/themes.xml
- android/app/src/test/java/com/cavesketch/app/AppInitStateTest.kt
- android/app/src/test/java/com/cavesketch/app/ui/AboutScreenTest.kt
- android/app/src/test/java/com/cavesketch/app/util/ErrorMessagesTest.kt
- android/app/src/test/java/com/cavesketch/app/util/SafeCopyTest.kt
- android/app/src/test/java/com/cavesketch/app/util/SessionCleanupTest.kt
- android/tools/gen_launcher_icons.py
- android/RELEASE.md

**Deviations from spec:** None

**Assumptions:** Splash uses core-splashscreen with the launcher foreground as the splash icon; About link points at the public repo.

**Next session notes:** Phase 4 (visual redesign) is the next roadmap item.
