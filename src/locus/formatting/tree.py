import logging
import os
from typing import Any, Dict

from ..models import FileAnalysis
from .helpers import get_summary_from_analysis

logger = logging.getLogger(__name__)


def format_tree_markdown(
    tree_data: Dict[str, Any],
    file_details: Dict[str, FileAnalysis],
    include_comments: bool,
    current_path: str = "",
    prefix: str = "",
    ascii_tree: bool = False,
) -> str:
    """Recursively formats a file tree into a Markdown string."""
    details_map = {fa.file_info.relative_path.replace("\\", "/"): fa for fa in file_details.values()}
    sorted_keys = sorted(tree_data.keys(), key=lambda k: (isinstance(tree_data[k], dict), k.lower()))

    output_lines = []
    for i, key in enumerate(sorted_keys):
        is_last = i == len(sorted_keys) - 1
        connector = "- " if ascii_tree else ("└── " if is_last else "├── ")

        node_rel_path = os.path.join(current_path, key).replace("\\", "/")
        node_value = tree_data[key]

        comment_suffix = ""
        analysis = None
        if include_comments:
            analysis = details_map.get(node_rel_path) or details_map.get(os.path.join(node_rel_path, "__init__.py"))
            # Keep single-line summary for directories; for files we will render multiline below
            if isinstance(tree_data.get(key), dict):
                summary = get_summary_from_analysis(analysis)
                if summary:
                    comment_suffix = f"  # {summary}"

        if isinstance(node_value, dict):  # Directory
            output_lines.append(f"{prefix}{connector}{key}/{comment_suffix}")
            child_prefix = prefix + ("  " if is_last else "| ") if ascii_tree else prefix + ("    " if is_last else "│   ")
            output_lines.append(
                format_tree_markdown(
                    node_value,
                    file_details,
                    include_comments,
                    node_rel_path,
                    child_prefix,
                    ascii_tree,
                )
            )
        else:  # File
            # For files, keep a one-line suffix for compatibility, then add remaining
            # comment lines as indented multiline below the file entry.
            if include_comments and analysis and not comment_suffix:
                summary = get_summary_from_analysis(analysis)
                if summary:
                    comment_suffix = f"  # {summary}"

            output_lines.append(f"{prefix}{connector}{key}{comment_suffix}")

            # If requested, render additional top-of-file comment lines below
            if include_comments and analysis and getattr(analysis, "comments", None):
                extra = analysis.comments[1:] if len(analysis.comments) > 1 else []
                if extra:
                    child_prefix = (
                        prefix + ("  " if is_last else "| ") if ascii_tree else prefix + ("    " if is_last else "│   ")
                    )
                    for c in extra:
                        output_lines.append(f"{child_prefix}# {c}" if c else f"{child_prefix}#")

    return "\n".join(output_lines)


def format_flat_list(file_details: Dict[str, FileAnalysis], include_comments: bool) -> str:
    """Formats a flat list of files with optional one-line summaries.

    Output format: `path/to/file.py # summary`
    """
    details = list(file_details.values())
    details.sort(key=lambda fa: fa.file_info.relative_path.lower())
    lines = []
    for fa in details:
        rel = fa.file_info.relative_path.replace("\\", "/")
        summary = get_summary_from_analysis(fa) if include_comments else None
        lines.append(f"{rel}  # {summary}" if summary else rel)
    return "\n".join(lines)
