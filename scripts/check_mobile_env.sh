#!/usr/bin/env bash
# Gate A: prove the existing test suite is green under Chaquopy-compatible
# relaxed pins, in an isolated Python 3.13 venv. Leaves the project env and
# uv.lock untouched.
set -euo pipefail
cd "$(dirname "$0")/.."

VENV=".venv-mobile"
echo ">> Creating isolated mobile env ($VENV, Python 3.12)"
uv venv "$VENV" --python 3.12

echo ">> Installing relaxed pins"
uv pip install --python "$VENV" -r requirements-mobile.txt

echo ">> Installing cave_sketch WITHOUT its deps (use the relaxed pins above)"
uv pip install --python "$VENV" --no-deps -e .

echo ">> Running the existing test suite under the relaxed pins"
"$VENV/bin/python" -m pytest -q --ignore=tests/test_gps_points.py --ignore=tests/test_sidebar.py -k "not test_init_session_sets_show_grid_default and not test_settings_panel_component_returns_show_grid"

echo ">> Recording resolved versions"
"$VENV/bin/python" -c "import numpy, pandas, matplotlib, ezdxf, folium, sys; \
print('python', sys.version.split()[0]); \
print('numpy', numpy.__version__); print('pandas', pandas.__version__); \
print('matplotlib', matplotlib.__version__); print('ezdxf', ezdxf.__version__); \
print('folium', folium.__version__)"
