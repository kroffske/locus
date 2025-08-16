import logging
from typing import Optional, Pattern, Tuple

from ..models import AnnotationInfo, FileAnalysis

logger = logging.getLogger(__name__)


def get_summary_from_analysis(analysis: Optional[FileAnalysis]) -> Optional[str]:
    """Extracts a one-line summary from a FileAnalysis object."""
    if not analysis:
        return None

    if analysis.annotations and analysis.annotations.module_docstring:
        return _extract_first_sentence(analysis.annotations.module_docstring)

    if analysis.comments:
        return _extract_first_sentence(analysis.comments[0])

    return None


def _extract_first_sentence(text: str) -> str:
    """Extracts the first sentence of a text block."""
    if not text:
        return ""
    sentence = text.split(".")[0].strip()
    return sentence[:117] + "..." if len(sentence) > 120 else sentence


def get_output_content(
    analysis: FileAnalysis,
    full_code_re: Optional[Pattern],
    annotation_re: Optional[Pattern],
) -> Tuple[str, str]:
    """Determines the content string and mode for a file.
    Returns (content, mode).
    """
    rel_path = analysis.file_info.relative_path.replace("\\", "/")
    content_to_use = analysis.content or f"# ERROR: No content for {rel_path}"
    mode = "default"

    if analysis.file_info.is_data_preview:
        mode = "data_preview"
    elif full_code_re and full_code_re.search(rel_path):
        mode = "full_code"
    elif annotation_re and annotation_re.search(rel_path) and analysis.annotations:
        content_to_use = format_annotations_as_py_stub(rel_path, analysis.annotations)
        mode = "annotation_stub"

    source_header = f"# source: {analysis.file_info.relative_path}"
    if not content_to_use.strip().lower().startswith(source_header.lower()):
        content_to_use = f"{source_header}\n{content_to_use}"

    return content_to_use, mode


def format_annotations_as_py_stub(relative_path: str, annotations: AnnotationInfo) -> str:
    """Formats annotations into a Python stub file string."""
    lines = []
    if annotations.module_docstring:
        lines.append(f'"""{annotations.module_docstring}"""\n')

    # Add imports
    if annotations.imports:
        for import_stmt in annotations.imports:
            lines.append(import_stmt)
        lines.append("")

    for name, details in sorted(annotations.elements.items()):
        if details["type"] == "function":
            lines.append(f"{details.get('signature', f'def {name}(...):')} ...")
        elif details["type"] == "class":
            # Add decorators
            decorators = details.get("decorators", [])
            for decorator in decorators:
                lines.append(decorator)

            # Class definition
            lines.append(f"class {name}:")
            if details.get("docstring"):
                lines.append(f'    """{details["docstring"]}"""')

            # Add class attributes
            attributes = details.get("attributes", [])
            for attr in attributes:
                lines.append(f"    {attr}")

            # Add methods
            for m_name, m_details in sorted(details.get("methods", {}).items()):
                lines.append(f"    {m_details.get('signature', f'def {m_name}(...):')} ...")

            # Only add ... if empty
            if not attributes and not details.get("methods"):
                lines.append("    ...")
        lines.append("")

    return "\n".join(lines)
