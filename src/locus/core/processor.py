import ast
import logging
import os
from typing import List

from ..formatting import data_preview
from ..models import AnnotationInfo, FileAnalysis, FileInfo
from ..utils.file_cache import FileCache

logger = logging.getLogger(__name__)


def process_file(file_info: FileInfo, file_cache: FileCache) -> FileAnalysis:
    """Processes a single file, dispatching to the correct analyzer based on file type."""
    file_path = file_info.absolute_path
    _, extension = os.path.splitext(file_path)

    if extension.lower() in data_preview.ALL_DATA_EXTENSIONS:
        return analyze_data_file(file_info)

    if extension.lower() == ".py":
        return analyze_python_file(file_info, file_cache)

    # Default for all other text-based files
    content = file_cache.get_content(file_path)
    return FileAnalysis(file_info=file_info, content=content)


def analyze_data_file(file_info: FileInfo) -> FileAnalysis:
    """Generates a preview for a known data file type."""
    logger.debug(f"Generating data preview for: {file_info.relative_path}")
    file_info.is_data_preview = True
    preview_content = data_preview.preview_data_file(file_info.absolute_path)

    analysis = FileAnalysis(file_info=file_info, content=preview_content)
    return analysis


def analyze_python_file(file_info: FileInfo, file_cache: FileCache) -> FileAnalysis:
    """Extracts content, comments, and AST-based annotations from a Python file."""
    content = file_cache.get_content(file_info.absolute_path)
    if content is None:
        file_info.is_empty = True
        return FileAnalysis(file_info=file_info, content="# ERROR: Could not read file content.")

    analysis = FileAnalysis(file_info=file_info, content=content)

    try:
        tree = ast.parse(content, filename=file_info.absolute_path)

        analysis.comments = _extract_header_comments(content)
        analysis.annotations = _extract_annotations(tree)
    except (SyntaxError, ValueError) as e:
        logger.warning(f"AST analysis failed for '{file_info.relative_path}': {e}.")

    return analysis


def _extract_header_comments(content: str) -> List[str]:
    """Extracts comments from the top of a file."""
    comments = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            comments.append(stripped.lstrip("# ").strip())
        elif stripped:
            break
    return comments


def _extract_annotations(tree: ast.AST) -> AnnotationInfo:
    """Extracts docstrings, signatures, and imports from an AST."""
    annotations = AnnotationInfo()
    annotations.module_docstring = ast.get_docstring(tree)

    # Extract imports
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_stmt = f"import {alias.name}"
                if alias.asname:
                    import_stmt += f" as {alias.asname}"
                annotations.imports.append(import_stmt)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names = ", ".join(f"{n.name} as {n.asname}" if n.asname else n.name for n in node.names)
                level = "." * node.level
                import_stmt = f"from {level}{node.module} import {names}"
            else:
                # Relative import without module name
                names = ", ".join(f"{n.name} as {n.asname}" if n.asname else n.name for n in node.names)
                level = "." * node.level
                import_stmt = f"from {level} import {names}"
            annotations.imports.append(import_stmt)

    # Extract functions and classes
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                signature = ast.unparse(node).split("\n", 1)[0].strip(":")
            except Exception:
                signature = f"def {node.name}(...)"
            annotations.elements[node.name] = {"type": "function", "signature": signature, "docstring": ast.get_docstring(node)}
        elif isinstance(node, ast.ClassDef):
            # Extract decorators
            decorators = []
            for decorator in node.decorator_list:
                try:
                    decorators.append(f"@{ast.unparse(decorator)}")
                except Exception:
                    decorators.append("@...")

            # Extract class attributes and methods
            attributes = []
            methods = {}

            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    # Type annotated attribute (e.g., path: str)
                    try:
                        attr_name = ast.unparse(item.target)
                        attr_type = ast.unparse(item.annotation)
                        if item.value:
                            attr_value = ast.unparse(item.value)
                            attributes.append(f"{attr_name}: {attr_type} = {attr_value}")
                        else:
                            attributes.append(f"{attr_name}: {attr_type}")
                    except Exception:
                        pass
                elif isinstance(item, ast.Assign):
                    # Regular assignment (e.g., x = 5)
                    try:
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attr_value = ast.unparse(item.value)
                                attributes.append(f"{target.id} = {attr_value}")
                    except Exception:
                        pass
                elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    try:
                        m_sig = ast.unparse(item).split("\n", 1)[0].strip(":")
                    except Exception:
                        m_sig = f"def {item.name}(...)"
                    methods[item.name] = {"signature": m_sig, "docstring": ast.get_docstring(item)}

            annotations.elements[node.name] = {"type": "class", "docstring": ast.get_docstring(node), "decorators": decorators, "attributes": attributes, "methods": methods}
    return annotations
