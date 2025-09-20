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

    def test_get_template_content_agents(self):
        """Test AGENTS template generation."""
        content = get_template_content("agents", {"project_name": "test_project"})
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

    def test_get_template_content_architecture(self):
        """Test ARCHITECTURE template generation."""
        content = get_template_content("architecture", {"project_name": "test_project"})
        assert "# System Architecture Guide — test_project" in content
        assert "System Design Principles" in content
        assert "Why We Separate Concerns" in content

    def test_get_template_content_mcp(self):
        """Test MCP configuration template generation."""
        content = get_template_content("mcp")
        assert '"mcpServers"' in content
        assert '"sequential-thinking"' in content
        assert '"type": "stdio"' in content

    def test_get_template_content_unknown(self):
        """Test error handling for unknown template."""
        with pytest.raises(ValueError, match="Unknown template: unknown"):
            get_template_content("unknown")

    def test_get_default_templates(self):
        """Test default template mapping."""
        templates = get_default_templates()
        expected = {
            "AGENTS.md": "agents",
            "ARCHITECTURE.md": "architecture",
            "DEEPDIVE_PROMTING.md": "deepdive",
            ".mcp.json": "mcp",
            "README.md": "readme",
            "SESSION.md": "session",
            "TESTS.md": "tests",
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

    @patch("locus.init.creator.confirm", return_value=True)
    def test_prompt_user_for_overwrite_yes(self, mock_confirm):
        """Test user prompt for overwrite - yes response."""
        existing = {"CLAUDE.md", "TESTS.md"}
        result = prompt_user_for_overwrite(existing)
        assert result is True
        mock_confirm.assert_called_once()

    @patch("locus.init.creator.confirm", return_value=False)
    def test_prompt_user_for_overwrite_no(self, mock_confirm):
        """Test user prompt for overwrite - no response."""
        existing = {"CLAUDE.md"}
        result = prompt_user_for_overwrite(existing)
        assert result is False

    @patch("locus.init.creator.confirm", return_value=False)
    def test_prompt_user_for_overwrite_default_no(self, mock_confirm):
        """Test user prompt for overwrite - default (empty) response."""
        existing = {"CLAUDE.md"}
        result = prompt_user_for_overwrite(existing)
        assert result is False

    def test_prompt_user_for_overwrite_no_files(self):
        """Test user prompt when no files exist."""
        result = prompt_user_for_overwrite(set())
        assert result is True

    @patch("locus.init.creator.confirm", side_effect=[True, False, True])
    def test_prompt_user_for_each_file(self, mock_confirm):
        """Test prompting for each file individually."""
        existing = {"AGENTS.md", "TESTS.md", "SESSION.md"}
        result = prompt_user_for_each_file(existing)

        # Files are processed in sorted order: AGENTS.md, SESSION.md, TESTS.md
        # Responses: True, False, True -> AGENTS.md (yes), SESSION.md (no), TESTS.md (yes)
        # With new behavior, continues asking even after "no"
        expected = {"AGENTS.md", "TESTS.md"}
        assert result == expected
        assert mock_confirm.call_count == 3  # All files are asked about

    @patch("locus.init.creator.confirm", side_effect=KeyboardInterrupt())
    def test_prompt_user_for_each_file_interrupt(self, mock_confirm):
        """Test handling keyboard interrupt during individual prompts."""
        existing = {"AGENTS.md", "TESTS.md"}
        result = prompt_user_for_each_file(existing)
        assert result == set()

    def test_create_template_files_success(self, tmp_path: Path):
        """Test successful template file creation."""
        template_files = {"AGENTS.md": "agents", "TESTS.md": "tests"}
        substitutions = {"project_name": "test_project"}
        files_to_create = {"AGENTS.md", "TESTS.md"}

        created = create_template_files(tmp_path, template_files, substitutions, files_to_create)

        assert set(created) == {"AGENTS.md", "TESTS.md"}
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "TESTS.md").exists()

        agents_content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "test_project" in agents_content

    def test_create_template_files_subset(self, tmp_path: Path):
        """Test creating only a subset of template files."""
        template_files = {"AGENTS.md": "agents", "TESTS.md": "tests", "SESSION.md": "session"}
        files_to_create = {"AGENTS.md", "SESSION.md"}

        created = create_template_files(tmp_path, template_files, files_to_create=files_to_create)

        assert set(created) == {"AGENTS.md", "SESSION.md"}
        assert (tmp_path / "AGENTS.md").exists()
        assert not (tmp_path / "TESTS.md").exists()
        assert (tmp_path / "SESSION.md").exists()

    def test_create_template_files_unknown_template(self, tmp_path: Path):
        """Test error handling for unknown template in files_to_create."""
        template_files = {"AGENTS.md": "agents"}
        files_to_create = {"AGENTS.md", "UNKNOWN.md"}

        created = create_template_files(tmp_path, template_files, files_to_create=files_to_create)

        # Should create known file and skip unknown
        assert created == ["AGENTS.md"]
        assert (tmp_path / "AGENTS.md").exists()

    def test_create_template_files_io_error(self, tmp_path: Path):
        """Test error handling for I/O errors during file creation."""
        # Create a directory where we expect a file
        (tmp_path / "AGENTS.md").mkdir()

        template_files = {"AGENTS.md": "agents"}
        files_to_create = {"AGENTS.md"}

        with pytest.raises(InitError, match="Failed to create AGENTS.md"):
            create_template_files(tmp_path, template_files, files_to_create=files_to_create)


