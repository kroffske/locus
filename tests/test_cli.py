from src.project_analyzer.cli import args
from src.project_analyzer.models import TargetSpecifier


def test_parse_target_specifier_simple_path():
    """Test parsing a simple file path."""
    spec = "src/main.py"
    result = args.parse_target_specifier(spec)
    assert isinstance(result, TargetSpecifier)
    assert result.path == "src/main.py"
    assert result.line_ranges == []


def test_parse_target_specifier_with_lines():
    """Test parsing a path with line and range specifiers."""
    spec = "src/app.py:10-15,30,45-50"
    result = args.parse_target_specifier(spec)
    assert result.path == "src/app.py"
    assert result.line_ranges == [(10, 15), (30, 30), (45, 50)]


def test_parse_target_specifier_invalid_range():
    """Test that an invalid range is handled gracefully."""
    spec = "src/app.py:50-10"
    result = args.parse_target_specifier(spec)
    # It should fall back to treating the whole string as a path
    assert result.path == "src/app.py:50-10"
    assert result.line_ranges == []


def test_argument_parser(monkeypatch):
    """Test the main argument parser with a typical command."""
    # Simulate command-line arguments
    monkeypatch.setattr(
        "sys.argv",
        [
            "project-analyzer",
            "src/",
            "-o",
            "output_dir",
            "--depth",
            "5",
            "--logs",
            "-v",
        ],
    )
    parsed_args = args.parse_arguments()
    assert parsed_args.targets == ["src/"]
    assert parsed_args.output == "output_dir"
    assert parsed_args.depth == 5
    assert parsed_args.logs is True
    assert parsed_args.verbose is True
