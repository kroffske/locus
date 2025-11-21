import logging
import os
import sys

from ..core.orchestrator import analyze
from ..formatting import code, report, tree
from ..formatting.colors import (
    console,
    print_divider,
    print_header,
    print_info,
    setup_rich_logging,
)
from ..init import init_project
from ..similarity import run as run_similarity
from ..similarity.formatting import print_similarity_summary, serialize_similarity
from ..similarity.search import SimilarityConfig
from ..updater import parser as updater_parser
from ..updater import writer as updater_writer
from ..utils.helpers import compile_regex
from .args import parse_arguments, parse_target_specifier

logger = logging.getLogger(__name__)


def handle_analyze_command(args):
    """Orchestrates the 'analyze' command workflow."""
    # Handle deprecated --generate-summary
    if args.generate_summary:
        logger.warning(
            "--generate-summary is deprecated. Use: -o file.md --style minimal"
        )
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
    project_path = os.path.abspath(
        os.path.commonpath([spec.path for spec in target_specs])
    )
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

    # Optional similarity pass
    if getattr(args, "similarity", False):
        cfg = SimilarityConfig(
            strategy=getattr(args, "sim_strategy", "exact"),
            threshold=getattr(args, "sim_threshold", 1.0),
            max_candidates=getattr(args, "sim_max_candidates", 0),
        )
        try:
            sim_result = run_similarity(result, cfg)
            result.similarity = sim_result
        except Exception as e:
            logger.error(f"Similarity analysis failed: {e}")

    if result.errors:
        logger.error("Analysis completed with errors:")
        for error in result.errors:
            logger.error(f"- {error}")

    # Determine README/docs inclusion (default: off unless requested)
    include_readme = False
    include_root_docs = False
    if getattr(args, "readme", False) or getattr(args, "with_readme", False):
        include_readme = True
    if getattr(args, "root_docs", False):
        include_root_docs = True
    if args.skip_readme:
        include_readme = False

    # Validate option combinations
    if mode == "collection" and args.style == "annotations":
        logger.error(
            "For directory output, use --add-annotations instead of --style annotations"
        )
        return 1

    try:
        if mode == "interactive":
            # Interactive mode: print to stdout with colors
            if include_readme and result.project_readme_content:
                print_header("Project README")
                console.print(result.project_readme_content)
                print_divider()
            if result.file_tree:
                include_tree_comments = args.comments or getattr(args, "headers", False)
                ascii_flag = getattr(args, "ascii_tree", False)

                # Tree output (default)
                if not getattr(args, "flat", False) or getattr(args, "tree", False):
                    print_header("Project Structure")
                    tree_md = tree.format_tree_markdown(
                        result.file_tree,
                        result.required_files,
                        include_tree_comments,
                        ascii_tree=ascii_flag,
                    )
                    try:
                        console.print(tree_md, style="tree")
                    except UnicodeEncodeError:
                        # Re-render using ASCII connectors
                        tree_md_ascii = tree.format_tree_markdown(
                            result.file_tree,
                            result.required_files,
                            include_tree_comments,
                            ascii_tree=True,
                        )
                        print(tree_md_ascii)

                # Flat output when requested
                if getattr(args, "flat", False):
                    print_divider()
                    print_header("Flat Summary")
                    flat_md = tree.format_flat_list(
                        result.required_files, include_tree_comments
                    )
                    print(flat_md)

            # Optional annotations summary hint in interactive mode
            if getattr(args, "annotations", False):
                annotated = [
                    fa
                    for fa in result.required_files.values()
                    if fa.annotations
                    and (fa.annotations.module_docstring or fa.annotations.elements)
                ]
                print_info(
                    f"Annotations extracted for {len(annotated)} files. Use -o to write a report."
                )

            # Similarity output when requested
            if getattr(args, "similarity", False):
                sim = getattr(result, "similarity", None)
                strat = (
                    getattr(sim, "meta", {}).get(
                        "strategy", getattr(args, "sim_strategy", "exact")
                    )
                    if sim
                    else getattr(args, "sim_strategy", "exact")
                )
                print_divider()
                print_similarity_summary(
                    sim, strat, show_members=True, member_bullet="·"
                )

        elif mode == "report":
            # Report mode: write to file
            output_path = args.output

            # Determine what to include based on style
            include_code = args.style == "full"
            include_annotations = args.style == "annotations" or args.annotations
            include_headers = (args.style == "headers") or getattr(
                args, "headers", False
            )

            # Determine tree inclusion
            include_tree = True
            if getattr(args, "no_tree", False):
                include_tree = False
            elif getattr(args, "tree", False):
                include_tree = True

            include_flat = getattr(args, "flat", False)

            # Code inclusion overrides and defaults:
            if getattr(args, "no_code", False):
                include_code = False
            elif getattr(args, "code", False):
                include_code = True
            elif (
                getattr(args, "headers", False) or getattr(args, "annotations", False)
            ) and args.style == "full":
                # Default to no code when composing headers/annotations without explicit --code
                include_code = False

            # If headers requested, also enable tree comments to surface summaries
            if getattr(args, "headers", False):
                args.comments = True

            ascii_flag = getattr(args, "ascii_tree", False)
            content = report.generate_full_report(
                result,
                include_tree=include_tree,
                include_flat=include_flat,
                include_code=include_code,
                include_annotations_report=include_annotations,
                include_readme=include_readme,
                include_root_docs=include_root_docs,
                include_comments_in_tree=args.comments,
                include_headers=include_headers,
                ascii_tree=ascii_flag,
                full_code_re=full_code_re,
                annotation_re=annotation_re,
            )

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Successfully wrote output to {output_path}")

        elif mode == "collection":
            # Collection mode: write to directory (with modular grouping)
            output_path = args.output
            code.collect_files_modular(result, output_path, full_code_re, annotation_re)

            # Add annotations report if requested
            if args.add_annotations or args.annotations:
                report.generate_annotations_report_file(
                    result, output_path, "OUT.md", args.comments
                )

            # Copy README if present and not skipped
            if include_readme and result.project_readme_content:
                readme_path = os.path.join(output_path, "README.md")
                os.makedirs(output_path, exist_ok=True)
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(result.project_readme_content)
                logger.info(f"Copied README to {readme_path}")

        # Raw similarity JSON output (any mode)
        if getattr(args, "similarity", False) and getattr(args, "sim_output", None):
            import json

            path = args.sim_output
            try:
                payload = serialize_similarity(result)
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                logger.info(f"Wrote similarity JSON to {path}")
            except Exception as e:
                logger.error(f"Failed writing similarity JSON: {e}")

    except OSError as e:
        logger.error(f"Fatal error during output generation: {e}", exc_info=True)
        return 1
    return 0