class TestInitProject:
    """Test the main init_project function."""

    def test_init_project_success_empty_dir(self, tmp_path: Path):
        """Test successful initialization in empty directory."""
        created = init_project(target_dir=tmp_path, project_name="test_project")

        expected_files = {"AGENTS.md", "ARCHITECTURE.md", "DEEPDIVE_PROMTING.md", ".mcp.json", "README.md", "SESSION.md", "TESTS.md", "TODO.md", "CLAUDE.md (symlink)"}
        assert set(created) == expected_files

        # Check physical files exist (excluding symlink notation)
        physical_files = {"AGENTS.md", "ARCHITECTURE.md", "DEEPDIVE_PROMTING.md", ".mcp.json", "README.md", "SESSION.md", "TESTS.md", "TODO.md", "CLAUDE.md"}
        for filename in physical_files:
            assert (tmp_path / filename).exists()

        # Check content substitution
        agents_content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "test_project" in agents_content

    def test_init_project_default_project_name(self, tmp_path: Path):
        """Test that project name defaults to directory name."""
        created = init_project(target_dir=tmp_path)

        claude_content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert tmp_path.name in claude_content

    @patch("locus.init.creator.create_claude_symlink", return_value=True)
    def test_init_project_force_overwrite(self, mock_symlink, tmp_path: Path):
        """Test force overwrite of existing files."""
        # Create existing file with different content
        (tmp_path / "AGENTS.md").write_text("old content")

        created = init_project(target_dir=tmp_path, force=True, project_name="test_project")

        assert "AGENTS.md" in created
        assert "CLAUDE.md (symlink)" in created
        agents_content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "old content" not in agents_content
        assert "test_project" in agents_content

    @patch("locus.init.creator.prompt_user_for_overwrite", return_value=True)
    @patch("locus.init.creator.create_claude_symlink", return_value=True)
    def test_init_project_user_confirms_overwrite(self, mock_symlink, mock_prompt, tmp_path: Path):
        """Test non-interactive mode with user confirming overwrite."""
        (tmp_path / "AGENTS.md").write_text("existing")

        created = init_project(target_dir=tmp_path, interactive=False)

        assert "AGENTS.md" in created
        assert "CLAUDE.md (symlink)" in created
        mock_prompt.assert_called_once()

    @patch("locus.init.creator.prompt_user_for_overwrite", return_value=False)
    def test_init_project_user_rejects_overwrite(self, mock_prompt, tmp_path: Path):
        """Test non-interactive mode with user rejecting overwrite."""
        (tmp_path / "AGENTS.md").write_text("existing")

        with pytest.raises(FileConflictError):
            init_project(target_dir=tmp_path, interactive=False)

    @patch("locus.init.creator.prompt_user_for_each_file")
    @patch("locus.init.creator.create_claude_symlink", return_value=True)
    def test_init_project_interactive_mode(self, mock_symlink, mock_prompt, tmp_path: Path):
        """Test interactive mode with individual file prompts."""
        (tmp_path / "AGENTS.md").write_text("existing")
        (tmp_path / "TESTS.md").write_text("existing")

        # User chooses to overwrite only AGENTS.md
        mock_prompt.return_value = {"AGENTS.md"}

        created = init_project(target_dir=tmp_path, interactive=True)

        # Should create AGENTS.md (overwrite), and new files, plus symlink
        # Should NOT recreate TESTS.md (user said no)
        expected_created = {"AGENTS.md", "ARCHITECTURE.md", "DEEPDIVE_PROMTING.md", ".mcp.json", "README.md", "SESSION.md", "TODO.md", "CLAUDE.md (symlink)"}
        assert set(created) == expected_created

        mock_prompt.assert_called_once_with({"AGENTS.md", "TESTS.md"})

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

        assert len(created) == 9  # Should create all default files + symlink
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "CLAUDE.md").exists()  # Symlink
        assert (tmp_path / "ARCHITECTURE.md").exists()
