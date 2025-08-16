import argparse
import logging
from typing import List, Tuple

from ..models import TargetSpecifier

logger = logging.getLogger(__name__)


def parse_target_specifier(spec: str) -> TargetSpecifier:
    """Parses a target string (e.g., "path/to/file.py:10-25,40") into a TargetSpecifier."""
    path = spec
    line_ranges: List[Tuple[int, int]] = []

    if ":" in spec:
        parts = spec.split(":", 1)
        path, line_part = parts[0], parts[1]
        try:
            for range_str in line_part.split(","):
                if "-" in range_str:
                    start_str, end_str = range_str.split("-", 1)
                    line_ranges.append((int(start_str), int(end_str)))
                else:
                    line_num = int(range_str)
                    line_ranges.append((line_num, line_num))
        except ValueError:
            logger.warning(f"Invalid line range format in '{spec}'. Treating as a simple path.")
            return TargetSpecifier(path=spec)

    return TargetSpecifier(path=path, line_ranges=line_ranges)


def parse_arguments() -> argparse.Namespace:
    """Defines and configures the argument parser with sub-commands."""
    parser = argparse.ArgumentParser(
        description="A tool for analyzing and updating project files.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- ANALYZE Sub-command ---
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze project files and generate reports.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    analyze_parser.add_argument(
        "targets",
        nargs="*",
        default=["."],
        help='One or more targets to analyze. Can be:\n- A directory path (e.g., src/)\n- A file path (e.g., src/main.py)\n- A file with line ranges (e.g., "src/main.py:10-50")',
    )
    analyze_parser.add_argument(
        "-o",
        "--output",
        help="Output destination. A path to a file (.md) or a directory.",
    )
    # File Selection Group for Analyze
    file_selection = analyze_parser.add_argument_group("File Selection")
    file_selection.add_argument("--include", nargs="+", metavar="PATTERN", help="Glob patterns to forcefully include.")
    file_selection.add_argument("--exclude", nargs="+", metavar="PATTERN", help="Glob patterns to explicitly exclude.")
    file_selection.add_argument("-d", "--depth", type=int, default=-1, help="Max depth for dependency resolution.")
    # Output Formatting Group for Analyze
    output_formatting = analyze_parser.add_argument_group("Output Formatting")
    output_formatting.add_argument("-c", "--comments", action="store_true", help="Include summary comments in the file tree.")
    output_formatting.add_argument("-a", "--annotations", action="store_true", help="Add a detailed OUT.md annotations report.")
    output_formatting.add_argument("--full-code-regex", metavar="REGEX", help="Regex for files to include full code.")
    output_formatting.add_argument("--annotation-regex", metavar="REGEX", help="Regex for files to show as stubs.")

    # Content Style Group for Analyze
    content_style = analyze_parser.add_argument_group("Content Style")
    content_style.add_argument(
        "--style",
        choices=["full", "annotations", "minimal"],
        default="full",
        help="Output style for report mode: full (default, includes code), annotations (stubs only), or minimal (tree only)",
    )
    content_style.add_argument("--skip-readme", action="store_true", help="Exclude README from output")
    content_style.add_argument("--with-readme", action="store_true", help="Force include README (useful when piping)")
    content_style.add_argument("--add-annotations", action="store_true", help="Add OUT.md annotations file to directory output")

    # Deprecated option (kept for backward compatibility)
    content_style.add_argument(
        "--generate-summary", metavar="FILENAME", nargs="?", const="claude.md", default=None, help="(DEPRECATED: Use -o file.md --style minimal) Generate summary file"
    )
    # Logging Group (shared)
    for p in [analyze_parser]:
        logging_group = p.add_argument_group("Logging")
        logging_group.add_argument("-v", "--verbose", action="store_true", help="Enable verbose console logging.")
        logging_group.add_argument("--logs", action="store_true", help="Enable writing logs to a file.")
        logging_group.add_argument("--log-file", default="pr-analyze_log.txt", help="Specify the log file path.")

    # --- UPDATE Sub-command ---
    update_parser = subparsers.add_parser(
        "update",
        help="Update local files from a Markdown document via stdin.",
        description="Updates local files by reading a specially formatted Markdown document from standard input (stdin).",
        epilog="Example:\n  cat your_changes.md | pr-analyze update",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    update_parser.add_argument("--backup", action="store_true", help="Create a .bak backup of each file before modifying it.")
    update_parser.add_argument("--dry-run", action="store_true", help="Show what would be modified without writing any changes.")

    return parser.parse_args()
