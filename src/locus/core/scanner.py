import fnmatch
import logging
import os
from typing import List, Set

from ..utils import helpers

logger = logging.getLogger(__name__)


def scan_directory(
    project_path: str,
    ignore_patterns: Set[str],
    allow_patterns: Set[str],
) -> List[str]:
    """Walks a directory, applying ignore and allow patterns to find relevant files.
    Returns a list of absolute paths.
    """
    logger.info(f"Scanning project: {project_path}")
    candidate_files: List[str] = []

    for root, dirs, files in os.walk(project_path, topdown=True):
        original_dirs = dirs[:]
        dirs[:] = [d for d in original_dirs]

        for file in files:
            abs_path = os.path.join(root, file)
            
            # Skip special Windows device files like NUL, CON, PRN, etc.
            if os.name == 'nt' and file.upper() in ['NUL', 'CON', 'PRN', 'AUX', 'COM1', 'COM2', 'COM3', 'COM4', 'LPT1', 'LPT2', 'LPT3']:
                logger.debug(f"Skipping Windows device file: {file}")
                continue
            
            try:
                rel_path = helpers.get_relative_path(abs_path, project_path)
            except (ValueError, OSError) as e:
                logger.warning(f"Skipping file due to path error: {abs_path} - {e}")
                continue

            if helpers.is_path_ignored(rel_path, ignore_patterns):
                continue

            rel_path_norm = rel_path.replace("\\", "/")
            if any(fnmatch.fnmatch(rel_path_norm, pattern) or fnmatch.fnmatch(os.path.basename(rel_path_norm), pattern) for pattern in allow_patterns):
                candidate_files.append(abs_path)

    unique_files = sorted(list(set(candidate_files)))
    logger.info(f"Scan found {len(unique_files)} files matching allow patterns.")
    return unique_files
