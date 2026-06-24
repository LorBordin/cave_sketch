# Phase 1 — Survey Plot — Review & Findings

**Initiative:** CaveSketch Mobile App  
**Phase:** 1 · Survey Plot Screen  
**Status:** Completed & Verified on Device  
**Date:** 2026-06-19  

---

## 1. Executive Summary

Phase 1 successfully built and shipped the first complete, user-facing screen of the CaveSketch mobile app: the **Survey Plot** screen. This implementation delivers full feature parity with the web version (`app/pages/1_survey_plot.py`) on real Android devices.

Key achievements:
- **UI Parity:** Developed a responsive Jetpack Compose interface supporting single/dual DXF file pickers, survey metadata input, rotation, zoom, rule length, and layout options.
- **Python Bridge:** Implemented `survey_bridge.py` under the Android assets to coordinate input serialization, validation, and invoking the core library without any Streamlit dependency.
- **State & Navigation:** Established a ViewModel-driven architecture with clean state handling (`Idle`, `Generating`, `Success`, `Error`) and a two-destination Jetpack Compose navigation graph with a stub for the Phase 2 Satellite Map.
- **Sharing & Preview:** Integrated Android `PdfRenderer` for instant page-1 vector preview, and `FileProvider` to trigger the native Android sharing/saving sheet.

---

## 2. Latency Measurement Breakdown

As required by Step 1 of the plan, a measurement spike was conducted on a physical device (Samsung Galaxy S22, SM-S901B) to profile the rendering bottlenecks:

| Step | Cold Start (Fresh Process) | Warm Start (Subsequent Run) |
| :--- | :--- | :--- |
| **Python / Library Imports** | `3,250 ms` (~3.25 seconds) | `0 ms` (fully cached) |
| **DXF Parsing (`parse_dxf`)** | `4,215 ms` (~4.22 seconds) | `4,529 ms` (~4.53 seconds) |
| **Matplotlib Render (`draw_survey`)** | `60,406 ms` (~60.41 seconds) | `60,624 ms` (~60.62 seconds) |
| **Total Latency** | **`67,871 ms`** (~68 seconds) | **`65,153 ms`** (~65 seconds) |

### Key Conclusions:
- **Runtime Import Cache:** Python interpreter startup and heavy scientific wheel loading (`numpy`, `pandas`, `matplotlib`) takes ~3.25 seconds. Pre-warming this at application launch successfully drops import cost to `0 ms` for the user.
- **Rendering Dominates:** The `draw_survey` execution is the primary bottleneck, consuming over 90% of the total runtime (~60 seconds) even in a warm state.

---

## 3. Deferred Optimizations (Added Scope)

During the measurement spike, the agent observed that the rendering function (`draw_survey`) dominates the runtime even when warm. Following the instructions outlined in the implementation plan ([plan.md:L115](file:///Users/lorenzo/python/cave_sketch/docs/mobile-app/phases/phase-1-survey-plot/plan.md#L115) and [L1390](file:///Users/lorenzo/python/cave_sketch/docs/mobile-app/phases/phase-1-survey-plot/plan.md#L1390)):
1. **Scope Splitting:** Optimization of the rendering pipeline was logged as **added scope** to be addressed separately rather than blocking the delivery of the Phase 1 UI.
2. **UX Mitigation:** To keep the application responsive, the UI was designed with an asynchronous background worker and a staged progress indicator (`Starting engine...` $\rightarrow$ `Rendering survey...`) so the user is informed of the backend processing.
3. **Action Item:** Rendering optimization remains an open investigation task to be addressed post-Task 10/Phase 1.

---

## 4. Architectural Highlights & Completed Codebase

The resulting system establishes a robust modular foundation:
- **`CaveSketchApplication.kt`**: Handles per-session directory cleanup and triggers a background daemon thread to pre-warm the Python environment and imports immediately upon app launch.
- **`PythonBridge.kt` & `survey_bridge.py`**: A clean serialization layer using JSON payloads. It handles coordinate validations, merges child/parent surveys, catching core errors (e.g., station-matching exceptions), and formats them to Kotlin-readable errors.
- **`SurveyPlotViewModel.kt`**: Exposes a reactive state machine using Kotlin `StateFlow`.
- **`SurveyPlotScreen.kt` & `PdfPreview.kt`**: Employs standard material design sliders, checkboxes, text fields, and file pickers, feeding inputs into the ViewModel. The success state draws page 1 of the generated PDF inside a `PdfRenderer`-derived bitmap.
- **`Share.kt`**: Wraps native intents to stream the PDF securely to other system-level targets.

---

## 5. Input & Recommendations for Phase 2 (Satellite Map)

Phase 2 will implement the **Satellite Map** screen. The findings and architecture of Phase 1 suggest the following guidelines:

### A. Routing and Navigation
- The navigation architecture is already in place. The bottom bar navigation switches between `SurveyPlotScreen` and a stubbed `SatelliteScreen`. Phase 2 should replace this stub directly without renaming or changing `AppNavHost`.

### B. Python Bridge Extension
- Just like `survey_bridge.py`, Phase 2 will need a `satellite_bridge.py` or equivalent entry point under the assets.
- This bridge will coordinate georeferencing logic (e.g., taking station-to-GPS coordinates pairs, checking affine transform feasibility) and invoke `cave_sketch.geo` utilities.
- It needs to output:
  1. An HTML map file (from `folium`).
  2. A KML/KMZ zip package for Google Earth.
  3. A JSON survey representation.

### C. Map Rendering and Display (WebView)
- Since the web app uses `folium` to render an interactive map, the mobile app will need to display the generated HTML in an Android `WebView` composable.
- Ensure the `WebView` is configured to run locally (loading file paths from `filesDir`) and supports JavaScript interaction.

### D. Offline Constraints
- Caving operations usually occur offline. Folium maps typically fetch Mapbox/OpenStreetMap tiles from the network.
- **Task:** Investigate how to bundle/cache satellite tiles or how the app behaves when offline. Ensure proper fallback error handling when no internet is available to load online basemaps.

### E. File Management & Export
- The `FileProvider` setup in `AndroidManifest.xml` and `Share.kt` is broad enough to share general file paths.
- Phase 2 can reuse `sharePdf` (generalized to `shareFile`) to share the exported KMZ, HTML, and JSON files directly.

### F. Rendering Engine Optimization (Revisiting the Added Scope)
- Before shipping the app to production, the `draw_survey` (~60s runtime) must be optimized. 
- Since the core `cave_sketch` library is shared, optimizations should be made directly in the Python core codebase (e.g., by optimizing matplotlib's data structures or rendering pipeline), which will speed up both the Streamlit web version and the Android app.
