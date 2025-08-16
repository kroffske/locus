import os
import sys
import logging

from .args import parse_arguments, parse_target_specifier
from ..core.orchestrator import analyze
from ..formatting import report, code, tree
from ..utils.helpers import setup_logging, compile_regex

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the CLI."""
    args = parse_arguments()

    # --- Setup Logging ---
    log_level = 'DEBUG' if args.verbose else 'INFO'
    if args.logs:
        setup_logging(level=log_level, log_file=args.log_file)
        logger.info(f"Detailed logging enabled to: {args.log_file}")
    else:
        setup_logging(level=log_level, log_format='%(message)s')
        if args.verbose:
            logger.info("Verbose console logging enabled.")

    # --- Argument Validation and Preparation ---
    is_default_mode = args.targets == ['.'] and not args.output and not args.generate_summary
    is_action_mode = not is_default_mode

    if is_action_mode and not args.generate_summary and not args.output:
        logger.error("Error: An output file/directory (-o) is required when specifying targets or other options.")
        return 1

    try:
        full_code_re = compile_regex(args.full_code_regex)
        annotation_re = compile_regex(args.annotation_regex)
    except ValueError as e:
        logger.error(f"Invalid regex pattern: {e}")
        return 1

    target_specs = [parse_target_specifier(t) for t in args.targets]

    # Assume the first target path is the project root for now.
    # A more sophisticated approach might find a common ancestor path.
    project_path = os.path.abspath(os.path.dirname(target_specs[0].path) if os.path.isfile(target_specs[0].path) else target_specs[0].path)
    logger.info(f"Starting analysis in project root: {project_path}")

    # --- Run Analysis ---
    result = analyze(
        project_path=project_path,
        target_specs=target_specs,
        max_depth=args.depth,
        include_patterns=args.include,
        exclude_patterns=args.exclude
    )

    if result.errors:
        logger.error("Analysis completed with errors:")
        for error in result.errors:
            logger.error(f"- {error}")

    # --- Generate Output ---
    try:
        if is_default_mode:
            if result.file_tree:
                print("## Project Structure")
                tree_md = tree.format_tree_markdown(result.file_tree, result.required_files, args.comments)
                print(tree_md)
            else:
                logger.warning("No files found to display.")

        elif args.generate_summary:
            report.generate_summary_readme(result, project_path, args.generate_summary, args.comments)

        elif is_action_mode and args.output:
            output_path = args.output
            _, output_ext = os.path.splitext(output_path)

            if output_ext:  # Single file output
                logger.info(f"Generating single output file: {output_path}")
                content = report.generate_full_report(
                    result,
                    include_code=True,
                    include_tree=True,
                    include_annotations_report=args.annotations,
                    include_comments_in_tree=args.comments,
                    full_code_re=full_code_re,
                    annotation_re=annotation_re
                )
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Successfully wrote output to {output_path}")

            else:  # Directory output
                logger.info(f"Collecting files into directory: {output_path}")
                code.collect_files_to_directory(
                    result,
                    output_path,
                    full_code_re=full_code_re,
                    annotation_re=annotation_re
                )
                if args.annotations:
                    report.generate_annotations_report_file(result, output_path, "OUT.md", args.comments)

    except (IOError, OSError) as e:
        logger.error(f"Fatal error during output generation: {e}", exc_info=True)
        return 1

    logger.info("Processing complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
