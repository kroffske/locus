import ast
from typing import List

from ..models import AnalysisResult
from .types import CodeUnit


def _qualify_name(stack: List[str], name: str) -> str:
    return ".".join(stack + [name]) if stack else name


def extract_code_units(result: AnalysisResult) -> List[CodeUnit]:
    """Extract function-level code units from analyzed Python files.

    Uses the already-processed file contents from AnalysisResult to avoid re-reading.
    """
    units: List[CodeUnit] = []
    next_id = 0

    for abs_path, analysis in result.required_files.items():
        # Only consider Python modules
        if not analysis.file_info.filename.lower().endswith(".py"):
            continue
        src = analysis.content or ""
        if not src:
            continue
        try:
            tree = ast.parse(src, filename=analysis.file_info.absolute_path)
        except Exception:
            continue

        stack: List[str] = []

        def visit(node, class_stack: List[str]):
            nonlocal next_id
            if isinstance(node, ast.ClassDef):
                class_stack.append(node.name)
                for child in node.body:
                    visit(child, class_stack)
                class_stack.pop()
                return
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", start)
                try:
                    segment = ast.get_source_segment(src, node) or ""
                except Exception:
                    # Fallback to slicing by lines
                    lines = src.splitlines()
                    segment = "\n".join(lines[start - 1 : end])
                qual = _qualify_name(class_stack, node.name)
                units.append(
                    CodeUnit(
                        id=next_id,
                        file=analysis.file_info.absolute_path,
                        rel_path=analysis.file_info.relative_path,
                        qualname=qual,
                        span=(start, end),
                        source=segment,
                    )
                )
                next_id += 1
                # Recurse into nested functions if present
                for child in node.body:
                    visit(child, class_stack)
                return
            # Generic traversal for other containers
            for child in getattr(node, "body", []):
                visit(child, class_stack)

        visit(tree, stack)

    return units
