import os
import logging
import re
from typing import Optional, Pattern

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
    
    sorted_files = sorted(result.required_files.values(), key=lambda fa: fa.file_info.relative_path)

    for analysis in sorted_files:
        rel_path = analysis.file_info.relative_path
        content, _ = get_output_content(analysis, full_code_re, annotation_re)
        
        output_parts.append(f"### File: `{rel_path}`")
        # Determine language for syntax highlighting
        lang = 'python' if rel_path.endswith('.py') else ''
        output_parts.append(f"```{lang}")
        output_parts.append(content.strip())
        output_parts.append("```\n")

    return "\n".join(output_parts)

def collect_files_to_directory(
    result: AnalysisResult,
    output_dir: str,
    full_code_re: Optional[Pattern] = None,
    annotation_re: Optional[Pattern] = None
) -> int:
    """Collects analyzed files into an output directory, creating individual files."""
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        return 0

    collected_count = 0
    sorted_files = sorted(result.required_files.values(), key=lambda fa: fa.file_info.relative_path)
    
    for analysis in sorted_files:
        content, mode = get_output_content(analysis, full_code_re, annotation_re)
        
        # Don't create files for empty or errored content
        if not content or content.startswith('# ERROR'):
            logger.debug(f"Skipping empty or errored file: {analysis.file_info.relative_path}")
            continue

        target_path = os.path.join(output_dir, analysis.file_info.relative_path)
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            collected_count += 1
            logger.debug(f"Collected '{analysis.file_info.relative_path}' ({mode} mode) to '{target_path}'")
        except (IOError, OSError) as e:
            logger.error(f"Error writing collected file {target_path}: {e}")

    logger.info(f"Successfully collected {collected_count} files into {output_dir}")
    return collected_count
