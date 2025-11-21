from pathlib import Path
from unittest.mock import mock_open, patch

from locus.models import FileInfo
from locus.utils import config, helpers
from locus.utils.file_cache import FileCache


def test_load_project_config(project_structure: Path):
    """Test loading of .locus/ignore and .locus/allow files."""
    ignore_patterns, allow_patterns = config.load_project_config(str(project_structure))
    assert "*.py" in allow_patterns
    assert "*.md" in allow_patterns
    assert "*.csv" in allow_patterns
    assert "build/" in ignore_patterns
    assert "*.log" in ignore_patterns


def test_is_path_ignored():
    """Test the path ignoring logic with various patterns."""
    ignore_patterns = {"build/", "*.log", "docs/internal"}

    # Test hardcoded ignores
    assert helpers.is_path_ignored(".git/config", "/root", ignore_patterns) is True
    assert (
        helpers.is_path_ignored("__pycache__/cache", "/root", ignore_patterns) is True
    )

    # Test default patterns
    assert helpers.is_path_ignored("file.pyc", "/root", ignore_patterns) is True

    # Test custom patterns
    assert helpers.is_path_ignored("build/output.txt", "/root", ignore_patterns) is True
    assert helpers.is_path_ignored("app.log", "/root", ignore_patterns) is True
    assert (
        helpers.is_path_ignored("docs/internal/api.md", "/root", ignore_patterns)
        is True
    )

    # Test paths that should NOT be ignored
    assert helpers.is_path_ignored("src/main.py", "/root", ignore_patterns) is False
    assert (
        helpers.is_path_ignored("docs/public/guide.md", "/root", ignore_patterns)
        is False
    )


def test_build_file_tree():
    """Test the construction of the nested dictionary file tree."""
    file_infos = [
        FileInfo(
            absolute_path="/proj/src/main.py",
            relative_path="src/main.py",
            filename="main.py",
        ),
        FileInfo(
            absolute_path="/proj/src/utils.py",
            relative_path="src/utils.py",
            filename="utils.py",
        ),
        FileInfo(
            absolute_path="/proj/README.md",
            relative_path="README.md",
            filename="README.md",
        ),
    ]
    tree = helpers.build_file_tree(file_infos)

    assert "README.md" in tree
    assert "src" in tree
    assert isinstance(tree["src"], dict)
    assert "main.py" in tree["src"]
    assert "utils.py" in tree["src"]
    assert tree["src"]["main.py"] is None  # Files are marked with None


def test_file_cache(tmp_path: Path):
    """Test the FileCache logic."""
    cache = FileCache()
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    # Mock open to verify it's only called once
    with patch("builtins.open", mock_open(read_data="hello world")) as mocked_open:
        # First call should read from disk
        content1 = cache.get_content(str(test_file))
        mocked_open.assert_called_once_with(
            str(test_file), "r", encoding="utf-8", errors="ignore"
        )
        assert content1 == "hello world"

        # Second call should hit the cache
        content2 = cache.get_content(str(test_file))
        mocked_open.assert_called_once()  # Still only called once
        assert content2 == "hello world"

    # Test clearing the cache
    cache.clear()
    assert not cache.content_cache
