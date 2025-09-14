"""Template content definitions for project initialization.

Contains the template content for various project documentation files.
Templates support basic string substitution for customization.
"""

from typing import Dict

CLAUDE_TEMPLATE = """# AI Agent Guidelines — {project_name}

**Goal:** Fast, reliable changes with tight quality gates.

## Golden Rules
1.  **Single Responsibility**: One module for one job (scanner, resolver, processor, formatting).
2.  **Separate Concerns**: I/O and error handling at boundaries; core logic must be pure and testable.
3.  **Small Interfaces**: Pass explicit arguments; no hidden globals or entire config objects.
4.  **Stable Contracts**: Use Pydantic models for data with typed, documented fields.
5.  **Fail Fast**: Raise narrow, specific exceptions. Never use `except Exception:` or return silent defaults.

## Required Workflow
**analyze → plan → code → lint → format → test → if OK → log session & commit | else → fix**

### Commands
```bash
# 1. Lint and auto-fix
ruff check --fix src/ tests/

# 2. Format code (the project standard)
ruff format src/ tests/

# 3. Run tests
pytest -q
```

### Definition of Done
*   Lint clean and correctly formatted.
*   All tests passing (including new, minimal tests for changes).
*   A `SESSION.md` entry is appended.
*   Commit message follows Conventional Commits format (`feat:`, `fix:`, etc.).

## Core Examples

### Boundary vs Logic (keep logic pure)

```python
from pathlib import Path

class ProcessingError(Exception): ...

def load_text(path: Path) -> str:
    \"\"\"Boundary function: Handles I/O and converts low-level errors.\"\"\"
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError) as e:
        raise ProcessingError(f"Error loading {{path}}: {{e}}") from e
```

```python
import ast

def analyze_content(text: str) -> dict:
    \"\"\"Pure logic function: Assumes valid input, raises specific errors.\"\"\"
    tree = ast.parse(text)  # May raise SyntaxError, which is expected to be handled upstream.
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    return {{"functions": funcs, "classes": classes}}
```

### Small Interface (pass only what's needed)

```python
def format_tree(files: list, show_comments: bool = False) -> str:
    \"\"\"This function only needs a list of files and a boolean, not the whole config.\"\"\"
    lines = []
    for f in files:
        line = f"├─ {{f.rel_path}}"
        if show_comments and getattr(f, 'comment', None):
            line += f"  # {{f.comment}}"
        lines.append(line)

    if lines:
        lines[-1] = lines[-1].replace("├", "└", 1)
    return "\\n".join(lines)
```

## Project Context

### Architecture Flow
Add your project's main workflow here.

### Module Mapping
*   **Core Logic**: `src/{project_name}/core/`
*   **Output Generation**: `src/{project_name}/formatting/`
*   **Data Models**: `src/{project_name}/models.py`

## Contribution & Logging

*   Tests are mandatory → see **[TESTS.md](TESTS.md)**
*   Track live progress in **[TODO.md](TODO.md)** (gitignored)
*   After completion, append notes to **[SESSION.md](SESSION.md)**
"""

TESTS_TEMPLATE = """# TESTS.md — Minimal, Fast, Reliable

A dedicated, minimal guide for writing effective tests.

## Structure
```
tests/
├─ conftest.py          # Shared fixtures (e.g., temp project structure)
├─ test_core.py         # Core functionality tests
├─ test_formatting.py   # Rendering logic only (no I/O)
├─ test_cli.py          # Argument parsing and basic CLI flows
└─ test_utils.py
```

## Rules
-   **Tiny Tests**: One behavior, few assertions.
-   **Use Fixtures**: No repeated setup; use temp dirs/files.
-   **Deterministic**: No network/external state; fix random seeds.
-   **Test Edges**: Empty files, syntax errors, circular imports.

## Quick Commands
```bash
pytest -q
pytest tests/test_core.py::test_function_name -q
```

## Examples

### Basic Test Structure

```python
from pathlib import Path

def test_function_behavior(tmp_path: Path):
    # Setup
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    # Action
    result = your_function(test_file)

    # Assert
    assert result.is_valid
    assert "hello" in result.content
```

### Pure Function Testing

```python
class MockData:
    def __init__(self, name, value=None):
        self.name, self.value = name, value

def test_pure_function():
    data = [MockData("a"), MockData("b", "test")]
    result = format_data(data, include_values=True)

    assert "a" in result
    assert "b" in result
    assert "test" in result
```
"""

SESSION_TEMPLATE = """# SESSION.md — Agent Session Log (Append-Only)

## YYYY-MM-DD — Brief summary of the task
**Request:** [One-line summary of the user's goal.]
**Plan:**
- [Step 1]
- [Step 2]
**Work Notes:** [Key decisions, trade-offs, or changes to the plan.]
**Changes:**
- **Updated:** `path/to/file1.py`
- **Added:** `path/to/file2.py`
**Tests:** `pytest -q` passed successfully.
**Next:** [Optional: Note any follow-up actions needed.]
"""

TODO_TEMPLATE = """# TODO.md — Live Progress Tracker (gitignored)

This file tracks current work and is automatically gitignored.
Use it to capture tasks, blockers, and progress notes during development.

## Current Sprint

### In Progress
- [ ]

### Planned
- [ ]
- [ ]

### Completed ✓
- [x] Initial project setup

## Notes
-
-

## Blockers
- None currently
"""

README_TEMPLATE = """# {project_name}

Brief description of your project.

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m {project_name} --help
```

## Development

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest -q

# Lint and format
ruff check --fix src/ tests/
ruff format src/ tests/
```

## License

[Add your license here]
"""


def get_template_content(template_name: str, substitutions: Dict[str, str] = None) -> str:
    """Get template content with optional substitutions.

    Args:
        template_name: Name of the template ('claude', 'tests', 'session', 'todo', 'readme')
        substitutions: Dict of key-value pairs for string substitution

    Returns:
        Template content with substitutions applied

    Raises:
        ValueError: If template_name is not recognized
    """
    templates = {
        "claude": CLAUDE_TEMPLATE,
        "tests": TESTS_TEMPLATE,
        "session": SESSION_TEMPLATE,
        "todo": TODO_TEMPLATE,
        "readme": README_TEMPLATE,
    }

    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(templates.keys())}")

    content = templates[template_name]

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
    }
