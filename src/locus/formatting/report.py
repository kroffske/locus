import datetime
import logging
import os
from typing import Optional, Pattern

from ..models import AnalysisResult, AnnotationInfo
from . import code, tree

logger = logging.getLogger(__name__)


def generate_full_report(
    result: AnalysisResult,
    include_tree: bool,
    include_flat: bool,
    include_code: bool,
    include_annotations_report: bool,
    include_readme: bool,
    include_root_docs: bool,
    include_comments_in_tree: bool,
    include_headers: bool = False,
    ascii_tree: bool = False,
    full_code_re: Optional[Pattern] = None,
    annotation_re: Optional[Pattern] = None,
) -> str:
    """Generates a single, comprehensive Markdown report file."""
    parts = ["# Code Analysis Report"]
    parts.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Add LLM instructions for code modifications
    parts.append("## Instructions for LLM Code Modifications\n")
    parts.append("When providing code changes or new files, use the following format for each file:")
    parts.append("```")
    parts.append("```python")
    parts.append("# source: path/to/file.py")
    parts.append("# Complete code content here - do not skip any lines")
    parts.append("```")
    parts.append("```")
    parts.append("**Important:** Include complete file contents without omissions. Do not use ellipsis (...) or skip any lines, even if previously shown.\n")

    # Add README and other root docs if requested
    if include_readme and result.project_readme_content:
        parts.extend(["## Project Documentation\n", result.project_readme_content, "\n---\n"])
    if include_readme and include_root_docs:
        root_for_docs = result.config_root_path or result.project_path
        other_docs = _load_root_markdown_docs(root_for_docs)
        for name, content in other_docs:
            parts.extend([f"## {name}", content, "\n---\n"])

    if result.errors:
        parts.extend(["## Errors Encountered", *[f"- `{e}`" for e in result.errors], "\n---\n"])

    if include_tree and result.file_tree:
        tree_md = tree.format_tree_markdown(
            result.file_tree,
            result.required_files,
            include_comments_in_tree,
            ascii_tree=ascii_tree,
        )
        parts.extend(["## Project Structure", f"```\n{tree_md}\n```\n", "\n---\n"])

    if include_flat:
        flat_md = tree.format_flat_list(result.required_files, include_comments_in_tree)
        parts.extend(["## Flat Summary", f"```\n{flat_md}\n```\n", "\n---\n"])

    if include_annotations_report:
        parts.extend([generate_annotations_report_str(result), "\n---\n"])

    if include_headers:
        parts.extend(["## Top-of-file Comments", code.format_top_comments_collection(result), "\n---\n"])

    if include_code and result.required_files:
        parts.extend(["## File Contents", code.format_code_collection(result, full_code_re, annotation_re)])

    return "\n".join(parts)


def generate_headers_report(
    result: AnalysisResult,
    include_readme: bool,
    include_comments_in_tree: bool,
) -> str:
    """Generates a report with project tree and only top-of-file comments/docstrings."""
    parts = ["# Code Analysis Report (Headers)"]
    parts.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if include_readme and result.project_readme_content:
        parts.extend(["## Project Documentation\n", result.project_readme_content, "\n---\n"])

    if result.errors:
        parts.extend(["## Errors Encountered", *[f"- `{e}`" for e in result.errors], "\n---\n"])

    if result.file_tree:
        tree_md = tree.format_tree_markdown(result.file_tree, result.required_files, include_comments_in_tree)
        parts.extend(["## Project Structure", f"```\n{tree_md}\n```\n", "\n---\n"])

    parts.append("## Top-of-file Comments")
    parts.append(code.format_top_comments_collection(result))

    return "\n".join(parts)


