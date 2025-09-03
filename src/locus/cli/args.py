"""CLI argument definitions for Locus Analyzer.

This module configures the `analyze` and `update` subcommands and flags
such as `-p/--headers` (preamble), `-t/--tree`, `-a/--annotations`, and
code/README toggles for report output composition.
"""

# Locus Analyzer CLI: short preamble comments are allowed here.
# The module docstring above is used for header summaries.

import argparse
import logging
import sys
from typing import List, Tuple
from importlib.metadata import PackageNotFoundError, version as pkg_version
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
                if not range_str:
                    continue
                if "-" in range_str:
                    start_str, end_str = range_str.split("-", 1)
                    start_i, end_i = int(start_str), int(end_str)
                    if end_i < start_i:
                        raise ValueError("invalid range: start > end")
                    line_ranges.append((start_i, end_i))
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
        description="Analyze project structure and optionally update files from Markdown.",
        formatter_class=argparse.HelpFormatter,
    )
    try:
        _ver = pkg_version("locus-analyzer")
    except PackageNotFoundError:
        _ver = "unknown"
    parser.add_argument("--version", action="version", version=f"locus-analyzer {_ver}")
    subparsers = parser.add_subparsers(dest="command", required=False, help="Available commands")

    # --- ANALYZE Sub-command ---
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze code and generate a report or interactive view.",
        formatter_class=argparse.HelpFormatter,
        add_help=False,
    )
    # Custom help flags (we render a concise, colorful help screen)
    analyze_parser.add_argument("-h", "--help", action="store_true", help="Show help for analyze")
    analyze_parser.add_argument("--help-advanced", action="store_true", help="Show advanced flags for analyze")
    analyze_parser.add_argument(
        "targets",
        nargs="*",
        default=["."],
        help="Targets: dir, file, or file:lines (e.g., src/ or a.py:10-50)",
    )
    analyze_parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output destination (optional). Write to a file (.md) or directory; "
            "if omitted, the report is printed to stdout (console)."
        ),
    )
    # File Selection Group for Analyze
    file_selection = analyze_parser.add_argument_group("File Selection")
    file_selection.add_argument(
        "--include",
        nargs="+",
        metavar="PATTERN",
        help="Glob patterns to include (e.g., 'src/**/*.py' '*.md')",
    )
    file_selection.add_argument(
        "--exclude",
        nargs="+",
        metavar="PATTERN",
        help="Glob patterns to exclude (e.g., 'tests/**' '**/migrations/**' '*.log')",
    )
    file_selection.add_argument(
        "-d",
        "--depth",
        type=int,
        default=-1,
        help="Import depth: 0=off, 1=direct, 2=nested, -1=unlimited",
    )
    # Output Formatting Group for Analyze
    output_formatting = analyze_parser.add_argument_group("Output Formatting")
    output_formatting.add_argument("-c", "--comments", action="store_true", help="Add one-line summaries to tree")
    output_formatting.add_argument(
        "-a",
        "--annotations",
        action="store_true",
        help=("Include Python annotations (docstrings, imports, function/class signatures). " "In report mode adds an 'Annotations' section; in directory mode writes OUT.md."),
    )
    output_formatting.add_argument("-t", "--tree", action="store_true", help="Show tree in report")
    output_formatting.add_argument("-f", "--flat", action="store_true", help="Show flat list: path  # summary")
    output_formatting.add_argument("--no-tree", action="store_true", help="Hide tree in report")
    output_formatting.add_argument("-p", "--headers", action="store_true", help="Include preamble/docstrings; adds tree summaries")
    output_formatting.add_argument("--ascii-tree", action="store_true", help="ASCII tree connectors")
    output_formatting.add_argument("--code", action="store_true", help="Include full file contents")
    output_formatting.add_argument("--no-code", action="store_true", help="Exclude full file contents")
    output_formatting.add_argument("--full-code-regex", metavar="REGEX", help=argparse.SUPPRESS)
    output_formatting.add_argument("--annotation-regex", metavar="REGEX", help=argparse.SUPPRESS)

    # Content Style Group for Analyze
    content_style = analyze_parser.add_argument_group("Content Style (advanced)")
    content_style.add_argument(
        "--style",
        choices=["full", "annotations", "minimal", "headers"],
        default="full",
        help=argparse.SUPPRESS,
    )
    content_style.add_argument("-r", "--readme", action="store_true", help=argparse.SUPPRESS)
    content_style.add_argument("--root-docs", action="store_true", help=argparse.SUPPRESS)
    content_style.add_argument("--skip-readme", action="store_true", help=argparse.SUPPRESS)
    content_style.add_argument("--with-readme", action="store_true", help=argparse.SUPPRESS)
    content_style.add_argument("--add-annotations", action="store_true", help="Add OUT.md annotations file to directory output")

    # Deprecated option (kept for backward compatibility)
    content_style.add_argument("--generate-summary", metavar="FILENAME", nargs="?", const="claude.md", default=None, help=argparse.SUPPRESS)
    # Logging Group (shared)
    for p in [analyze_parser]:
        logging_group = p.add_argument_group("Logging")
        logging_group.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
        logging_group.add_argument("--logs", action="store_true", help="Write logs to file")
        logging_group.add_argument("--log-file", default="pr-analyze_log.txt", help=argparse.SUPPRESS)
        logging_group.add_argument("--no-color", action="store_true", help="Disable color")

    # --- UPDATE Sub-command ---
    update_parser = subparsers.add_parser(
        "update",
        help="Update local files from Markdown via stdin.",
        description="Read Markdown from stdin and update files.",
        formatter_class=argparse.HelpFormatter,
    )
    update_parser.add_argument("--backup", action="store_true", help="Create .bak backups")
    update_parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    update_parser.add_argument("--no-color", action="store_true", help="Disable color")

    # Capture original argv to differentiate top-level help vs subcommand help
    original_argv = sys.argv[1:]

    # If user asked for top-level help (e.g., `locus -h` or `locus --help`),
    # show a concise CLI overview with both commands.
    if original_argv and original_argv[0] in {"-h", "--help"}:
        try:
            from ..formatting.colors import console
        except Exception:
            console = None

        lines_top = [
            ("header", "Locus CLI"),
            ("divider", "-" * 60),
            ("", "Usage: locus [command] [options]"),
            ("", ""),
            ("subheader", "Commands"),
            ("", "  analyze   Analyze code and generate a report (default)"),
            ("", "  update    Update local files from Markdown via stdin"),
            ("", ""),
            ("subheader", "Quick Start"),
            ("", "  locus analyze -p"),
            ("", "  locus update --dry-run < blocks.md   # preview changes"),
            ("", "  locus update --backup < blocks.md    # write files with .bak"),
            ("", ""),
            ("", "Hint: use 'locus analyze --help' or 'locus update --help' for details."),
        ]

        if console:
            for style, text in lines_top:
                if style in {"header", "subheader", "divider"}:
                    console.print(f"[{style}]{text}[/{style}]")
                else:
                    console.print(text)
        else:
            for _, text in lines_top:
                print(text)

        sys.exit(0)

    # Pre-parse to allow calling without explicit subcommand (default to 'analyze')
    argv = list(original_argv)
    if argv and argv[0] not in {"analyze", "update"}:
        argv = ["analyze"] + argv
    args = parser.parse_args(argv)

    # Render custom, concise help for analyze
    if getattr(args, "command", None) == "analyze" and (getattr(args, "help", False) or getattr(args, "help_advanced", False)):
        try:
            from ..formatting.colors import console
        except Exception:
            console = None

        advanced = getattr(args, "help_advanced", False)

        lines_basic = [
            ("header", "Locus Analyze"),
            ("divider", "-" * 60),
            ("", "Usage: locus analyze [targets ...] [options]"),
            ("", "Targets: dir, file, or file:lines (e.g., src/ or a.py:10-50)"),
            ("", ""),
            ("subheader", "Quick Start"),
            ("", "  locus analyze -p           # fast overview to console"),
            ("", "  locus analyze -o out.md -p -t -a --no-code  # write Markdown report"),
            ("", ""),
            ("subheader", "Common Options"),
            ("", "  -p, --headers     Include preamble/docstrings; adds tree summaries"),
            ("", "  -f, --flat        Flat list: path  # summary"),
            ("", "  -t, --tree        Show tree in report  (use --no-tree to hide)"),
            (
                "",
                "  -a, --annotations Include Python annotations (docstrings, imports, signatures);" " adds section in report or OUT.md in dir mode",
            ),
            ("", "  --code / --no-code  Include or exclude full file contents"),
            (
                "",
                "  -d, --depth N     Import depth: 0=off, 1=direct, 2=nested, -1=unlimited" " (e.g., main->utils is 1; utils->helpers is 2)",
            ),
            ("", "  -o, --output PATH Optional file/dir; omit to print to stdout"),
            ("", "  --include PATTERN  Glob patterns to include (e.g., 'src/**/*.py' '*.md')"),
            ("", "  --exclude PATTERN  Glob patterns to exclude (e.g., 'tests/**' '**/migrations/**')"),
            ("", "  --ascii-tree      ASCII connectors for tree"),
            ("", ""),
            ("subheader", "Examples"),
            ("", "  locus analyze -p                      # headers + tree (interactive)"),
            ("", "  locus analyze -p -f                   # flat list (grep-friendly)"),
            ("", "  locus analyze -o out.md -p -t -a --no-code  # report: headers+tree+annotations"),
            ("", "  locus analyze src/ -p                 # analyze subdir as root"),
            ("", "  locus analyze a.py -d 1               # include direct imports of a.py"),
            ("", "  locus analyze -p --include 'src/**/*.py' --exclude 'tests/**'"),
        ]

        lines_advanced = [
            ("subheader", "Advanced"),
            ("", "  --style {full,annotations,minimal,headers}  (preset; flags override)"),
            ("", "  -r, --readme      Include README in report"),
            ("", "  --root-docs       Include other root-level .md docs"),
            ("", "  --add-annotations Add OUT.md (dir mode)"),
            ("", "  --generate-summary [FILENAME]  (deprecated)"),
        ]

        def _emit(lines):
            if console:
                for style, text in lines:
                    if style in {"header", "subheader", "divider"}:
                        console.print(f"[{style}]{text}[/{style}]")
                    else:
                        console.print(text)
            else:
                for _, text in lines:
                    print(text)

        _emit(lines_basic)
        if advanced:
            print()
            _emit(lines_advanced)

        sys.exit(0)

    return args
