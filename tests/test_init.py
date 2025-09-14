"""Tests for the init module functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest

from locus.init.creator import (
    FileConflictError,
    InitError,
    check_existing_files,
    create_template_files,
    init_project,
    prompt_user_for_each_file,
    prompt_user_for_overwrite,
)
from locus.init.templates import get_default_templates, get_template_content


class TestTemplates:
    """Test template content generation."""

    def test_get_template_content_claude(self):
        """Test CLAUDE template generation."""
        content = get_template_content("claude", {"project_name": "test_project"})
        assert "# AI Agent Guidelines — test_project" in content
        assert "**Goal:** Fast, reliable changes with tight quality gates." in content
        assert "pytest -q" in content

    def test_get_template_content_tests(self):
        """Test TESTS template generation."""
        content = get_template_content("tests")
        assert "# TESTS.md — Minimal, Fast, Reliable" in content
        assert "pytest -q" in content
        assert "tmp_path: Path" in content

    def test_get_template_content_session(self):
        """Test SESSION template generation."""
        content = get_template_content("session")
        assert "# SESSION.md — Agent Session Log (Append-Only)" in content
        assert "**Request:**" in content
        assert "**Plan:**" in content

    def test_get_template_content_todo(self):
        """Test TODO template generation."""
        content = get_template_content("todo")
        assert "# TODO.md — Live Progress Tracker (gitignored)" in content
        assert "## Current Sprint" in content
        assert "### In Progress" in content

    def test_get_template_content_readme(self):
        """Test README template generation."""
        content = get_template_content("readme", {"project_name": "my_project"})
        assert "# my_project" in content
        assert "pip install -e ." in content
        assert "python -m my_project --help" in content

    def test_get_template_content_unknown(self):
        """Test error handling for unknown template."""
        with pytest.raises(ValueError, match="Unknown template: unknown"):
            get_template_content("unknown")

    def test_get_default_templates(self):
        """Test default template mapping."""
        templates = get_default_templates()
        expected = {
            "CLAUDE.md": "claude",
            "TESTS.md": "tests",
            "SESSION.md": "session",
            "TODO.md": "todo",
        }
        assert templates == expected


class TestCreatorLogic:
    """Test pure logic functions in creator module."""

    def test_check_existing_files_none_exist(self, tmp_path: Path):
        """Test checking for existing files when none exist."""
        template_files = {"CLAUDE.md": "claude", "TESTS.md": "tests"}
        existing = check_existing_files(tmp_path, template_files)
        assert existing == set()

    def test_check_existing_files_some_exist(self, tmp_path: Path):
        """Test checking for existing files when some exist."""
        (tmp_path / "CLAUDE.md").write_text("existing content")
        template_files = {"CLAUDE.md": "claude", "TESTS.md": "tests", "SESSION.md": "session"}

        existing = check_existing_files(tmp_path, template_files)
        assert existing == {"CLAUDE.md"}

    def test_check_existing_files_all_exist(self, tmp_path: Path):
        """Test checking for existing files when all exist."""
        (tmp_path / "CLAUDE.md").write_text("existing")
        (tmp_path / "TESTS.md").write_text("existing")
        template_files = {"CLAUDE.md": "claude", "TESTS.md": "tests"}

        existing = check_existing_files(tmp_path, template_files)
        assert existing == {"CLAUDE.md", "TESTS.md"}

    @patch("builtins.input", return_value="y")
    def test_prompt_user_for_overwrite_yes(self, mock_input):
        """Test user prompt for overwrite - yes response."""
        existing = {"CLAUDE.md", "TESTS.md"}
        result = prompt_user_for_overwrite(existing)
        assert result is True
        mock_input.assert_called_once()

    @patch("builtins.input", return_value="n")
    def test_prompt_user_for_overwrite_no(self, mock_input):
        """Test user prompt for overwrite - no response."""
        existing = {"CLAUDE.md"}
        result = prompt_user_for_overwrite(existing)
        assert result is False

    @patch("builtins.input", return_value="")
    def test_prompt_user_for_overwrite_default_no(self, mock_input):
        """Test user prompt for overwrite - default (empty) response."""
        existing = {"CLAUDE.md"}
        result = prompt_user_for_overwrite(existing)
        assert result is False

    def test_prompt_user_for_overwrite_no_files(self):
        """Test user prompt when no files exist."""
        result = prompt_user_for_overwrite(set())
        assert result is True

    @patch("builtins.input", side_effect=["y", "n", "yes"])
    def test_prompt_user_for_each_file(self, mock_input):
        """Test prompting for each file individually."""
        existing = {"CLAUDE.md", "TESTS.md", "SESSION.md"}
        result = prompt_user_for_each_file(existing)

        # Files are processed in sorted order: CLAUDE.md, SESSION.md, TESTS.md
        # Responses: y, n, yes -> CLAUDE.md (y=yes), SESSION.md (n=no), TESTS.md (yes=yes)
        expected = {"CLAUDE.md", "TESTS.md"}
        assert result == expected
        assert mock_input.call_count == 3

    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_prompt_user_for_each_file_interrupt(self, mock_input):
        """Test handling keyboard interrupt during individual prompts."""
        existing = {"CLAUDE.md", "TESTS.md"}
        result = prompt_user_for_each_file(existing)
        assert result == set()

    def test_create_template_files_success(self, tmp_path: Path):
        """Test successful template file creation."""
        template_files = {"CLAUDE.md": "claude", "TESTS.md": "tests"}
        substitutions = {"project_name": "test_project"}
        files_to_create = {"CLAUDE.md", "TESTS.md"}

        created = create_template_files(tmp_path, template_files, substitutions, files_to_create)

        assert set(created) == {"CLAUDE.md", "TESTS.md"}
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / "TESTS.md").exists()

        claude_content = (tmp_path / "CLAUDE.md").read_text()
        assert "test_project" in claude_content

    def test_create_template_files_subset(self, tmp_path: Path):
        """Test creating only a subset of template files."""
        template_files = {"CLAUDE.md": "claude", "TESTS.md": "tests", "SESSION.md": "session"}
        files_to_create = {"CLAUDE.md", "SESSION.md"}

        created = create_template_files(tmp_path, template_files, files_to_create=files_to_create)

        assert set(created) == {"CLAUDE.md", "SESSION.md"}
        assert (tmp_path / "CLAUDE.md").exists()
        assert not (tmp_path / "TESTS.md").exists()
        assert (tmp_path / "SESSION.md").exists()

    def test_create_template_files_unknown_template(self, tmp_path: Path):
        """Test error handling for unknown template in files_to_create."""
        template_files = {"CLAUDE.md": "claude"}
        files_to_create = {"CLAUDE.md", "UNKNOWN.md"}

        created = create_template_files(tmp_path, template_files, files_to_create=files_to_create)

        # Should create known file and skip unknown
        assert created == ["CLAUDE.md"]
        assert (tmp_path / "CLAUDE.md").exists()

    def test_create_template_files_io_error(self, tmp_path: Path):
        """Test error handling for I/O errors during file creation."""
        # Create a directory where we expect a file
        (tmp_path / "CLAUDE.md").mkdir()

        template_files = {"CLAUDE.md": "claude"}
        files_to_create = {"CLAUDE.md"}

        with pytest.raises(InitError, match="Failed to create CLAUDE.md"):
            create_template_files(tmp_path, template_files, files_to_create=files_to_create)


class TestInitProject:
    """Test the main init_project function."""

    def test_init_project_success_empty_dir(self, tmp_path: Path):
        """Test successful initialization in empty directory."""
        created = init_project(target_dir=tmp_path, project_name="test_project")

        expected_files = {"CLAUDE.md", "TESTS.md", "SESSION.md", "TODO.md"}
        assert set(created) == expected_files

        for filename in expected_files:
            assert (tmp_path / filename).exists()

        # Check content substitution
        claude_content = (tmp_path / "CLAUDE.md").read_text()
        assert "test_project" in claude_content

    def test_init_project_default_project_name(self, tmp_path: Path):
        """Test that project name defaults to directory name."""
        created = init_project(target_dir=tmp_path)

        claude_content = (tmp_path / "CLAUDE.md").read_text()
        assert tmp_path.name in claude_content

    def test_init_project_force_overwrite(self, tmp_path: Path):
        """Test force overwrite of existing files."""
        # Create existing file with different content
        (tmp_path / "CLAUDE.md").write_text("old content")

        created = init_project(target_dir=tmp_path, force=True, project_name="test_project")

        assert "CLAUDE.md" in created
        claude_content = (tmp_path / "CLAUDE.md").read_text()
        assert "old content" not in claude_content
        assert "test_project" in claude_content

    @patch("locus.init.creator.prompt_user_for_overwrite", return_value=True)
    def test_init_project_user_confirms_overwrite(self, mock_prompt, tmp_path: Path):
        """Test non-interactive mode with user confirming overwrite."""
        (tmp_path / "CLAUDE.md").write_text("existing")

        created = init_project(target_dir=tmp_path, interactive=False)

        assert "CLAUDE.md" in created
        mock_prompt.assert_called_once()

    @patch("locus.init.creator.prompt_user_for_overwrite", return_value=False)
    def test_init_project_user_rejects_overwrite(self, mock_prompt, tmp_path: Path):
        """Test non-interactive mode with user rejecting overwrite."""
        (tmp_path / "CLAUDE.md").write_text("existing")

        with pytest.raises(FileConflictError):
            init_project(target_dir=tmp_path, interactive=False)

    @patch("locus.init.creator.prompt_user_for_each_file")
    def test_init_project_interactive_mode(self, mock_prompt, tmp_path: Path):
        """Test interactive mode with individual file prompts."""
        (tmp_path / "CLAUDE.md").write_text("existing")
        (tmp_path / "TESTS.md").write_text("existing")

        # User chooses to overwrite only CLAUDE.md
        mock_prompt.return_value = {"CLAUDE.md"}

        created = init_project(target_dir=tmp_path, interactive=True)

        # Should create CLAUDE.md (overwrite), SESSION.md, TODO.md (new)
        # Should NOT recreate TESTS.md (user said no)
        expected_created = {"CLAUDE.md", "SESSION.md", "TODO.md"}
        assert set(created) == expected_created

        mock_prompt.assert_called_once_with({"CLAUDE.md", "TESTS.md"})

    def test_init_project_nonexistent_directory(self):
        """Test error handling for nonexistent target directory."""
        nonexistent = Path("/nonexistent/path")

        with pytest.raises(InitError, match="Target directory does not exist"):
            init_project(target_dir=nonexistent)

    def test_init_project_file_instead_of_directory(self, tmp_path: Path):
        """Test error handling when target path is a file, not directory."""
        file_path = tmp_path / "somefile.txt"
        file_path.write_text("content")

        with pytest.raises(InitError, match="Target path is not a directory"):
            init_project(target_dir=file_path)

    def test_init_project_current_directory_default(self, tmp_path: Path, monkeypatch):
        """Test that None target_dir defaults to current working directory."""
        monkeypatch.chdir(tmp_path)

        created = init_project(target_dir=None, project_name="test_project")

        assert len(created) == 4  # Should create all default files
        assert (tmp_path / "CLAUDE.md").exists()