def _load_root_markdown_docs(project_path: str):
    """Returns a list of (display_name, content) for root-level .md files excluding README.*"""
    docs = []
    try:
        for entry in sorted(os.listdir(project_path)):
            lower = entry.lower()
            if not lower.endswith(".md"):
                continue
            if lower.startswith("readme"):
                continue
            abs_path = os.path.join(project_path, entry)
            if not os.path.isfile(abs_path):
                continue
            try:
                with open(abs_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                docs.append((entry, content))
            except OSError:
                continue
    except OSError:
        pass
    return docs


def generate_summary_readme(result: AnalysisResult, output_dir: str, filename: str, include_comments: bool):
    """Generates a claude.md-style summary file."""
    readme_path = os.path.join(output_dir, filename)
    logger.info(f"Generating summary file: {readme_path}")
    try:
        os.makedirs(os.path.dirname(readme_path) or ".", exist_ok=True)
        with open(readme_path, "w", encoding="utf-8") as f:
            if result.project_readme_content:
                f.write(f"{result.project_readme_content}\n\n---\n\n")

            f.write("## Instructions for LLM Code Modifications\n\n")
            f.write("When providing code changes or new files, use the following format for each file:\n")
            f.write("```\n")
            f.write("```python\n")
            f.write("# source: path/to/file.py\n")
            f.write("# Complete code content here - do not skip any lines\n")
            f.write("```\n")
            f.write("```\n")
            f.write("**Important:** Include complete file contents without omissions. Do not use ellipsis (...) or skip any lines, even if previously shown.\n\n")

            f.write("## Project File Structure\n\n")
            if result.file_tree:
                tree_md = tree.format_tree_markdown(result.file_tree, result.required_files, include_comments)
                f.write(f"```\n{tree_md}\n```\n")
            else:
                f.write("(No file tree generated.)\n")
        logger.info(f"Successfully generated summary at {readme_path}")
    except OSError as e:
        logger.error(f"Error generating {readme_path}: {e}")
        raise


def generate_annotations_report_file(result: AnalysisResult, output_dir: str, filename: str, include_comments: bool):
    """Generates a dedicated OUT.md file with annotations."""
    report_path = os.path.join(output_dir, filename)
    logger.info(f"Generating annotations report: {report_path}")
    # Instructions are already included in generate_annotations_report_str
    content = generate_annotations_report_str(result)
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Successfully wrote annotations report to {report_path}")
    except OSError as e:
        logger.error(f"Error writing annotations report to {report_path}: {e}")
        raise


def generate_annotations_report_str(result: AnalysisResult) -> str:
    """Generates the annotations section as a string."""
    annotated = [fa for fa in result.required_files.values() if fa.annotations and (fa.annotations.module_docstring or fa.annotations.elements)]
    if not annotated:
        return "## Detailed Annotations\n\nNo detailed annotations were extracted."

    parts = ["## Detailed Annotations"]
    parts.append("\nThe following shows the structure and documentation of all analyzed Python files.")
    parts.append("Each file contains function and class signatures with their docstrings, without implementation details.\n")
    parts.append("### Instructions for LLM Code Modifications\n")
    parts.append("When providing code changes or new files based on these annotations, use the following format:")
    parts.append("```")
    parts.append("```python")
    parts.append("# source: path/to/file.py")
    parts.append("# Complete code content here - do not skip any lines")
    parts.append("```")
    parts.append("```")
    parts.append("**Important:** Include complete file contents without omissions. Do not use ellipsis (...) or skip any lines, even if previously shown.\n")
    parts.append("```python")

    for analysis in sorted(annotated, key=lambda fa: fa.file_info.relative_path):
        parts.append(f"\n# source: {analysis.file_info.relative_path}")
        parts.append(_format_single_annotation_as_stub(analysis.annotations))

    parts.append("```")
    return "\n".join(parts)


def _format_single_annotation(annotations: AnnotationInfo) -> str:
    """Formats the annotations for a single file into Markdown."""
    lines = []
    if annotations.module_docstring:
        lines.append(f"\n**Module Docstring:**\n> {annotations.module_docstring}\n")

    for name, details in sorted(annotations.elements.items()):
        lines.append(f"#### {details.get('type', 'unknown').capitalize()}: `{name}`")
        if "signature" in details:
            lines.append(f"```python\n{details['signature']}\n```")
        if details.get("docstring"):
            lines.append(f"**Docstring:**\n> {details['docstring']}\n")
    return "\n".join(lines)


def _format_single_annotation_as_stub(annotations: AnnotationInfo) -> str:
    """Formats the annotations for a single file as Python stubs."""
    lines = []

    # Add module docstring if present
    if annotations.module_docstring:
        lines.append(f'"""{annotations.module_docstring}"""')
        lines.append("")

    # Add imports
    if annotations.imports:
        for import_stmt in annotations.imports:
            lines.append(import_stmt)
        lines.append("")

    # Process each element (function or class)
    for name, details in sorted(annotations.elements.items()):
        if details.get("type") == "function":
            # Function stub
            signature = details.get("signature", f"def {name}(...)")
            lines.append(signature)
            if details.get("docstring"):
                lines.append(f'    """{details["docstring"]}"""')
            lines.append("    ...")
            lines.append("")
        elif details.get("type") == "class":
            # Add decorators
            decorators = details.get("decorators", [])
            for decorator in decorators:
                lines.append(decorator)

            # Class definition
            lines.append(f"class {name}:")
            if details.get("docstring"):
                lines.append(f'    """{details["docstring"]}"""')
                lines.append("")

            # Add class attributes
            attributes = details.get("attributes", [])
            if attributes:
                for attr in attributes:
                    lines.append(f"    {attr}")
                if attributes:
                    lines.append("")

            # Add class methods
            methods = details.get("methods", {})
            if methods:
                for method_name, method_details in sorted(methods.items()):
                    method_sig = method_details.get("signature", f"def {method_name}(...)")
                    lines.append(f"    {method_sig}")
                    if method_details.get("docstring"):
                        lines.append(f'        """{method_details["docstring"]}"""')
                    lines.append("        ...")
                    lines.append("")
            elif not attributes:
                # Only add ... if there are no attributes or methods
                lines.append("    ...")
                lines.append("")

    return "\n".join(lines)
