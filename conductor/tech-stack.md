# CaveSketch Tech Stack

## Language
- **Python (>= 3.11)**: Primary language for all logic and the UI.

## Core Frameworks & Libraries
- **Streamlit**: Multi-page web framework for the user interface.
- **Matplotlib**: Engine for rendering PDF survey plots and previews.
- **Folium**: Library for generating interactive georeferenced satellite maps.
- **KML**: Manual XML generation for Google Earth 3D exports.
- **ezdxf**: High-level CAD library for parsing and manipulating TopoDroid DXF exports.
- **NumPy & Pandas**: Data manipulation for georeferencing, station remapping, and coordinate transformations (merging).

## Infrastructure & Tools
- **uv**: Modern Python package and environment manager.
- **Ruff**: Fast Python linter and formatter.
- **Mypy**: Static type checker for Python.
- **Pytest**: Testing framework for library logic.

## Deployment
- **Streamlit Cloud**: Primary target for the live application.
- **GitHub Actions**: CI/CD for linting, type checking, and testing.
