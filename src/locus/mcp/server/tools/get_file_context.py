from __future__ import annotations

import os
from typing import List

from locus.core.orchestrator import analyze
from locus.formatting.helpers import get_output_content
from locus.models import TargetSpecifier


def get_file_context(
    path: str,
    start_line: int | None = None,
    end_line: int | None = None,
    style: str = "full",
) -> List[dict]:
    """Return full or ranged file content, with optional formatting."""
    try:
        from mcp import TextContent
    except ImportError:
        raise ImportError("MCP types not found. Please install with: pip install 'locus-analyzer[mcp]'")

    # Security: Validate path within repo root
    repo_root = os.getcwd()
    abs_path = os.path.abspath(os.path.join(repo_root, path))
    if not abs_path.startswith(repo_root):
        return [TextContent(text=f"Error: Invalid path '{path}' (outside repo).")]

    line_ranges = []
    if start_line and end_line:
        line_ranges.append((start_line, end_line))

    spec = TargetSpecifier(path=path, line_ranges=line_ranges)
    result = analyze(
        project_path=repo_root,
        target_specs=[spec],
        max_depth=0,
        include_patterns=None,
        exclude_patterns=None,
    )

    file_analysis = next(iter(result.required_files.values()), None)
    if not file_analysis:
        return [TextContent(text=f"Error: Could not find or access file '{path}'.")]

    content = file_analysis.content or ""
    if style == "annotations" and file_analysis.annotations:
        content, _ = get_output_content(file_analysis, None, ".*")

    return [TextContent(text=content)]
