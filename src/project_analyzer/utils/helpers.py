import os
import logging
import fnmatch
import re
from typing import Set, Dict, Any, List, Optional, Pattern

from ..models import FileInfo

logger = logging.getLogger(__name__)

# --- Hardcoded directories and patterns to always ignore ---
ALWAYS_IGNORE_DIRS = {
    '.git', '.hg', '.svn', '.venv', 'venv', 'env', '.env', '__pycache__',
    'node_modules', 'build', 'dist', 'target', '.idea', '.vscode',
}
DEFAULT_IGNORE_PATTERNS = {
    '*.pyc', '*.pyo', '*.pyd', '*.so', '*.egg-info', '.DS_Store', '*.swp',
}

def setup_logging(level: str = 'INFO', log_format: str = '%(asctime)s - %(levelname)s - %(message)s', log_file: Optional[str] = None):
    """Configures logging for the application."""
    log_level_int = getattr(logging, level.upper(), logging.INFO)
    
    root_logger = logging.getLogger()
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handlers = [logging.StreamHandler()]
    if log_file:
        try:
            handlers.append(logging.FileHandler(log_file, mode='w', encoding='utf-8'))
        except IOError as e:
            print(f"Warning: Could not open log file {log_file}: {e}", file=sys.stderr)

    logging.basicConfig(level=log_level_int, format=log_format, handlers=handlers)
    logger.info(f"Logging configured at level {level.upper()}")

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
    try:
        return os.path.relpath(abs_path, project_root)
    except ValueError:
        return os.path.basename(abs_path)

def get_module_name(relative_path: str) -> Optional[str]:
    """Converts a file's relative path to a Python module name."""
    if not relative_path.endswith('.py'):
        return None
    
    # Remove .py extension
    module_path = relative_path[:-3]
    # Handle __init__.py files
    if module_path.endswith('__init__'):
        module_path = os.path.dirname(module_path)
    
    # Convert path separators to dots
    return module_path.replace(os.sep, '.')

def is_path_ignored(relative_path: str, project_root: str, ignore_patterns: Set[str]) -> bool:
    """Checks if a path should be ignored based on default and custom rules."""
    path_parts = set(relative_path.replace('\\', '/').split('/'))
    
    # 1. Check hardcoded directory names
    if any(part in ALWAYS_IGNORE_DIRS for part in path_parts):
        return True
    
    # 2. Check default file patterns against the basename
    basename = os.path.basename(relative_path)
    if any(fnmatch.fnmatch(basename, pattern) for pattern in DEFAULT_IGNORE_PATTERNS):
        return True
        
    # 3. Check custom patterns from .claudeignore
    norm_rel_path = relative_path.replace('\\', '/')
    if any(fnmatch.fnmatch(norm_rel_path, pattern) for pattern in ignore_patterns):
        return True

    return False

def build_file_tree(file_infos: List[FileInfo]) -> Dict[str, Any]:
    """Builds a nested dictionary representing the file tree structure."""
    tree: Dict[str, Any] = {}
    for info in file_infos:
        parts = info.relative_path.replace('\\', '/').split('/')
        current_level = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1: # It's a file
                current_level[part] = None
            else: # It's a directory
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
    return tree
