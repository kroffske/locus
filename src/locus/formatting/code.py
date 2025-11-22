import logging
import os
from typing import Optional, Pattern, Tuple

from ..core.config import LocusConfig, load_config
from ..core.modular_export import (
    check_and_split_large_groups,
    format_grouped_content,
    group_files_by_module,
)
from ..models import AnalysisResult, FileAnalysis
from .helpers import get_output_content

logger = logging.getLogger(__name__)

# Constants for modular export file format
# These correspond to the format in format_grouped_content():
# "# File: {path}\n# ===...\n\n{content}\n\n\n"
FILE_HEADER_LINES = 3  # "# File: ...", "# ===...", empty line
FILE_FOOTER_LINES = 2  # Two empty lines after content


def format_code_collection(
    result: AnalysisResult,
    full_code_re: Optional[Pattern] = None,
    annotation_re: Optional[Pattern] = None,
) -> str:
    """Formats the collected file contents into a single string for Markdown output."""
    output_parts = []
    sorted_files = sorted(
        result.required_files.values(), key=lambda fa: fa.file_info.relative_path
    )

    for analysis in sorted_files:
        content, _ = get_output_content(analysis, full_code_re, annotation_re)
        lang = "python" if analysis.file_info.filename.endswith(".py") else ""

        output_parts.append(f"### File: `{analysis.file_info.relative_path}`")
        output_parts.append(f"```{lang}\n{content.strip()}\n```\n")

    return "\n".join(output_parts)


def collect_files_to_directory(
    result: AnalysisResult,
    output_dir: str,
    full_code_re: Optional[Pattern] = None,
    annotation_re: Optional[Pattern] = None,
) -> int:
    """Collects analyzed files into an output directory with flat structure."""
    os.makedirs(output_dir, exist_ok=True)
    collected_count = 0

    for analysis in result.required_files.values():
        content, mode = get_output_content(analysis, full_code_re, annotation_re)
        if not content or content.startswith("# ERROR"):
            continue

        # Create flat filename by replacing path separators with underscores
        flat_filename = analysis.file_info.relative_path.replace(os.sep, "_").replace(
            "/", "_"
        )
        target_path = os.path.join(output_dir, flat_filename)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            collected_count += 1
            logger.debug(
                f"Collected '{analysis.file_info.relative_path}' ({mode}) to '{flat_filename}'"
            )
        except OSError as e:
            logger.error(f"Error writing file {target_path}: {e}")

    logger.info(f"Collected {collected_count} files into {output_dir}")
    return collected_count


def _extract_top_comments_block(analysis: FileAnalysis) -> Optional[str]:
    """Builds a string containing only the file's header comments and module docstring.
    Returns None if neither exists.
    """
    # Only meaningful for Python files
    if not analysis.file_info.filename.endswith(".py"):
        return None

    lines = []

    # Pre-import hash comments at the very top (already stripped of '# ')
    if analysis.comments:
        for c in analysis.comments:
            # Reconstruct as Python comments
            if c:
                lines.append(f"# {c}")
            else:
                lines.append("#")

    # Module docstring (can be multiple lines)
    doc = analysis.annotations.module_docstring if analysis.annotations else None
    if doc:
        if lines:
            lines.append("")
        lines.append('"""' + doc + '"""')

    content = "\n".join(lines).strip()
    return content or None


def format_top_comments_collection(result: AnalysisResult) -> str:
    """Formats only top-of-file comments (hash preamble + module docstrings) for Python files.
    Skips files without such content.
    """
    output_parts = []
    sorted_files = sorted(
        result.required_files.values(), key=lambda fa: fa.file_info.relative_path
    )

    for analysis in sorted_files:
        content = _extract_top_comments_block(analysis)
        if not content:
            continue

        output_parts.append(f"### File: `{analysis.file_info.relative_path}`")
        output_parts.append(f"```python\n{content}\n```\n")

    if not output_parts:
        return (
            "_No top-of-file comments or module docstrings found in analyzed files._\n"
        )
    return "\n".join(output_parts)


