import json
import os
from pathlib import Path

from locus.core import orchestrator, processor, resolver, scanner
from locus.models import FileInfo, TargetSpecifier
from locus.utils.file_cache import FileCache


def test_scanner(project_structure: Path):
    """Test that the scanner correctly applies ignore and allow patterns."""
    ignore_patterns, allow_patterns = {"*.log", "build/"}, {"*.py", "*.md"}

    scanned_files = scanner.scan_directory(
        str(project_structure),
        ignore_patterns,
        allow_patterns,
    )

    # Convert to relative paths for easier assertion
    rel_files = {
        os.path.relpath(p, project_structure).replace("\\", "/") for p in scanned_files
    }

    assert "src/main.py" in rel_files
    assert "src/utils.py" in rel_files
    assert "README.md" in rel_files

    # Ignored files should not be present
    assert "app.log" not in rel_files
    assert "build/output.bin" not in rel_files
    assert ".git/config" not in rel_files

    # Non-allowed files should not be present
    assert "data/sample.csv" not in rel_files


def test_scanner_double_star_include_matches_root_level_file(tmp_path: Path):
    """`**/*.ext` include patterns should also match root-level files."""
    project_root = tmp_path / "repo"
    project_root.mkdir()
    (project_root / "root.ipynb").write_text("{}", encoding="utf-8")
    (project_root / "nested").mkdir()
    (project_root / "nested" / "cell.ipynb").write_text("{}", encoding="utf-8")

    scanned_files = scanner.scan_directory(
        str(project_root),
        ignore_patterns=set(),
        allow_patterns={"**/*.ipynb"},
    )

    rel_files = {
        os.path.relpath(path, project_root).replace("\\", "/") for path in scanned_files
    }
    assert "root.ipynb" in rel_files
    assert "nested/cell.ipynb" in rel_files


def test_orchestrator_gitignore_directory_rule_ignores_nested_dirs(tmp_path: Path):
    """`.gitignore` directory rules like `cache/` should ignore nested cache dirs."""
    project_root = tmp_path / "repo"
    (project_root / "src" / "cache").mkdir(parents=True)
    (project_root / "src" / "keep").mkdir(parents=True)
    (project_root / ".gitignore").write_text("cache/\n", encoding="utf-8")
    (project_root / "src" / "cache" / "ignored.py").write_text(
        "print(1)\n", encoding="utf-8"
    )
    (project_root / "src" / "keep" / "kept.py").write_text(
        "print(2)\n", encoding="utf-8"
    )

    result = orchestrator.analyze(
        project_path=str(project_root),
        target_specs=[TargetSpecifier(path=".")],
        max_depth=0,
        include_patterns=["**/*.py"],
        exclude_patterns=None,
    )
    rel_paths = sorted(
        analysis.file_info.relative_path.replace("\\", "/")
        for analysis in result.required_files.values()
    )

    assert "src/keep/kept.py" in rel_paths
    assert "src/cache/ignored.py" not in rel_paths


def test_resolver(project_structure: Path):
    """Test dependency resolution."""
    # Simplified test setup for resolver
    main_path = str(project_structure / "src" / "main.py")
    utils_path = str(project_structure / "src" / "utils.py")
    models_path = str(project_structure / "src" / "models.py")

    initial_files = {main_path}

    file_map = {
        main_path: {"relative_path": "src/main.py"},
        utils_path: {"relative_path": "src/utils.py"},
        models_path: {"relative_path": "src/models.py"},
    }

    # Simplified mocks for FileInfo objects
    class MockFileInfo:
        def __init__(self, rel_path):
            self.relative_path = rel_path

    file_info_map = {
        path: MockFileInfo(file_map[path]["relative_path"]) for path in file_map
    }

    module_to_file_map = {
        "src.utils": utils_path,
        "src.models": models_path,
    }

    # Mock extract_imports to return known dependencies for main.py
    resolver.extract_imports = (
        lambda path, rel_path: {"src.utils", "src.models"}
        if "main.py" in path
        else set()
    )

    # Test with unlimited depth
    resolved = resolver.resolve_dependencies(
        initial_files, file_info_map, module_to_file_map, -1
    )
    assert resolved == {main_path, utils_path, models_path}

    # Test with depth=0 (no resolution)
    resolved_d0 = resolver.resolve_dependencies(
        initial_files, file_info_map, module_to_file_map, 0
    )
    assert resolved_d0 == {main_path}


