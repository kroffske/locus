import logging
import os
from typing import Set, Tuple

logger = logging.getLogger(__name__)

def load_project_config(project_path: str) -> Tuple[Set[str], Set[str]]:
    """Loads ignore and allow patterns from .claudeignore and .claudeallow files.
    """
    ignore_file = os.path.join(project_path, ".claudeignore")
    allow_file = os.path.join(project_path, ".claudeallow")

    ignore_patterns = _read_pattern_file(ignore_file)
    allow_patterns = _read_pattern_file(allow_file)

    logger.debug(f"Loaded {len(ignore_patterns)} ignore patterns.")
    logger.debug(f"Loaded {len(allow_patterns)} allow patterns.")

    return ignore_patterns, allow_patterns

def _read_pattern_file(filepath: str) -> Set[str]:
    """Reads a pattern file, ignoring comments and empty lines."""
    patterns: Set[str] = set()
    if not os.path.isfile(filepath):
        return patterns

    try:
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
    except OSError as e:
        logger.error(f"Could not read pattern file {filepath}: {e}")

    return patterns
