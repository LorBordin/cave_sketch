import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

import streamlit as st
from matplotlib.figure import Figure


class AppState(TypedDict):
    files_dir: Path
    cave_survey: Optional[Figure]
    pdf_output_path: Optional[Path]
    map_loaded: bool
    map_csv: Optional[Path]
    section_csv: Optional[Path]
    known_points: List[Dict[str, Any]]
    rotation_angle: float
    html_content: Optional[str]
    html_path: Optional[Path]
    current_json_path: Optional[Path]
    uploaded_json_paths: List[str]


def init_session() -> None:
    """Initialize all session state keys with default values if they are missing."""
    if "files_dir" not in st.session_state:
        session_id = str(uuid.uuid4())
        temp_root = tempfile.gettempdir()
        st.session_state.files_dir = Path(temp_root) / f"cavesketch_{session_id}"
        os.makedirs(st.session_state.files_dir, exist_ok=True)

    defaults = {
        "cave_survey": None,
        "pdf_output_path": None,
        "map_loaded": False,
        "map_csv": None,
        "section_csv": None,
        "known_points": [{"station": "", "lat": 0.0, "lon": 0.0}],
        "rotation_angle": 0.0,
        "html_content": None,
        "html_path": None,
        "current_json_path": None,
        "uploaded_json_paths": [],
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_state() -> AppState:
    """Type-safe helper to get the session state."""
    return st.session_state  # type: ignore
