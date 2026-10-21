# ⛰️ CaveSketch v1.2.0 for Android

**CaveSketch v1.2.0** brings extended survey title blocks, magnetic declination correction, flexible multi-survey merging protocols, iterative CSV merging for large cave systems, direct device storage saving, and expanded TopoDroid DXF symbol rendering — all running **100% offline on your Android device**.

---

## 🌟 New Features

- **Extended & Adaptive Title Block**: Add optional **drawer**, **municipality**, **entrance GPS coordinates** (latitude/longitude in decimal degrees), and **elevation (m a.s.l.)** to your PDF survey plots. Only populated fields are printed, and the title block automatically places itself in a collision-free corner so it never overlaps your cave drawing.
- **Magnetic Declination Correction**: Enter your survey's **magnetic variation (+E / −W)** in Settings to automatically rotate plan views and satellite overlays to **true geographic north**, with the declination value recorded in the PDF title block.
- **Save to Device or Share**: Every exported artifact (PDF, Map CSV, Section CSV, HTML map, JSON, KMZ) now opens a **Save / Share** menu — choose **Save to Device** to pick a local folder via the Android system file picker (e.g., `Downloads`) or **Share** to send directly to another app.
- **Map Merge Protocol (Simple / Displacement)**: When merging a parent and child survey, you can now choose between **Simple** (true relative position) and **Displacement** (non-overlapping placement connected by a bold dashed reference line) for the **plan view** as well as the section view.
- **Map & Section CSV Export for Iterative Merging (>2 Surveys)**: Save or share the processed **Map CSV** and **Section CSV** directly from the Survey Plot screen, then load them back as the primary survey to iteratively merge 3, 4, or more sub-surveys into a single unified cave plot.
- **Expanded TopoDroid DXF Symbols**: **Entrance**, **continuation (`?`)**, **water-flow** (point & line), and **blocks/debris** icons are now rendered as ground-scaled vector geometry across PDF survey plots, interactive satellite HTML maps, and Google Earth KMZ exports.

---

## 🛠️ Bug Fixes

- **Entrance & Point Symbol Orientation**: Fixed entrance and directional point symbol orientation on survey plots and preserved accurate symbol angles when magnetic declination rotation is applied.
- **Snow Icon in KMZ Export**: Fixed `B_snow` (`*`) icons so they render properly in Google Earth KMZ exports alongside PDF plots and satellite maps.

---

## 📲 How to Install

1. Download **[`CaveSketch-v1.2.0.apk`](https://github.com/LorBordin/cave_sketch/releases/download/v1.2.0/CaveSketch-v1.2.0.apk)** from the **Assets** section below.
2. Open the downloaded `.apk` file on your Android phone. If prompted, allow installation from unknown sources (**Settings → Apps → Special access → Install unknown apps**).
3. Tap **Install** (or **Update**).

> 💡 **Upgrading from v1.0.0 or v1.1.0?** Simply install `CaveSketch-v1.2.0.apk` directly over your existing installation — it is signed with the same release key, so your app data and settings are preserved.
