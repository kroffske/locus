"""Initialize project with template files.

This module provides functionality to create template markdown files
(CLAUDE.md, TESTS.md, SESSION.md, etc.) in a project directory.
"""

from .creator import init_project

__all__ = ["init_project"]
