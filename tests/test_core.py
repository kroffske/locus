import os
from pathlib import Path

from src.project_analyzer.core import orchestrator, resolver, scanner
from src.project_analyzer.models import TargetSpecifier


def test_scanner(project_structure: Path):
    """Test that the scanner correctly applies ignore and allow patterns."""
    ignore_patterns, allow_patterns = {"*.log", "build/"}, {"*.py", "*.md"}

    scanned_files = scanner.scan_directory(
        str(project_structure),
        ignore_patterns,
        allow_patterns,
    )

    # Convert to relative paths for easier assertion
    rel_files = {os.path.relpath(p, project_structure).replace("\\", "/") for p in scanned_files}

    assert "src/main.py" in rel_files
    assert "src/utils.py" in rel_files
    assert "README.md" in rel_files

    # Ignored files should not be present
    assert "app.log" not in rel_files
    assert "build/output.bin" not in rel_files
    assert ".git/config" not in rel_files

    # Non-allowed files should not be present
    assert "data/sample.csv" not in rel_files


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

    file_info_map = {path: MockFileInfo(file_map[path]["relative_path"]) for path in file_map}

    module_to_file_map = {
        "src.utils": utils_path,
        "src.models": models_path,
    }

    # Mock extract_imports to return known dependencies for main.py
    resolver.extract_imports = lambda path, rel_path: {"src.utils", "src.models"} if "main.py" in path else set()

    # Test with unlimited depth
    resolved = resolver.resolve_dependencies(initial_files, file_info_map, module_to_file_map, -1)
    assert resolved == {main_path, utils_path, models_path}

    # Test with depth=0 (no resolution)
    resolved_d0 = resolver.resolve_dependencies(initial_files, file_info_map, module_to_file_map, 0)
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
    required_rel_paths = {fi.file_info.relative_path.replace("\\", "/") for fi in result.required_files.values()}
    assert "src/main.py" in required_rel_paths
    assert "src/utils.py" in required_rel_paths
    assert "src/models.py" in required_rel_paths

    # Check that annotations were extracted from main.py
    main_abs_path = str(project_structure / "src" / "main.py")
    main_analysis = result.required_files[main_abs_path]
    assert main_analysis.annotations.module_docstring == "Module docstring for main."
    assert "main_func" in main_analysis.annotations.elements
