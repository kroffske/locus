import re


_ws_re = re.compile(r"\s+")


def normalize_text(source: str) -> str:
    """Lightweight normalization: trim and collapse whitespace.

    MVP: keeps comments/docstrings; good enough for exact duplicates that match verbatim
    ignoring whitespace differences.
    """
    s = source.strip()
    s = _ws_re.sub(" ", s)
    return s

