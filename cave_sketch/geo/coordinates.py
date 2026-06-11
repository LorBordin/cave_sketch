"""Utility functions for coordinate parsing and validation."""


def parse_coordinate(value: str) -> float | None:
    """Parses a coordinate string (latitude or longitude) into a float.

    Accepts both '.' and ',' as decimal separators.

    Args:
        value: The coordinate string to parse.

    Returns:
        The float value if successfully parsed, or None otherwise.
    """
    cleaned = value.strip()
    if not cleaned:
        return None

    # Replace comma with dot to normalize decimal separator
    normalized = cleaned.replace(",", ".")

    try:
        return float(normalized)
    except ValueError:
        return None