def handle_sim_command(args):
    """Similarity-only subcommand: analyze targets and print similarity summary."""
    # Resolve project root from targets
    target_specs = [parse_target_specifier(t) for t in args.targets]
    project_path = os.path.abspath(
        os.path.commonpath([spec.path for spec in target_specs])
    )
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

    # Run similarity
    cfg = SimilarityConfig(
        strategy=getattr(args, "strategy", "ast"),
        threshold=getattr(args, "threshold", 1.0),
        include_init=getattr(args, "include_init", False),
    )
    try:
        sim_result = run_similarity(result, cfg)
        result.similarity = sim_result
    except Exception as e:
        logger.error(f"Similarity analysis failed: {e}")
        return 1

    # Print concise similarity summary using shared helper
    print_similarity_summary(
        result.similarity,
        cfg.strategy,
        show_members=getattr(args, "print_members", True),
        member_bullet="·",
    )

    # Optional JSON output
    out = getattr(args, "json_out", None)
    if out:
        import json

        try:
            payload = serialize_similarity(result)
            os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Wrote similarity JSON to {out}")
        except Exception as e:
            logger.error(f"Failed writing similarity JSON: {e}")
            return 1

    return 0


def handle_update_command(args):
    """Orchestrates the 'update' command workflow."""
    if sys.stdin.isatty():
        print_info(
            "Paste your Markdown content below. Press Ctrl+D (Unix) or Ctrl+Z (Windows) when done:"
        )
        print_divider()
    else:
        logger.info("Reading from standard input to update files...")

    markdown_content = sys.stdin.read()
    if not markdown_content:
        logger.error("Error: No input provided.")
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
        logger.error(
            f"An unexpected error occurred during the update process: {e}",
            exc_info=True,
        )
        return 1
    return 0


def handle_init_command(args):
    """Orchestrates the 'init' command workflow."""
    from pathlib import Path

    from ..core.config import save_default_config
    from ..init.creator import FileConflictError, InitError

    try:
        target_dir = Path.cwd()
        force = getattr(args, "force", False)
        interactive = not getattr(args, "non_interactive", False)
        project_name = getattr(args, "project_name", None)
        init_config = getattr(args, "config", False)

        created_files = init_project(
            target_dir=target_dir,
            force=force,
            interactive=interactive,
            project_name=project_name,
        )

        if created_files:
            print_info(f"Successfully created {len(created_files)} template files:")
            for filename in sorted(created_files):
                print_info(f"  ✓ {filename}")
        else:
            print_info("No files were created.")

        # Optionally create .locus/settings.json
        if init_config:
            config_path = save_default_config(target_dir)
            print_info(
                f"Created default configuration: {config_path.relative_to(target_dir)}"
            )

    except FileConflictError:
        logger.info("Initialization cancelled due to file conflicts.")
        return 1
    except InitError as e:
        logger.error(f"Initialization failed: {e}")
        return 1
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during initialization: {e}", exc_info=True
        )
        return 1

    return 0


def main():
    """Main entry point for the CLI."""
    args = parse_arguments()

    # Handle no-color flag (must be done before importing color utilities)
    no_color = getattr(args, "no_color", False)
    if no_color:
        import os

        os.environ["NO_COLOR"] = "1"
        # Reload the colors module to pick up the environment variable
        from importlib import reload

        from ..formatting import colors

        reload(colors)

    # Setup logging based on shared args if they exist
    verbose = getattr(args, "verbose", False)
    enable_logs = getattr(args, "logs", False)
    log_file = getattr(args, "log_file", "pr-analyze_log.txt")

    log_level = "DEBUG" if verbose else "INFO"
    if enable_logs:
        setup_rich_logging(level=log_level, log_file=log_file)
    else:
        setup_rich_logging(level=log_level)

    if args.command == "analyze":
        return handle_analyze_command(args)
    if args.command == "sim":
        return handle_sim_command(args)
    if args.command == "update":
        return handle_update_command(args)
    if args.command == "init":
        return handle_init_command(args)
    logger.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
