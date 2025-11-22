from locus.formatting import code, helpers, tree
from locus.models import (
    AnalysisResult,
    AnnotationInfo,
    FileAnalysis,
    FileInfo,
)


def test_format_tree():
    """Test the Markdown tree formatting."""
    file_tree = {
        "src": {
            "main.py": None,
            "utils.py": None,
        },
        "README.md": None,
    }

    # Setup mock analysis results
    main_info = FileInfo(
        absolute_path="", relative_path="src/main.py", filename="main.py"
    )
    main_ann = AnnotationInfo(module_docstring="This is the main entry point.")
    main_analysis = FileAnalysis(file_info=main_info, annotations=main_ann)

    utils_info = FileInfo(
        absolute_path="", relative_path="src/utils.py", filename="utils.py"
    )
    utils_analysis = FileAnalysis(file_info=utils_info, comments=["Helper functions."])

    file_details = {
        "abs/path/to/main.py": main_analysis,
        "abs/path/to/utils.py": utils_analysis,
    }

    # Test with comments disabled
    output_no_comments = tree.format_tree_markdown(
        file_tree, file_details, include_comments=False
    )
    assert "├── README.md" in output_no_comments
    assert "└── src/" in output_no_comments
    assert "#" not in output_no_comments

    # Test with comments enabled
    output_with_comments = tree.format_tree_markdown(
        file_tree, file_details, include_comments=True
    )
    assert "main.py  # This is the main entry point" in output_with_comments
    assert "utils.py  # Helper functions" in output_with_comments


def test_get_output_content():
    """Test the logic for selecting file content (full, stub, etc.)."""
    info = FileInfo(absolute_path="", relative_path="src/logic.py", filename="logic.py")
    ann = AnnotationInfo(elements={"my_func": {"type": "function"}})
    analysis = FileAnalysis(
        file_info=info,
        content="def my_func():\n    pass",
        annotations=ann,
    )

    # Test default mode (should return full content)
    content, mode = helpers.get_output_content(analysis, None, None)
    assert mode == "default"
    assert "def my_func()" in content

    # Test annotation stub mode
    stub_content, stub_mode = helpers.get_output_content(
        analysis, None, ".*"
    )  # Regex matches anything
    assert stub_mode == "annotation_stub"
    assert "def my_func(...): ..." in stub_content


def test_format_code_collection():
    """Test the aggregation of files into a single string."""
    info1 = FileInfo(absolute_path="", relative_path="a.py", filename="a.py")
    analysis1 = FileAnalysis(file_info=info1, content="print('a')")

    info2 = FileInfo(absolute_path="", relative_path="b.py", filename="b.py")
    analysis2 = FileAnalysis(file_info=info2, content="print('b')")

    result = AnalysisResult(project_path="")
    result.required_files = {"path1": analysis1, "path2": analysis2}

    output = code.format_code_collection(result)

    assert "### File: `a.py`" in output
    assert "```python\n# source: a.py\nprint('a')\n```" in output
    assert "### File: `b.py`" in output
    assert "```python\n# source: b.py\nprint('b')\n```" in output


def test_line_range_slicing():
    """Selected line ranges should slice content in output."""
    info = FileInfo(absolute_path="", relative_path="mod.py", filename="mod.py")
    content = "\n".join([f"L{i}" for i in range(1, 21)])
    analysis = FileAnalysis(
        file_info=info, content=content, line_ranges=[(3, 5), (10, 10)]
    )

    result = AnalysisResult(project_path="")
    result.required_files = {"p": analysis}

    out = code.format_code_collection(result)
    assert "# source: mod.py" in out
    # Lines 3..5 and line 10 should be present
    assert "L3" in out and "L4" in out and "L5" in out and "L10" in out
    # A line not in the ranges should be absent
    assert "L2" not in out and "L6" not in out and "L11" not in out


def test_extract_file_description():
    """Test extracting description from file's comments or docstring."""
    # Test with module docstring
    info1 = FileInfo(
        absolute_path="", relative_path="src/module.py", filename="module.py"
    )
    ann1 = AnnotationInfo(module_docstring="This is a module.\nWith multiple lines.")
    analysis1 = FileAnalysis(file_info=info1, annotations=ann1)

    description1 = code._extract_file_description(analysis1)
    assert description1 == "This is a module."

    # Test with comments
    info2 = FileInfo(
        absolute_path="", relative_path="src/utils.py", filename="utils.py"
    )
    analysis2 = FileAnalysis(
        file_info=info2, comments=["", "Helper functions", "More text"]
    )

    description2 = code._extract_file_description(analysis2)
    assert description2 == "Helper functions"

    # Test with no description
    info3 = FileInfo(
        absolute_path="", relative_path="src/empty.py", filename="empty.py"
    )
    analysis3 = FileAnalysis(file_info=info3)

    description3 = code._extract_file_description(analysis3)
    assert description3 == "No description available"


def test_generate_index_content():
    """Test generating index content for modular export."""
    # Create mock file analysis objects
    info1 = FileInfo(
        absolute_path="",
        relative_path="src/main.py",
        filename="main.py",
        module_name="src.main",
    )
    ann1 = AnnotationInfo(module_docstring="Main entry point")
    analysis1 = FileAnalysis(
        file_info=info1, annotations=ann1, content="def main():\n    pass"
    )

    info2 = FileInfo(
        absolute_path="",
        relative_path="src/utils.py",
        filename="utils.py",
        module_name="src.utils",
    )
    analysis2 = FileAnalysis(
        file_info=info2,
        comments=["Utility functions"],
        content="def helper():\n    pass",
    )

    # Create groups (simulating modular export grouping)
    groups = {"src": [analysis1, analysis2]}

    # Mock get_content function
    def mock_get_content(analysis):
        return (
            f"# source: {analysis.file_info.relative_path}\n{analysis.content}",
            "default",
        )

    # Generate index content
    index_content = code.generate_index_content(groups, mock_get_content)

    # Verify index header
    assert "# Locus Export Index" in index_content
    assert "# Quick Search Tips:" in index_content
    assert 'grep "^## " index.txt' in index_content

    # Verify file entries
    assert "## src/main.py" in index_content
    assert "Module: src.main" in index_content
    assert "Description: Main entry point" in index_content
    assert "Export: src.txt" in index_content
    assert "Lines:" in index_content

    assert "## src/utils.py" in index_content
    assert "Module: src.utils" in index_content
    assert "Description: Utility functions" in index_content

    # Verify line numbers are calculated correctly
    # First file should start at line 4 (after header lines)
    assert "Lines: 4-" in index_content
