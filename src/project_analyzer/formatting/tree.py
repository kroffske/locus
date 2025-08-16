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
) -> str:
    """Recursively formats a file tree into a Markdown string."""
    details_map = {fa.file_info.relative_path: fa for fa in file_details.values()}
    sorted_keys = sorted(tree_data.keys(), key=lambda k: (isinstance(tree_data[k], dict), k.lower()))

    output_lines = []
    for i, key in enumerate(sorted_keys):
        is_last = i == len(sorted_keys) - 1
        connector = "└── " if is_last else "├── "

        node_rel_path = os.path.join(current_path, key).replace("\\", "/")
        node_value = tree_data[key]

        comment_suffix = ""
        if include_comments:
            analysis = details_map.get(node_rel_path) or details_map.get(os.path.join(node_rel_path, "__init__.py"))
            summary = get_summary_from_analysis(analysis)
            if summary:
                comment_suffix = f"  # {summary}"

        if isinstance(node_value, dict):  # Directory
            output_lines.append(f"{prefix}{connector}{key}/{comment_suffix}")
            child_prefix = prefix + ("    " if is_last else "│   ")
            output_lines.append(format_tree_markdown(node_value, file_details, include_comments, node_rel_path, child_prefix))
        else:  # File
            output_lines.append(f"{prefix}{connector}{key}{comment_suffix}")

    return "\n".join(output_lines)
