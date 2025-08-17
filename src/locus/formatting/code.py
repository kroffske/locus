import logging
import os
from typing import Optional, Pattern

from ..models import AnalysisResult
from .helpers import get_output_content

logger = logging.getLogger(__name__)


def format_code_collection(
    result: AnalysisResult,
    full_code_re: Optional[Pattern] = None,
    annotation_re: Optional[Pattern] = None,
) -> str:
    """Formats the collected file contents into a single string for Markdown output."""
    output_parts = []
    sorted_files = sorted(result.required_files.values(), key=lambda fa: fa.file_info.relative_path)

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
        flat_filename = analysis.file_info.relative_path.replace(os.sep, "_").replace("/", "_")
        target_path = os.path.join(output_dir, flat_filename)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            collected_count += 1
            logger.debug(f"Collected '{analysis.file_info.relative_path}' ({mode}) to '{flat_filename}'")
        except OSError as e:
            logger.error(f"Error writing file {target_path}: {e}")

    logger.info(f"Collected {collected_count} files into {output_dir}")
    return collected_count
