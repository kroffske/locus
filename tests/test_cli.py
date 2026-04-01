from pathlib import Path
from types import SimpleNamespace

from locus.cli import args
from locus.cli import main as cli_main
from locus.models import TargetSpecifier


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


def test_argument_parser_notebook_outputs(monkeypatch):
    """Notebook output toggle is parsed as an additive analyze flag."""
    monkeypatch.setattr("sys.argv", ["locus", "analyze", "--notebook-outputs"])
    parsed_args = args.parse_arguments()
    assert parsed_args.notebook_outputs is True


def test_argument_parser_notebook_markdown(monkeypatch):
    """Notebook markdown sidecar toggle is parsed as an analyze flag."""
    monkeypatch.setattr("sys.argv", ["locus", "analyze", "--notebook-markdown"])
    parsed_args = args.parse_arguments()
    assert parsed_args.notebook_markdown is True


def test_argument_parser_stdout(monkeypatch):
    """Stdout toggle is parsed for explicit interactive mode."""
    monkeypatch.setattr("sys.argv", ["locus", "analyze", "--stdout"])
    parsed_args = args.parse_arguments()
    assert parsed_args.stdout is True


def test_collection_mode_without_output_uses_default_local_path(
    monkeypatch,
    tmp_path: Path,
):
    """Without -o, analyze writes a package to .local/locus-* by default."""
    captured = {}

    def fake_analyze(**kwargs):
        return SimpleNamespace(
            errors=[],
            required_files={},
            file_tree={},
            project_readme_content=None,
            similarity=None,
            config_root_path=str(tmp_path),
        )

    def fake_collect(result, output_path, *_args):
        captured["output_path"] = output_path
        return (0, None)

    monkeypatch.setattr(cli_main, "analyze", fake_analyze)
    monkeypatch.setattr(
        cli_main,
        "_default_collection_output_path",
        lambda project_root: str(Path(project_root) / ".local" / "locus-test"),
    )
    monkeypatch.setattr(cli_main.code, "collect_files_modular", fake_collect)
    monkeypatch.setattr("sys.argv", ["locus", "analyze"])
    parsed_args = args.parse_arguments()

    exit_code = cli_main.handle_analyze_command(parsed_args)

    assert exit_code == 0
    assert captured["output_path"] == str(tmp_path / ".local" / "locus-test")


def test_stdout_mode_without_output_skips_default_collection(
    monkeypatch,
):
    """`--stdout` keeps the old interactive flow and does not call collection export."""
    called = {"collect_called": False}

    def fake_analyze(**kwargs):
        return SimpleNamespace(
            errors=[],
            required_files={},
            file_tree={},
            project_readme_content=None,
            similarity=None,
            config_root_path=".",
        )

    def fake_collect(*_args, **_kwargs):
        called["collect_called"] = True
        return (0, None)

    monkeypatch.setattr(cli_main, "analyze", fake_analyze)
    monkeypatch.setattr(cli_main.code, "collect_files_modular", fake_collect)
    monkeypatch.setattr("sys.argv", ["locus", "analyze", "--stdout"])
    parsed_args = args.parse_arguments()

    exit_code = cli_main.handle_analyze_command(parsed_args)

    assert exit_code == 0
    assert called["collect_called"] is False


def test_collection_mode_passes_notebook_markdown_flag(
    monkeypatch,
    tmp_path: Path,
):
    """Notebook markdown rendering stays opt-in and reaches directory export."""
    captured = {}

    def fake_analyze(**kwargs):
        return SimpleNamespace(
            errors=[],
            required_files={},
            file_tree={},
            project_readme_content=None,
            similarity=None,
            config_root_path=str(tmp_path),
        )

    def fake_collect(_result, _output_path, *_args):
        captured["render_notebook_markdown"] = _args[2]
        return (0, None)

    monkeypatch.setattr(cli_main, "analyze", fake_analyze)
    monkeypatch.setattr(
        cli_main,
        "_default_collection_output_path",
        lambda project_root: str(Path(project_root) / ".local" / "locus-test"),
    )
    monkeypatch.setattr(cli_main.code, "collect_files_modular", fake_collect)
    monkeypatch.setattr("sys.argv", ["locus", "analyze", "--notebook-markdown"])
    parsed_args = args.parse_arguments()

    exit_code = cli_main.handle_analyze_command(parsed_args)

    assert exit_code == 0
    assert captured["render_notebook_markdown"] is True


def test_collection_mode_for_existing_directory_with_extension(
    monkeypatch,
    tmp_path: Path,
):
    """Existing directories should use collection mode even if path has a suffix."""
    output_dir = tmp_path / "existing.export"
    output_dir.mkdir()

    captured = {}

    def fake_analyze(**kwargs):
        return SimpleNamespace(
            errors=[],
            required_files={},
            file_tree={},
            project_readme_content=None,
            similarity=None,
        )

    def fake_collect(result, output_path, *_args):
        captured["output_path"] = output_path
        return (0, None)

    monkeypatch.setattr(cli_main, "analyze", fake_analyze)
    monkeypatch.setattr(cli_main.code, "collect_files_modular", fake_collect)
    monkeypatch.setattr("sys.argv", ["locus", "analyze", "-o", str(output_dir)])
    parsed_args = args.parse_arguments()

    exit_code = cli_main.handle_analyze_command(parsed_args)

    assert exit_code == 0
    assert captured["output_path"] == str(output_dir)


def test_collection_mode_rejects_existing_file_path(
    monkeypatch,
    tmp_path: Path,
):
    """Directory export path without extension must fail if path exists as file."""
    output_path = tmp_path / "existing_output"
    output_path.write_text("already here", encoding="utf-8")

    def fake_analyze(**kwargs):
        return SimpleNamespace(
            errors=[],
            required_files={},
            file_tree={},
            project_readme_content=None,
            similarity=None,
        )

    called = {"collect_called": False}

    def fake_collect(*_args, **_kwargs):
        called["collect_called"] = True
        return (0, None)

    monkeypatch.setattr(cli_main, "analyze", fake_analyze)
    monkeypatch.setattr(cli_main.code, "collect_files_modular", fake_collect)
    monkeypatch.setattr("sys.argv", ["locus", "analyze", "-o", str(output_path)])
    parsed_args = args.parse_arguments()

    exit_code = cli_main.handle_analyze_command(parsed_args)

    assert exit_code == 1
    assert called["collect_called"] is False


def test_stdout_and_output_are_mutually_exclusive(
    monkeypatch,
):
    """Explicit stdout mode should reject simultaneous --output usage."""

    monkeypatch.setattr("sys.argv", ["locus", "analyze", "--stdout", "-o", "out.md"])
    parsed_args = args.parse_arguments()

    exit_code = cli_main.handle_analyze_command(parsed_args)

    assert exit_code == 1
