🌍 Available languages: [🇬🇧 English](architecture.md) | [🇮🇹 Italiano](architecture.it.md)

# CaveSketch Android — Architecture & Tech Stack

This document describes the architecture, technology choices, and key learnings
from the CaveSketch Android app. It is intended for contributors and developers
who want to understand how the mobile app is structured and how it shares code
with the Python core library.

---

## 1. Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Language | **Kotlin** | Android app language |
| UI | **Jetpack Compose** | Declarative UI with dark Material 3 theme |
| Python Runtime | **Chaquopy 17.0** | Python SDK for Android, embedding Python 3.13 |
| PDF Preview | **Native PdfRenderer** | On-screen PDF preview of generated survey plots |
| Map Preview | **WebView** | Folium / Leaflet satellite map preview |

---

## 2. Architecture

### High-level overview

```
┌─────────────────────────────────────────────┐
│  Android UI (Kotlin + Jetpack Compose)      │
│  Survey Plot · Satellite Map · About        │
└───────────────────┬─────────────────────────┘
                    │ file paths in, output paths back
┌───────────────────▼───────────────────────────┐
│  Bridge layer (Kotlin ↔ Python)               │
│  PythonBridge · SurveyBridge · SatelliteBridge│
└───────────────────┬───────────────────────────┘
                    │ Chaquopy (embedded CPython)
┌───────────────────▼───────────────────────────┐
│  Python bridge modules                        │
│  survey_bridge.py · satellite_bridge.py       │
└───────────────────┬───────────────────────────┘
                    │
┌───────────────────▼────────────────────────────┐
│  cave_sketch core (symlinked, Streamlit-free)  │
│  ezdxf · matplotlib · numpy · pandas · folium  │
└────────────────────────────────────────────────┘
```

### Kotlin bridge files

Located in `android/app/src/main/java/com/cavesketch/app/bridge/`:

| File | Responsibility |
|------|---------------|
| `PythonBridge.kt` | Base bridge for Chaquopy integration |
| `SurveyBridge.kt` | Calls `parse_dxf` + `draw_survey` |
| `SatelliteBridge.kt` | Calls `draw_map` |

### Python bridge modules

Located in `android/app/src/main/python/`:

| File | Responsibility |
|------|---------------|
| `survey_bridge.py` | Wraps `cave_sketch` survey functions for Android |
| `satellite_bridge.py` | Wraps `cave_sketch` geo functions for Android |
| `cave_sketch` | **Symlink** to the shared core library |

---

## 3. Key Learnings

### Symlink trick

`android/app/src/main/python/cave_sketch` is a **relative symlink** pointing to
the top-level `cave_sketch/` package. Both the Streamlit web app and the Android
app use the exact same core library with **zero code duplication**.

> [!NOTE]
> The symlink approach replaced an earlier attempt using Gradle's `srcDir
> "../.."`, which failed because the path also contained build output. The
> symlink cleanly decouples the Python source from Gradle's build tree.

### Render latency

Performance benchmarks on **Samsung S22 (SM-S901B)**:

| Operation | Cold (first run) | Warm (cached) |
|-----------|----------------:|---------------:|
| `draw_survey` | ~60.6 s | **~3.0 s** |
| `parse_dxf` | ~4.5 s | **~1.2 s** |

The dramatic improvement from cold → warm is achieved via rendering pipeline
optimizations that cache intermediate results.

### Build requirements

- **JDK 17+** (Gradle 9.5.1 / AGP 8.5)
- **Chaquopy 17** with **Python 3.13**
- Target ABIs: `arm64-v8a` + `x86_64`

### APK size

~**104 MB** — this includes the bundled Python interpreter and the full
scientific stack (matplotlib, numpy, pandas, folium, ezdxf).

---

## 4. Build & Release

For keystore setup, build commands, and publishing instructions, see
[RELEASE.md](../../android/RELEASE.md).

**Quick build:**

```bash
cd android && ./gradlew assembleRelease
```

**Output:**

```
android/app/build/outputs/apk/release/app-release.apk
```

---

## 5. Quality Gates

All gates must pass before merging:

| Scope | Command |
|-------|---------|
| Python lint | `uv run ruff check .` |
| Python types | `uv run mypy cave_sketch/` |
| Python tests | `uv run pytest` |
| Kotlin tests | Unit tests in `android/app/src/test/` |

---

[Back to Android User Guide](README.md) · [Back to main README](../../README.md)
