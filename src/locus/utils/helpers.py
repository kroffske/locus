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
    ".bzr",
    ".venv",
    "venv",
    "env",
    ".env",
    "ENV",  # Uppercase virtualenv (common on Windows)
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "target",
    ".idea",
    ".vscode",
    # Output directories
    "out",
    "output",
    "outputs",
    "bin",  # Common build output (C/C++, .NET, etc.)
    "obj",  # Common build output (.NET, C++, etc.)
    # Cache directories
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    # Temporary directories
    "tmp",
    "temp",
    ".tmp",
    ".temp",
    # Log directories
    "logs",
}
DEFAULT_IGNORE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.egg-info",
    ".DS_Store",
    "*.swp",
    "*.swo",
    "*~",
    "*.bak",
    "*.log",
    "Thumbs.db",
}


def setup_logging(
    level: str = "INFO", log_format: str = "%(message)s", log_file: Optional[str] = None
):
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


def is_path_ignored(
    relative_path: str, project_root: Optional[str], ignore_patterns: Set[str]
) -> bool:
    """Checks if a path should be ignored based on default and custom rules."""
    norm_rel_path = relative_path.replace("\\", "/")
    path_parts = norm_rel_path.split("/")

    # Check if any directory component is in ALWAYS_IGNORE_DIRS
    if any(part in ALWAYS_IGNORE_DIRS for part in path_parts):
        return True

    # Ignore all directories starting with dot (except current directory marker)
    # This catches .cache, .pytest_cache, .mypy_cache, etc.
    if any(part.startswith(".") and part != "." for part in path_parts):
        return True

    basename = os.path.basename(relative_path)
    if any(fnmatch.fnmatch(basename, pattern) for pattern in DEFAULT_IGNORE_PATTERNS):
        return True

    for pattern in ignore_patterns:
        # Handle **/folder/** patterns (gitignore-style)
        if pattern.startswith("**/") and pattern.endswith("/**"):
            folder_name = pattern[3:-3]  # Extract 'folder' from '**/folder/**'
            # The **/folder/** pattern means files INSIDE matching directories
            # So we check all path components except the last one (which is the file/final dir)
            if any(ch in folder_name for ch in "*?["):
                # Use fnmatch to match against each path component (except last)
                for part in path_parts[:-1]:
                    if fnmatch.fnmatch(part, folder_name):
                        return True
            else:
                # Exact match for folder name without wildcards (except last)
                if folder_name in path_parts[:-1]:
                    return True
            continue

        # Handle **/folder patterns
        if pattern.startswith("**/"):
            target = pattern[3:]
            if fnmatch.fnmatch(basename, target) or any(
                fnmatch.fnmatch(part, target) for part in path_parts
            ):
                return True
            continue

        # Glob patterns with wildcards
        if any(ch in pattern for ch in "*?["):
            if fnmatch.fnmatch(norm_rel_path, pattern) or fnmatch.fnmatch(
                basename, pattern
            ):
                return True
            continue

        # Directory-style patterns (with or without trailing slash)
        pat = pattern.rstrip("/")
        if norm_rel_path == pat or norm_rel_path.startswith(pat + "/"):
            return True
    return False


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
