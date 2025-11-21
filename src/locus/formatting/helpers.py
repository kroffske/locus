import logging
import re
from typing import List, Optional, Pattern, Tuple, Union

from ..models import AnnotationInfo, FileAnalysis

logger = logging.getLogger(__name__)


def get_summary_from_analysis(analysis: Optional[FileAnalysis]) -> Optional[str]:
    """Extracts a one-line summary from a FileAnalysis object."""
    if not analysis:
        return None

    if analysis.annotations and analysis.annotations.module_docstring:
        return _extract_first_sentence(analysis.annotations.module_docstring)

    if analysis.comments:
        # Join all top-of-file comment lines into a single line for tree display
        joined = " ".join((c or "").strip() for c in analysis.comments)
        return joined.strip() or None

    return None


def _extract_first_sentence(text: str) -> str:
    """Extracts a clean, single-line first sentence/line from text.

    - Prefer the first non-empty line to avoid embedded newlines in summaries.
    - Then truncate at the first period for a concise sentence.
    - Clamp to a reasonable length.
    """
    if not text:
        return ""
    # Take first non-empty line to avoid multi-line spillover in tree
    first_line = next(
        (ln.strip() for ln in text.splitlines() if ln.strip()), ""
    ).strip()
    if not first_line:
        return ""
    sentence = first_line.split(".")[0].strip()
    # Do not clamp length; allow long lines to wrap naturally in output
    return sentence


def get_output_content(
    analysis: FileAnalysis,
    full_code_re: Optional[Union[Pattern, str]],
    annotation_re: Optional[Union[Pattern, str]],
) -> Tuple[str, str]:
    """Determines the content string and mode for a file.
    Returns (content, mode).
    """
    rel_path = analysis.file_info.relative_path.replace("\\", "/")
    content_to_use = analysis.content or f"# ERROR: No content for {rel_path}"
    mode = "default"

    if analysis.file_info.is_data_preview:
        mode = "data_preview"
    # Line range selection takes precedence over regex modes
    elif analysis.line_ranges:
        content_to_use = _slice_content_by_ranges(content_to_use, analysis.line_ranges)
        mode = "line_range"
    elif full_code_re:
        if isinstance(full_code_re, str):
            try:
                full_code_re = re.compile(full_code_re)
            except re.error:
                full_code_re = None
        if full_code_re and full_code_re.search(rel_path):
            mode = "full_code"
    elif annotation_re:
        if isinstance(annotation_re, str):
            try:
                annotation_re = re.compile(annotation_re)
            except re.error:
                annotation_re = None
        if annotation_re and annotation_re.search(rel_path) and analysis.annotations:
            content_to_use = format_annotations_as_py_stub(
                rel_path, analysis.annotations
            )
            mode = "annotation_stub"

    source_header = f"# source: {analysis.file_info.relative_path}"
    if not content_to_use.strip().lower().startswith(source_header.lower()):
        content_to_use = f"{source_header}\n{content_to_use}"

    return content_to_use, mode


def format_annotations_as_py_stub(
    relative_path: str, annotations: AnnotationInfo
) -> str:
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
                lines.append(
                    f"    {m_details.get('signature', f'def {m_name}(...):')} ..."
                )

            # Only add ... if empty
            if not attributes and not details.get("methods"):
                lines.append("    ...")
        lines.append("")

    return "\n".join(lines)


def _slice_content_by_ranges(
    content_with_header: str, ranges: List[Tuple[int, int]]
) -> str:
    """Returns content with only the lines in the provided 1-based inclusive ranges.

    Expects content_with_header to start with a '# source:' header line; preserves it.
    """
    lines = content_with_header.splitlines()
    out: List[str] = []
    # Preserve the first line if it's a source header
    if lines and lines[0].lower().startswith("# source:"):
        out.append(lines[0])
        body = lines[1:]
    else:
        body = lines

    total = len(body)
    # Build a boolean mask for selected lines
    select = [False] * total
    for s, e in ranges:
        s0 = max(1, s)
        e0 = max(1, e)
        if e0 < s0:
            s0, e0 = e0, s0
        # Convert to 0-based indices within body
        start_idx = max(0, s0 - 1)
        end_idx = min(total - 1, e0 - 1)
        for i in range(start_idx, end_idx + 1):
            select[i] = True

    # Extract selected lines
    sliced = [body[i] for i in range(total) if select[i]]
    if not sliced:
        # If nothing selected, return header plus empty line
        if out:
            return "\n".join(out + [""])
        return ""

    out.extend(sliced)
    return "\n".join(out)