def test_orchestrator_integration(project_structure: Path):
    """Test the main `analyze` orchestrator function."""
    target_specs = [TargetSpecifier(path=str(project_structure / "src"))]

    result = orchestrator.analyze(
        project_path=str(project_structure),
        target_specs=target_specs,
        max_depth=-1,
        include_patterns=None,
        exclude_patterns=None,
    )

    assert not result.errors
    assert "src" in result.file_tree

    # Check that required files are found
    required_rel_paths = {
        fi.file_info.relative_path.replace("\\", "/")
        for fi in result.required_files.values()
    }
    assert "src/main.py" in required_rel_paths
    assert "src/utils.py" in required_rel_paths
    assert "src/models.py" in required_rel_paths

    # Check that annotations were extracted from main.py
    main_abs_path = str(project_structure / "src" / "main.py")
    main_analysis = result.required_files[main_abs_path]
    assert main_analysis.annotations.module_docstring == "Module docstring for main."
    assert "main_func" in main_analysis.annotations.elements


def test_orchestrator_applies_include_and_exclude(project_structure: Path):
    """CLI include/exclude overrides should affect scanned/exported files."""
    target_specs = [TargetSpecifier(path=".")]

    result = orchestrator.analyze(
        project_path=str(project_structure),
        target_specs=target_specs,
        max_depth=-1,
        include_patterns=["**/*.py"],
        exclude_patterns=["**/models.py"],
    )

    required_rel_paths = {
        fi.file_info.relative_path.replace("\\", "/")
        for fi in result.required_files.values()
    }

    assert required_rel_paths
    assert all(path.endswith(".py") for path in required_rel_paths)
    assert "src/models.py" not in required_rel_paths
    assert "README.md" not in required_rel_paths


def test_orchestrator_does_not_create_locus_side_effects(tmp_path: Path):
    """Default analyze path must not create .locus/settings.json."""
    project_root = tmp_path / "repo"
    project_root.mkdir()
    src = project_root / "src"
    src.mkdir()
    (src / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (project_root / ".gitignore").write_text("dist/\n", encoding="utf-8")

    result = orchestrator.analyze(
        project_path=str(project_root),
        target_specs=[TargetSpecifier(path=".")],
        max_depth=0,
        include_patterns=None,
        exclude_patterns=None,
    )

    assert not result.errors
    assert not (project_root / ".locus").exists()
    assert not (project_root / ".locus" / "settings.json").exists()


def test_notebook_processing_defaults_without_outputs(tmp_path: Path):
    """Notebook export should include markdown/code cells and skip outputs by default."""
    nb_path = tmp_path / "sample.ipynb"
    notebook = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Title\n", "Some text"]},
            {
                "cell_type": "code",
                "source": ["print('hello')\n"],
                "outputs": [
                    {"output_type": "stream", "text": ["hello\n"]},
                    {
                        "output_type": "display_data",
                        "data": {"text/plain": ["42"], "image/png": "AAA"},
                    },
                ],
            },
        ]
    }
    nb_path.write_text(json.dumps(notebook), encoding="utf-8")

    info = FileInfo(
        absolute_path=str(nb_path),
        relative_path="sample.ipynb",
        filename="sample.ipynb",
    )
    analysis = processor.process_file(info, FileCache(), include_notebook_outputs=False)

    assert "# Notebook: sample.ipynb" in analysis.content
    assert "## Cell 1 [markdown]" in analysis.content
    assert "## Cell 2 [code]" in analysis.content
    assert "### Outputs" not in analysis.content
    assert "[media image/png" not in analysis.content


def test_notebook_processing_with_outputs_enabled(tmp_path: Path):
    """Notebook outputs/media should be included only behind explicit flag."""
    nb_path = tmp_path / "sample.ipynb"
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["x = 1\n", "x\n"],
                "outputs": [
                    {"output_type": "stream", "text": ["line1\nline2\n"]},
                    {
                        "output_type": "display_data",
                        "data": {"text/plain": ["1"], "image/png": "AABB"},
                    },
                ],
            }
        ]
    }
    nb_path.write_text(json.dumps(notebook), encoding="utf-8")

    info = FileInfo(
        absolute_path=str(nb_path),
        relative_path="sample.ipynb",
        filename="sample.ipynb",
    )
    analysis = processor.process_file(info, FileCache(), include_notebook_outputs=True)

    assert "### Outputs" in analysis.content
    assert "- Output 1 (stream)" in analysis.content
    assert "- Output 2 (display_data)" in analysis.content
    assert "[media image/png: 4 chars]" in analysis.content
