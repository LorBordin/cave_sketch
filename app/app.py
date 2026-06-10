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
