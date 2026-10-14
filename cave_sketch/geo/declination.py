import pandas as pd

from cave_sketch.features.geometry import rotate_points


def apply_magnetic_variation(df: pd.DataFrame, variation_deg: float) -> pd.DataFrame:
    """Rotate map X/Y coordinates and symbol rotations from magnetic to true north.

    Positive `variation_deg` is East declination, negative is West (true
    bearing = magnetic bearing + variation). A station recorded on the
    magnetic-north axis must end up at its true azimuth, which is a
    clockwise turn of `variation_deg` — hence the negation before calling
    the CCW-positive `rotate_points`. Similarly, symbol `Rotation` values
    are rotated clockwise by `variation_deg` (adjusted by `-variation_deg` modulo 360°).
    """
    df = df.copy()
    if variation_deg == 0:
        return df

    center = (float(df["X"].mean()), float(df["Y"].mean()))
    df.loc[:, ["X", "Y"]] = rotate_points(df[["X", "Y"]].values, center, -variation_deg)
    if "Rotation" in df.columns:
        df.loc[:, "Rotation"] = (df["Rotation"] - variation_deg) % 360.0
    return df