def generate_index_content(
    groups: dict,
    get_content_func,
) -> str:
    """Generate index content mapping source files to their locations in export files.

    Args:
        groups: Dictionary mapping group keys to lists of FileAnalysis objects
        get_content_func: Function to get content from FileAnalysis

    Returns:
        Formatted index content as string

    Raises:
        ValueError: If groups is empty or get_content_func is not callable
    """
    # Input validation (fail-fast principle)
    if not groups:
        raise ValueError("Groups dictionary cannot be empty")
    if not callable(get_content_func):
        raise ValueError("get_content_func must be callable")

    index_parts = []

    # Add header with grep instructions
    index_parts.extend(
        [
            "# Locus Export Index",
            "# ===================",
            "#",
            "# This index helps you quickly find and filter source files in the export.",
            "#",
            "# Quick Search Tips:",
            '#   Find file:        grep "^## " index.txt | grep "filename"',
            '#   Find in module:   grep "Module:" index.txt | grep "module_name"',
            '#   Get line range:   grep -A 4 "filename" index.txt',
            '#   List all files:   grep "^## " index.txt',
            "#",
            "# Exported Files:",
            "# ---------------",
            "",
        ]
    )

    # Process each group to build file index entries
    file_entries = []

    for group_key, files in sorted(groups.items()):
        output_filename = f"{group_key}.txt"

        # Calculate line ranges for each file in this group
        current_line = 1
        sorted_files = sorted(files, key=lambda fa: fa.file_info.relative_path)

        for analysis in sorted_files:
            content, _ = get_content_func(analysis)
            if not content or content.startswith("# ERROR"):
                continue

            # Calculate how many lines this file takes in the output
            # Use constants for consistent format calculation
            content_lines = _count_lines(content.strip())

            start_line = current_line + FILE_HEADER_LINES
            end_line = start_line + content_lines - 1

            # Extract description from comments or docstring
            description = _extract_file_description(analysis)

            # Build entry
            entry_parts = [
                f"## {analysis.file_info.relative_path}",
                f"   Module: {analysis.file_info.module_name or 'N/A'}",
                f"   Description: {description}",
                f"   Export: {output_filename}",
                f"   Lines: {start_line}-{end_line}",
                "",
            ]
            file_entries.append("\n".join(entry_parts))

            # Update line counter for next file
            current_line += FILE_HEADER_LINES + content_lines + FILE_FOOTER_LINES

    index_parts.extend(file_entries)
    return "\n".join(index_parts)


def _count_lines(content: str) -> int:
    """Count lines in content efficiently.

    Args:
        content: String content to count lines in

    Returns:
        Number of lines in content
    """
    if not content:
        return 0
    # More efficient than splitlines() for large files
    return content.count("\n") + 1


def _extract_file_description(analysis: FileAnalysis) -> str:
    """Extract a short description from file's comments or docstring.

    Args:
        analysis: FileAnalysis object

    Returns:
        Description string (first non-empty comment or first line of docstring)
    """
    # Try module docstring first
    if analysis.annotations and analysis.annotations.module_docstring:
        docstring = analysis.annotations.module_docstring.strip()
        # Get first line
        first_line = docstring.split("\n")[0].strip()
        if first_line:
            return first_line

    # Try top comments
    if analysis.comments:
        for comment in analysis.comments:
            if comment.strip():
                return comment.strip()

    return "No description available"


def collect_files_modular(
    result: AnalysisResult,
    output_dir: str,
    full_code_re: Optional[Pattern] = None,
    annotation_re: Optional[Pattern] = None,
    config: Optional[LocusConfig] = None,
) -> Tuple[int, Optional[str]]:
    """Collects analyzed files into an output directory with modular grouping.

    Args:
        result: Analysis result containing files to collect
        output_dir: Output directory path
        full_code_re: Regex for full code extraction
        annotation_re: Regex for annotation extraction
        config: Locus configuration (loaded if not provided)

    Returns:
        Tuple of (number of output files created, index content string or None)
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load config if not provided
    if config is None:
        config = load_config(result.project_path)

    # Check if modular export is enabled
    if not config.modular_export.enabled:
        logger.info("Modular export disabled, falling back to flat collection")
        files_created = collect_files_to_directory(
            result, output_dir, full_code_re, annotation_re
        )
        return (files_created, None)

    # Group files by module
    groups = group_files_by_module(result, config)
    logger.info(
        f"Grouped {len(result.required_files)} files into {len(groups)} modules"
    )

    # Helper function to get content
    def get_content(analysis):
        return get_output_content(analysis, full_code_re, annotation_re)

    # Check and split large groups
    groups = check_and_split_large_groups(
        groups,
        config.modular_export.max_lines_per_file,
        get_content,
    )

    # Write each group to a file
    files_created = 0
    for group_key, files in groups.items():
        content, line_count = format_grouped_content(files, get_content)

        if not content.strip():
            logger.debug(f"Skipping empty group '{group_key}'")
            continue

        # Create output filename
        output_filename = f"{group_key}.txt"
        output_path = os.path.join(output_dir, output_filename)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            files_created += 1
            logger.info(
                f"Created '{output_filename}': {line_count} lines from {len(files)} source files"
            )
        except OSError as e:
            logger.error(f"Error writing file {output_path}: {e}")

    # Generate and write index file
    index_content = None
    if groups:  # Only generate index if we have groups
        try:
            index_content = generate_index_content(groups, get_content)
            index_path = os.path.join(output_dir, "index.txt")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)
            logger.info("Created index file: index.txt")
        except (ValueError, OSError) as e:
            logger.error(f"Error writing index file: {e}")
            index_content = None

    logger.info(f"Created {files_created} modular output files in {output_dir}")
    return (files_created, index_content)
