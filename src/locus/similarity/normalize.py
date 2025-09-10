import re
from typing import Set

_ws_re = re.compile(r"\s+")


def normalize_text(source: str) -> str:
    """Lightweight normalization: trim and collapse whitespace.

    MVP: keeps comments/docstrings; good enough for exact duplicates that match verbatim
    ignoring whitespace differences.
    """
    s = source.strip()
    s = _ws_re.sub(" ", s)
    return s


_TRIVIAL_NAMES: Set[str] = {
    "__repr__",
    "__str__",
    "__eq__",
    "__hash__",
    "__len__",
    "__iter__",
    "__enter__",
    "__exit__",
    "__aenter__",
    "__aexit__",
    "__bool__",
}


def is_trivial_qualname(qualname: str) -> bool:
    """Heuristic: treat common boilerplate methods and tiny helpers as trivial.

    KISS: simple suffix/prefix checks; callers can override via flags.
    """
    base = qualname.split(".")[-1]
    if base in _TRIVIAL_NAMES:
        return True
    # Common helper prefixes
    prefixes = ("get_", "set_", "to_", "as_")
    return base.startswith(prefixes)


def below_min_nodes(node_count: int, min_nodes: int) -> bool:
    if min_nodes <= 0:
        return False
    if node_count <= 0:
        # Unknown node count: do not exclude on size
        return False
    return node_count < min_nodes
