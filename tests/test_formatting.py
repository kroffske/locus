from src.locus.formatting import code, helpers, tree
from src.locus.models import (
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
    main_info = FileInfo(absolute_path="", relative_path="src/main.py", filename="main.py")
    main_ann = AnnotationInfo(module_docstring="This is the main entry point.")
    main_analysis = FileAnalysis(file_info=main_info, annotations=main_ann)

    utils_info = FileInfo(absolute_path="", relative_path="src/utils.py", filename="utils.py")
    utils_analysis = FileAnalysis(file_info=utils_info, comments=["Helper functions."])

    file_details = {
        "abs/path/to/main.py": main_analysis,
        "abs/path/to/utils.py": utils_analysis,
    }

    # Test with comments disabled
    output_no_comments = tree.format_tree_markdown(file_tree, file_details, include_comments=False)
    assert "└── README.md" in output_no_comments
    assert "├── src/" in output_no_comments
    assert "#" not in output_no_comments

    # Test with comments enabled
    output_with_comments = tree.format_tree_markdown(file_tree, file_details, include_comments=True)
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
    stub_content, stub_mode = helpers.get_output_content(analysis, None, ".*")  # Regex matches anything
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
