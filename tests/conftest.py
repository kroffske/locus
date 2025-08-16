import pytest
from pathlib import Path

@pytest.fixture
def project_structure(tmp_path: Path):
    """
    Creates a temporary, realistic project directory structure for testing.
    Returns the root path of the created project.
    """
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # --- Create config files ---
    (project_root / ".claudeallow").write_text("*.py\n*.md\n*.csv\n")
    (project_root / ".claudeignore").write_text("build/\n*.log\n")

    # --- Create source directory ---
    src_dir = project_root / "src"
    src_dir.mkdir()

    (src_dir / "main.py").write_text(
        '"""Module docstring for main."""\n'
        'from . import utils\n'
        'from .models import User\n\n'
        'def main_func():\n'
        '    """A simple function."""\n'
        '    pass\n'
    )
    (src_dir / "utils.py").write_text(
        '# Header comment for utils.\n'
        'def helper_func():\n'
        '    pass\n'
    )
    (src_dir / "models.py").write_text(
        'class User:\n'
        '    pass\n'
    )
    (src_dir / "__init__.py").touch()
    
    # --- Create ignored files and directories ---
    (project_root / "README.md").write_text("# Test Project")
    (project_root / "app.log").write_text("log entry")
    build_dir = project_root / "build"
    build_dir.mkdir()
    (build_dir / "output.bin").touch()
    
    # --- Create data files ---
    data_dir = project_root / "data"
    data_dir.mkdir()
    (data_dir / "sample.csv").write_text("id,name\n1,test\n")

    # --- Create .git directory (should always be ignored) ---
    git_dir = project_root / ".git"
    git_dir.mkdir()
    (git_dir / "config").touch()
    
    return project_root

