import os
import logging
import fnmatch
from typing import List, Set

from ..utils import helpers

logger = logging.getLogger(__name__)

def scan_directory(
    project_path: str,
    ignore_patterns: Set[str],
    allow_patterns: Set[str]
) -> List[str]:
    """
    Walks a directory, applying ignore and allow patterns to find relevant files.
    Returns a list of absolute paths.
    """
    logger.info(f"Scanning project: {project_path}")
    candidate_files: List[str] = []

    for root, dirs, files in os.walk(project_path, topdown=True):
        # Filter directories in-place to prevent os.walk from traversing them
        original_dirs = list(dirs)
        dirs[:] = [
            d for d in original_dirs
            if not helpers.is_path_ignored(
                os.path.join(os.path.relpath(root, project_path), d, ''),
                project_path,
                ignore_patterns
            )
        ]
        
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = helpers.get_relative_path(abs_path, project_path)
            
            if helpers.is_path_ignored(rel_path, project_path, ignore_patterns):
                continue

            # Apply allow patterns
            rel_path_norm = rel_path.replace('\\', '/')
            if any(fnmatch.fnmatch(rel_path_norm, pattern) for pattern in allow_patterns):
                candidate_files.append(abs_path)

    unique_files = sorted(list(set(candidate_files)))
    logger.info(f"Scan found {len(unique_files)} files matching allow patterns.")
    return unique_files
