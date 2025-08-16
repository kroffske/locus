import argparse
import logging
import re
from typing import List, Tuple
from ..models import TargetSpecifier

logger = logging.getLogger(__name__)

def parse_target_specifier(spec: str) -> TargetSpecifier:
    """
    Parses a target string (e.g., "path/to/file.py:10-25,40") into a TargetSpecifier.
    """
    path = spec
    line_ranges: List[Tuple[int, int]] = []

    if ':' in spec:
        parts = spec.split(':', 1)
        path, line_part = parts[0], parts[1]

        try:
            for range_str in line_part.split(','):
                range_str = range_str.strip()
                if '-' in range_str:
                    start_str, end_str = range_str.split('-', 1)
                    start = int(start_str)
                    end = int(end_str)
                    if start > end:
                        raise ValueError(f"Start line cannot be greater than end line: {range_str}")
                    line_ranges.append((start, end))
                else:
                    line_num = int(range_str)
                    line_ranges.append((line_num, line_num))
        except ValueError as e:
            logger.error(f"Invalid line range format in '{spec}': {e}. Ignoring line specifier.")
            # Reset path to the full specifier if parsing fails, treating it as a plain path
            return TargetSpecifier(path=spec)

    return TargetSpecifier(path=path, line_ranges=line_ranges)

def parse_arguments() -> argparse.Namespace:
    """
    Defines and configures the argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(
        description="A highly configurable tool to analyze and collect source code and data files.",
        formatter_class=argparse.RawTextHelpFormatter  # Allows for better formatting of help text
    )

    parser.add_argument(
        'targets',
        nargs='*',
        default=['.'],
        help='One or more targets to analyze. Can be:\n'
             '- A directory path (e.g., src/)\n'
             '- A file path (e.g., src/main.py)\n'
             '- A file with line ranges (e.g., "src/main.py:10-50,75-80")'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output destination. A path to a file (.md) or a directory.\n'
             'Required if targets are specified beyond the default.'
    )

    # --- File Selection Group ---
    file_selection = parser.add_argument_group('File Selection')
    file_selection.add_argument(
        '--include',
        nargs='+',
        metavar='PATTERN',
        help='Glob patterns for files to forcefully include (e.g., "**/*.py", "docs/**/*.md").'
    )
    file_selection.add_argument(
        '--exclude',
        nargs='+',
        metavar='PATTERN',
        help='Glob patterns to explicitly exclude (e.g., "**/test_*.py", "*.tmp").'
    )
    file_selection.add_argument(
        '-d', '--depth',
        type=int,
        default=-1,
        help='Max depth for dependency resolution (-1 for unlimited, 0 to disable).'
    )

    # --- Output Formatting Group ---
    output_formatting = parser.add_argument_group('Output Formatting')
    output_formatting.add_argument(
        '-c', '--comments',
        action='store_true',
        help='Include summary comments from docstrings in the file tree view.'
    )
    output_formatting.add_argument(
        '-a', '--annotations',
        action='store_true',
        help='In directory output, add an OUT.md with a detailed annotation report.'
    )
    output_formatting.add_argument(
        '--full-code-regex',
        metavar='REGEX',
        help='Regex pattern. Files with a relative path matching this will include their full code.'
    )
    output_formatting.add_argument(
        '--annotation-regex',
        metavar='REGEX',
        help='Regex pattern. Python files matching this will be output as stubs (annotations only).'
    )

    # --- Alternate Modes Group ---
    alternate_modes = parser.add_argument_group('Alternate Modes')
    alternate_modes.add_argument(
        '--generate-summary',
        metavar='FILENAME',
        nargs='?',
        const="claude.md",
        default=None,
        help='Generate a summary file (default: claude.md) with the project README and file tree.\nOverrides other output options.'
    )

    # --- Logging Group ---
    logging_group = parser.add_argument_group('Logging')
    logging_group.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose console logging (DEBUG level).'
    )
    logging_group.add_argument(
        '--logs',
        action='store_true',
        help='Enable writing detailed logs to a file.'
    )
    logging_group.add_argument(
        '--log-file',
        default="project_analyzer_log.txt",
        help='Specify the log file path (default: project_analyzer_log.txt).'
    )

    return parser.parse_args()
