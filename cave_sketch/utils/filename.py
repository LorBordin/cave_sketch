import re


def sanitize_filename(name: str) -> str:
    """Sanitize a survey name to be used as a safe filename.

    Sanitization rules:
    - Strip leading/trailing whitespace.
    - Replace spaces and sequences of non-alphanumeric characters (except hyphens and
      underscores) with a single underscore.
    - Convert to lowercase.
    - If the result is empty after sanitization, fall back to "my_survey".
    """
    # Convert to lowercase
    name = name.lower()
    # Strip leading/trailing whitespace
    name = name.strip()
    # Replace spaces and sequences of non-alphanumeric (except hyphens and
    # underscores) with a single underscore.
    name = re.sub(r"[^\w-]+", "_", name)

    # If the result is empty after sanitization, fall back to "my_survey"
    if not name:
        return "my_survey"
    return name
