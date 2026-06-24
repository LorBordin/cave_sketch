🌍 Lingue disponibili: [🇬🇧 English](architecture.md) | [🇮🇹 Italiano](architecture.it.md)

# CaveSketch Android — Architettura e Stack Tecnologico

Questo documento descrive l'architettura, le scelte tecnologiche e le lezioni
apprese dall'app Android di CaveSketch. È rivolto a contributori e sviluppatori
che vogliono comprendere come è strutturata l'app mobile e come condivide il
codice con la libreria Python core.

---

## 1. Stack Tecnologico

| Livello | Tecnologia | Ruolo |
|---------|-----------|-------|
| Linguaggio | **Kotlin** | Linguaggio dell'app Android |
| UI | **Jetpack Compose** | UI dichiarativa con tema scuro Material 3 |
| Runtime Python | **Chaquopy 17.0** | SDK Python per Android, con Python 3.13 integrato |
| Anteprima PDF | **PdfRenderer nativo** | Anteprima a schermo dei plot di rilievo generati |
| Anteprima mappe | **WebView** | Anteprima mappe satellitari Folium / Leaflet |

---

## 2. Architettura

### Panoramica generale

```
┌─────────────────────────────────────────────┐
│  Android UI (Kotlin + Jetpack Compose)      │
│  Survey Plot · Satellite Map · About        │
└───────────────────┬─────────────────────────┘
                    │ percorsi file in ingresso, percorsi output in uscita
┌───────────────────▼───────────────────────────┐
│  Livello bridge (Kotlin ↔ Python)             │
│  PythonBridge · SurveyBridge · SatelliteBridge│
└───────────────────┬───────────────────────────┘
                    │ Chaquopy (CPython integrato)
┌───────────────────▼───────────────────────────┐
│  Moduli bridge Python                         │
│  survey_bridge.py · satellite_bridge.py       │
└───────────────────┬───────────────────────────┘
                    │
┌───────────────────▼────────────────────────────┐
│  cave_sketch core (symlink, senza Streamlit)   │
│  ezdxf · matplotlib · numpy · pandas · folium  │
└────────────────────────────────────────────────┘
```

### File bridge Kotlin

Situati in `android/app/src/main/java/com/cavesketch/app/bridge/`:

| File | Responsabilità |
|------|---------------|
| `PythonBridge.kt` | Bridge base per l'integrazione con Chaquopy |
| `SurveyBridge.kt` | Chiama `parse_dxf` + `draw_survey` |
| `SatelliteBridge.kt` | Chiama `draw_map` |

### Moduli bridge Python

Situati in `android/app/src/main/python/`:

| File | Responsabilità |
|------|---------------|
| `survey_bridge.py` | Incapsula le funzioni survey di `cave_sketch` per Android |
| `satellite_bridge.py` | Incapsula le funzioni geo di `cave_sketch` per Android |
| `cave_sketch` | **Symlink** alla libreria core condivisa |

---

## 3. Lezioni Apprese

### Trucco del symlink

`android/app/src/main/python/cave_sketch` è un **symlink relativo** che punta
al pacchetto `cave_sketch/` di primo livello. Sia l'app web Streamlit che l'app
Android utilizzano la stessa identica libreria core con **zero duplicazione del
codice**.

> [!NOTE]
> L'approccio con symlink ha sostituito un precedente tentativo con `srcDir
> "../.."` di Gradle, che falliva perché il percorso conteneva anche l'output
> della build. Il symlink separa in modo pulito i sorgenti Python dall'albero di
> build di Gradle.

### Latenza di rendering

Benchmark di performance su **Samsung S22 (SM-S901B)**:

| Operazione | A freddo (prima esecuzione) | A caldo (cache) |
|------------|----------------------------:|----------------:|
| `draw_survey` | ~60,6 s | **~3,0 s** |
| `parse_dxf` | ~4,5 s | **~1,2 s** |

Il miglioramento drastico da freddo → caldo è ottenuto tramite ottimizzazioni
della pipeline di rendering che memorizzano in cache i risultati intermedi.

### Requisiti di build

- **JDK 17+** (Gradle 9.5.1 / AGP 8.5)
- **Chaquopy 17** con **Python 3.13**
- ABI target: `arm64-v8a` + `x86_64`

### Dimensione APK

~**104 MB** — include l'interprete Python integrato e l'intero stack scientifico
(matplotlib, numpy, pandas, folium, ezdxf).

---

## 4. Build e Release

Per la configurazione del keystore, i comandi di build e le istruzioni di
pubblicazione, consultare [RELEASE.md](../../android/RELEASE.md).

**Build rapida:**

```bash
cd android && ./gradlew assembleRelease
```

**Output:**

```
android/app/build/outputs/apk/release/app-release.apk
```

---

## 5. Quality Gate

Tutti i gate devono essere superati prima del merge:

| Ambito | Comando |
|--------|---------|
| Lint Python | `uv run ruff check .` |
| Tipi Python | `uv run mypy cave_sketch/` |
| Test Python | `uv run pytest` |
| Test Kotlin | Unit test in `android/app/src/test/` |

---

[Torna alla guida utente Android](README.it.md) · [Torna al README principale](../../README.it.md)
