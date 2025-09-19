"""Template content definitions for project initialization.

Loads template content from template files in the templates/ directory.
Templates support basic string substitution for customization.
"""

import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# Template file mappings
TEMPLATE_FILES = {
    "claude": "CLAUDE.md.template",
    "tests": "TESTS.md.template",
    "session": "SESSION.md.template",
    "todo": "TODO.md.template",
    "readme": "README.md.template",
    "architecture": "ARCHITECTURE.md.template",
    "mcp": "mcp.json.template",
}


def _get_templates_dir() -> Path:
    """Get the path to the templates directory."""
    return Path(__file__).parent / "templates"


def _load_template_file(template_file: str) -> str:
    """Load template content from a file.

    Args:
        template_file: Name of the template file

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template file doesn't exist
        UnicodeDecodeError: If template file can't be decoded
    """
    templates_dir = _get_templates_dir()
    template_path = templates_dir / template_file

    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode template file {template_path}: {e}")
        raise


def get_template_content(template_name: str, substitutions: Dict[str, str] = None) -> str:
    """Get template content with optional substitutions.

    Args:
        template_name: Name of the template ('claude', 'tests', 'session', 'todo', 'readme', 'architecture', 'mcp')
        substitutions: Dict of key-value pairs for string substitution

    Returns:
        Template content with substitutions applied

    Raises:
        ValueError: If template_name is not recognized
        FileNotFoundError: If template file doesn't exist
        UnicodeDecodeError: If template file can't be decoded
    """
    if template_name not in TEMPLATE_FILES:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(TEMPLATE_FILES.keys())}")

    template_file = TEMPLATE_FILES[template_name]
    content = _load_template_file(template_file)

    if substitutions:
        content = content.format(**substitutions)

    return content


def get_default_templates() -> Dict[str, str]:
    """Get the default set of template files and their names.

    Returns:
        Dict mapping filename to template name
    """
    return {
        "CLAUDE.md": "claude",
        "TESTS.md": "tests",
        "SESSION.md": "session",
        "TODO.md": "todo",
        "ARCHITECTURE.md": "architecture",
        ".mcp.json": "mcp",
    }
