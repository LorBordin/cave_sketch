# Implementation Plan: Persistent 'Clear Session Files' Button

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the "Clear Session Files" button visible and functional in the sidebar on every page of the app, with a toast notification on success.

**Architecture:** Extract the sidebar clear-button logic into a shared `render_sidebar()` function in a new `app/components/sidebar.py` module, then call it from `app.py`, `pages/1_survey_plot.py`, and `pages/2_satellite_map.py`. This avoids duplicating the button logic and keeps all three pages consistent.

**Tech Stack:** Python, Streamlit (`st.sidebar`, `st.button`, `st.toast`, `st.rerun`), `shutil` for temp-dir cleanup.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `app/components/sidebar.py` | `render_sidebar()` — renders the clear button with toast |
| Modify | `app/app.py` | Replace inline button with `render_sidebar()` call |
| Modify | `app/pages/1_survey_plot.py` | Add `render_sidebar()` call |
| Modify | `app/pages/2_satellite_map.py` | Add `render_sidebar()` call |

---

### Task 1: Create the shared sidebar component

**Files:**
- Create: `app/components/sidebar.py`

- [ ] **Step 1: Write the file with the `render_sidebar` function**

```python
# app/components/sidebar.py
import shutil

import streamlit as st


def render_sidebar() -> None:
    with st.sidebar:
        if st.button("🗑️ Clear Session Files"):
            shutil.rmtree(st.session_state.files_dir, ignore_errors=True)
            st.session_state.clear()
            st.toast("Session cleared!", icon="✅")
            st.rerun()
```

- [ ] **Step 2: Verify the file exists and imports cleanly**

```bash
cd app && python -c "from components.sidebar import render_sidebar; print('OK')"
```

Expected output: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/components/sidebar.py
git commit -m "feat: add shared sidebar component with clear-session button and toast"
```

---

### Task 2: Update `app.py` to use the shared sidebar

**Files:**
- Modify: `app/app.py`

- [ ] **Step 1: Replace the inline sidebar block with `render_sidebar()`**

Current `app/app.py` (lines 22–29):
```python
with st.sidebar:
    st.info("Select a page above to get started.")
    if st.button("🗑️ Clear Session Files"):
        import shutil

        shutil.rmtree(st.session_state.files_dir, ignore_errors=True)
        st.session_state.clear()
        st.rerun()
```

Replace with:
```python
from components.sidebar import render_sidebar

render_sidebar()
```

Add the import at the top of the file alongside the other imports:
```python
import streamlit as st
from components.sidebar import render_sidebar
from session import init_session

st.set_page_config(page_title="CaveSketch", layout="centered")
init_session()

st.title("🗺️ CaveSketch")
st.markdown("""
Welcome to **CaveSketch**, your mobile-friendly tool for generating cave survey plots
and satellite overlays.

### 🧭 Navigation
Use the sidebar to navigate between features:

1. **📐 Survey Plot**: Generate clean PDF maps and sections from your TopoDroid DXF exports.
2. **🌍 Satellite Map**: Georeference your cave and overlay it on satellite imagery.

---
*Created for cavers, by cavers.*
""")

render_sidebar()
```

- [ ] **Step 2: Run the app and manually verify the button appears on the main page**

```bash
streamlit run app/app.py
```

Open http://localhost:8501. Confirm:
- The sidebar shows the `🗑️ Clear Session Files` button
- Clicking it shows a green `✅ Session cleared!` toast
- Page reloads cleanly (no error)

- [ ] **Step 3: Commit**

```bash
git add app/app.py
git commit -m "refactor: use shared render_sidebar() in app.py"
```

---

### Task 3: Add sidebar to Survey Plot page

**Files:**
- Modify: `app/pages/1_survey_plot.py`

- [ ] **Step 1: Add `render_sidebar()` call after `init_session()`**

In `app/pages/1_survey_plot.py`, add the import and call:

```python
from pathlib import Path

import streamlit as st
from components.file_upload import (
    child_file_uploader_component,
    file_uploader_component,
    survey_name_component,
)
from components.settings_panel import settings_panel_component
from components.sidebar import render_sidebar
from session import init_session

from cave_sketch.survey import draw_survey

st.set_page_config(page_title="Cave Survey Plot", layout="centered")
init_session()
render_sidebar()

# ... rest of file unchanged ...
```

- [ ] **Step 2: Navigate to the Survey Plot page and verify the button**

With the app running (`streamlit run app/app.py`), navigate to the Survey Plot page.

Confirm:
- `🗑️ Clear Session Files` button appears in the sidebar
- Uploading a DXF file, then clicking the button clears the file state and returns to the initial state
- Toast `✅ Session cleared!` appears

- [ ] **Step 3: Commit**

```bash
git add app/pages/1_survey_plot.py
git commit -m "feat: add persistent clear-session sidebar to Survey Plot page"
```

---

### Task 4: Add sidebar to Satellite Map page

**Files:**
- Modify: `app/pages/2_satellite_map.py`

- [ ] **Step 1: Add `render_sidebar()` call after `init_session()`**

In `app/pages/2_satellite_map.py`, add the import and call:

```python
import streamlit as st
from components.gps_points import gps_points_editor_component, validate_known_points
from components.sidebar import render_sidebar
from session import init_session

from cave_sketch.satellite_view import draw_map

st.set_page_config(page_title="Satellite Map", layout="centered")
init_session()
render_sidebar()

# ... rest of file unchanged ...
```

- [ ] **Step 2: Navigate to the Satellite Map page and verify the button**

With the app running, navigate to the Satellite Map page.

Confirm:
- `🗑️ Clear Session Files` button appears in the sidebar
- After generating an HTML map, clicking the button clears `html_content`, `html_path`, `kml_path`, and all other state
- Toast `✅ Session cleared!` appears

- [ ] **Step 3: Commit**

```bash
git add app/pages/2_satellite_map.py
git commit -m "feat: add persistent clear-session sidebar to Satellite Map page"
```

---

### Task 5: Acceptance criteria walkthrough

- [ ] **Step 1: Full end-to-end verification**

Run: `streamlit run app/app.py`

Walk through each acceptance criterion:

| Criterion | Steps to verify |
|-----------|----------------|
| Button visible on all 3 pages | Visit Main, Survey Plot, Satellite Map — button must appear in sidebar on each |
| Button clears session state | Upload a file on Survey Plot, click clear — file uploader must reset to empty |
| Toast appears | Click clear on any page — `✅ Session cleared!` toast must appear briefly |
| New workflow possible immediately | After clearing, re-upload a file — must work without page refresh |

- [ ] **Step 2: Conductor - User Manual Verification 'Implementation' (Protocol in workflow.md)**
