import ast
import logging
import os
from typing import Dict, List, Optional, Set, Tuple

from ..models import FileInfo

logger = logging.getLogger(__name__)

def resolve_dependencies(
    initial_files: Set[str],
    file_map: Dict[str, FileInfo],
    module_to_file: Dict[str, str],
    max_depth: int,
) -> Set[str]:
    """Recursively finds dependencies for a given set of initial files up to a max depth.
    """
    required_files: Set[str] = set()
    queue: List[Tuple[str, int]] = [(f, 0) for f in initial_files]
    visited: Set[str] = set(initial_files)

    while queue:
        current_file, depth = queue.pop(0)
        required_files.add(current_file)

        if max_depth != -1 and depth >= max_depth:
            continue

        if not current_file.endswith(".py"):
            continue

        imported_modules = extract_imports(current_file, file_map[current_file].relative_path)

        for module_name in imported_modules:
            dep_file = module_to_file.get(module_name)
            if dep_file and dep_file not in visited:
                visited.add(dep_file)
                queue.append((dep_file, depth + 1))

    logger.info(f"Resolved {len(required_files)} files from {len(initial_files)} initial targets.")
    return required_files


def extract_imports(file_path: str, relative_path: str) -> Set[str]:
    """Extracts a set of imported module names from a Python file."""
    imports: Set[str] = set()
    try:
        with open(file_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception as e:
        logger.warning(f"Could not parse imports from '{relative_path}': {e}")
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                resolved = _resolve_relative_import(relative_path, node.level, node.module)
                if resolved: imports.add(resolved.split(".")[0])
            elif node.module:
                imports.add(node.module.split(".")[0])

    return imports

def _resolve_relative_import(current_rel_path: str, level: int, module: Optional[str]) -> Optional[str]:
    """Resolves a relative import to an absolute module path."""
    path_parts = os.path.dirname(current_rel_path).replace("\\", "/").split("/")
    if path_parts == [""]: path_parts = []

    if level > len(path_parts): return None
    base_parts = path_parts[:-level+1] if level > 1 else path_parts

    resolved_parts = base_parts + (module.split(".") if module else [])
    return ".".join(filter(None, resolved_parts))
