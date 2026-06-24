# 🗺️ CaveSketch

[![CI](https://github.com/LorBordin/cave_sketch/actions/workflows/ci.yml/badge.svg)](https://github.com/LorBordin/cave_sketch/actions/workflows/ci.yml)

🌍 Available languages: [🇬🇧 English](README.md) | [🇮🇹 Italiano](README.it.md)

**Draw your cave surveys in seconds — directly from TopoDroid!**
No more heavy tools, no more painful setups. Just DXF files, your phone or browser, and your next expedition.

---

## 🚀 Two Ways to Use CaveSketch

### 🌐 Web App (Online)
No installation required. Run directly in your web browser.
- 🔗 **Try the live app:** [cavesketch.streamlit.app](https://cavesketch.streamlit.app/)
- 📖 **Web Documentation:** See the [Web App Guides](docs/web/README.md) for details on advanced online features.

### 📱 Android App (Fully Offline)
Perfect for field research and offline base camps. Run all survey rendering on-device.
- 📥 **Download APK:** Get the latest release from [GitHub Releases](https://github.com/LorBordin/cave_sketch/releases).
- 📖 **Android Documentation:** See the [Android User Guide](docs/android/README.md) for installation and usage.
- 💻 **Android Contributors:** Read the [Android Architecture & Stack](docs/android/architecture.md) guide.

---

## 🧭 Features at a Glance

- 🖨️ **PDF Cave Survey Plots** — Generate high-quality print-ready plan and section maps with customizable scale, rotation, grid, and drawn scale bars.
- 🔗 **Survey Merging** — Join a parent and child survey directly in the survey plot, supporting multiple section layout protocols (Simple, Mirror, Displacement).
- 🌍 **Satellite Imagery Overlay** — Position your cave map on GPS-georeferenced satellite images (more referenced points = higher accuracy).
- 🗺️ **Multi-Survey Maps** — Combine multiple independent surveys into a single geographic view using JSON export and re-import.
- 📦 **Offline KMZ & KML Export** — Export self-contained, optimized KMZ archives for offline use in mobile mapping tools like Locus Map or OsmAnd.

For detailed guides on how to use these features, explore the [Web App Documentation](docs/web/README.md) or the [Android User Guide](docs/android/README.md).

---

## 📸 Prerequisite: Exporting from TopoDroid

To use CaveSketch, you need to export your sketches from TopoDroid as **.dxf** files:

1. From the project main window in TopoDroid, tap on the Sketch Editing button <img src="imgs/topodroid_icon.png" style="width: 20px;"> and select the cave map.
2. Tap on the 3 dots/buttons on the Top Left and select `Export`.
3. Select the `DXF` option and tap `Save`.
4. Export the cave section in the same way.

<div style="display: flex; gap: 10px; justify-content: space-between;">
  <img src="imgs/map_export.jpg" style="width: 200px;">
  <img src="imgs/export_format.jpg" style="width: 200px;">
  <img src="imgs/section_export.jpg" style="width: 200px;">
</div>

---

## 💻 For Developers

### 🔧 Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/LorBordin/cave_sketch.git
   cd cave_sketch
   ```
2. **Install dependencies**:
   ```bash
   uv sync
   ```
3. **Install pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```
4. **Run the local development app**:
   ```bash
   uv run streamlit run app/app.py
   ```

### 🧑‍💻 Contribute
Found a bug? Got an idea? PRs welcome!
To contribute:
1. Fork the repo.
2. Create a new branch.
3. Commit your changes.
4. Open a pull request 🚀

---

## 📋 ToDo List (Open for Contributors)

Help us make CaveSketch even better!

- 🎨 Add option to color areas, not just draw lines.
- 🛰️ Improve satellite HTML map rendering.
- 🧊 Draw and export 3D cave models.
