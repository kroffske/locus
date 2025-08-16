import os
import ast
import logging
from typing import Set, Dict, List, Tuple, Optional

from ..models import FileInfo
from ..utils.file_cache import FileCache

logger = logging.getLogger(__name__)

def resolve_dependencies(
    initial_files: Set[str],
    file_map: Dict[str, FileInfo],
    module_to_file: Dict[str, str],
    max_depth: int
) -> Set[str]:
    """
    Recursively finds dependencies for a given set of initial files up to a max depth.
    """
    if not initial_files:
        return set()

    required_files: Set[str] = set()
    queue: List[Tuple[str, int]] = [(f, 0) for f in initial_files]
    visited: Set[str] = set(initial_files)

    while queue:
        current_file, depth = queue.pop(0)
        required_files.add(current_file)

        if max_depth != -1 and depth >= max_depth:
            continue
        
        # Only resolve dependencies for Python files
        if not current_file.endswith('.py'):
            continue

        imported_modules = extract_imports(current_file, file_map[current_file].relative_path)
        
        for module_name in imported_modules:
            dep_file = module_to_file.get(module_name)
            if dep_file and dep_file not in visited:
                visited.add(dep_file)
                queue.append((dep_file, depth + 1))

    logger.info(f"Resolved {len(required_files)} total required files from {len(initial_files)} initial targets.")
    return required_files


def extract_imports(file_path: str, relative_path: str) -> Set[str]:
    """Extracts a set of imported module names from a Python file."""
    imports: Set[str] = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=file_path)
    except (IOError, SyntaxError, UnicodeDecodeError) as e:
        logger.warning(f"Could not read or parse imports from '{relative_path}': {e}")
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(alias.name.split('.')[0]) # Add top-level package
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0: # Relative import
                resolved = _resolve_relative_import(relative_path, node.level, node.module)
                if resolved:
                    imports.add(resolved.split('.')[0])
            elif node.module: # Absolute import
                imports.add(node.module.split('.')[0])
    
    return imports

def _resolve_relative_import(current_rel_path: str, level: int, module: Optional[str]) -> Optional[str]:
    """Resolves a relative import to an absolute module path."""
    path_parts = os.path.dirname(current_rel_path).replace('\\', '/').split('/')
    if path_parts == ['']: path_parts = []

    # Go up the directory structure based on the level
    if level > len(path_parts):
        return None # Goes beyond project root
    
    base_parts = path_parts[:-level+1] if level > 1 else path_parts
    
    if module:
        module_parts = module.split('.')
        resolved_parts = base_parts + module_parts
    else: # from . import ...
        resolved_parts = base_parts

    return '.'.join(filter(None, resolved_parts))
