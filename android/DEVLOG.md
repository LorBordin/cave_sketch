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


