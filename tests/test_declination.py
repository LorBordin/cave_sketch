import numpy as np
import pandas as pd
import pytest

from cave_sketch.geo.declination import apply_magnetic_variation


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "Node_Id": ["st1", "st2"],
        "Links": ["st2", "st1"],
        "X": [0.0, 0.0],
        "Y": [-10.0, 10.0],
        "Type": ["station", "station"],
    })


def test_zero_variation_is_a_noop_copy() -> None:
    df = _sample_df()
    result = apply_magnetic_variation(df, 0.0)

    assert result is not df
    pd.testing.assert_series_equal(result["X"], df["X"])
    pd.testing.assert_series_equal(result["Y"], df["Y"])


def test_east_variation_rotates_clockwise() -> None:
    """Worked example from the design spec: +10 deg East declination rotates
    a point on the local +Y axis, (0, 10), to approximately (1.736, 9.848)."""
    result = apply_magnetic_variation(_sample_df(), 10.0)
    row = result[result["Node_Id"] == "st2"].iloc[0]

    assert row["X"] == pytest.approx(1.7364817766693033, abs=1e-6)
    assert row["Y"] == pytest.approx(9.848077530122081, abs=1e-6)


def test_west_variation_rotates_counterclockwise() -> None:
    """-10 deg West mirrors the East case across the X axis."""
    result = apply_magnetic_variation(_sample_df(), -10.0)
    row = result[result["Node_Id"] == "st2"].iloc[0]

    assert row["X"] == pytest.approx(-1.7364817766693033, abs=1e-6)
    assert row["Y"] == pytest.approx(9.848077530122081, abs=1e-6)


def test_round_trip_restores_original_coordinates() -> None:
    df = _sample_df()
    rotated = apply_magnetic_variation(df, 7.5)
    restored = apply_magnetic_variation(rotated, -7.5)

    np.testing.assert_allclose(restored["X"].to_numpy(), df["X"].to_numpy(), atol=1e-9)
    np.testing.assert_allclose(restored["Y"].to_numpy(), df["Y"].to_numpy(), atol=1e-9)
