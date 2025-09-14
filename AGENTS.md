# AI Agent Guidelines — locus

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
    """Boundary function: Handles I/O and converts low-level errors."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError) as e:
        raise ProcessingError(f"Error loading {path}: {e}") from e
```

```python
import ast

def analyze_content(text: str) -> dict:
    """Pure logic function: Assumes valid input, raises specific errors."""
    tree = ast.parse(text)  # May raise SyntaxError, which is expected to be handled upstream.
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    return {"functions": funcs, "classes": classes}
```

### Small Interface (pass only what's needed)

```python
def format_tree(files: list, show_comments: bool = False) -> str:
    """This function only needs a list of files and a boolean, not the whole config."""
    lines = []
    for f in files:
        line = f"├─ {f.rel_path}"
        if show_comments and getattr(f, 'comment', None):
            line += f"  # {f.comment}"
        lines.append(line)

    if lines:
        lines[-1] = lines[-1].replace("├", "└", 1)
    return "\n".join(lines)
```

## Project Context

### Architecture Flow
Add your project's main workflow here.

### Module Mapping
*   **Core Logic**: `src/locus/core/`
*   **Output Generation**: `src/locus/formatting/`
*   **Data Models**: `src/locus/models.py`

## Contribution & Logging

*   Tests are mandatory → see **[TESTS.md](TESTS.md)**
*   Track live progress in **[TODO.md](TODO.md)** (gitignored)
*   After completion, append notes to **[SESSION.md](SESSION.md)**
