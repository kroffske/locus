import json
import logging
import os
from typing import Dict, List, Optional, Pattern, Tuple

from ..core.config import LocusConfig, load_config
from ..core.modular_export import (
    HARD_PART_LINE_CEILING,
    TARGET_PART_LINES,
    ExportPart,
    build_export_parts,
    group_files_by_module,
)
from ..models import AnalysisResult, FileAnalysis
from ..utils import helpers as core_helpers
from . import tree as tree_formatter
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

    groups = group_files_by_module(result, config)
    logger.info(
        f"Grouped {len(result.required_files)} files into {len(groups)} modules"
    )

    def get_content(analysis: FileAnalysis) -> Tuple[str, str]:
        return get_output_content(analysis, full_code_re, annotation_re)

    target_lines = max(1, config.modular_export.max_lines_per_file)
    if target_lines > HARD_PART_LINE_CEILING:
        logger.warning(
            f"Configured max_lines_per_file={target_lines} exceeds hard ceiling "
            f"{HARD_PART_LINE_CEILING}; clamping target."
        )
        target_lines = HARD_PART_LINE_CEILING
    if target_lines == 0:
        target_lines = TARGET_PART_LINES

    parts = build_export_parts(
        groups,
        get_content_func=get_content,
        target_lines=target_lines,
        hard_max_lines=HARD_PART_LINE_CEILING,
    )

    written_parts = _write_export_parts(output_dir, parts)
    manifest = _build_manifest(result, written_parts, target_lines)
    tree_content = _build_tree_content(result)
    description_content = _build_description_content(manifest)
    index_content = _build_index_content(manifest)

    _write_text_file(os.path.join(output_dir, "manifest.json"), manifest, as_json=True)
    _write_text_file(os.path.join(output_dir, "tree.txt"), tree_content)
    _write_text_file(os.path.join(output_dir, "description.md"), description_content)
    _write_text_file(os.path.join(output_dir, "index.txt"), index_content)

    files_created = len(written_parts)
    logger.info(
        f"Created {files_created} modular part file(s) and package metadata in {output_dir}"
    )
    return (files_created, index_content)


def _write_export_parts(output_dir: str, parts: List[ExportPart]) -> List[Dict]:
    """Write part files and return serialized part metadata."""
    written_parts: List[Dict] = []
    for part in parts:
        output_path = os.path.join(output_dir, part.filename)
        content = "\n".join(segment.content for segment in part.segments).rstrip() + "\n"
        line_count = _count_lines(content.rstrip("\n"))
        if line_count > HARD_PART_LINE_CEILING:
            raise ValueError(
                f"Part '{part.filename}' exceeds hard ceiling: "
                f"{line_count} > {HARD_PART_LINE_CEILING}"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        segment_entries = [
            {
                "source_path": segment.source_path,
                "group_key": segment.group_key,
                "chunk_index": segment.chunk_index,
                "chunk_count": segment.chunk_count,
            }
            for segment in part.segments
        ]
        written_parts.append(
            {
                "filename": part.filename,
                "line_count": line_count,
                "segments": segment_entries,
            }
        )
        logger.info(
            f"Created '{part.filename}': {line_count} lines from {len(part.segments)} segment(s)"
        )
    return written_parts


def _build_manifest(
    result: AnalysisResult,
    written_parts: List[Dict],
    target_lines: int,
) -> Dict:
    """Build deterministic manifest payload for the LLM export package."""
    analysis_by_rel = {
        analysis.file_info.relative_path: analysis
        for analysis in result.required_files.values()
    }

    file_map: Dict[str, Dict] = {}
    for part in written_parts:
        for segment in part["segments"]:
            source_path = segment["source_path"]
            analysis = analysis_by_rel.get(source_path)
            file_entry = file_map.setdefault(
                source_path,
                {
                    "path": source_path,
                    "module": analysis.file_info.module_name if analysis else None,
                    "description": _extract_file_description(analysis)
                    if analysis
                    else "No description available",
                    "parts": [],
                    "chunk_count": 0,
                },
            )
            file_entry["parts"].append(part["filename"])
            file_entry["chunk_count"] += 1

    files = []
    for source_path in sorted(file_map.keys()):
        entry = file_map[source_path]
        entry["parts"] = sorted(set(entry["parts"]))
        files.append(entry)

    return {
        "format": "locus-llm-package-v1",
        "target_lines_per_part": target_lines,
        "hard_max_lines_per_part": HARD_PART_LINE_CEILING,
        "parts": written_parts,
        "files": files,
        "totals": {
            "source_files": len(files),
            "parts": len(written_parts),
        },
    }


def _build_tree_content(result: AnalysisResult) -> str:
    """Render tree.txt for exported files only."""
    file_infos = sorted(
        [analysis.file_info for analysis in result.required_files.values()],
        key=lambda info: info.relative_path.lower(),
    )
    if not file_infos:
        return "# Export Tree\n\n_(no files exported)_\n"

    file_tree = core_helpers.build_file_tree(file_infos)
    body = tree_formatter.format_tree_markdown(
        file_tree,
        result.required_files,
        include_comments=False,
        ascii_tree=True,
    )
    return "\n".join(["# Export Tree", "", body, ""])


def _build_description_content(manifest: Dict) -> str:
    """Create human-readable package description surface."""
    totals = manifest.get("totals", {})
    return "\n".join(
        [
            "# Locus LLM Export Package",
            "",
            "This directory contains a deterministic code export package for LLM/tool usage.",
            "",
            f"- Source files: {totals.get('source_files', 0)}",
            f"- Parts: {totals.get('parts', 0)}",
            f"- Target lines per part: {manifest.get('target_lines_per_part')}",
            f"- Hard max lines per part: {manifest.get('hard_max_lines_per_part')}",
            "",
            "Package surfaces:",
            "- `manifest.json` - machine-readable package and chunk mapping",
            "- `tree.txt` - exported source tree",
            "- `description.md` - package summary",
            "- `part-*.txt` - chunked source payloads",
            "- `index.txt` - quick grep-friendly lookup table",
            "",
        ]
    )


def _build_index_content(manifest: Dict) -> str:
    """Create compatibility index lookup from manifest data."""
    lines = [
        "# Locus Export Index",
        "# ===================",
        "#",
        "# Quick Search Tips:",
        '#   Find file:      grep "^## " index.txt | grep "filename"',
        '#   Find part:      grep "Part:" index.txt | grep "part-0001"',
        '#   List all files: grep "^## " index.txt',
        "",
    ]

    for file_entry in manifest.get("files", []):
        part_list = ", ".join(file_entry.get("parts", [])) or "N/A"
        lines.extend(
            [
                f"## {file_entry.get('path', 'N/A')}",
                f"   Module: {file_entry.get('module') or 'N/A'}",
                f"   Description: {file_entry.get('description') or 'N/A'}",
                f"   Part: {part_list}",
                "",
            ]
        )
    return "\n".join(lines)


def _write_text_file(path: str, payload, as_json: bool = False) -> None:
    """Write text/json payload with UTF-8 encoding."""
    with open(path, "w", encoding="utf-8") as f:
        if as_json:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        else:
            f.write(payload)
