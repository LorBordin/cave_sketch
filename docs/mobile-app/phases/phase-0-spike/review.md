# Phase 0 — Spike (De-risk) — Review & Findings

**Initiative:** CaveSketch Mobile App  
**Phase:** 0 · Spike (De-risk)  
**Status:** Completed & Verified on Device  
**Date:** 2026-06-18  

---

## 1. Executive Summary

Phase 0 successfully retired the primary feasibility risk of the CaveSketch mobile app: running the CPython scientific stack (`numpy`, `pandas`, `matplotlib`, `ezdxf`, `folium`) under Chaquopy on a real Android phone. 

The vertical slice proved that the untouched `cave_sketch` core library can be imported, parse a DXF file, generate a correct survey PDF, and display it natively on-device. The thinnest Kotlin-to-Python bridge was built, packaged into an APK, and verified on a physical device.

---

## 2. Core Metrics & Findings

### Gate A: Laptop Proof
- **Result:** **PASSED**
- **Test Suite Status:** 94 tests passed (2 Streamlit app-layer tests deselected/ignored).
- **Laptop Environment:** macOS (x86_64), CPython 3.12.1.
- **Dependency Pins Proven:**
  - `numpy==1.26.2` (ceiling on Chaquopy 17.0 for Python 3.13)
  - `pandas==2.1.3`
  - `matplotlib==3.8.4`
  - `ezdxf==1.4.1`
  - `folium==0.19.5`

### Gate B: On-Device Proof
- **Result:** **SUCCESS**
- **APK Size:** **104 MB**
- **Device Used:** Samsung Galaxy S22 (SM-S901B)
- **Cold Render Time (average):** **69.8 seconds** (~70,000 ms)
- **Visual Correctness:** Verified; on-screen PDF vector layout of `sample.dxf` matches the desktop output exactly.

---

## 3. Key Discoveries & Technical Surprises

### 1. High Cold Render Time (~70s)
* **Observation:** The first rendering of the survey plot takes ~70 seconds on the S22. Subsequent renders in the same app session will be faster due to package import caching, but the initial cold load is high.
* **Why:** 
  1. Python interpreter startup under Android.
  2. Loading heavy native scientific wheels (`numpy`, `pandas`, `matplotlib`) on a mobile CPU.
  3. Matplotlib's font manager caching and layout computations.
* **Impact on Phase 1:** A cold startup rendering block of 70 seconds will feel frozen to a user unless properly handled. We must optimize this.

### 2. Gradle Output Overlap Error
* **Observation:** Using `srcDir "../.."` in `app/build.gradle` (as originally drafted in the spec) caused a fatal Gradle task validation warning because it included the `android/` build output directory as part of the input.
* **Solution:** We resolved this by creating a relative symbolic link `android/app/src/main/python/cave_sketch` -> `../../../../../cave_sketch`. This exposes the core package to Chaquopy without copying or duplicating files, maintaining a clean single source of truth.

### 3. Toolchain JVM Requirements
* **Observation:** Gradle 9.5.1 and AGP 8.5.0 require JVM 17+. The build host's default Java was JDK 15.
* **Solution:** We successfully configured the build task using Android Studio's bundled OpenJDK 21 by specifying the `JAVA_HOME` environment variable:
  `JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"`

### 4. Segmented Rule Validation Exception
* **Observation:** Matplotlib's `_add_rule` throws an `AssertionError` if `rule_length` is not evenly divisible by `segment_len` (which defaults to `4.0`). The initial plan used `rule_length=1.0`, causing a Python exception.
* **Solution:** Adjusted `rule_length` to `20.0` in `spike.py` to satisfy this condition.

---

## 4. Recommendations for Phase 1 (Survey Plot Screen)

The next step is **Phase 1 — Survey Plot Screen**, where we build the full interactive interface with settings, merging, and sharing. The following learnings should shape Phase 1's design:

### 1. Pre-Warming the Python Runtime (Crucial)
To combat the ~70s cold render time, we should:
- Start the Python runtime and run imports (`numpy`, `pandas`, `matplotlib`) in a background thread **immediately when the app launches**, rather than waiting for the user to tap "Generate".
- Keep the python state warm throughout the application's lifecycle.

### 2. Non-blocking UI & Loading Indicators
- The "Generate" action must be asynchronous and non-blocking to the main Compose thread.
- We must design a clear, animated loading screen or progress bar with helpful messages (e.g., *"Initializing Python Engine..."*, *"Loading survey data..."*, *"Rendering layout..."*) so the user knows progress is being made.

### 3. Sharing via Native Android Sheet
- Instead of downloading files directly as done in Streamlit, we must leverage the Android `ShareCompat` or `FileProvider` to launch the native sharing sheet. This allows cavers to save the PDF to local storage (e.g., Files) or send it directly to offline mapping apps (like Locus Map).

### 4. Maintain the Symlink
- Keep the `android/app/src/main/python/cave_sketch` symbolic link in place. It works perfectly, resolves Gradle validation checks, and guarantees zero duplication of core business logic.
