from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from cave_sketch.survey import draw_survey


@pytest.fixture
def map_csv(tmp_path: Path) -> Path:
    df = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "Links": ["st2", "st1"],
        "X": [0.0, 0.0],
        "Y": [-10.0, 10.0],
        "Type": ["station", "station"],
    })
    path = tmp_path / "map.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def section_csv(tmp_path: Path) -> Path:
    df = pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "Links": ["st2", "st1"],
        "X": [0.0, 20.0],
        "Y": [0.0, -5.0],
        "Type": ["station", "station"],
    })
    path = tmp_path / "section.csv"
    df.to_csv(path, index=False)
    return path


def _map_view_axes(fig: plt.Figure) -> List[plt.Axes]:
    """Filter out the title-block axes, same convention as test_survey_rendering.py."""
    return [ax for ax in fig.get_axes() if ax.get_position().y0 < 0.8]


def test_default_variation_matches_omitted_kwarg(map_csv: Path, tmp_path: Path) -> None:
    fig_default = draw_survey(
        title="A", rule_length=20, csv_map_path=str(map_csv),
        output_path=str(tmp_path / "a.pdf"),
    )
    fig_explicit_zero = draw_survey(
        title="A", rule_length=20, csv_map_path=str(map_csv),
        magnetic_variation_deg=0.0, output_path=str(tmp_path / "b.pdf"),
    )

    offsets_default = sorted(
        _map_view_axes(fig_default)[0].collections[-1].get_offsets().tolist()
    )
    offsets_zero = sorted(
        _map_view_axes(fig_explicit_zero)[0].collections[-1].get_offsets().tolist()
    )

    np.testing.assert_allclose(offsets_default, offsets_zero)
    np.testing.assert_allclose(offsets_default, sorted([[0.0, -10.0], [0.0, 10.0]]))


def test_variation_rotates_map_but_not_section(
    map_csv: Path, section_csv: Path, tmp_path: Path
) -> None:
    fig = draw_survey(
        title="A", rule_length=20,
        csv_map_path=str(map_csv), csv_section_path=str(section_csv),
        magnetic_variation_deg=10.0,
        output_path=str(tmp_path / "c.pdf"),
    )
    axes = _map_view_axes(fig)
    assert len(axes) == 2
    section_ax, map_ax = axes

    section_offsets = sorted(section_ax.collections[-1].get_offsets().tolist())
    np.testing.assert_allclose(section_offsets, sorted([[0.0, 0.0], [20.0, -5.0]]))

    map_offsets = sorted(map_ax.collections[-1].get_offsets().tolist())
    expected = sorted([
        [-1.7364817766693033, -9.848077530122081],
        [1.7364817766693033, 9.848077530122081],
    ])
    np.testing.assert_allclose(map_offsets, expected, atol=1e-6)
