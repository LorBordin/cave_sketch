# CaveSketch for Android — User Guide

CaveSketch for Android is an offline-capable native Android app that uses the same Python cave survey engine as the CaveSketch web app. All survey processing happens **entirely on-device** — no server required.

---

## The Three Screens

### 📋 Survey Plot

Pick DXF files from your device and configure the survey output:

- **Survey name** and **surveyor**
- **Scale** and **rule length**
- **Rotation**
- **Marker / text / line-width zoom**
- **Station markers** and **grid** toggle
- Optional **merge with a child survey** (station IDs + section protocol)

Tap **Generate** to produce a PDF preview, then **Save** or **Share** the result.

![Survey Plot — file picker and basic settings](screenshots/survey_1.jpg)

![Survey Plot — zoom and marker options](screenshots/survey_2.jpg)

![Survey Plot — merge with child survey](screenshots/survey_3.jpg)

![Survey Plot — PDF preview](screenshots/survey_4.jpg)

---

### 🌍 Satellite Map

Add GPS reference points (station ID, latitude, longitude) and configure:

- **Survey name** and **rotation**
- Optional **JSON map import** for multi-survey overlay

Tap **Generate** to produce:

- **HTML preview** (requires network for satellite tile servers)
- **JSON export** (cave map format)
- **KMZ export** (for Google Earth)

**Save** or **Share** each output independently.

![Satellite Map — GPS point entry](screenshots/satellite_1.jpg)

![Satellite Map — configuration and generation](screenshots/satellite_2.jpg)

![Satellite Map — HTML satellite preview](screenshots/satellite_3.jpg)

---

### ℹ️ About

Displays the app version and provides a link to the GitHub repository.

![About screen](screenshots/about.jpg)

---

## Offline Behavior

| Feature | Offline | Notes |
|---|---|---|
| PDF generation | ✅ | Fully on-device |
| KMZ export | ✅ | Fully on-device |
| JSON export | ✅ | Fully on-device |
| Satellite HTML preview | 🌐 | Requires network for online tile servers |

> [!NOTE]
> When offline, the satellite HTML preview shows a **"No connection — satellite preview unavailable"** banner, but KMZ and JSON exports still generate normally.
