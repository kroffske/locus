# TESTS.md — Minimal, Fast, Reliable

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
