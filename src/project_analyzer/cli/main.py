import logging
import os
import sys

from ..core.orchestrator import analyze
from ..formatting import code, report, tree
from ..updater import parser as updater_parser
from ..updater import writer as updater_writer
from ..utils.helpers import compile_regex, setup_logging
from .args import parse_arguments, parse_target_specifier

logger = logging.getLogger(__name__)


def handle_analyze_command(args):
    """Orchestrates the 'analyze' command workflow."""
    # Handle deprecated --generate-summary
    if args.generate_summary:
        logger.warning("--generate-summary is deprecated. Use: -o file.md --style minimal")
        if not args.output:
            args.output = args.generate_summary
            args.style = "minimal"

    # Determine mode based on output
    if not args.output:
        mode = "interactive"
    elif os.path.splitext(args.output)[1]:  # Has extension
        mode = "report"
    else:
        mode = "collection"

    logger.debug(f"Operating in {mode} mode")

    try:
        full_code_re = compile_regex(args.full_code_regex)
        annotation_re = compile_regex(args.annotation_regex)
    except ValueError as e:
        logger.error(f"Invalid regex pattern: {e}")
        return 1

    target_specs = [parse_target_specifier(t) for t in args.targets]
    project_path = os.path.abspath(os.path.commonpath([spec.path for spec in target_specs]))
    if not os.path.isdir(project_path):
        project_path = os.path.dirname(project_path)
    logger.info(f"Starting analysis in project root: {project_path}")

    result = analyze(
        project_path=project_path,
        target_specs=target_specs,
        max_depth=args.depth,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
    )

    if result.errors:
        logger.error("Analysis completed with errors:")
        for error in result.errors:
            logger.error(f"- {error}")

    # Determine README inclusion
    include_readme = True
    if mode == "interactive" and not sys.stdout.isatty() and not args.with_readme:
        include_readme = False
    if args.skip_readme:
        include_readme = False

    # Validate option combinations
    if mode == "collection" and args.style == "annotations":
        logger.error("For directory output, use --add-annotations instead of --style annotations")
        return 1

    try:
        if mode == "interactive":
            # Interactive mode: print to stdout
            if include_readme and result.project_readme_content:
                print("## Project README\n")
                print(result.project_readme_content)
                print("\n---\n")
            if result.file_tree:
                print("## Project Structure")
                tree_md = tree.format_tree_markdown(result.file_tree, result.required_files, args.comments)
                print(tree_md)

        elif mode == "report":
            # Report mode: write to file
            output_path = args.output

            # Determine what to include based on style
            include_code = args.style == "full"
            include_annotations = args.style == "annotations" or args.annotations

            content = report.generate_full_report(
                result,
                include_tree=True,
                include_code=include_code,
                include_annotations_report=include_annotations,
                include_readme=include_readme,
                include_comments_in_tree=args.comments,
                full_code_re=full_code_re,
                annotation_re=annotation_re,
            )

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Successfully wrote output to {output_path}")

        elif mode == "collection":
            # Collection mode: write to directory
            output_path = args.output
            code.collect_files_to_directory(result, output_path, full_code_re, annotation_re)

            # Add annotations report if requested
            if args.add_annotations or args.annotations:
                report.generate_annotations_report_file(result, output_path, "OUT.md", args.comments)

            # Copy README if present and not skipped
            if include_readme and result.project_readme_content:
                readme_path = os.path.join(output_path, "README.md")
                os.makedirs(output_path, exist_ok=True)
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(result.project_readme_content)
                logger.info(f"Copied README to {readme_path}")

    except OSError as e:
        logger.error(f"Fatal error during output generation: {e}", exc_info=True)
        return 1
    return 0


def handle_update_command(args):
    """Orchestrates the 'update' command workflow."""
    logger.info("Reading from standard input to update files...")
    if sys.stdin.isatty():
        logger.error("Error: No input provided. Pipe a Markdown file to this command.")
        print("Example: cat your_changes.md | pr-analyze update")
        return 1

    markdown_content = sys.stdin.read()
    if not markdown_content:
        logger.error("Error: Standard input was empty.")
        return 1

    try:
        update_operations = updater_parser.parse_markdown_to_updates(markdown_content)
        if not update_operations:
            logger.warning("No valid file update blocks found in the input.")
            return 0

        updater_writer.apply_updates(
            operations=update_operations,
            backup=args.backup,
            dry_run=args.dry_run,
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during the update process: {e}", exc_info=True)
        return 1
    return 0


def main():
    """Main entry point for the CLI."""
    args = parse_arguments()

    # Setup logging based on shared args if they exist
    verbose = getattr(args, "verbose", False)
    enable_logs = getattr(args, "logs", False)
    log_file = getattr(args, "log_file", "pr-analyze_log.txt")

    log_level = "DEBUG" if verbose else "INFO"
    if enable_logs:
        setup_logging(level=log_level, log_file=log_file)
    else:
        setup_logging(level=log_level, log_format="%(message)s")

    if args.command == "analyze":
        return handle_analyze_command(args)
    if args.command == "update":
        return handle_update_command(args)
    logger.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
