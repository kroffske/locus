"""Modular file export logic for grouping source files."""

import logging
import os
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models import AnalysisResult, FileAnalysis
from .config import GroupingRule, LocusConfig

logger = logging.getLogger(__name__)


def get_group_key(
    file_path: str,
    rule: Optional[GroupingRule],
    default_depth: int,
) -> str:
    """Determine the group key for a file based on grouping rules.

    Args:
        file_path: Relative path of the file
        rule: Matching grouping rule (if any)
        default_depth: Default depth to use if no rule matches

    Returns:
        Group key string (used as output filename)
    """
    if not rule:
        # Default behavior: group by directory at default_depth
        parts = Path(file_path).parts
        depth = min(default_depth, len(parts) - 1)
        group_parts = parts[:depth] if depth > 0 else [parts[0]]
        return "_".join(group_parts)

    if rule.separate:
        # Each file gets its own output file
        return file_path.replace(os.sep, "_").replace("/", "_")

    if rule.group_by == "file":
        # Group by individual file
        return file_path.replace(os.sep, "_").replace("/", "_")

    if rule.group_by == "directory":
        # Group by directory at specified depth
        parts = Path(file_path).parts
        depth = rule.depth if rule.depth else default_depth
        depth = min(depth, len(parts) - 1)
        group_parts = parts[:depth] if depth > 0 else [parts[0]]
        return "_".join(group_parts)

    if rule.group_by == "module":
        # Group by module path at specified depth
        parts = Path(file_path).parts
        depth = rule.depth if rule.depth else default_depth
        depth = min(depth, len(parts))
        group_parts = parts[:depth]
        return "_".join(group_parts)

    # Fallback to default
    parts = Path(file_path).parts
    depth = min(default_depth, len(parts) - 1)
    group_parts = parts[:depth] if depth > 0 else [parts[0]]
    return "_".join(group_parts)


def find_matching_rule(
    file_path: str,
    rules: List[GroupingRule],
) -> Optional[GroupingRule]:
    """Find the first rule that matches the given file path.

    Args:
        file_path: Relative path of the file
        rules: List of grouping rules to check

    Returns:
        First matching GroupingRule or None
    """
    for rule in rules:
        if fnmatch(file_path, rule.pattern):
            return rule
    return None


def group_files_by_module(
    result: AnalysisResult,
    config: LocusConfig,
) -> Dict[str, List[FileAnalysis]]:
    """Group files according to modular export configuration.

    Args:
        result: Analysis result containing files to group
        config: Locus configuration with grouping rules

    Returns:
        Dictionary mapping group keys to lists of FileAnalysis objects
    """
    groups: Dict[str, List[FileAnalysis]] = defaultdict(list)

    for analysis in result.required_files.values():
        rel_path = analysis.file_info.relative_path

        # Find matching rule
        rule = find_matching_rule(rel_path, config.modular_export.grouping_rules)

        # Get group key
        group_key = get_group_key(
            rel_path,
            rule,
            config.modular_export.default_depth,
        )

        groups[group_key].append(analysis)

    return groups


def check_and_split_large_groups(
    groups: Dict[str, List[FileAnalysis]],
    max_lines: int,
    get_content_func,
) -> Dict[str, List[FileAnalysis]]:
    """Split groups that exceed max_lines into smaller subgroups.

    Args:
        groups: Dictionary of grouped files
        max_lines: Maximum lines allowed per group
        get_content_func: Function to get content from FileAnalysis

    Returns:
        Updated groups dictionary with large groups split
    """
    new_groups: Dict[str, List[FileAnalysis]] = {}

    for group_key, files in groups.items():
        # Calculate total lines for this group
        total_lines = 0
        for analysis in files:
            content, _ = get_content_func(analysis)
            if content:
                total_lines += len(content.splitlines())

        # If under limit, keep as-is
        if total_lines <= max_lines:
            new_groups[group_key] = files
            logger.debug(
                f"Group '{group_key}': {total_lines} lines ({len(files)} files)"
            )
            continue

        # Split into subdirectories
        logger.info(
            f"Group '{group_key}' has {total_lines} lines, splitting by subdirectory"
        )

        subgroups: Dict[str, List[FileAnalysis]] = defaultdict(list)
        for analysis in files:
            rel_path = analysis.file_info.relative_path
            parts = Path(rel_path).parts

            # Try to split by one more level of depth
            if len(parts) > 1:
                # Get parent directory
                parent = parts[:-1]
                subgroup_key = "_".join(parent)
            else:
                subgroup_key = group_key

            subgroups[subgroup_key].append(analysis)

        # Add all subgroups
        for subgroup_key, subgroup_files in subgroups.items():
            new_groups[subgroup_key] = subgroup_files

            # Log the subgroup
            subgroup_lines = 0
            for analysis in subgroup_files:
                content, _ = get_content_func(analysis)
                if content:
                    subgroup_lines += len(content.splitlines())
            logger.debug(
                f"  Subgroup '{subgroup_key}': {subgroup_lines} lines ({len(subgroup_files)} files)"
            )

    return new_groups


def format_grouped_content(
    files: List[FileAnalysis],
    get_content_func,
) -> Tuple[str, int]:
    """Format a group of files into a single text output.

    Args:
        files: List of FileAnalysis objects to format
        get_content_func: Function to get content from FileAnalysis

    Returns:
        Tuple of (formatted content string, total line count)
    """
    output_parts = []
    total_lines = 0

    # Sort files by relative path for consistent ordering
    sorted_files = sorted(files, key=lambda fa: fa.file_info.relative_path)

    for analysis in sorted_files:
        content, _ = get_content_func(analysis)
        if not content or content.startswith("# ERROR"):
            continue

        # Add separator comment
        output_parts.append(f"# File: {analysis.file_info.relative_path}")
        output_parts.append("# " + "=" * 78)
        output_parts.append("")
        output_parts.append(content.strip())
        output_parts.append("")
        output_parts.append("")

        total_lines += len(content.splitlines()) + 5  # +5 for separators

    full_content = "\n".join(output_parts)
    return full_content, total_lines
