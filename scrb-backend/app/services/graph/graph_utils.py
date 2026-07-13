import re


def normalize_name(name: str) -> str:
    """
    Normalise names (lowercase, strip whitespace, remove special characters)
    for grouping accused/victims when identifiers are missing or dirty.
    """
    if not name:
        return ""
    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^a-z0-9 ]", "", name)
    return name
