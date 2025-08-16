import ast
import logging
from typing import List, Optional

from ..models import FileInfo, FileAnalysis, AnnotationInfo
from ..utils.file_cache import FileCache
from ..formatting import data_preview

logger = logging.getLogger(__name__)

def process_file(file_info: FileInfo, file_cache: FileCache) -> FileAnalysis:
    """
    Processes a single file, dispatching to the correct analyzer based on file type.
    """
    file_path = file_info.absolute_path
    _, extension = os.path.splitext(file_path)

    if extension.lower() in data_preview.ALL_DATA_EXTENSIONS:
        return analyze_data_file(file_info, file_cache)
    
    if extension.lower() == '.py':
        return analyze_python_file(file_info, file_cache)

    # Default for all other text-based files
    content = file_cache.get_content(file_path)
    return FileAnalysis(file_info=file_info, content=content)


def analyze_data_file(file_info: FileInfo, file_cache: FileCache) -> FileAnalysis:
    """
    Generates a preview for a known data file type.
    """
    logger.debug(f"Generating data preview for: {file_info.relative_path}")
    file_info.is_data_preview = True
    preview_content = data_preview.preview_data_file(file_info.absolute_path)
    
    analysis = FileAnalysis(file_info=file_info, content=preview_content)
    return analysis

def analyze_python_file(file_info: FileInfo, file_cache: FileCache) -> FileAnalysis:
    """
    Extracts content, comments, and AST-based annotations from a Python file.
    """
    content = file_cache.get_content(file_info.absolute_path)
    if content is None:
        file_info.is_empty = True
        return FileAnalysis(file_info=file_info, content="# ERROR: Could not read file content.")

    analysis = FileAnalysis(file_info=file_info, content=content)
    
    try:
        tree = ast.parse(content, filename=file_info.absolute_path)
        
        # Check for effective emptiness
        if not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign)) for node in tree.body):
             if not file_info.is_init: # Allow empty __init__.py files
                 file_info.is_empty = True

        # Extract header comments
        analysis.comments = _extract_header_comments(content)
        
        # Extract annotations
        analysis.annotations = _extract_annotations(tree)

    except SyntaxError as e:
        logger.warning(f"Syntax error in '{file_info.relative_path}': {e}. Skipping annotation extraction.")
        analysis.content = content + f"\n\n# NOTE: Syntax error prevented annotation analysis: {e}"
    except Exception as e:
        logger.error(f"Unexpected error analyzing AST for '{file_info.relative_path}': {e}", exc_info=True)

    return analysis

def _extract_header_comments(content: str) -> List[str]:
    """Extracts comments from the top of a file."""
    comments = []
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            comments.append(stripped.lstrip('# ').strip())
        elif stripped:  # Stop at the first non-empty, non-comment line
            break
    return comments

def _extract_annotations(tree: ast.AST) -> AnnotationInfo:
    """Extracts docstrings and signatures from an AST."""
    annotations = AnnotationInfo()
    annotations.module_docstring = ast.get_docstring(tree)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            docstring = ast.get_docstring(node)
            try:
                # ast.unparse is available in Python 3.9+
                signature = ast.unparse(node).split('\n')[0].strip(':')
            except AttributeError:
                signature = f"def {func_name}(...)"

            annotations.elements[func_name] = {
                "type": "function",
                "signature": signature,
                "docstring": docstring
            }
        elif isinstance(node, ast.ClassDef):
            class_name = node.name
            docstring = ast.get_docstring(node)
            methods = {}
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_name = item.name
                    method_doc = ast.get_docstring(item)
                    try:
                        m_sig = ast.unparse(item).split('\n')[0].strip(':')
                    except AttributeError:
                        m_sig = f"def {method_name}(...)"
                    methods[method_name] = {
                        "signature": m_sig,
                        "docstring": method_doc
                    }
            annotations.elements[class_name] = {
                "type": "class",
                "docstring": docstring,
                "methods": methods
            }
    return annotations
