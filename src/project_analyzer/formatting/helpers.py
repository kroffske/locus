import logging
from typing import Optional, Pattern, Tuple

from ..models import FileAnalysis

logger = logging.getLogger(__name__)

def get_summary_from_analysis(analysis: Optional[FileAnalysis]) -> Optional[str]:
    """Extracts a one-line summary from a FileAnalysis object."""
    if not analysis:
        return None
    
    # Prioritize module docstring
    if analysis.annotations and analysis.annotations.module_docstring:
        return _extract_first_sentence(analysis.annotations.module_docstring)
    
    # Fallback to header comments
    if analysis.comments:
        return _extract_first_sentence(analysis.comments[0])
        
    return None

def _extract_first_sentence(text: str) -> str:
    """Extracts the first sentence of a text block."""
    if not text: return ""
    # Simple split, can be improved with regex
    sentence = text.split('.')[0].strip()
    if len(sentence) > 120: # Truncate long sentences
        return sentence[:117] + "..."
    return sentence

def get_output_content(
    analysis: FileAnalysis,
    full_code_re: Optional[Pattern],
    annotation_re: Optional[Pattern]
) -> Tuple[str, str]:
    """
    Determines the appropriate content string and mode for a file based on regex and file type.
    Returns (content, mode).
    """
    rel_path = analysis.file_info.relative_path.replace('\\', '/')
    content_to_use = analysis.content or f"# ERROR: No content available for {rel_path}"
    mode = "default"
    
    if analysis.file_info.is_data_preview:
        mode = "data_preview"
    elif full_code_re and full_code_re.search(rel_path):
        mode = "full_code"
    elif annotation_re and annotation_re.search(rel_path):
        if analysis.annotations:
            content_to_use = format_annotations_as_py_stub(rel_path, analysis.annotations)
            mode = "annotation_stub"
        else: # Fallback for non-python files or files with no annotations
            mode = "full_code" # Treat as full code if stub is not possible
    
    # Add a source header if not already present
    source_header = f"# source: {analysis.file_info.relative_path}"
    if not content_to_use.strip().lower().startswith(source_header.lower()):
        content_to_use = f"{source_header}\n{content_to_use}"

    return content_to_use, mode

def format_annotations_as_py_stub(relative_path: str, annotations) -> str:
    """Formats annotations into a Python stub file string."""
    lines = []
    if annotations.module_docstring:
        lines.append(f'"""{annotations.module_docstring}"""\n')

    for name, details in sorted(annotations.elements.items()):
        if details['type'] == 'function':
            lines.append(f"def {name}(...): ...")
        elif details['type'] == 'class':
            lines.append(f"class {name}:")
            if details.get('docstring'):
                lines.append(f'    """{details["docstring"]}"""')
            for m_name, m_details in sorted(details.get('methods', {}).items()):
                lines.append(f"    def {m_name}(...): ...")
            lines.append("    ...") # Indicate there might be more in the class
        lines.append("")

    return "\n".join(lines)
