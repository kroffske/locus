import os
import logging
import datetime
from typing import Optional, Pattern

from ..models import AnalysisResult, AnnotationInfo
from . import tree, code

logger = logging.getLogger(__name__)

def generate_full_report(
    result: AnalysisResult,
    include_tree: bool,
    include_code: bool,
    include_annotations_report: bool,
    include_comments_in_tree: bool,
    full_code_re: Optional[Pattern] = None,
    annotation_re: Optional[Pattern] = None
) -> str:
    """Generates a single, comprehensive Markdown report file."""
    parts = [f"# Code Analysis Report for: {result.project_path}"]
    parts.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if result.errors:
        parts.append("## Errors Encountered")
        parts.extend([f"- `{error}`" for error in result.errors])
        parts.append("\n---\n")

    if include_tree and result.file_tree:
        parts.append("## Project Structure")
        tree_md = tree.format_tree_markdown(result.file_tree, result.required_files, include_comments_in_tree)
        parts.append(f"```\n{tree_md}\n```\n")
        parts.append("\n---\n")
    
    if include_annotations_report:
        parts.append(generate_annotations_report_str(result))
        parts.append("\n---\n")

    if include_code and result.required_files:
        parts.append("## File Contents")
        code_md = code.format_code_collection(result, full_code_re, annotation_re)
        parts.append(code_md)

    return "\n".join(parts)

def generate_summary_readme(result: AnalysisResult, output_dir: str, filename: str, include_comments: bool):
    """Generates a claude.md-style summary file."""
    readme_path = os.path.join(output_dir, filename)
    logger.info(f"Generating summary file: {readme_path}")

    try:
        os.makedirs(os.path.dirname(readme_path) or '.', exist_ok=True)
        with open(readme_path, 'w', encoding='utf-8') as f:
            if result.project_readme_content:
                f.write(result.project_readme_content)
                f.write("\n\n---\n\n")
            
            f.write("## Project File Structure\n\n")
            if result.file_tree:
                tree_md = tree.format_tree_markdown(result.file_tree, result.required_files, include_comments)
                f.write(f"```\n{tree_md}\n```\n")
            else:
                f.write("(No file tree could be generated.)\n")

        logger.info(f"Successfully generated summary file at {readme_path}")
    except (IOError, OSError) as e:
        logger.error(f"Error generating {readme_path}: {e}")
        raise

def generate_annotations_report_file(result: AnalysisResult, output_dir: str, filename: str, include_comments: bool):
    """Generates a dedicated OUT.md file with annotations."""
    report_path = os.path.join(output_dir, filename)
    logger.info(f"Generating annotations report: {report_path}")
    
    content = generate_annotations_report_str(result)
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully wrote annotations report to {report_path}")
    except (IOError, OSError) as e:
        logger.error(f"Error writing annotations report to {report_path}: {e}")
        raise

def generate_annotations_report_str(result: AnalysisResult) -> str:
    """Generates the annotations section as a string."""
    parts = ["## Detailed Annotations"]
    
    annotated_files = [
        fa for fa in result.required_files.values()
        if fa.annotations and (fa.annotations.module_docstring or fa.annotations.elements)
    ]

    if not annotated_files:
        parts.append("\nNo detailed annotations were extracted for the analyzed files.")
        return "".join(parts)

    for analysis in sorted(annotated_files, key=lambda fa: fa.file_info.relative_path):
        parts.append(f"\n### File: `{analysis.file_info.relative_path}`")
        parts.append(_format_single_annotation(analysis.annotations))

    return "\n".join(parts)

def _format_single_annotation(annotations: AnnotationInfo) -> str:
    """Formats the annotations for a single file into Markdown."""
    lines = []
    if annotations.module_docstring:
        lines.append(f"\n**Module Docstring:**\n> {annotations.module_docstring}\n")

    sorted_elements = sorted(annotations.elements.items())
    for name, details in sorted_elements:
        elem_type = details.get("type", "unknown").capitalize()
        signature = details.get("signature", "")
        docstring = details.get("docstring")

        lines.append(f"#### {elem_type}: `{name}`")
        if signature:
            lines.append(f"```python\n{signature}\n```")
        if docstring:
            lines.append(f"**Docstring:**\n> {docstring}\n")

        if elem_type == "Class":
            methods = details.get("methods", {})
            if methods:
                lines.append("**Methods:**")
                for m_name, m_details in sorted(methods.items()):
                    lines.append(f"- `{m_details.get('signature', m_name)}`")
    return "\n".join(lines)
