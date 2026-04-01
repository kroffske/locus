import json
from pathlib import Path

from locus.core.config import LocusConfig, ModularExportConfig
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


def test_get_summary_from_markdown_content():
    """Markdown files should expose a tree/description summary from the first heading."""
    info = FileInfo(absolute_path="", relative_path="README.md", filename="README.md")
    analysis = FileAnalysis(
        file_info=info,
        content="# Locus Title\n\nMore details below.\n",
    )

    assert helpers.get_summary_from_analysis(analysis) == "Locus Title"


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
    assert description1 == "This is a module"

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


def test_generate_index_content_validation():
    """Test input validation for generate_index_content."""
    import pytest

    # Test with empty groups
    with pytest.raises(ValueError, match="Groups dictionary cannot be empty"):
        code.generate_index_content({}, lambda x: ("", ""))

    # Test with non-callable function
    with pytest.raises(ValueError, match="get_content_func must be callable"):
        code.generate_index_content({"test": []}, "not_a_function")


def test_count_lines():
    """Test the _count_lines helper function."""
    # Test empty content
    assert code._count_lines("") == 0

    # Test single line
    assert code._count_lines("single line") == 1

    # Test multiple lines
    assert code._count_lines("line1\nline2\nline3") == 3

    # Test with trailing newline
    assert code._count_lines("line1\nline2\n") == 3


def test_collect_files_modular_writes_package_surfaces(tmp_path: Path):
    """Directory export should emit deterministic package metadata + part files."""
    out_dir = tmp_path / "export"
    result = AnalysisResult(project_path="")

    info1 = FileInfo(absolute_path="", relative_path="src/a.py", filename="a.py")
    analysis1 = FileAnalysis(
        file_info=info1,
        content="def a():\n    return 1\n",
        annotations=AnnotationInfo(module_docstring="Alpha module."),
    )
    info2 = FileInfo(absolute_path="", relative_path="README.md", filename="README.md")
    analysis2 = FileAnalysis(
        file_info=info2,
        content="# Readme heading\n\nSome docs.\n",
    )
    result.required_files = {"a": analysis1, "readme": analysis2}

    config = LocusConfig(
        modular_export=ModularExportConfig(
            enabled=True,
            max_lines_per_file=20,
            grouping_rules=[],
            default_depth=1,
        )
    )

    files_created, index_content = code.collect_files_modular(
        result,
        str(out_dir),
        config=config,
    )

    assert files_created >= 1
    assert index_content is not None
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "tree.txt").exists()
    assert (out_dir / "description.md").exists()
    assert (out_dir / "index.txt").exists()

    part_files = sorted(path.name for path in out_dir.glob("part-*.txt"))
    assert part_files
    assert part_files == sorted(part_files)

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["format"] == "locus-llm-package-v1"
    assert manifest["totals"]["source_files"] == 2
    assert manifest["totals"]["parts"] == len(part_files)

    tree_content = (out_dir / "tree.txt").read_text(encoding="utf-8")
    assert "a.py  # Alpha module" in tree_content
    assert "README.md  # Readme heading" in tree_content

    description_content = (out_dir / "description.md").read_text(encoding="utf-8")
    assert "`src/a.py` — Alpha module" in description_content
    assert "`README.md` — Readme heading" in description_content


def test_collect_files_modular_splits_oversized_file_with_hard_ceiling(
    tmp_path: Path,
):
    """Oversized single files should be split into continuation parts <= 10k lines."""
    out_dir = tmp_path / "export_big"
    result = AnalysisResult(project_path="")

    big_lines = "\n".join(f"line_{i}" for i in range(1, 12051))
    info = FileInfo(absolute_path="", relative_path="src/big.py", filename="big.py")
    analysis = FileAnalysis(file_info=info, content=big_lines)
    result.required_files = {"big": analysis}

    config = LocusConfig(
        modular_export=ModularExportConfig(
            enabled=True,
            max_lines_per_file=5000,
            grouping_rules=[],
            default_depth=1,
        )
    )

    files_created, _ = code.collect_files_modular(result, str(out_dir), config=config)

    assert files_created >= 2
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["totals"]["parts"] >= 2
    assert all(part["line_count"] <= 10000 for part in manifest["parts"])

    part_payload = "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(out_dir.glob("part-*.txt"))
    )
    assert "(continued 2/" in part_payload


def test_collect_files_modular_renders_notebook_markdown_sidecars(
    tmp_path: Path,
    monkeypatch,
):
    """Notebook markdown rendering should emit sidecar markdown + assets paths."""
    out_dir = tmp_path / "export"
    nb_path = tmp_path / "notebooks" / "sample.ipynb"
    nb_path.parent.mkdir(parents=True)
    nb_path.write_text("{}", encoding="utf-8")

    result = AnalysisResult(project_path="")
    info = FileInfo(
        absolute_path=str(nb_path),
        relative_path="notebooks/sample.ipynb",
        filename="sample.ipynb",
    )
    analysis = FileAnalysis(
        file_info=info,
        content="# Notebook: notebooks/sample.ipynb\n\n## Cell 1 [markdown]\n# Title\n",
    )
    result.required_files = {"nb": analysis}

    config = LocusConfig(
        modular_export=ModularExportConfig(
            enabled=True,
            max_lines_per_file=20,
            grouping_rules=[],
            default_depth=1,
        )
    )

    def fake_run(command, capture_output, text, check):
        assert command[:5] == [
            code.sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
        ]
        output_dir = Path(command[-1])
        output_name = command[-3]
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{output_name}.md").write_text("# Rendered notebook\n", encoding="utf-8")
        assets_dir = output_dir / f"{output_name}_files"
        assets_dir.mkdir()
        (assets_dir / "plot.png").write_bytes(b"png")

        class Result:
            returncode = 0
            stderr = ""
            stdout = "ok"

        return Result()

    monkeypatch.setattr(code.subprocess, "run", fake_run)

    files_created, index_content = code.collect_files_modular(
        result,
        str(out_dir),
        render_notebook_markdown=True,
        config=config,
    )

    assert files_created == 1
    assert index_content is not None
    assert (out_dir / "rendered" / "notebooks" / "sample.md").exists()
    assert (out_dir / "rendered" / "notebooks" / "sample_files" / "plot.png").exists()

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["totals"]["rendered_notebooks"] == 1
    assert manifest["rendered_notebooks"] == [
        {
            "source_path": "notebooks/sample.ipynb",
            "markdown_path": "rendered/notebooks/sample.md",
            "assets_dir": "rendered/notebooks/sample_files",
        }
    ]
    assert manifest["files"][0]["rendered_markdown"] == "rendered/notebooks/sample.md"
    assert (
        manifest["files"][0]["rendered_assets_dir"]
        == "rendered/notebooks/sample_files"
    )

    description_content = (out_dir / "description.md").read_text(encoding="utf-8")
    assert "rendered/notebooks/sample.md" in description_content
    assert "rendered/notebooks/sample_files" in description_content

    index_content = (out_dir / "index.txt").read_text(encoding="utf-8")
    assert "Rendered Markdown: rendered/notebooks/sample.md" in index_content
    assert "Rendered Assets: rendered/notebooks/sample_files" in index_content
