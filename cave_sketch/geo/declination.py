import pandas as pd

from cave_sketch.features.geometry import rotate_points


def apply_magnetic_variation(df: pd.DataFrame, variation_deg: float) -> pd.DataFrame:
    """Rotate map X/Y coordinates from a magnetic-north to a true-north reference.

    Positive `variation_deg` is East declination, negative is West (true
    bearing = magnetic bearing + variation). A station recorded on the
    magnetic-north axis must end up at its true azimuth, which is a
    clockwise turn of `variation_deg` — hence the negation before calling
    the CCW-positive `rotate_points`.
    """
    df = df.copy()
    if variation_deg == 0:
        return df

    center = (float(df["X"].mean()), float(df["Y"].mean()))
    df.loc[:, ["X", "Y"]] = rotate_points(df[["X", "Y"]].values, center, -variation_deg)
    return df
