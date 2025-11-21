import logging
import os
from typing import Optional, Pattern

from ..core.config import LocusConfig, load_config
from ..core.modular_export import (
    check_and_split_large_groups,
    format_grouped_content,
    group_files_by_module,
)
from ..models import AnalysisResult, FileAnalysis
from .helpers import get_output_content

logger = logging.getLogger(__name__)


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


def collect_files_modular(
    result: AnalysisResult,
    output_dir: str,
    full_code_re: Optional[Pattern] = None,
    annotation_re: Optional[Pattern] = None,
    config: Optional[LocusConfig] = None,
) -> int:
    """Collects analyzed files into an output directory with modular grouping.

    Args:
        result: Analysis result containing files to collect
        output_dir: Output directory path
        full_code_re: Regex for full code extraction
        annotation_re: Regex for annotation extraction
        config: Locus configuration (loaded if not provided)

    Returns:
        Number of output files created
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load config if not provided
    if config is None:
        config = load_config(result.project_path)

    # Check if modular export is enabled
    if not config.modular_export.enabled:
        logger.info("Modular export disabled, falling back to flat collection")
        return collect_files_to_directory(
            result, output_dir, full_code_re, annotation_re
        )

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

    logger.info(f"Created {files_created} modular output files in {output_dir}")
    return files_created
