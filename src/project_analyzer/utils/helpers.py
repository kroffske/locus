import fnmatch
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, Pattern, Set

from ..models import FileInfo

logger = logging.getLogger(__name__)

ALWAYS_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    ".env",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "target",
    ".idea",
    ".vscode",
}
DEFAULT_IGNORE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.egg-info",
    ".DS_Store",
    "*.swp",
    "*.bak",
}


def setup_logging(level: str = "INFO", log_format: str = "%(message)s", log_file: Optional[str] = None):
    """Configures logging for the application."""
    log_level_int = getattr(logging, level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        try:
            handlers.append(logging.FileHandler(log_file, mode="w", encoding="utf-8"))
        except OSError as e:
            print(f"Warning: Could not open log file {log_file}: {e}", file=sys.stderr)

    logging.basicConfig(level=log_level_int, format=log_format, handlers=handlers)


def compile_regex(pattern: Optional[str]) -> Optional[Pattern]:
    """Compiles a regex pattern, raising ValueError on failure."""
    if not pattern:
        return None
    try:
        return re.compile(pattern)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e


def get_relative_path(abs_path: str, project_root: str) -> str:
    """Safely computes a relative path."""
    return os.path.relpath(abs_path, project_root)


def get_module_name(relative_path: str) -> Optional[str]:
    """Converts a file's relative path to a Python module name."""
    if not relative_path.endswith(".py"):
        return None
    module_path = os.path.splitext(relative_path)[0]
    if os.path.basename(module_path) == "__init__":
        module_path = os.path.dirname(module_path)
    return module_path.replace(os.sep, ".")


def is_path_ignored(relative_path: str, ignore_patterns: Set[str]) -> bool:
    """Checks if a path should be ignored based on default and custom rules."""
    path_parts = set(relative_path.replace("\\", "/").split("/"))

    if any(part in ALWAYS_IGNORE_DIRS for part in path_parts):
        return True

    basename = os.path.basename(relative_path)
    if any(fnmatch.fnmatch(basename, pattern) for pattern in DEFAULT_IGNORE_PATTERNS):
        return True

    norm_rel_path = relative_path.replace("\\", "/")
    return any(fnmatch.fnmatch(norm_rel_path, pattern) for pattern in ignore_patterns)


def build_file_tree(file_infos: List[FileInfo]) -> Dict[str, Any]:
    """Builds a nested dictionary representing the file tree structure."""
    tree: Dict[str, Any] = {}
    for info in file_infos:
        parts = info.relative_path.replace("\\", "/").split("/")
        current_level = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current_level[part] = None
            else:
                current_level = current_level.setdefault(part, {})
    return tree
